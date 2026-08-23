"""
test_threat_intelligence.py — Unit tests for Threat Intelligence pre-filter & data lifecycle.
"""

import sys
import os
import tempfile
import json

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.threat_intelligence import cache, engine, updater


class TestThreatIntelligenceEngine:
    def test_clean_email_returns_not_matched(self):
        result = engine.check(
            subject="Hello Friend",
            body="Hope you have a nice day!",
            sender_email="user@example.com",
            sender_domain="example.com"
        )
        assert result["matched"] is False

    def test_disposable_domain_matched(self):
        cache.DISPOSABLE_DOMAINS.add("tempmail.org")
        try:
            result = engine.check(
                subject="Quick note",
                body="Please reply",
                sender_email="test@tempmail.org",
                sender_domain="tempmail.org"
            )
            assert result["matched"] is True
            assert result["rule_name"] == "DISPOSABLE_EMAIL"
            assert result["severity"] == "high"
            assert result["detection_source"] == "threat_intelligence"
        finally:
            cache.DISPOSABLE_DOMAINS.discard("tempmail.org")

    def test_phishing_domain_in_body_matched(self):
        cache.PHISHING_DOMAINS.add("fake-bank-login.com")
        try:
            result = engine.check(
                subject="Account Urgent",
                body="Verify at http://fake-bank-login.com/secure now",
                sender_email="alerts@bank.com",
                sender_domain="bank.com"
            )
            assert result["matched"] is True
            assert result["rule_name"] == "PHISHING_DOMAIN_IN_BODY"
            assert result["severity"] == "critical"
        finally:
            cache.PHISHING_DOMAINS.discard("fake-bank-login.com")

    def test_malicious_http_url_matched(self):
        url = "http://bad-site.com/payload.exe"
        cache.MALICIOUS_URLS.add(url)
        try:
            result = engine.check(
                subject="Invoice attached",
                body=f"Download invoice: {url}",
                sender_email="billing@vendor.com",
                sender_domain="vendor.com"
            )
            assert result["matched"] is True
            assert result["rule_name"] == "MALICIOUS_URL"
        finally:
            cache.MALICIOUS_URLS.discard(url)

    def test_malicious_ftp_url_matched(self):
        """Verify FTP URLs (e.g. from URLhaus) are extracted and matched."""
        ftp_url = "ftp://185.93.89.72/ftpget"
        cache.MALICIOUS_URLS.add(ftp_url)
        try:
            result = engine.check(
                subject="FTP Download",
                body=f"Fetch files from {ftp_url} immediately",
                sender_email="admin@unknown.com",
                sender_domain="unknown.com"
            )
            assert result["matched"] is True
            assert result["rule_name"] == "MALICIOUS_URL"
        finally:
            cache.MALICIOUS_URLS.discard(ftp_url)


class TestThreatIntelligenceDataLifecycle:
    def test_seed_fallback_when_runtime_dir_empty(self, tmp_path, monkeypatch):
        """When runtime directory is empty, cache falls back to SEED_DATA_DIR."""
        monkeypatch.setattr(cache, "RUNTIME_DATA_DIR", str(tmp_path))
        cache.reload_cache()
        # Seed disposable domains file exists and has entries
        assert len(cache.DISPOSABLE_DOMAINS) > 0

    def test_runtime_data_overrides_seed(self, tmp_path, monkeypatch):
        """When runtime directory contains updated files, cache loads from runtime directory."""
        monkeypatch.setattr(cache, "RUNTIME_DATA_DIR", str(tmp_path))

        runtime_disposable = tmp_path / "disposable_domains.txt"
        runtime_disposable.write_text("custom-runtime-disposable.com\n", encoding="utf-8")

        cache.reload_cache()
        assert "custom-runtime-disposable.com" in cache.DISPOSABLE_DOMAINS

        # Clean up cache
        cache.reload_cache()
