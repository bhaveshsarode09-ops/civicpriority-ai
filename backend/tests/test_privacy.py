"""Unit tests for Phase 3 Privacy and PII Protection.
"""

from datetime import datetime, timedelta, timezone
import pytest

from civicpriority.models import ComplaintRecord, ComplaintSource
from civicpriority.privacy import (
    PrivacyConfig,
    anonymize_expired_record,
    hash_contact_identifier,
    is_record_expired,
    mask_email_addresses,
    mask_government_ids,
    mask_phone_numbers,
    sanitize_text_for_ai,
    validate_consent,
)


def test_user_prompt_example_phone_masking():
    """Verify the exact user prompt example:
    Input: 'Call me at 9876543210. The road near Ward 7 is broken.'
    Output: 'Call me at [PHONE_REDACTED]. The road near Ward 7 is broken.'
    """
    raw_input = "Call me at 9876543210. The road near Ward 7 is broken."
    expected_output = "Call me at [PHONE_REDACTED]. The road near Ward 7 is broken."
    masked = mask_phone_numbers(raw_input)
    assert masked == expected_output


def test_phone_number_variations():
    """Verify various domestic and international phone formatting patterns."""
    cases = [
        ("+91 98765 43210 please call", "please call"),
        ("Phone: +91-9876543210 immediately", "Phone:"),
        ("Contact (555) 234-5678 for access", "for access"),
        ("Dial 8888877777 now", "now"),
    ]
    for text, trailing in cases:
        masked = mask_phone_numbers(text)
        assert "[PHONE_REDACTED]" in masked
        assert trailing in masked
        assert "9876543210" not in masked
        assert "8888877777" not in masked


def test_email_masking():
    """Verify standard, subdomain, and plus-addressed emails are redacted."""
    raw = "Reach out to rajesh.sharma+ward4@sub.district.gov.in or admin@city.org."
    masked = mask_email_addresses(raw)
    assert "[EMAIL_REDACTED]" in masked
    assert "rajesh.sharma" not in masked
    assert "admin@city.org" not in masked
    assert "Reach out to [EMAIL_REDACTED] or [EMAIL_REDACTED]." == masked


def test_government_id_masking():
    """Verify 12-digit national IDs and tax IDs are masked."""
    text_aadhaar = "Citizen ID is 4321 8765 2109 and PAN is ABCDE1234F."
    masked = mask_government_ids(text_aadhaar)
    assert "[ID_REDACTED]" in masked
    assert "4321" not in masked
    assert "ABCDE1234F" not in masked


def test_salted_contact_hashing():
    """Verify contact hashing is deterministic, salted, and normalized."""
    phone_clean = "9876543210"
    phone_formatted = "+91 (987) 654-3210"

    hash1 = hash_contact_identifier(phone_clean)
    hash2 = hash_contact_identifier(phone_formatted)

    assert hash1 is not None
    # Formatting differences should normalize to identical hash
    assert hash1 == hash2
    assert phone_clean not in hash1

    # Different salt produces different hash
    diff_hash = hash_contact_identifier(phone_clean, salt="custom_salt_999")
    assert diff_hash != hash1

    # None or empty returns None
    assert hash_contact_identifier(None) is None
    assert hash_contact_identifier("   ") is None


def test_sanitize_text_for_ai():
    """Ensure complete PII scrubbing before sending to Gemini / LLM."""
    prompt_with_pii = (
        "My phone is 9876543210, email is resident@ward12.com, and ID is 9999 8888 7777. "
        "The government school in Ward 12 lacks clean drinking water."
    )
    sanitized = sanitize_text_for_ai(prompt_with_pii)

    # All PII tokens replaced
    assert "[PHONE_REDACTED]" in sanitized
    assert "[EMAIL_REDACTED]" in sanitized
    assert "[ID_REDACTED]" in sanitized
    assert "9876543210" not in sanitized
    assert "resident@ward12.com" not in sanitized
    assert "9999 8888 7777" not in sanitized

    # Core civic information is preserved
    assert "government school in Ward 12 lacks clean drinking water" in sanitized


def test_consent_validation():
    """Verify consent validation logic."""
    rec_consented = ComplaintRecord(
        id="CMP-C1",
        source=ComplaintSource.DIRECT_WEB,
        original_text="Valid issue in Ward 5",
        locality="Ward 5",
        consent_obtained=True,
    )
    assert validate_consent(rec_consented) is True

    rec_unconsented = ComplaintRecord(
        id="CMP-C2",
        source=ComplaintSource.DIRECT_WEB,
        original_text="Issue without consent",
        locality="Ward 5",
        consent_obtained=False,
    )
    assert validate_consent(rec_unconsented) is False


def test_retention_and_anonymization():
    """Verify retention check and anonymization of expired records."""
    now = datetime.now(timezone.utc)
    recent_time = now - timedelta(days=30)
    old_time = now - timedelta(days=200)

    # 1. Recent record (30 days old)
    assert is_record_expired(recent_time, retention_days=180) is False

    # 2. Expired record (200 days old)
    assert is_record_expired(old_time, retention_days=180) is True

    old_record = ComplaintRecord(
        id="CMP-OLD-1",
        source=ComplaintSource.DIRECT_WEB,
        source_reference="REF-OLD-999",
        original_text="Road broken. Call me at 9876543210.",
        locality="Ward 7",
        citizen_contact_hash=hash_contact_identifier("9876543210"),
        submitted_at=old_time,
        consent_obtained=True,
    )

    anonymized = anonymize_expired_record(old_record, retention_days=180)
    # Contact hash and references scrubbed
    assert anonymized.citizen_contact_hash is None
    assert anonymized.source_reference is None
    # Text scrubbed
    assert "[PHONE_REDACTED]" in anonymized.original_text
    assert anonymized.metadata.get("retention_status") == "anonymized_expired"
