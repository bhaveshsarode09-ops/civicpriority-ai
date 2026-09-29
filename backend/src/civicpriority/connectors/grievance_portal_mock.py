"""Grievance Portal Mock Connector for CivicPriority AI.
Simulates structured grievance tickets from municipal or state e-governance portals.
NOTE: Marked as Synthetic demonstration data — not official government data.
"""

from typing import Any, Union
import json
from civicpriority.connectors.base import BaseConnector, ConnectorError
from civicpriority.models import ComplaintRecord, ComplaintSource


class GrievancePortalMockConnector(BaseConnector):
    """Parses ticket exports from municipal grievance management systems."""

    DISCLAIMER = "Synthetic demonstration data — not official government data."

    def __init__(self):
        super().__init__(default_source=ComplaintSource.GRIEVANCE_PORTAL)

    def load(self, input_data: Union[list[dict[str, Any]], str]) -> list[ComplaintRecord]:
        if isinstance(input_data, str):
            try:
                tickets = json.loads(input_data)
            except Exception as e:
                raise ConnectorError(f"Failed to parse grievance portal JSON: {e}") from e
        elif isinstance(input_data, list):
            tickets = input_data
        else:
            raise ConnectorError("GrievancePortalMockConnector expects a JSON string or list of dicts.")

        records: list[ComplaintRecord] = []
        for ticket in tickets:
            description = (
                ticket.get("grievance_description")
                or ticket.get("details")
                or ticket.get("complaint_text")
                or ticket.get("text")
            )
            if not description or len(str(description).strip()) < 5:
                continue

            masked = self.mask_contact_in_text(str(description).strip())
            ticket_id = ticket.get("ticket_id") or ticket.get("token") or ticket.get("id")
            if ticket_id:
                rec_id = f"CMP-GRV-{ticket_id}"
            else:
                rec_id = self.generate_stable_id(self.default_source.value, masked[:80])

            # Citizen phone/email hashed
            contact = ticket.get("citizen_phone") or ticket.get("citizen_email") or ticket.get("contact")
            contact_hash = self.hash_contact(str(contact)) if contact else None

            locality = (
                ticket.get("ward")
                or ticket.get("locality")
                or ticket.get("zone")
                or "General Municipality"
            )

            records.append(
                ComplaintRecord(
                    id=rec_id,
                    source=self.default_source,
                    source_reference=str(ticket_id) if ticket_id else None,
                    original_text=masked,
                    original_language=ticket.get("language", "en"),
                    submitted_at=self.parse_datetime(ticket.get("created_at") or ticket.get("date")),
                    locality=str(locality),
                    district=ticket.get("district"),
                    state=ticket.get("state"),
                    citizen_contact_hash=contact_hash,
                    consent_obtained=bool(ticket.get("consent_obtained", True)),
                    metadata={
                        "portal_department": ticket.get("department_tag"),
                        "portal_priority_claim": ticket.get("citizen_urgency"),
                        "synthetic_disclaimer": self.DISCLAIMER,
                    },
                )
            )

        return records
