"""
rule_engine.py — Layer 2 rule-based email classifier for Igrris AI.

This module runs AFTER the TF-IDF + LinearSVC model (Layer 1) and applies
category-specific rules to produce a more granular label.

Classification flow:
    1. Layer 1 (ML) outputs: label=spam|ham, confidence=float
    2. This engine receives those results plus raw email fields
    3. Runs rules in priority order from rules_config.yaml
    4. Returns: primary_label, optional secondary_label, matched_rule, layer

All rule sets live in rules_config.yaml — no code changes needed to tune.
Logs every match with: rule name, matched text excerpt, and layer (ML/rule).
"""

from __future__ import annotations

import logging
import os
import re
from functools import lru_cache
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config Loading
# ---------------------------------------------------------------------------

_CONFIG_FILE = os.path.join(
    os.path.dirname(__file__),
    "rules_config.yaml",
)


@lru_cache(maxsize=1)
def _load_config() -> dict[str, Any]:
    """Load and cache the rules config YAML. Thread-safe via Python GIL."""
    with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    logger.info("Rule engine: loaded config from %s", _CONFIG_FILE)
    return cfg


def reload_config() -> None:
    """Force reload of the config (clears lru_cache). Call after editing YAML."""
    _load_config.cache_clear()
    _load_config()


# ---------------------------------------------------------------------------
# Helper: keyword matcher
# ---------------------------------------------------------------------------

def _contains_any(text: str, keywords: list[str]) -> str | None:
    """
    Return the first matching keyword found in text (case-insensitive),
    or None if no match.
    """
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return kw
    return None


def _sender_domain(sender: str) -> str:
    """Extract domain from a sender string like 'Name <email@domain.com>'."""
    match = re.search(r"@([\w.\-]+)", sender.lower())
    return match.group(1) if match else ""


def _domain_in_list(sender: str, domains: list[str]) -> str | None:
    """Return the matching domain if the sender's domain is in the list."""
    domain = _sender_domain(sender)
    for allowed in domains:
        if domain == allowed.lower() or domain.endswith("." + allowed.lower()):
            return allowed
    return None


def _matches_suspicious_domain(sender: str, patterns: list[str]) -> str | None:
    """Return the matching pattern if sender domain looks suspicious."""
    domain = _sender_domain(sender)
    for pattern in patterns:
        if re.search(pattern, domain, re.IGNORECASE):
            return pattern
    return None


# ---------------------------------------------------------------------------
# Per-label rule checks
# ---------------------------------------------------------------------------

def _check_phishing(subject: str, body: str, sender: str, cfg: dict) -> str | None:
    """Return matched rule description if email looks like phishing, else None."""
    ph = cfg.get("phishing", {})

    kw = _contains_any(subject, ph.get("subject_keywords", []))
    if kw:
        return f"subject_keyword:{kw}"

    kw = _contains_any(body, ph.get("body_keywords", []))
    if kw:
        return f"body_keyword:{kw}"

    pat = _matches_suspicious_domain(sender, ph.get("suspicious_domain_patterns", []))
    if pat:
        return f"suspicious_domain_pattern:{pat}"

    return None


def _check_security(subject: str, body: str, sender: str, cfg: dict) -> str | None:
    sec = cfg.get("security", {})

    # Subject keyword match — strong enough signal on its own
    kw_sub = _contains_any(subject, sec.get("subject_keywords", []))
    if kw_sub:
        # Extra check: if it's from a *social* platform and has no urgent keyword,
        # don't classify as Security (e.g. LinkedIn 'new message' notifications)
        domain = _domain_in_list(sender, sec.get("trusted_security_domains", []))
        if domain:
            return f"trusted_domain:{domain}+subject_keyword:{kw_sub}"
        # Unknown sender with security subject keywords — still flag
        return f"subject_keyword:{kw_sub}"

    # Body keyword match ONLY when sender is from a trusted security domain
    # BOTH conditions required — domain alone is not sufficient
    domain = _domain_in_list(sender, sec.get("trusted_security_domains", []))
    if domain:
        kw_body = _contains_any(body, sec.get("body_keywords", []))
        if kw_body:
            return f"trusted_domain:{domain}+body_keyword:{kw_body}"
        # Domain matched but NO security keywords found — not a security email
        return None

    return None


def _check_banking(subject: str, body: str, sender: str, cfg: dict) -> str | None:
    bnk = cfg.get("banking", {})

    domain = _domain_in_list(sender, bnk.get("trusted_banking_domains", []))
    kw = _contains_any(subject, bnk.get("subject_keywords", []))

    if domain and kw:
        return f"trusted_domain:{domain}+subject_keyword:{kw}"
    if domain:
        return f"trusted_domain:{domain}"
    if kw:
        return f"subject_keyword:{kw}"

    return None


def _check_orders(subject: str, body: str, sender: str, cfg: dict) -> str | None:
    ord_ = cfg.get("orders", {})

    kw = _contains_any(subject, ord_.get("subject_keywords", []))
    if not kw:
        return None

    domain = _domain_in_list(sender, ord_.get("trusted_retail_domains", []))
    if domain:
        return f"trusted_domain:{domain}+subject_keyword:{kw}"
    return f"subject_keyword:{kw}"


def _check_promotions(subject: str, body: str, sender: str, cfg: dict) -> str | None:
    prm = cfg.get("promotions", {})
    
    domain = _domain_in_list(sender, prm.get("promotional_domains", []))
    if domain:
        return f"promotional_domain:{domain}"

    kw = _contains_any(subject, prm.get("subject_keywords", []))
    if kw:
        return f"subject_keyword:{kw}"
    
    return None


def _check_education(subject: str, body: str, sender: str, cfg: dict) -> str | None:
    edu = cfg.get("education", {})

    domain = _domain_in_list(sender, edu.get("trusted_education_domains", []))
    kw = _contains_any(subject, edu.get("subject_keywords", []))

    if domain:
        return f"trusted_domain:{domain}"
    if kw:
        return f"subject_keyword:{kw}"
    return None


def _check_work(subject: str, body: str, sender: str, cfg: dict) -> str | None:
    wrk = cfg.get("work", {})

    domain = _domain_in_list(sender, wrk.get("work_domains", []))
    if domain:
        return f"work_domain:{domain}"

    kw = _contains_any(subject, wrk.get("subject_keywords", []))
    if kw:
        return f"subject_keyword:{kw}"
        
    return None


def _check_personal(subject: str, body: str, sender: str, cfg: dict) -> str | None:
    per = cfg.get("personal", {})

    domain = _domain_in_list(sender, per.get("personal_domains", []))
    if domain:
        return f"personal_domain:{domain}"

    return None


# ---------------------------------------------------------------------------
# Rule dispatcher
# ---------------------------------------------------------------------------

_RULE_CHECKERS: dict[str, Any] = {
    "Phishing":   _check_phishing,
    "Security":   _check_security,
    "Banking":    _check_banking,
    "Orders":     _check_orders,
    "Promotions": _check_promotions,
    "Education":  _check_education,
    "Work":       _check_work,
    "Personal":   _check_personal,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_layer2(
    subject: str,
    sender: str,
    body: str,
    ml_label: str,
    ml_confidence: float,
) -> dict:
    """
    Determine the final Gmail label(s) from ML output + rule engine.

    Parameters
    ----------
    subject : str
    sender  : str
    body    : str
    ml_label : str
        "spam" or "ham" from Layer 1 ML model.
    ml_confidence : float
        0.0–1.0 from Layer 1 ML model.

    Returns
    -------
    dict
        {
            "primary_label"   : str,   # one of the 11 labels
            "secondary_label" : str | None,
            "matched_rule"    : str,   # description for logging
            "layer"           : str,   # "ML" or "rule:<category>"
        }
    """
    cfg = _load_config()
    threshold = cfg.get("confidence_threshold", 0.70)
    priority = cfg.get("priority", [])
    secondary_pairs = cfg.get("secondary_label_pairs", {})

    # Step 1: Low confidence from ML → Needs Review regardless of content
    if ml_confidence < threshold:
        logger.info(
            "Email classified as 'Needs Review' (ML confidence %.0f%% < %.0f%%)",
            ml_confidence * 100,
            threshold * 100,
        )
        return {
            "primary_label": "Needs Review",
            "secondary_label": None,
            "matched_rule": f"ml_confidence:{ml_confidence:.2f}<{threshold:.2f}",
            "layer": "ML",
        }

    # Step 2: Run rule checkers in priority order
    # We run ALL checkers first to collect all matches, then apply priority
    all_matches: dict[str, str] = {}

    for label in priority:
        checker = _RULE_CHECKERS.get(label)
        if checker:
            rule_match = checker(subject, body, sender, cfg)
            if rule_match:
                all_matches[label] = rule_match

    # Step 3: If ML says spam AND Phishing didn't match → Spam wins over other rules
    if ml_label == "spam" and "Phishing" not in all_matches:
        primary = "Spam"
        matched_rule = f"ml_label:spam,confidence:{ml_confidence:.2f}"
        layer = "ML"
    elif "Phishing" in all_matches:
        # Phishing always wins, even over Spam
        primary = "Phishing"
        matched_rule = all_matches["Phishing"]
        layer = "rule:Phishing"
    elif ml_label == "spam":
        # Phishing matched → override Spam
        primary = "Phishing"
        matched_rule = all_matches["Phishing"]
        layer = "rule:Phishing"
    else:
        # Ham: pick highest-priority rule match
        primary = None
        matched_rule = "no_rule_match"
        layer = "rule:none"

        for label in priority:
            if label in ("Spam", "Phishing", "Needs Review"):
                continue
            if label in all_matches:
                primary = label
                matched_rule = all_matches[label]
                layer = f"rule:{label}"
                break

        if not primary:
            # No rule matched → Personal (or Trusted if we had history — defaulting to Trusted)
            primary = "Trusted"
            matched_rule = "fallback:no_rule_match"
            layer = "ML"

    logger.info(
        "Label decision: '%s' | rule=%s | layer=%s",
        primary, matched_rule, layer,
    )

    # Step 4: Check for valid secondary label
    secondary = None
    allowed_secondaries = secondary_pairs.get(primary, [])
    for sec_candidate in allowed_secondaries:
        if sec_candidate in all_matches and sec_candidate != primary:
            secondary = sec_candidate
            logger.info(
                "Secondary label: '%s' | rule=%s",
                secondary, all_matches[sec_candidate],
            )
            break

    return {
        "primary_label": primary,
        "secondary_label": secondary,
        "matched_rule": matched_rule,
        "layer": layer,
    }
