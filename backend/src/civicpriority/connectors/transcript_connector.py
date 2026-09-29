"""Public Meeting & Voice Transcript Connector for CivicPriority AI.
Extracts individual complaints from town halls, council meetings, and voice dictations.
"""

from pathlib import Path
import re
from typing import Any, Union

from civicpriority.connectors.base import BaseConnector, ConnectorError
from civicpriority.models import ComplaintRecord, ComplaintSource, utc_now


class TranscriptConnector(BaseConnector):
    """Parses multi-speaker meeting transcripts and voice transcripts into individual ComplaintRecords."""

    def __init__(self, is_voice: bool = False):
        default_source = ComplaintSource.VOICE_TRANSCRIPT if is_voice else ComplaintSource.PUBLIC_MEETING
        super().__init__(default_source=default_source)

    def load(self, input_data: Union[str, Path]) -> list[ComplaintRecord]:
        is_file_input = isinstance(input_data, Path)
        if isinstance(input_data, str):
            try:
                is_file_input = Path(input_data).is_file()
            except (OSError, ValueError):
                # Long or malformed transcript text is content, not a candidate path.
                is_file_input = False

        if is_file_input:
            try:
                with open(input_data, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                raise ConnectorError(f"Failed to read transcript: {e}") from e
        elif isinstance(input_data, str):
            content = input_data
        else:
            raise ConnectorError("TranscriptConnector requires a string or file path.")

        content = content.strip()
        if not content:
            raise ConnectorError("Transcript content cannot be empty.")

        # Identify meeting metadata (e.g. Header line: "Public Hearing: Ward 12 Council Hall, Date: 2026-03-15")
        meeting_locality = "General Council"
        meeting_loc_match = re.search(r"Meeting\s+Location:\s*(.+)$", content, re.MULTILINE | re.IGNORECASE)
        if meeting_loc_match:
            meeting_locality = meeting_loc_match.group(1).strip()

        # Split turns by speaker pattern:
        # e.g. "Speaker [Citizen 1 - Ward 12]: ...", "Citizen 2:", "[00:14:20] Resident (Ward 7):"
        speaker_pattern = re.compile(
            r"(?:^|\n)\s*(?:\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s*)?(?:Speaker\s+\d+|Citizen\s+\d+|Resident|Participant|Attendee|Parent|Moderator|Chair|Q\d+)(?:\s*\[([^\]]+)\]|\s*\(([^)]+)\))?:\s*",
            re.IGNORECASE,
        )

        splits = list(speaker_pattern.finditer(content))
        records: list[ComplaintRecord] = []

        if not splits:
            # Fallback: treat paragraphs as discrete citizen interventions
            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 20]
            for idx, para in enumerate(paragraphs):
                # Search for ward mention in paragraph
                ward_match = re.search(r"(Ward\s+\d+|Sector\s+\d+|Village\s+\w+)", para, re.IGNORECASE)
                loc = ward_match.group(1) if ward_match else meeting_locality
                masked = self.mask_contact_in_text(para)
                rec_id = self.generate_stable_id(self.default_source.value, f"turn_{idx}_{masked[:80]}")
                records.append(
                    ComplaintRecord(
                        id=rec_id,
                        source=self.default_source,
                        source_reference=f"Turn-{idx + 1}",
                        original_text=masked,
                        original_language="en",
                        submitted_at=utc_now(),
                        locality=loc,
                        consent_obtained=True,
                        metadata={"type": "transcript_turn", "index": idx},
                    )
                )
        else:
            for i, match in enumerate(splits):
                start = match.end()
                end = splits[i + 1].start() if i + 1 < len(splits) else len(content)
                turn_text = content[start:end].strip()

                matched_tag = match.group(0).lower()
                # Skip moderator / chair announcements
                if "moderator" in matched_tag or "chair" in matched_tag:
                    continue

                if len(turn_text) < 15:
                    continue  # skip brief remarks like "Thank you" or "Yes"

                # Check if speaker metadata contained locality
                speaker_meta = match.group(1) or match.group(2) or ""
                loc = meeting_locality
                if speaker_meta:
                    ward_m = re.search(r"(Ward\s+\d+|Sector\s+\d+|Village\s+\w+)", speaker_meta, re.IGNORECASE)
                    if ward_m:
                        loc = ward_m.group(1)

                # Also search text if still general
                if loc == meeting_locality:
                    text_ward = re.search(r"(Ward\s+\d+|Sector\s+\d+|Village\s+\w+)", turn_text, re.IGNORECASE)
                    if text_ward:
                        loc = text_ward.group(1)

                masked = self.mask_contact_in_text(turn_text)
                rec_id = self.generate_stable_id(self.default_source.value, f"turn_{i}_{masked[:80]}")

                records.append(
                    ComplaintRecord(
                        id=rec_id,
                        source=self.default_source,
                        source_reference=f"Meeting-Turn-{i + 1}",
                        original_text=masked,
                        original_language="hi" if any("\u0900" <= ch <= "\u097f" for ch in masked) else "en",
                        submitted_at=utc_now(),
                        locality=loc,
                        consent_obtained=True,
                        metadata={"speaker_meta": speaker_meta, "turn_index": i},
                    )
                )

        if not records:
            raise ConnectorError("Could not extract any complaint statements from transcript.")

        return records
