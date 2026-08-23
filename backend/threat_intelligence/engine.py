import logging
import re
import json
import os
from . import cache

logger = logging.getLogger(__name__)

# Load severity config
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
try:
    with open(CONFIG_FILE, 'r') as f:
        _config = json.load(f)
except Exception:
    _config = {"block_severity": ["critical", "high"]}

BLOCK_SEVERITY = _config.get("block_severity", ["critical", "high"])

def _extract_domains(text: str) -> set:
    """Extract all domains and emails from text."""
    emails = re.findall(r'[\w\.-]+@([\w\.-]+)', text)
    urls = re.findall(r'(?:https?|ftp)://(?:www\.)?([\w\.-]+)', text)
    return set(emails + urls)

def _extract_urls(text: str) -> set:
    """Extract all HTTP, HTTPS, FTP, and WWW URLs from text."""
    return set(re.findall(r'(?:https?|ftp)://[^\s<>"]+|www\.[^\s<>"]+', text))

def check(
    subject: str,
    body: str,
    sender_email: str | None = None,
    sender_domain: str | None = None,
    attachments: list | None = None,
    headers: dict | None = None
) -> dict:
    """
    Threat Intelligence Engine pre-filter check.
    Returns early if a known threat is detected.
    """
    text_content = f"{subject}\n{body}"
    
    # 1. Check Sender Domain
    if sender_domain:
        sd = sender_domain.lower()
        if sd in cache.BLACKLIST_DOMAINS or sd in cache.USER_BLACKLIST:
            return {
                "matched": True,
                "rule_name": "BLACKLISTED_SENDER",
                "severity": "critical",
                "reason": "Sender domain is explicitly blacklisted",
                "source": "Local Blacklist",
                "detection_source": "threat_intelligence"
            }
        if sd in cache.DISPOSABLE_DOMAINS:
            return {
                "matched": True,
                "rule_name": "DISPOSABLE_EMAIL",
                "severity": "high",
                "reason": "Sender uses a disposable email provider",
                "source": "DisposableFeed",
                "detection_source": "threat_intelligence"
            }

    # 2. Extract and check all domains/URLs in content
    extracted_domains = _extract_domains(text_content)
    for dom in extracted_domains:
        d = dom.lower()
        if d in cache.PHISHING_DOMAINS:
            return {
                "matched": True,
                "rule_name": "PHISHING_DOMAIN_IN_BODY",
                "severity": "critical",
                "reason": f"Body contains known phishing domain: {d}",
                "source": "OpenPhish",
                "detection_source": "threat_intelligence"
            }
            
    extracted_urls = _extract_urls(text_content)
    for u in extracted_urls:
        u_lower = u.lower()
        if u_lower in cache.MALICIOUS_URLS:
            return {
                "matched": True,
                "rule_name": "MALICIOUS_URL",
                "severity": "critical",
                "reason": "Known malicious URL found",
                "source": "URLhaus",
                "detection_source": "threat_intelligence"
            }

    # 3. Attachments
    if attachments:
        dangerous_exts = {'.exe', '.scr', '.bat', '.cmd', '.js', '.vbs', '.ps1', '.docm', '.xlsm'}
        for att in attachments:
            ext = os.path.splitext(att.lower())[1]
            if ext in dangerous_exts:
                return {
                    "matched": True,
                    "rule_name": "DANGEROUS_ATTACHMENT",
                    "severity": "critical",
                    "reason": f"Dangerous attachment extension: {ext}",
                    "source": "StaticRule",
                    "detection_source": "threat_intelligence"
                }

    return {"matched": False}
