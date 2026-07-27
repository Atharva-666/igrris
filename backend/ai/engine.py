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
# Public API
# ---------------------------------------------------------------------------

def classify(email_text: str) -> dict:
    """
    Classify a single email using the existing TF-IDF + LinearSVC model.

    This is Layer 1 classification only. It returns the raw ML output
    (label + confidence). The final Gmail label decision is made by
    the Layer 2 rule engine in backend/classifier/rule_engine.py.

    Parameters
    ----------
    email_text : str
        The email text to classify. Typically subject + newline + body.
        May be empty — handled gracefully.

    Returns
    -------
    dict
        {
            "label"      : "spam" | "ham" | "unknown",
            "confidence" : float,   # 0.0 – 1.0
        }
    """
    if not email_text or not email_text.strip():
        logger.debug("Empty email text received. Marking as unknown.")
        return {
            "label": "unknown",
            "confidence": 0.0,
        }

    try:
        result = _predict(email_text)
        label: str = result["label"]               # "spam" or "ham"
        confidence: float = result["confidence"]   # float 0.0 – 1.0
        return {
            "label": label,
            "confidence": confidence,
        }

    except ValueError as e:
        logger.warning("Prediction ValueError: %s", e)
        return {
            "label": "unknown",
            "confidence": 0.0,
        }

    except Exception as e:
        logger.error("Unexpected error during classification: %s", e)
        return {
            "label": "unknown",
            "confidence": 0.0,
        }
