"""Base connector interface for CivicPriority AI data ingestion.
Defines the common protocol, stable ID hashing, contact masking, and error reporting.
"""

from abc import ABC, abstractmethod
import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Optional

from civicpriority.models import ComplaintRecord, ComplaintSource, utc_now


class ConnectorError(Exception):
    """Custom exception raised when connector ingestion fails."""
    pass


class BaseConnector(ABC):
    """Abstract base class that all ingestion connectors must inherit from."""

    def __init__(self, default_source: ComplaintSource):
        self.default_source = default_source

    @abstractmethod
    def load(self, input_data: Any) -> list[ComplaintRecord]:
        """Ingest input data and return a list of validated ComplaintRecord objects."""
        pass

    @staticmethod
    def generate_stable_id(source: str, unique_seed: str, prefix: str = "CMP") -> str:
        """Generate a deterministic, stable identifier based on source and content."""
        hasher = hashlib.sha256()
        hasher.update(source.encode("utf-8"))
        hasher.update(unique_seed.strip().encode("utf-8"))
        digest = hasher.hexdigest()[:8].upper()
        return f"{prefix}-{source[:3].upper()}-{digest}"

    @staticmethod
    def hash_contact(contact: Optional[str], salt: str = "civic_privacy_salt_2026") -> Optional[str]:
        """Generate a salted SHA-256 hash of personal contact information."""
        if not contact or not contact.strip():
            return None
        cleaned = re.sub(r"[\s\-\(\)\+]", "", contact.strip().lower())
        hasher = hashlib.sha256()
        hasher.update(salt.encode("utf-8"))
        hasher.update(cleaned.encode("utf-8"))
        return hasher.hexdigest()

    @staticmethod
    def mask_contact_in_text(text: str) -> str:
        """Redact phone numbers and email addresses in complaint text before saving."""
        if not text:
            return ""
        # Redact emails
        text = re.sub(
            r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            "[EMAIL_REDACTED]",
            text,
        )
        # Redact 10-12 digit phone numbers
        text = re.sub(
            r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "[PHONE_REDACTED]",
            text,
        )
        # Indian 10-digit mobile pattern
        text = re.sub(
            r"\b[6-9]\d{9}\b",
            "[PHONE_REDACTED]",
            text,
        )
        return text

    @staticmethod
    def parse_datetime(dt_val: Any) -> datetime:
        """Safely parse various datetime formats into UTC datetime."""
        if isinstance(dt_val, datetime):
            return dt_val.astimezone(timezone.utc) if dt_val.tzinfo else dt_val.replace(tzinfo=timezone.utc)
        if isinstance(dt_val, str) and dt_val.strip():
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
                try:
                    dt = datetime.strptime(dt_val.strip(), fmt)
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            try:
                dt = datetime.fromisoformat(dt_val.strip())
                return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return utc_now()
