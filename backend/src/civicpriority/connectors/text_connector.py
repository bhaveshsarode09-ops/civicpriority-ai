"""Text File & Petition Connector for CivicPriority AI.
Ingests citizen letters, typed representations, and document text exports.
"""

from pathlib import Path
import re
from typing import Any, Union

from civicpriority.connectors.base import BaseConnector, ConnectorError
from civicpriority.models import ComplaintRecord, ComplaintSource, utc_now


class TextFileConnector(BaseConnector):
    """Processes plain text documents, official representations, and letter extracts."""

    def __init__(self):
        super().__init__(default_source=ComplaintSource.LETTER_PDF)

    def load(self, input_data: Union[str, Path]) -> list[ComplaintRecord]:
        is_file_input = isinstance(input_data, Path)
        if isinstance(input_data, str):
            try:
                is_file_input = Path(input_data).is_file()
            except (OSError, ValueError):
                # Long or malformed text is content, not a candidate path.
                is_file_input = False

        if is_file_input:
            try:
                with open(input_data, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                raise ConnectorError(f"Failed to read file: {e}") from e
        elif isinstance(input_data, str):
            content = input_data
        else:
            raise ConnectorError("TextFileConnector expects a filepath string or text string.")

        content = content.strip()
        if not content:
            raise ConnectorError("Provided text content is empty.")

        # Extract metadata if structured headers exist
        locality = "General Municipality"
        contact_raw = None
        submitted_at = utc_now()
        source_ref = None

        # Regex header extractors
        loc_match = re.search(r"^\s*(?:Locality|Ward|Area|Location):\s*(.+)$", content, re.MULTILINE | re.IGNORECASE)
        if loc_match:
            locality = loc_match.group(1).strip()

        date_match = re.search(r"^\s*(?:Date|Submitted|Dated):\s*(.+)$", content, re.MULTILINE | re.IGNORECASE)
        if date_match:
            submitted_at = self.parse_datetime(date_match.group(1).strip())

        contact_match = re.search(r"^\s*(?:From|Contact|Phone|Email):\s*(.+)$", content, re.MULTILINE | re.IGNORECASE)
        if contact_match:
            contact_raw = contact_match.group(1).strip()

        ref_match = re.search(r"^\s*(?:Ref|Subject|Petition ID):\s*(.+)$", content, re.MULTILINE | re.IGNORECASE)
        if ref_match:
            source_ref = ref_match.group(1).strip()

        # Clean body text
        masked_text = self.mask_contact_in_text(content)
        contact_hash = self.hash_contact(contact_raw) if contact_raw else None
        complaint_id = self.generate_stable_id(self.default_source.value, masked_text[:120])

        record = ComplaintRecord(
            id=complaint_id,
            source=self.default_source,
            source_reference=source_ref,
            original_text=masked_text,
            original_language="en",
            submitted_at=submitted_at,
            locality=locality,
            citizen_contact_hash=contact_hash,
            consent_obtained=True,
            metadata={"format": "letter_text", "ingestion": "TextFileConnector"},
        )
        return [record]
