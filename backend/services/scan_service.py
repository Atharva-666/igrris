"""
scan_service.py — Orchestrates the complete email scan pipeline.

Full workflow per scan:
  1. Ensure all AI labels exist in Gmail (idempotent)
  2. Build a Gmail search query to SKIP already-labeled emails
     (first scan: all messages matched; subsequent scans: only new ones)
  3. Collect all matching message IDs via paginated API calls
  4. For each message:
       a. Fetch full message details (subject, sender, body)
       b. Classify with the existing TF-IDF + LinearSVC engine
       c. Apply the appropriate AI label (add new, remove old)
  5. Yield each result so the UI can show live progress

Skipping already-labeled emails:
  Gmail search supports negative label queries:
    -label:"AI Safe" -label:"AI Spam" -label:"AI Needs Review"
  This returns only messages that have NONE of our AI labels,
  making subsequent scans very fast.
"""

import logging
import time
from typing import Callable, Generator

from googleapiclient.errors import HttpError

from backend.ai.engine import classify
from backend.config import AI_LABELS, API_CALL_DELAY
from backend.gmail.connector import fetch_all_message_ids, get_message_details
from backend.labels.manager import apply_label, ensure_labels_exist

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result type (what each yield / list item contains)
# ---------------------------------------------------------------------------
# {
#   "msg_id": str,
#   "sender": str,
#   "subject": str,
#   "label": "spam" | "ham" | "unknown",
#   "gmail_label": "AI Spam" | "AI Safe" | "AI Needs Review",
#   "confidence": float,
#   "status": "labeled" | "skipped" | "error",
# }


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
        Already authenticated Gmail service from connector.get_gmail_service().

    on_start : callable(total: int) | None
        Called once after all message IDs are collected, with the total count.
        Use this to initialize a progress bar.

    on_progress : callable(current: int, total: int) | None
        Called after each email is processed.
        Use this to update a progress bar.

    Yields
    ------
    dict
        Result for each processed email (see type definition above).
    """
    # ------------------------------------------------------------------
    # Step 1: Ensure all three AI labels exist in Gmail
    # ------------------------------------------------------------------
    logger.info("Ensuring AI labels exist...")
    label_ids_map = ensure_labels_exist(service)

    if not label_ids_map:
        logger.error("Failed to create/find AI labels. Aborting scan.")
        return

    all_ai_label_ids = list(label_ids_map.values())

    # ------------------------------------------------------------------
    # Step 2: Build Gmail search query to skip already-labeled emails
    #
    # Assumption: label names are from AI_LABELS config.
    # Gmail search syntax: -label:"name with spaces"
    # ------------------------------------------------------------------
    exclusion_parts = [f'-label:"{name}"' for name in AI_LABELS]
    exclusion_query = " ".join(exclusion_parts)
    logger.info("Gmail search query: %s", exclusion_query)

    # ------------------------------------------------------------------
    # Step 3: Collect ALL matching message IDs (paginated)
    # We collect the full list first so we know the total count for progress.
    # ------------------------------------------------------------------
    logger.info("Collecting message IDs from Gmail...")
    message_ids = list(fetch_all_message_ids(service, query=exclusion_query))
    total = len(message_ids)
    logger.info("Found %d unlabeled messages to process.", total)

    # Notify UI of total count (for progress bar initialization)
    if on_start:
        on_start(total)

    if total == 0:
        logger.info("All messages already have AI labels. Nothing to do.")
        return

    # ------------------------------------------------------------------
    # Step 4: Process each message
    # ------------------------------------------------------------------
    for idx, msg_id in enumerate(message_ids, start=1):

        # Update progress
        if on_progress:
            on_progress(idx, total)

        # 4a. Fetch message details
        details = get_message_details(service, msg_id)
        if not details:
            # API failure for this message — log, yield error, continue
            logger.warning("Skipping message %s (could not fetch details).", msg_id)
            yield {
                "msg_id": msg_id,
                "sender": "Unknown",
                "subject": "Unknown",
                "label": "unknown",
                "gmail_label": "AI Needs Review",
                "confidence": 0.0,
                "status": "error",
            }
            continue

        # 4b. Classify using AI engine
        #     Combine subject + body for richer context (matching training data format)
        email_text = f"{details['subject']}\n{details['body']}"
        classification = classify(email_text)

        # 4c. Apply Gmail label
        target_label_name = classification["gmail_label"]
        target_label_id = label_ids_map.get(target_label_name)

        if target_label_id:
            success = apply_label(
                service,
                msg_id,
                target_label_id,
                details["label_ids"],
                all_ai_label_ids,
            )
            status = "labeled" if success else "error"
        else:
            logger.error("No label ID found for '%s'. Label may not have been created.", target_label_name)
            status = "error"

        yield {
            "msg_id": msg_id,
            "sender": details["sender"],
            "subject": details["subject"],
            "label": classification["label"],
            "gmail_label": classification["gmail_label"],
            "confidence": classification["confidence"],
            "status": status,
        }

        # Respect Gmail API rate limits (free tier: ~10,000 units/day)
        time.sleep(API_CALL_DELAY)
