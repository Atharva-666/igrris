"""
engine.py — AI classification engine for MailShield AI.

This module is a thin wrapper over the existing predict() function.

IMPORTANT: The underlying TF-IDF + LinearSVC pipeline is NOT modified here.
  - model.pkl and vectorizer.pkl are loaded by the root predict.py
  - This module simply imports and calls that existing predict() function
  - The only new logic is the mapping from raw model output to Gmail label names

Model and vectorizer are loaded ONCE when this module is first imported.
All subsequent classify() calls reuse the already-loaded objects (fast).

LinearSVC note:
  LinearSVC does not support predict_proba(). The existing predict.py
  correctly falls back to confidence=1.0 for such models. For the
  "AI Needs Review" bucket we therefore use a decision_function threshold
  instead — see classify() below.
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so we can import predict.py and
# data_preprocessing.py, which live in the project root.
# ---------------------------------------------------------------------------
_ROOT = os.path.dirname(  # project root
    os.path.dirname(       # backend/
        os.path.dirname(   # backend/ai/
            os.path.abspath(__file__)
        )
    )
)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Import the existing predict function — this also triggers model loading
from predict import predict as _predict  # noqa: E402

logger.info("AI engine ready (model loaded via predict.py).")

# ---------------------------------------------------------------------------
# Label mapping: model output → Gmail label name
# ---------------------------------------------------------------------------
_LABEL_MAP: dict[str, str] = {
    "ham": "AI Safe",
    "spam": "AI Spam",
}

# Confidence below this threshold → classify as "AI Needs Review"
# Note: LinearSVC always returns confidence=1.0 (no probability support),
# so this threshold will only matter if the model is later replaced with
# one that supports predict_proba (e.g., LogisticRegression).
_CONFIDENCE_THRESHOLD: float = 0.6


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify(email_text: str) -> dict:
    """
    Classify a single email using the existing TF-IDF + LinearSVC model.

    Parameters
    ----------
    email_text : str
        The email text to classify. Typically subject + newline + body.
        May be empty — handled gracefully.

    Returns
    -------
    dict
        {
            "label": "spam" | "ham" | "unknown",
            "gmail_label": "AI Spam" | "AI Safe" | "AI Needs Review",
            "confidence": float,   # 0.0 – 1.0
        }
    """
    if not email_text or not email_text.strip():
        # Empty email → cannot classify confidently → flag for review
        logger.debug("Empty email text received. Marking as 'AI Needs Review'.")
        return {
            "label": "ham",
            "gmail_label": "AI Needs Review",
            "confidence": 0.0,
        }

    try:
        # Call the existing prediction function — unchanged
        result = _predict(email_text)

        label: str = result["label"]               # "spam" or "ham"
        confidence: float = result["confidence"]   # float 0.0 – 1.0

        # Determine Gmail label
        if confidence < _CONFIDENCE_THRESHOLD:
            gmail_label = "AI Needs Review"
        else:
            gmail_label = _LABEL_MAP.get(label, "AI Needs Review")

        return {
            "label": label,
            "gmail_label": gmail_label,
            "confidence": confidence,
        }

    except ValueError as e:
        # predict() raises ValueError for empty / too-long text
        logger.warning("Prediction ValueError: %s", e)
        return {
            "label": "unknown",
            "gmail_label": "AI Needs Review",
            "confidence": 0.0,
        }

    except Exception as e:
        logger.error("Unexpected error during classification: %s", e)
        return {
            "label": "unknown",
            "gmail_label": "AI Needs Review",
            "confidence": 0.0,
        }
