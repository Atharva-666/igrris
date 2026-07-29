"""
connector.py — Gmail API connector for MailShield AI.

Responsibilities:
  - Build authenticated Gmail API service object
  - Fetch ALL message IDs from inbox (handles pagination automatically)
  - Retrieve full message details (subject, sender, body)
  - Parse MIME multipart email bodies
  - Decode base64-encoded email content
  - Strip HTML tags and return clean plain text

Gmail API quota note:
  - messages.list  = 5 quota units per call
  - messages.get   = 5 quota units per call
  - Free tier limit = 10,000 units/day (~1,000 full email reads per day)
"""

import base64
import logging
import re
from typing import Generator

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from backend.config import MAX_RESULTS_PER_PAGE, MAX_PAGES_TO_FETCH

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Service factory
# ---------------------------------------------------------------------------

def get_gmail_service(credentials: Credentials):
    """
    Build and return an authenticated Gmail API v1 service object.

    cache_discovery=False prevents stale API discovery files from
    causing issues in development environments.
    """
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


# ---------------------------------------------------------------------------
# Message fetching
# ---------------------------------------------------------------------------

def fetch_all_message_ids(service, query: str = "") -> Generator[str, None, None]:
    """
    Yield message IDs for every message that matches the query.

    Uses Gmail API pagination — handles accounts with thousands of emails.
    Each page fetches up to MAX_RESULTS_PER_PAGE (500) message IDs.

    Parameters
    ----------
    service : Gmail API service object
    query : str
        Gmail search query, e.g. '-label:"AI Safe" -label:"AI Spam"'
        Empty string returns ALL messages.

    Yields
    ------
    str
        Gmail message ID.
    """
    page_token = None
    page_num = 0

    while True:
        page_num += 1
        logger.info("Fetching page %d of message IDs (query=%r)...", page_num, query or "(all)")

        try:
            params: dict = {
                "userId": "me",
                "maxResults": MAX_RESULTS_PER_PAGE,
                "q": query,
            }
            if page_token:
                params["pageToken"] = page_token

            response = service.users().messages().list(**params).execute()

        except HttpError as e:
            logger.error("Gmail API error while listing messages (page %d): %s", page_num, e)
            break

        messages = response.get("messages", [])
        for msg in messages:
            yield msg["id"]

        page_token = response.get("nextPageToken")
        if not page_token:
            logger.info("All pages fetched. Total pages: %d", page_num)
            break

        if page_num >= MAX_PAGES_TO_FETCH:
            logger.info("Reached maximum pages limit (%d). Stopping fetch to save API quota.", MAX_PAGES_TO_FETCH)
            break


def get_message_details(service, msg_id: str) -> dict | None:
    """
    Fetch full details for a single message.

    Returns
    -------
    dict | None
        {
            "id": str,
            "subject": str,
            "sender": str,
            "body": str,          # clean plain text
            "label_ids": list,    # current Gmail label IDs on this message
        }
        Returns None if the message cannot be fetched.
    """
    try:
        message = service.users().messages().get(
            userId="me",
            id=msg_id,
            format="full",
        ).execute()

    except HttpError as e:
        logger.error("Failed to fetch message %s: %s", msg_id, e)
        return None

    payload = message.get("payload", {})

    # Parse headers into a lowercase dict for easy lookup
    headers: dict[str, str] = {
        h["name"].lower(): h["value"]
        for h in payload.get("headers", [])
    }

    subject = headers.get("subject", "(No Subject)").strip()
    sender = headers.get("from", "(Unknown Sender)").strip()
    body = _extract_body(payload)
    existing_label_ids: list[str] = message.get("labelIds", [])

    return {
        "id": msg_id,
        "subject": subject,
        "sender": sender,
        "body": body,
        "label_ids": existing_label_ids,
    }


# ---------------------------------------------------------------------------
# Email body parsing
# ---------------------------------------------------------------------------

def _extract_body(payload: dict) -> str:
    """
    Recursively extract the best available plain-text body from a
    Gmail message payload.

    Priority:
      1. text/plain part
      2. text/html part (stripped of tags)
      3. Recurse into nested multipart parts
      4. Empty string if nothing found
    """
    mime_type: str = payload.get("mimeType", "")
    body_data: str = payload.get("body", {}).get("data", "")

    # --- Single-part message ---
    if body_data:
        text = _decode_base64(body_data)
        if mime_type == "text/html":
            return _strip_html(text)
        return text  # text/plain or other

    # --- Multipart message — search parts ---
    parts: list[dict] = payload.get("parts", [])

    # Pass 1: prefer text/plain
    for part in parts:
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return _decode_base64(data)

    # Pass 2: fallback to text/html
    for part in parts:
        if part.get("mimeType") == "text/html":
            data = part.get("body", {}).get("data", "")
            if data:
                return _strip_html(_decode_base64(data))

    # Pass 3: recurse into nested multipart (e.g. multipart/alternative inside multipart/mixed)
    for part in parts:
        result = _extract_body(part)
        if result.strip():
            return result

    return ""


def _decode_base64(data: str) -> str:
    """
    Decode a URL-safe base64 string (as used by Gmail API) to UTF-8 text.

    Gmail uses base64url encoding (RFC 4648 §5) without padding.
    We add padding back before decoding.
    """
    try:
        # Add missing padding characters
        padded = data + "=" * (4 - len(data) % 4)
        decoded_bytes = base64.urlsafe_b64decode(padded)
        return decoded_bytes.decode("utf-8", errors="replace")
    except Exception as e:
        logger.warning("Base64 decode failed: %s", e)
        return ""


def _strip_html(html: str) -> str:
    """
    Remove HTML markup and return clean plain text.

    Steps:
      1. Remove <script> and <style> blocks (including content)
      2. Remove all remaining HTML tags
      3. Collapse whitespace
    """
    # Remove script/style blocks and their content
    html = re.sub(
        r"<(script|style)[^>]*>.*?</(script|style)>",
        " ",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    # Remove all HTML tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Decode common HTML entities
    text = (
        text.replace("&nbsp;", " ")
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
    )
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text
