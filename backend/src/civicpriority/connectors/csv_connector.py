"""CSV Connector for CivicPriority AI.
Ingests structured complaint CSV exports from grievance portals, surveys, or administrative dumps.
"""

import io
from pathlib import Path
from typing import Any, Union
import pandas as pd

from civicpriority.connectors.base import BaseConnector, ConnectorError
from civicpriority.models import ComplaintRecord, ComplaintSource


class CSVConnector(BaseConnector):
    """Parses and validates CSV complaint exports into standardized ComplaintRecords."""

    def __init__(self):
        super().__init__(default_source=ComplaintSource.CSV)

    def load(self, input_data: Union[str, bytes, Path, io.StringIO, io.BytesIO]) -> list[ComplaintRecord]:
        try:
            read_kwargs = {"comment": "#", "skip_blank_lines": True}
            if isinstance(input_data, (str, Path)) and Path(str(input_data)).is_file():
                df = pd.read_csv(input_data, **read_kwargs)
            elif isinstance(input_data, str):
                df = pd.read_csv(io.StringIO(input_data), **read_kwargs)
            elif isinstance(input_data, bytes):
                df = pd.read_csv(io.BytesIO(input_data), **read_kwargs)
            elif isinstance(input_data, (io.StringIO, io.BytesIO)):
                df = pd.read_csv(input_data, **read_kwargs)
            else:
                raise ConnectorError(f"Unsupported CSV input type: {type(input_data)}")
        except Exception as e:
            raise ConnectorError(f"Failed to parse CSV: {str(e)}") from e

        records: list[ComplaintRecord] = []
        errors: list[str] = []

        # Standardize column headers (lower case, stripped)
        col_map = {c: str(c).strip().lower().replace(" ", "_") for c in df.columns}
        df = df.rename(columns=col_map)

        for index, row in df.iterrows():
            try:
                # Text extraction with fallbacks
                raw_text = (
                    row.get("original_text")
                    or row.get("text")
                    or row.get("complaint")
                    or row.get("description")
                    or row.get("issue")
                )
                if not raw_text or pd.isna(raw_text) or len(str(raw_text).strip()) < 3:
                    continue  # skip invalid empty rows

                raw_text_str = str(raw_text).strip()
                masked_text = self.mask_contact_in_text(raw_text_str)

                # Locality extraction
                locality = (
                    row.get("locality")
                    or row.get("ward")
                    or row.get("area")
                    or row.get("location")
                    or "General Municipality"
                )
                locality_str = str(locality).strip()

                # Source extraction
                source_val = row.get("source")
                if source_val and str(source_val).strip() in [s.value for s in ComplaintSource]:
                    source = ComplaintSource(str(source_val).strip())
                else:
                    source = self.default_source

                # ID extraction or stable generation
                row_id = row.get("id") or row.get("complaint_id")
                if row_id and not pd.isna(row_id) and str(row_id).strip():
                    complaint_id = str(row_id).strip()
                else:
                    complaint_id = self.generate_stable_id(source.value, f"{index}_{masked_text}")

                # Contact hashing
                contact = row.get("contact") or row.get("phone") or row.get("email")
                contact_hash = self.hash_contact(str(contact)) if contact and not pd.isna(contact) else None

                # Optional coordinates
                lat = float(row.get("latitude")) if pd.notna(row.get("latitude")) else None
                lon = float(row.get("longitude")) if pd.notna(row.get("longitude")) else None

                record = ComplaintRecord(
                    id=complaint_id,
                    source=source,
                    source_reference=str(row.get("source_reference")) if pd.notna(row.get("source_reference")) else None,
                    original_text=masked_text,
                    original_language=str(row.get("language") or row.get("original_language") or "en").strip(),
                    translated_text=str(row.get("translated_text")).strip() if pd.notna(row.get("translated_text")) else None,
                    submitted_at=self.parse_datetime(row.get("submitted_at") or row.get("date")),
                    locality=locality_str,
                    district=str(row.get("district")).strip() if pd.notna(row.get("district")) else None,
                    state=str(row.get("state")).strip() if pd.notna(row.get("state")) else None,
                    latitude=lat,
                    longitude=lon,
                    citizen_contact_hash=contact_hash,
                    consent_obtained=bool(row.get("consent_obtained", True)),
                    metadata={"csv_row_index": int(index), "ingestion": "CSVConnector"},
                )
                records.append(record)
            except Exception as e:
                errors.append(f"Row {index} skipped: {str(e)}")

        if not records and errors:
            raise ConnectorError(f"No valid records could be extracted. Errors: {'; '.join(errors[:5])}")

        return records
