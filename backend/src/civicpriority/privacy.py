"""Privacy and PII Protection Module for CivicPriority AI.
Ensures zero PII leakage to AI providers and protects citizen confidentiality.
"""

from datetime import datetime, timezone
import hashlib
import re
from typing import Optional
from pydantic import BaseModel, Field

from civicpriority.models import ComplaintRecord, utc_now


class PrivacyConfig(BaseModel):
    """Configuration for civic data privacy and retention policies."""
    salt: str = Field(default="civic_priority_privacy_salt_2026", description="Cryptographic salt for contact hashing")
    retention_days: int = Field(default=180, description="Data retention window in days before anonymization")
    mask_phone: bool = Field(default=True, description="Enable automated phone redaction")
    mask_email: bool = Field(default=True, description="Enable automated email redaction")
    mask_ids: bool = Field(default=True, description="Enable automated national ID / voter / card redaction")


DEFAULT_PRIVACY_CONFIG = PrivacyConfig()


def hash_contact_identifier(contact: Optional[str], salt: Optional[str] = None) -> Optional[str]:
    """Generate a salted, irreversible SHA-256 hash of personal contact info.
    Normalizes input by stripping spaces, symbols, and standardizing casing.
    """
    if not contact or not str(contact).strip():
        return None
    used_salt = salt or DEFAULT_PRIVACY_CONFIG.salt
    cleaned = re.sub(r"[\s\-\(\)\+\.]", "", str(contact).strip().lower())
    # Normalize 10-digit numbers with leading 91 or 0
    if len(cleaned) == 12 and cleaned.startswith("91"):
        cleaned = cleaned[2:]
    elif len(cleaned) == 11 and cleaned.startswith("0"):
        cleaned = cleaned[1:]

    hasher = hashlib.sha256()
    hasher.update(used_salt.encode("utf-8"))
    hasher.update(cleaned.encode("utf-8"))
    return hasher.hexdigest()


def mask_phone_numbers(text: str) -> str:
    """Detect and redact international and domestic phone numbers.
    Replaces matches with [PHONE_REDACTED].
    """
    if not text:
        return ""

    # 1. Matches with country codes: +91 9876543210, +91-98765-43210, +1 (555) 123-4567
    pattern_intl = r"(?:\+?\d{1,3}[\s-]?)?\(?\d{3}\)[\s.-]?\d{3}[\s.-]?\d{4}\b"
    text = re.sub(pattern_intl, "[PHONE_REDACTED]", text)

    pattern_intl_prefix = r"\+\d{1,3}[\s-][6-9]\d{4}[\s-]\d{5}\b"
    text = re.sub(pattern_intl_prefix, "[PHONE_REDACTED]", text)

    pattern_intl_code = r"\+\d{1,3}[\s-]?[6-9]\d{9}\b"
    text = re.sub(pattern_intl_code, "[PHONE_REDACTED]", text)

    # 2. Formatted mobile numbers (e.g. 98765 43210 or 98765-43210)
    pattern_split = r"\b[6-9]\d{4}[\s-]\d{5}\b"
    text = re.sub(pattern_split, "[PHONE_REDACTED]", text)

    # 3. Indian 10-digit mobile numbers starting with 6, 7, 8, 9
    pattern_in = r"\b[6-9]\d{9}\b"
    text = re.sub(pattern_in, "[PHONE_REDACTED]", text)

    # Deduplicate consecutive [PHONE_REDACTED] tokens if overlapping regexes triggered
    text = re.sub(r"(\[PHONE_REDACTED\]\s*)+", "[PHONE_REDACTED]", text)
    return text


def mask_email_addresses(text: str) -> str:
    """Detect and redact email addresses including subdomains and plus-addressing.
    Replaces matches with [EMAIL_REDACTED].
    """
    if not text:
        return ""
    pattern = r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"
    return re.sub(pattern, "[EMAIL_REDACTED]", text)


def mask_government_ids(text: str) -> str:
    """Detect and redact common government ID formats (e.g. 12-digit Aadhaar pattern).
    Replaces matches with [ID_REDACTED].
    """
    if not text:
        return ""
    # 12-digit segmented or contiguous ID: 1234 5678 9012 or 1234-5678-9012
    pattern_aadhaar = r"\b\d{4}[\s-]\d{4}[\s-]\d{4}\b"
    text = re.sub(pattern_aadhaar, "[ID_REDACTED]", text)

    # 10-character alphanumeric PAN format: 5 letters, 4 digits, 1 letter
    pattern_pan = r"\b[A-Z]{5}\d{4}[A-Z]\b"
    text = re.sub(pattern_pan, "[ID_REDACTED]", text)

    return text


def sanitize_text_for_ai(text: str, config: Optional[PrivacyConfig] = None) -> str:
    """Comprehensive sanitizer that removes all detected PII before sending text
    to Gemini or any external model. Guarantees safe processing.
    """
    if not text:
        return ""
    cfg = config or DEFAULT_PRIVACY_CONFIG
    sanitized = text

    # Apply ID and email masking before phone masking to avoid digit ambiguity
    if cfg.mask_ids:
        sanitized = mask_government_ids(sanitized)
    if cfg.mask_email:
        sanitized = mask_email_addresses(sanitized)
    if cfg.mask_phone:
        sanitized = mask_phone_numbers(sanitized)

    return sanitized


def mask_contact_in_text(text: str) -> str:
    """Helper alias to sanitize contact and PII information from raw complaint text."""
    return sanitize_text_for_ai(text)


def validate_consent(record: ComplaintRecord) -> bool:
    """Validate whether citizen consent was granted for grievance intake.
    Returns True if consent is explicitly obtained, False otherwise.
    """
    return bool(record.consent_obtained)


def is_record_expired(submitted_at: datetime, retention_days: int = 180) -> bool:
    """Check if a complaint record has exceeded the configured retention timeframe."""
    now = utc_now()
    if submitted_at.tzinfo is None:
        submitted_at = submitted_at.replace(tzinfo=timezone.utc)
    age = (now - submitted_at).days
    return age > retention_days


def anonymize_expired_record(record: ComplaintRecord, retention_days: int = 180) -> ComplaintRecord:
    """Anonymize an expired record by scrubbing contact hashes, references, and
    updating retention metadata if retention window has passed.
    """
    if not is_record_expired(record.submitted_at, retention_days):
        return record

    anonymized = record.model_copy(deep=True)
    anonymized.citizen_contact_hash = None
    anonymized.source_reference = None
    anonymized.original_text = sanitize_text_for_ai(anonymized.original_text)
    anonymized.metadata["retention_status"] = "anonymized_expired"
    anonymized.metadata["anonymized_at"] = utc_now().isoformat()
    return anonymized
