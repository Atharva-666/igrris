"""
manager.py — Gmail Label Manager for MailShield AI.

Responsibilities:
  - List all existing labels in the Gmail account
  - Create AI labels if they do not exist (idempotent — never duplicates)
  - Apply the correct AI label to a message
  - Remove outdated AI labels if the prediction changes on rescan

Managed labels:
  "AI Safe"         — green  — email predicted as ham with high confidence
  "AI Spam"         — red    — email predicted as spam with high confidence
  "AI Needs Review" — amber  — low confidence or empty content

Gmail label color note:
  Gmail accepts only a fixed palette of hex colors. The values used here
  are confirmed valid by the Gmail API documentation.
"""

import logging

from googleapiclient.errors import HttpError

from backend.config import AI_LABELS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ensure_labels_exist(service) -> dict[str, str]:
    """
    Ensure all three AI labels exist in the Gmail account.

    Creates any missing labels with the correct colors.
    Reuses existing labels if they already exist.
    Safe to call on every scan — never creates duplicates.

    Parameters
    ----------
    service : Gmail API service object

    Returns
    -------
    dict[str, str]
        Mapping of {label_name: label_id} for all AI labels.
        Returns empty dict if the labels API call fails.
    """
    existing = _list_all_labels(service)
    label_ids: dict[str, str] = {}

    for label_name in AI_LABELS:
        if label_name in existing:
            label_ids[label_name] = existing[label_name]
            logger.debug("Label '%s' already exists (id=%s).", label_name, existing[label_name])
        else:
            new_id = _create_label(service, label_name)
            if new_id:
                label_ids[label_name] = new_id

    return label_ids


def apply_label(
    service,
    msg_id: str,
    target_label_id: str,
    existing_label_ids: list[str],
    all_ai_label_ids: list[str],
) -> bool:
    """
    Apply the target AI label to a message, removing any other AI labels first.

    This ensures each message has exactly one AI label at any time.
    Does nothing if the correct label is already applied (avoids unnecessary API calls).

    Parameters
    ----------
    service : Gmail API service object
    msg_id : str
        Gmail message ID.
    target_label_id : str
        ID of the label to apply.
    existing_label_ids : list[str]
        Label IDs currently on the message (from messages.get response).
    all_ai_label_ids : list[str]
        IDs of all three AI-managed labels (to detect old AI labels to remove).

    Returns
    -------
    bool
        True if the operation succeeded, False otherwise.
    """
    # Determine which AI labels need to be removed (any AI label that is NOT the target)
    labels_to_remove = [
        lid for lid in existing_label_ids
        if lid in all_ai_label_ids and lid != target_label_id
    ]

    # Only add the label if it is not already present
    labels_to_add = [] if target_label_id in existing_label_ids else [target_label_id]

    # Nothing to do
    if not labels_to_add and not labels_to_remove:
        logger.debug("Message %s already has the correct label. Skipping API call.", msg_id)
        return True

    try:
        service.users().messages().modify(
            userId="me",
            id=msg_id,
            body={
                "addLabelIds": labels_to_add,
                "removeLabelIds": labels_to_remove,
            },
        ).execute()
        logger.debug("Applied label to message %s.", msg_id)
        return True

    except HttpError as e:
        logger.error("Failed to apply label to message %s: %s", msg_id, e)
        return False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _list_all_labels(service) -> dict[str, str]:
    """
    Fetch all labels in the account.

    Returns
    -------
    dict[str, str]
        {label_name: label_id}
    """
    try:
        response = service.users().labels().list(userId="me").execute()
        return {lbl["name"]: lbl["id"] for lbl in response.get("labels", [])}
    except HttpError as e:
        logger.error("Failed to list Gmail labels: %s", e)
        return {}


def _create_label(service, label_name: str) -> str | None:
    """
    Create a new Gmail label with the configured color.

    Parameters
    ----------
    label_name : str
        One of the keys in AI_LABELS config.

    Returns
    -------
    str | None
        The new label's ID, or None if creation failed.
    """
    color = AI_LABELS.get(label_name, {})
    label_body = {
        "name": label_name,
        "labelListVisibility": "labelShow",       # show in label list
        "messageListVisibility": "show",           # show in message list
        "color": {
            "textColor": color.get("textColor", "#FFFFFF"),
            "backgroundColor": color.get("backgroundColor", "#666666"),
        },
    }

    try:
        result = service.users().labels().create(
            userId="me",
            body=label_body,
        ).execute()
        logger.info("Created Gmail label '%s' (id=%s).", label_name, result["id"])
        return result["id"]

    except HttpError as e:
        logger.error("Failed to create label '%s': %s", label_name, e)
        return None
