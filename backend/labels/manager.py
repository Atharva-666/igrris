"""
manager.py — Gmail Label Manager for Igrris AI.

Responsibilities:
  - List all existing labels in the Gmail account
  - Create labels if they do not exist (idempotent — never duplicates)
  - Apply the correct label(s) to a message (primary + optional secondary)
  - Remove outdated managed labels if the prediction changes on rescan

Managed labels (11 total, no product branding):
  Trusted, Spam, Needs Review, Phishing, Security,
  Banking, Orders, Promotions, Education, Work, Personal
"""

import logging

from googleapiclient.errors import HttpError

from backend.config import LABELS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# Gmail system labels that conflict with our desired label names.
# Instead of creating a custom label, we re-use the system label ID.
_SYSTEM_LABEL_ALIASES: dict[str, str] = {
    "Spam": "SPAM",
}


def ensure_labels_exist(service) -> dict[str, str]:
    """
    Ensure all managed labels exist in the Gmail account.

    Creates any missing labels with the correct colors.
    Reuses existing labels if they already exist.
    Safe to call on every scan — never creates duplicates.

    Note: 'Spam' is mapped to Gmail's built-in SPAM system label (id='SPAM')
    instead of creating a conflicting custom label.

    Returns
    -------
    dict[str, str]
        Mapping of {label_name: label_id} for all managed labels.
        Returns empty dict if the labels API call fails.
    """
    existing = _list_all_labels(service)
    label_ids: dict[str, str] = {}

    for label_name in LABELS:
        # Check if this label has a system alias (e.g. Spam -> SPAM)
        system_alias = _SYSTEM_LABEL_ALIASES.get(label_name)
        if system_alias and system_alias in existing:
            label_ids[label_name] = existing[system_alias]
            logger.debug(
                "Label '%s' mapped to Gmail system label '%s' (id=%s).",
                label_name, system_alias, existing[system_alias],
            )
            continue

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
    primary_label_id: str,
    existing_label_ids: list[str],
    all_managed_label_ids: list[str],
    secondary_label_id: str | None = None,
) -> bool:
    """
    Apply the primary label (and optional secondary label) to a message,
    removing any other managed labels first.

    Parameters
    ----------
    service : Gmail API service object
    msg_id : str
    primary_label_id : str
        ID of the primary label to apply.
    existing_label_ids : list[str]
        Label IDs currently on the message.
    all_managed_label_ids : list[str]
        IDs of all managed labels (to detect stale labels to remove).
    secondary_label_id : str | None
        Optional secondary label ID to also apply.

    Returns
    -------
    bool
        True if the operation succeeded, False otherwise.
    """
    new_ids = [primary_label_id]
    if secondary_label_id:
        new_ids.append(secondary_label_id)

    # Remove any managed labels that are NOT in the new set
    labels_to_remove = [
        lid for lid in existing_label_ids
        if lid in all_managed_label_ids and lid not in new_ids
    ]

    # Only add labels that aren't already present
    labels_to_add = [lid for lid in new_ids if lid not in existing_label_ids]

    # Nothing to do
    if not labels_to_add and not labels_to_remove:
        logger.debug("Message %s already has the correct label(s). Skipping API call.", msg_id)
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
        logger.debug("Applied label(s) to message %s.", msg_id)
        return True

    except HttpError as e:
        logger.error("Failed to apply label to message %s: %s", msg_id, e)
        return False


def delete_managed_label(service, label_name: str) -> bool:
    """
    Delete a single managed Gmail label by name.

    System labels (like 'Spam' -> 'SPAM') cannot be deleted via Gmail API and are skipped.
    """
    if label_name in _SYSTEM_LABEL_ALIASES:
        logger.info("Label '%s' is mapped to a Gmail system label and cannot be deleted.", label_name)
        return False

    existing = _list_all_labels(service)
    label_id = existing.get(label_name)

    if not label_id:
        logger.info("Label '%s' does not exist in Gmail account.", label_name)
        return True

    try:
        service.users().labels().delete(userId="me", id=label_id).execute()
        logger.info("Deleted Gmail label '%s' (id=%s).", label_name, label_id)
        return True
    except HttpError as e:
        logger.error("Failed to delete Gmail label '%s' (id=%s): %s", label_name, label_id, e)
        return False


def delete_all_managed_labels(service, label_names: list[str] | None = None) -> dict[str, list[str]]:
    """
    Delete managed labels from the Gmail account.

    Parameters
    ----------
    service : Gmail API service object
    label_names : list[str] | None
        Specific label names to delete. If None or empty, targets all configured LABELS.

    Returns
    -------
    dict[str, list[str]]
        Summary dictionary containing:
        - 'deleted': list of deleted label names
        - 'failed': list of label names where deletion failed
        - 'skipped_system': list of system label names that were skipped
    """
    targets = label_names if label_names else list(LABELS.keys())
    existing = _list_all_labels(service)

    deleted: list[str] = []
    failed: list[str] = []
    skipped_system: list[str] = []

    for name in targets:
        if name in _SYSTEM_LABEL_ALIASES:
            skipped_system.append(name)
            continue

        label_id = existing.get(name)
        if not label_id:
            continue

        try:
            service.users().labels().delete(userId="me", id=label_id).execute()
            logger.info("Deleted Gmail label '%s' (id=%s).", name, label_id)
            deleted.append(name)
        except HttpError as e:
            logger.error("Failed to delete label '%s': %s", name, e)
            failed.append(name)

    return {
        "deleted": deleted,
        "failed": failed,
        "skipped_system": skipped_system,
    }


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
        One of the keys in LABELS config.

    Returns
    -------
    str | None
        The new label's ID, or None if creation failed.
    """
    color = LABELS.get(label_name, {})
    label_body = {
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
        "color": {
            "textColor": color.get("textColor", "#ffffff"),
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
        logger.warning("Failed to create label '%s' with color: %s. Retrying without color...", label_name, e)
        try:
            plain_body = {
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            }
            result = service.users().labels().create(
                userId="me",
                body=plain_body,
            ).execute()
            logger.info("Created Gmail label '%s' without color (id=%s).", label_name, result["id"])
            return result["id"]
        except HttpError as e2:
            logger.error("Failed to create label '%s': %s", label_name, e2)
            return None
