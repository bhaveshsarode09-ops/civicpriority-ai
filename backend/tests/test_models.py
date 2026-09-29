"""Unit tests for Phase 1 ML data models, enums, validation rules, and SQLite persistence.
"""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from civicpriority.models import (
    ComplaintCategory,
    ComplaintRecord,
    ComplaintSource,
    IssueCluster,
    IssueStatus,
    PriorityLevel,
    ProcessedComplaint,
)
from civicpriority.database import Database


def test_complaint_categories_completeness():
    """Verify all 11 required civic categories are defined."""
    expected_categories = {
        "Roads and transport",
        "Water and sanitation",
        "Education",
        "Healthcare",
        "Agriculture",
        "Electricity",
        "Pollution and environment",
        "Public safety",
        "Housing",
        "Digital public infrastructure",
        "Other",
    }
    actual_categories = {c.value for c in ComplaintCategory}
    assert expected_categories == actual_categories


def test_complaint_record_valid():
    """Verify standard instantiation of ComplaintRecord."""
    record = ComplaintRecord(
        id="CMP-TEST-001",
        source=ComplaintSource.DIRECT_WEB,
        original_text="Broken water pipe leaking clean water for 3 days near Ward 4 market.",
        original_language="en",
        locality="Ward 4",
        district="Central District",
        state="State Capital",
        latitude=18.5204,
        longitude=73.8567,
    )
    assert record.id == "CMP-TEST-001"
    assert record.source == "direct_web"
    assert record.consent_obtained is True
    assert record.attachment_paths == []
    assert record.citizen_contact_hash is None

    # JSON roundtrip
    json_str = record.model_dump_json()
    reconstructed = ComplaintRecord.model_validate_json(json_str)
    assert reconstructed.id == record.id
    assert reconstructed.original_text == record.original_text


def test_complaint_record_validation_errors():
    """Verify validation constraints on ComplaintRecord."""
    # Blank ID
    with pytest.raises(ValidationError):
        ComplaintRecord(
            id="   ",
            source=ComplaintSource.DIRECT_WEB,
            original_text="Valid text here",
            locality="Ward 1",
        )

    # Text too short
    with pytest.raises(ValidationError):
        ComplaintRecord(
            id="CMP-002",
            source=ComplaintSource.DIRECT_WEB,
            original_text="no",
            locality="Ward 1",
        )

    # Latitude out of bounds
    with pytest.raises(ValidationError):
        ComplaintRecord(
            id="CMP-003",
            source=ComplaintSource.DIRECT_WEB,
            original_text="Valid text here",
            locality="Ward 1",
            latitude=95.0,  # Max is 90
        )


def test_processed_complaint_valid():
    """Verify processed complaint creation and score bounds."""
    processed = ProcessedComplaint(
        complaint_id="CMP-TEST-001",
        language="en",
        translated_text="Broken water pipe leaking clean water for 3 days near Ward 4 market.",
        summary="Water supply pipeline rupture in Ward 4 commercial area.",
        category=ComplaintCategory.WATER_AND_SANITATION,
        subcategory="Drinking Water Pipe Leak",
        location="Ward 4 Market Area",
        department="Municipal Water Supply Board",
        severity_score=78.5,
        urgency_score=85.0,
        estimated_people_affected=1200,
        vulnerable_groups=["Market vendors", "Local residents"],
        infrastructure_gap_score=70.0,
        keywords=["water", "leak", "pipeline", "pressure"],
        entities=["Ward 4 Market"],
        ai_confidence=0.92,
        requires_human_review=False,
    )
    assert processed.severity_score == 78.5
    assert processed.category == "Water and sanitation"
    assert processed.estimated_people_affected == 1200

    # JSON serialization
    json_data = processed.model_dump_json()
    reconstructed = ProcessedComplaint.model_validate_json(json_data)
    assert reconstructed.summary == processed.summary
    assert reconstructed.category == processed.category


def test_processed_complaint_score_boundaries():
    """Verify scores outside 0-100 trigger validation errors."""
    with pytest.raises(ValidationError):
        ProcessedComplaint(
            complaint_id="CMP-TEST-002",
            language="en",
            translated_text="Test",
            summary="Test",
            category=ComplaintCategory.EDUCATION,
            location="Ward 12",
            department="Education Department",
            severity_score=105.0,  # > 100
            urgency_score=50.0,
        )

    with pytest.raises(ValidationError):
        ProcessedComplaint(
            complaint_id="CMP-TEST-003",
            language="en",
            translated_text="Test",
            summary="Test",
            category=ComplaintCategory.ROADS_AND_TRANSPORT,
            location="Ward 5",
            department="Public Works",
            severity_score=-5.0,  # < 0
            urgency_score=50.0,
        )


def test_issue_cluster_valid_and_auto_count():
    """Verify IssueCluster creation and auto-sync of complaint_count."""
    cluster = IssueCluster(
        cluster_id="CLU-WARD12-EDU-01",
        title="Severe classroom deficit and lack of drinking water in Ward 12 Government School",
        description="Multiple citizen reports indicating children lack clean drinking water and classroom infrastructure.",
        category=ComplaintCategory.EDUCATION,
        locality="Ward 12",
        complaint_ids=["CMP-101", "CMP-102", "CMP-103"],
        complaint_count=1,  # Intentional mismatch to test validator sync
        unique_sources=["direct_web", "public_meeting", "messaging"],
        average_severity=88.0,
        average_urgency=84.0,
        estimated_people_affected=650,
        vulnerable_groups=["School Children", "Teachers"],
        infrastructure_gap_score=90.0,
        priority_score=91.4,
        priority_level=PriorityLevel.CRITICAL,
        recommendation="Deploy emergency clean water tanker and allocate interim modular classrooms.",
        explanation="Ranked highly because it directly impacts school children, involves basic sanitation, and was raised across 3 separate channels.",
        confidence=0.94,
        fairness_warnings=[],
        requires_human_review=False,
        status=IssueStatus.OPEN,
        assigned_department="Department of School Education",
    )
    # Check validator synced complaint_count to length of complaint_ids
    assert cluster.complaint_count == 3
    assert cluster.priority_level == "Critical"
    assert cluster.status == "Open"

    # JSON roundtrip
    json_data = cluster.model_dump_json()
    reconstructed = IssueCluster.model_validate_json(json_data)
    assert reconstructed.cluster_id == cluster.cluster_id
    assert reconstructed.priority_score == 91.4


def test_sqlite_persistence_roundtrip():
    """Test full CRUD roundtrip in SQLite database."""
    db = Database(":memory:")

    # 1. Test Raw Complaint persistence
    record = ComplaintRecord(
        id="CMP-SQLITE-01",
        source=ComplaintSource.PUBLIC_MEETING,
        source_reference="Minute-Item-42",
        original_text="वार्ड 12 के सरकारी स्कूल में बच्चों के लिए पर्याप्त कक्षाएं नहीं हैं और पीने का साफ पानी भी नहीं है।",
        original_language="hi",
        translated_text="The government school in Ward 12 lacks adequate classrooms for children and also lacks clean drinking water.",
        locality="Ward 12",
        district="East District",
        state="Central State",
        attachment_paths=["/docs/meeting_transcript.pdf"],
        consent_obtained=True,
    )
    db.save_raw_complaint(record)
    fetched_record = db.get_raw_complaint("CMP-SQLITE-01")
    assert fetched_record is not None
    assert fetched_record.original_language == "hi"
    assert fetched_record.locality == "Ward 12"
    assert fetched_record.attachment_paths == ["/docs/meeting_transcript.pdf"]

    # 2. Test Processed Complaint persistence
    processed = ProcessedComplaint(
        complaint_id="CMP-SQLITE-01",
        language="hi",
        translated_text=record.translated_text,
        summary="Classroom shortage and missing potable drinking water at Ward 12 school.",
        category=ComplaintCategory.EDUCATION,
        subcategory="School Infrastructure & Sanitation",
        location="Ward 12 Government School",
        department="Education & Child Welfare",
        severity_score=92.0,
        urgency_score=88.0,
        estimated_people_affected=650,
        vulnerable_groups=["Children"],
        infrastructure_gap_score=95.0,
        keywords=["school", "classrooms", "drinking water", "children"],
        entities=["Ward 12 Government School"],
        ai_confidence=0.96,
        requires_human_review=False,
    )
    db.save_processed_complaint(processed)
    fetched_processed = db.get_processed_complaint("CMP-SQLITE-01")
    assert fetched_processed is not None
    assert fetched_processed.category == ComplaintCategory.EDUCATION
    assert fetched_processed.vulnerable_groups == ["Children"]
    assert fetched_processed.severity_score == 92.0

    # 3. Test Issue Cluster persistence and status update
    cluster = IssueCluster(
        cluster_id="CLU-SQLITE-01",
        title="Ward 12 School Sanitation & Classroom Crisis",
        description="Children studying without potable water and sufficient classroom facilities.",
        category=ComplaintCategory.EDUCATION,
        locality="Ward 12",
        complaint_ids=["CMP-SQLITE-01"],
        complaint_count=1,
        unique_sources=["public_meeting"],
        average_severity=92.0,
        average_urgency=88.0,
        estimated_people_affected=650,
        vulnerable_groups=["Children"],
        infrastructure_gap_score=95.0,
        priority_score=93.5,
        priority_level=PriorityLevel.CRITICAL,
        recommendation="Immediate delivery of clean drinking water solution and modular classroom provisioning.",
        explanation="High severity affecting vulnerable children with no access to basic sanitary water.",
        confidence=0.95,
        fairness_warnings=[],
        requires_human_review=False,
        status=IssueStatus.OPEN,
    )
    db.save_cluster(cluster)
    fetched_cluster = db.get_cluster("CLU-SQLITE-01")
    assert fetched_cluster is not None
    assert fetched_cluster.priority_level == PriorityLevel.CRITICAL
    assert fetched_cluster.status == IssueStatus.OPEN

    # Update status to Under Review
    updated = db.update_cluster_status(
        "CLU-SQLITE-01",
        IssueStatus.UNDER_REVIEW,
        assigned_department="Municipal Education Directorate",
    )
    assert updated is not None
    assert updated.status == IssueStatus.UNDER_REVIEW
    assert updated.assigned_department == "Municipal Education Directorate"

    # List clusters filter by category
    filtered = db.list_clusters(category="Education")
    assert len(filtered) == 1
    assert filtered[0].cluster_id == "CLU-SQLITE-01"
