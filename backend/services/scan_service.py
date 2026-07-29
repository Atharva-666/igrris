"""
scan_service.py — Orchestrates the complete email scan pipeline.

Full workflow per scan:
  1. Ensure all labels exist in Gmail (idempotent)
  2. Build Gmail search query to SKIP already-labeled emails
  3. Collect all matching message IDs via paginated API calls
  4. For each message (concurrent):
       a. Fetch full message details (subject, sender, body)
       b. Layer 1: TF-IDF + LinearSVC ML classification (spam/ham + confidence)
       c. Layer 2: Rule engine for granular category (Phishing, Security, etc.)
       d. Apply the primary label + optional secondary label
  5. Yield each result so the UI can show live progress

Label precedence (configured in backend/classifier/rules_config.yaml):
  Phishing > Spam > Security > Needs Review > Banking > Orders >
  Work > Education > Promotions > Personal > Trusted
"""

import concurrent.futures
import logging
import threading
import time
from typing import Generator
import json

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.ai.engine import classify
from backend.classifier.rule_engine import classify_layer2
from backend.config import LABELS, API_CALL_DELAY
from backend.gmail.connector import fetch_all_message_ids, get_message_details
from backend.labels.manager import apply_label, ensure_labels_exist

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rate Limiting
# Google allows 250 units/sec. Each email = ~10 units. Max ~22 emails/sec.
# ---------------------------------------------------------------------------
_rate_limit_lock = threading.Lock()
_last_api_call = 0.0
_MIN_DELAY = max(0.045, API_CALL_DELAY)


def _wait_for_rate_limit() -> None:
    global _last_api_call
    with _rate_limit_lock:
        now = time.time()
        elapsed = now - _last_api_call
        if elapsed < _MIN_DELAY:
            time.sleep(_MIN_DELAY - elapsed)
        _last_api_call = time.time()


# ---------------------------------------------------------------------------
# Thread-local Service Factory
# httplib2 (used by google-api-python-client) is NOT thread-safe.
# Each thread must have its own service instance with its own HTTP connection.
# ---------------------------------------------------------------------------
_thread_local = threading.local()


def _get_thread_service(credentials):
    """Return a thread-local Gmail API service object."""
    if not hasattr(_thread_local, "service"):
        _thread_local.service = build(
            "gmail", "v1", credentials=credentials, cache_discovery=False
        )
    return _thread_local.service


# ---------------------------------------------------------------------------
# Single Email Processor (Worker thread)
# ---------------------------------------------------------------------------
def _process_single_email(
    credentials,
    msg_id: str,
    label_ids_map: dict[str, str],
    all_managed_label_ids: list[str],
) -> dict:
    """Process one email: fetch → ML classify → rule classify → apply labels."""
    service = _get_thread_service(credentials)
    
    _wait_for_rate_limit()
    details = get_message_details(service, msg_id)
    if not details:
        logger.warning("Skipping message %s (could not fetch details).", msg_id)
        return {
            "msg_id": msg_id,
            "sender": "Unknown",
            "subject": "Unknown",
            "ml_label": "unknown",
            "primary_label": "Needs Review",
            "secondary_label": None,
            "confidence": 0.0,
            "matched_rule": "fetch_failed",
            "layer": "error",
            "status": "error",
        }

    subject = details["subject"]
    sender = details["sender"]
    body = details["body"]

    # 2. Layer 1: ML classification
    email_text = f"{subject}\n{body}"[:9900]
    ml_result = classify(email_text)
    ml_label = ml_result["label"]
    confidence = ml_result["confidence"]

    # 3. Layer 2: Rule engine
    rule_result = classify_layer2(
        subject=subject,
        sender=sender,
        body=body,
        ml_label=ml_label,
        ml_confidence=confidence,
    )

    primary_label = rule_result["primary_label"]
    secondary_label = rule_result["secondary_label"]
    matched_rule = rule_result["matched_rule"]
    layer = rule_result["layer"]

    # 4. Apply Gmail labels
    primary_label_id = label_ids_map.get(primary_label)
    secondary_label_id = label_ids_map.get(secondary_label) if secondary_label else None

    status = "error"
    if primary_label_id:
        _wait_for_rate_limit()
        success = apply_label(
            service,
            msg_id,
            primary_label_id,
            details["label_ids"],
            all_managed_label_ids,
            secondary_label_id=secondary_label_id,
        )
        status = "labeled" if success else "error"

    # 5. Log the decision
    sec_str = f" + {secondary_label}" if secondary_label else ""
    safe_subject = subject[:40].encode("ascii", errors="replace").decode("ascii")
    
    return {
        "msg_id": msg_id,
        "sender": sender,
        "subject": subject,
        "ml_label": ml_label,
        "primary_label": primary_label,
        "secondary_label": secondary_label,
        "confidence": confidence,
        "matched_rule": matched_rule,
        "layer": layer,
        "status": status,
        "log_msg": f"[{layer}] {safe_subject} -> {primary_label}{sec_str} ({confidence * 100:.0f}%)"
    }


# ---------------------------------------------------------------------------
# Main scan orchestrator
# ---------------------------------------------------------------------------

def run_scan(
    service,
    cancel_event: threading.Event | None = None,
) -> Generator[str, None, None]:
    """
    Run a complete inbox scan and yield JSON strings (SSE format events).
    """
    
    def emit(event_type: str, data: dict):
        # Format as SSE event string
        payload = json.dumps(data)
        return f"event: {event_type}\ndata: {payload}\n\n"

    # 1. Ensure Labels
    yield emit("log", {"message": "Ensuring all labels exist in Gmail..."})
    try:
        label_ids_map = ensure_labels_exist(service)
    except Exception as e:
        yield emit("log", {"message": f"Failed to verify labels: {e}"})
        yield emit("error", {"message": str(e)})
        return

    if not label_ids_map:
        msg = "Failed to create or access Gmail labels. Check your API scopes."
        yield emit("error", {"message": msg})
        return

    all_managed_label_ids = list(label_ids_map.values())

    # 2. Build Query
    from backend.labels.manager import _SYSTEM_LABEL_ALIASES
    _SYSTEM_SKIP_SYNTAX = {"Spam": "-in:spam"}
    exclusion_parts = []
    for name in LABELS:
        if name in _SYSTEM_SKIP_SYNTAX:
            exclusion_parts.append(_SYSTEM_SKIP_SYNTAX[name])
        else:
            exclusion_parts.append(f'-label:"{name}"')
    exclusion_query = " ".join(exclusion_parts)
    
    yield emit("log", {"message": f"Built Gmail search query to skip already-labeled items."})

    # 3. Collect Message IDs
    yield emit("log", {"message": "Collecting message IDs from Gmail..."})
    message_ids = []
    try:
        for count, msg_id in enumerate(fetch_all_message_ids(service, query=exclusion_query), 1):
            if cancel_event and cancel_event.is_set():
                yield emit("log", {"message": "Scan cancelled by user during ID collection."})
                yield emit("done", {"status": "cancelled"})
                return
                
            message_ids.append(msg_id)
            if count % 50 == 0:
                yield emit("log", {"message": f"Found {count} unlabeled messages..."})
    except Exception as e:
        yield emit("error", {"message": f"Error fetching message IDs: {e}"})
        return

    total = len(message_ids)
    yield emit("log", {"message": f"Found {total} unlabeled messages to process."})
    yield emit("start", {"total": total})

    if total == 0:
        yield emit("log", {"message": "All messages already labeled. Nothing to do."})
        yield emit("done", {"status": "complete"})
        return

    # 4. Process Concurrently
    try:
        credentials = service._http.credentials
    except AttributeError:
        credentials = getattr(service, "_credentials", None)
    
    if not credentials:
        yield emit("error", {"message": "Could not extract credentials from Gmail service."})
        return

    processed_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_msg_id = {
            executor.submit(
                _process_single_email,
                credentials, msg_id, label_ids_map, all_managed_label_ids
            ): msg_id
            for msg_id in message_ids
        }

        for future in concurrent.futures.as_completed(future_to_msg_id):
            if cancel_event and cancel_event.is_set():
                # Try to cancel remaining futures
                for f in future_to_msg_id:
                    f.cancel()
                yield emit("log", {"message": "Scan cancelled by user. Shutting down workers..."})
                yield emit("done", {"status": "cancelled"})
                return

            processed_count += 1
            try:
                result = future.result()
                log_msg = result.pop("log_msg")
                
                yield emit("result", result)
                yield emit("log", {"message": log_msg})
                yield emit("progress", {"current": processed_count, "total": total})
                
            except Exception as exc:
                msg_id = future_to_msg_id[future]
                yield emit("log", {"message": f"Error processing message {msg_id}: {exc}"})
                
    yield emit("log", {"message": "Scan complete!"})
    yield emit("done", {"status": "complete"})
