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
from typing import Callable, Generator

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.ai.engine import classify
from backend.classifier.rule_engine import classify_layer2
from backend.config import LABELS, API_CALL_DELAY
from backend.gmail.connector import fetch_all_message_ids, get_message_details
from backend.labels.manager import apply_label, ensure_labels_exist

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------
# {
#   "msg_id"          : str,
#   "sender"          : str,
#   "subject"         : str,
#   "ml_label"        : "spam" | "ham" | "unknown",
#   "primary_label"   : str,   # one of the 11 labels
#   "secondary_label" : str | None,
#   "confidence"      : float,
#   "matched_rule"    : str,
#   "layer"           : str,
#   "status"          : "labeled" | "error",
# }

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
    # Each thread gets its own service to avoid httplib2 SSL race conditions
    service = _get_thread_service(credentials)
    # 1. Fetch message details
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
    else:
        logger.error("No label ID found for primary label '%s'.", primary_label)

    # 5. Log the decision — sanitize subject to ASCII to avoid emoji crash on Windows
    sec_str = f" + {secondary_label}" if secondary_label else ""
    safe_subject = subject[:40].encode("ascii", errors="replace").decode("ascii")
    logger.info(
        "[%s] %s -> %s%s (%.0f%%) | rule=%s",
        layer,
        safe_subject,
        primary_label,
        sec_str,
        confidence * 100,
        matched_rule,
    )

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
    }


# ---------------------------------------------------------------------------
# Main scan orchestrator
# ---------------------------------------------------------------------------

def run_scan(
    service,
    on_start: Callable[[int], None] | None = None,
    on_progress: Callable[[int, int], None] | None = None,
) -> Generator[dict, None, None]:
    """
    Run a complete inbox scan and yield a result dict for each email.

    Parameters
    ----------
    service : Gmail API service object
    on_start : callable(total: int) | None
    on_progress : callable(current: int, total: int) | None

    Yields
    ------
    dict  — result for each processed email
    """
    # ------------------------------------------------------------------
    # Step 1: Ensure all 11 labels exist in Gmail
    # ------------------------------------------------------------------
    logger.info("Ensuring all labels exist in Gmail...")
    label_ids_map = ensure_labels_exist(service)

    if not label_ids_map:
        msg = (
            "Failed to create or access Gmail labels. "
            "Please ensure the **Gmail API** is enabled in your Google Cloud Console "
            "(https://console.cloud.google.com/apis/library/gmail.googleapis.com)."
        )
        logger.error(msg)
        raise RuntimeError(msg)

    all_managed_label_ids = list(label_ids_map.values())

    # ------------------------------------------------------------------
    # Step 2: Build Gmail skip-query for all 11 managed labels
    # For custom labels: -label:"name". For SPAM system label: -in:spam
    # ------------------------------------------------------------------
    from backend.labels.manager import _SYSTEM_LABEL_ALIASES
    _SYSTEM_SKIP_SYNTAX: dict[str, str] = {"Spam": "-in:spam"}
    exclusion_parts = []
    for name in LABELS:
        if name in _SYSTEM_SKIP_SYNTAX:
            exclusion_parts.append(_SYSTEM_SKIP_SYNTAX[name])
        else:
            exclusion_parts.append(f'-label:"{name}"')
    exclusion_query = " ".join(exclusion_parts)
    logger.info("Gmail search query: %s", exclusion_query)

    # ------------------------------------------------------------------
    # Step 3: Collect all matching message IDs (paginated)
    # ------------------------------------------------------------------
    logger.info("Collecting message IDs from Gmail...")
    message_ids = []
    for count, msg_id in enumerate(fetch_all_message_ids(service, query=exclusion_query), 1):
        message_ids.append(msg_id)
        if count % 100 == 0 and on_progress:
            on_progress(0, count)

    total = len(message_ids)
    logger.info("Found %d unlabeled messages to process.", total)

    if on_start:
        on_start(total)

    if total == 0:
        logger.info("All messages already labeled. Nothing to do.")
        return

    # ------------------------------------------------------------------
    # Step 4: Process concurrently (15 workers, rate-limited)
    # Each worker gets its own Gmail service instance (thread-safe).
    # ------------------------------------------------------------------
    # Extract credentials from the main service for worker thread use.
    # google-api-python-client stores credentials on service._http.credentials
    try:
        credentials = service._http.credentials
    except AttributeError:
        # Fallback: some auth setups store it differently
        credentials = getattr(service, "_credentials", None)
    
    if not credentials:
        raise RuntimeError("Could not extract credentials from Gmail service for worker threads.")

    processed_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_to_msg_id = {
            executor.submit(
                _process_single_email,
                credentials, msg_id, label_ids_map, all_managed_label_ids
            ): msg_id
            for msg_id in message_ids
        }

        for future in concurrent.futures.as_completed(future_to_msg_id):
            processed_count += 1
            if on_progress:
                on_progress(processed_count, total)

            try:
                result = future.result()
                yield result
            except Exception as exc:
                msg_id = future_to_msg_id[future]
                logger.error("Message %s generated an exception: %s", msg_id, exc)
                yield {
                    "msg_id": msg_id,
                    "sender": "Unknown",
                    "subject": "Unknown",
                    "ml_label": "unknown",
                    "primary_label": "Needs Review",
                    "secondary_label": None,
                    "confidence": 0.0,
                    "matched_rule": "exception",
                    "layer": "error",
                    "status": "error",
                }
