"""Messaging App Mock Connector for CivicPriority AI.
Simulates citizen messaging helpline exports (e.g. municipal WhatsApp / SMS grievance bot).
NOTE: Marked as Synthetic demonstration data — not official government data.
"""

from typing import Any, Union
import json
from civicpriority.connectors.base import BaseConnector, ConnectorError
from civicpriority.models import ComplaintRecord, ComplaintSource


class MessagingMockConnector(BaseConnector):
    """Parses incoming message conversations from municipal messaging helplines."""

    DISCLAIMER = "Synthetic demonstration data — not official government data."

    def __init__(self):
        super().__init__(default_source=ComplaintSource.MESSAGING)

    def load(self, input_data: Union[list[dict[str, Any]], str]) -> list[ComplaintRecord]:
        if isinstance(input_data, str):
            try:
                chats = json.loads(input_data)
            except Exception as e:
                raise ConnectorError(f"Failed to parse messaging JSON: {e}") from e
        elif isinstance(input_data, list):
            chats = input_data
        else:
            raise ConnectorError("MessagingMockConnector requires a list of chat message objects or JSON string.")

        records: list[ComplaintRecord] = []
        for chat in chats:
            # Handle either raw text or conversation turn
            msg_text = chat.get("message") or chat.get("text") or chat.get("body")
            if not msg_text or len(str(msg_text).strip()) < 4:
                continue

            raw_text = str(msg_text).strip()
            masked_text = self.mask_contact_in_text(raw_text)

            sender_phone = chat.get("sender_phone") or chat.get("sender_id") or chat.get("from")
            contact_hash = self.hash_contact(str(sender_phone)) if sender_phone else None

            chat_id = chat.get("message_id") or chat.get("chat_id")
            if chat_id:
                rec_id = f"CMP-MSG-{chat_id}"
            else:
                rec_id = self.generate_stable_id(self.default_source.value, masked_text[:60])

            locality = chat.get("ward") or chat.get("locality") or chat.get("location") or "General Municipality"

            records.append(
                ComplaintRecord(
                    id=rec_id,
                    source=self.default_source,
                    source_reference=str(chat_id) if chat_id else None,
                    original_text=masked_text,
                    original_language=chat.get("language", "en"),
                    submitted_at=self.parse_datetime(chat.get("sent_at") or chat.get("timestamp")),
                    locality=str(locality),
                    district=chat.get("district"),
                    citizen_contact_hash=contact_hash,
                    consent_obtained=bool(chat.get("consent_obtained", True)),
                    metadata={
                        "channel": chat.get("channel", "WhatsApp/SMS"),
                        "bot_session": chat.get("session_id"),
                        "synthetic_disclaimer": self.DISCLAIMER,
                    },
                )
            )

        return records
