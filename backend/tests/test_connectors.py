"""Unit tests for Phase 2 data connectors and the 52-record synthetic dataset.
"""

from pathlib import Path
import pytest

from civicpriority.connectors import (
    ConnectorError,
    CSVConnector,
    GrievancePortalMockConnector,
    MessagingMockConnector,
    SocialMediaMockConnector,
    TextFileConnector,
    TranscriptConnector,
)
from civicpriority.models import ComplaintSource


def test_csv_connector_sample_data():
    """Verify CSVConnector parses all 52 complaints from sample_complaints.csv."""
    csv_path = Path("backend/data/sample_complaints.csv")
    assert csv_path.exists(), "Sample CSV dataset must exist."

    connector = CSVConnector()
    records = connector.load(csv_path)

    # 1. Total records count check
    assert len(records) == 52

    # 2. Check the specific Hindi Ward 12 complaint
    w12_hindi = next((r for r in records if r.id == "CMP-SYN-001"), None)
    assert w12_hindi is not None
    assert w12_hindi.original_language == "hi"
    assert "वार्ड 12 के सरकारी स्कूल में बच्चों के लिए पर्याप्त कक्षाएं नहीं हैं और पीने का साफ पानी भी नहीं है।" in w12_hindi.original_text
    assert w12_hindi.locality == "Ward 12"
    assert w12_hindi.source == ComplaintSource.PUBLIC_MEETING
    # Contact (9876543210) should be hashed, not raw
    assert w12_hindi.citizen_contact_hash is not None
    assert "9876543210" not in str(w12_hindi.citizen_contact_hash)

    # 3. Check language diversity (English, Hindi, Marathi)
    languages = {r.original_language for r in records}
    assert {"en", "hi", "mr"}.issubset(languages)

    # 4. Check 5 distinct wards
    localities = {r.locality for r in records}
    assert {"Ward 4", "Ward 7", "Ward 9", "Ward 12", "Ward 15"}.issubset(localities)

    # 5. Check multiple sources
    sources = {r.source for r in records}
    assert {
        ComplaintSource.PUBLIC_MEETING,
        ComplaintSource.DIRECT_WEB,
        ComplaintSource.MESSAGING,
        ComplaintSource.LETTER_PDF,
        ComplaintSource.SOCIAL_MEDIA,
        ComplaintSource.GRIEVANCE_PORTAL,
    }.issubset(sources)


def test_csv_connector_malformed():
    """Verify CSVConnector raises ConnectorError on unparseable input."""
    connector = CSVConnector()
    with pytest.raises(ConnectorError):
        connector.load(b"invalid\x00binary\xffdata\xfe")


def test_text_file_connector():
    """Verify TextFileConnector extracts metadata, masks PII, and returns valid ComplaintRecord."""
    letter_text = """
    Locality: Ward 7
    Date: 2026-03-04
    From: citizen_w7@example.com, Phone: 9876543210
    Subject: Broken Bridge on Main Canal

    To the Municipal Commissioner,
    The footbridge on Main Canal in Ward 7 has collapsed side rails.
    Call me at 9876543210 or email citizen_w7@example.com for site inspection.
    """
    connector = TextFileConnector()
    records = connector.load(letter_text)

    assert len(records) == 1
    rec = records[0]
    assert rec.locality == "Ward 7"
    assert rec.source == ComplaintSource.LETTER_PDF
    # PII in text must be masked
    assert "[PHONE_REDACTED]" in rec.original_text
    assert "[EMAIL_REDACTED]" in rec.original_text
    assert "9876543210" not in rec.original_text
    assert "citizen_w7@example.com" not in rec.original_text
    # Hashed contact exists
    assert rec.citizen_contact_hash is not None


def test_transcript_connector_multi_speaker():
    """Verify TranscriptConnector splits turns and extracts individual grievances."""
    transcript = """
    Public Hearing - Ward Committee Meeting
    Meeting Location: Ward 12 Municipal Center

    Speaker 1 [Resident - Ward 12]:
    Good morning officials. The government school in Ward 12 lacks clean drinking water and kids have to carry water bottles from home. Call me at 9811223344.

    Speaker 2 [Citizen - Ward 7]:
    वार्ड 7 की मुख्य सड़क पर दो फीट गहरा गड्ढा है जिससे हर रोज बाइक चालक गिर रहे हैं।

    Speaker 3 [Moderator]:
    Thank you. Next speaker.

    Speaker 4 [Parent - Ward 12]:
    Regarding the Ward 12 school, classrooms are so crowded that 70 children are packed in one small room.
    """
    connector = TranscriptConnector()
    records = connector.load(transcript)

    # Speaker 3 is a brief remark (< 15 chars) so should be skipped; 3 grievance records should remain
    assert len(records) == 3
    assert records[0].locality == "Ward 12"
    assert "[PHONE_REDACTED]" in records[0].original_text
    assert records[1].locality == "Ward 7"
    assert records[1].original_language == "hi"
    assert records[2].locality == "Ward 12"


def test_social_media_mock_connector():
    """Verify SocialMediaMockConnector marks synthetic notice and parses feed."""
    posts = [
        {
            "post_id": "TWT-1001",
            "handle": "@concerned_w15",
            "text": "Huge power outage in Ward 15! Transformer burned out 2 days ago. Please send maintenance crew #Ward15Power",
            "locality": "Ward 15",
            "likes": 42,
            "shares": 15,
            "timestamp": "2026-03-05 14:00:00",
        }
    ]
    connector = SocialMediaMockConnector()
    records = connector.load(posts)

    assert len(records) == 1
    rec = records[0]
    assert rec.id == "CMP-SOC-TWT-1001"
    assert rec.source == ComplaintSource.SOCIAL_MEDIA
    assert rec.locality == "Ward 15"
    assert rec.metadata["synthetic_disclaimer"] == "Synthetic demonstration data — not official government data."
    assert rec.citizen_contact_hash is not None


def test_grievance_portal_mock_connector():
    """Verify GrievancePortalMockConnector parses tickets and includes disclaimer."""
    tickets = [
        {
            "ticket_id": "GRV-2026-99",
            "complaint_text": "Water pipeline leak near Ward 4 tank causing road flooding. Contact: 9988776655",
            "ward": "Ward 4",
            "citizen_phone": "9988776655",
            "department_tag": "Water & Sewerage",
            "citizen_urgency": "High",
        }
    ]
    connector = GrievancePortalMockConnector()
    records = connector.load(tickets)

    assert len(records) == 1
    rec = records[0]
    assert rec.id == "CMP-GRV-GRV-2026-99"
    assert rec.source == ComplaintSource.GRIEVANCE_PORTAL
    assert rec.locality == "Ward 4"
    assert "[PHONE_REDACTED]" in rec.original_text
    assert rec.metadata["synthetic_disclaimer"] == "Synthetic demonstration data — not official government data."


def test_messaging_mock_connector():
    """Verify MessagingMockConnector parses WhatsApp/SMS conversation payloads."""
    chats = [
        {
            "message_id": "WA-8801",
            "sender_phone": "+919876543210",
            "message": "Hello, streetlights on Ward 9 bus road are broken for 2 weeks. Women feeling unsafe at night.",
            "ward": "Ward 9",
            "sent_at": "2026-03-04 21:15:00",
        }
    ]
    connector = MessagingMockConnector()
    records = connector.load(chats)

    assert len(records) == 1
    rec = records[0]
    assert rec.id == "CMP-MSG-WA-8801"
    assert rec.source == ComplaintSource.MESSAGING
    assert rec.locality == "Ward 9"
    assert rec.citizen_contact_hash is not None
    assert rec.metadata["synthetic_disclaimer"] == "Synthetic demonstration data — not official government data."
