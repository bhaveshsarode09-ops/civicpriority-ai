"""Unit tests for Phase 5 Similarity and Issue Clustering.
"""

from pathlib import Path
import pytest

from civicpriority.ai import MockAIProvider
from civicpriority.clustering import IssueClusterer, normalize_text
from civicpriority.connectors import CSVConnector
from civicpriority.models import ComplaintCategory, ComplaintRecord, ComplaintSource, PriorityLevel


@pytest.fixture
def processed_sample_data():
    """Load and process sample complaints dataset."""
    csv_path = Path("backend/data/sample_complaints.csv")
    connector = CSVConnector()
    raw_records = connector.load(csv_path)

    provider = MockAIProvider()
    processed_list = [provider.process_complaint_full(r) for r in raw_records]
    raw_map = {r.id: r for r in raw_records}
    return processed_list, raw_map


def test_text_normalization():
    """Verify text normalization removes punctuation and redaction tokens."""
    raw = "Call me at [PHONE_REDACTED]! Road is broken... near Ward 7."
    norm = normalize_text(raw)
    assert "phone_redacted" not in norm
    assert "!" not in norm
    assert norm == "call me at road is broken near ward 7"


def test_ward_12_school_clustering(processed_sample_data):
    """Verify that multiple reports about the Ward 12 school merge into a single cluster."""
    processed_list, raw_map = processed_sample_data

    # Filter complaints related to Ward 12 school
    # (CMP-SYN-001 through CMP-SYN-006)
    w12_school_cids = {f"CMP-SYN-{i:03d}" for i in range(1, 7)}
    w12_items = [p for p in processed_list if p.complaint_id in w12_school_cids]
    assert len(w12_items) == 6

    clusterer = IssueClusterer()
    clusters = clusterer.cluster_complaints(w12_items, raw_map)

    # All 6 complaints should merge into 1 unified cluster
    assert len(clusters) == 1
    school_cluster = clusters[0]

    # Verify ID preservation
    assert set(school_cluster.complaint_ids) == w12_school_cids
    assert school_cluster.complaint_count == 6

    # Verify multi-source representation
    assert len(school_cluster.unique_sources) >= 4
    assert "public_meeting" in school_cluster.unique_sources
    assert "direct_web" in school_cluster.unique_sources
    assert "messaging" in school_cluster.unique_sources

    # Verify metrics and vulnerable groups
    assert "Children" in school_cluster.vulnerable_groups
    assert school_cluster.locality == "Ward 12"
    assert school_cluster.category == ComplaintCategory.EDUCATION
    assert school_cluster.priority_level in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]
    assert school_cluster.priority_score >= 80.0


def test_different_wards_and_categories_do_not_merge(processed_sample_data):
    """Verify that complaints from different wards and categories remain separate."""
    processed_list, raw_map = processed_sample_data

    # CMP-SYN-001: Ward 12 School
    # CMP-SYN-007: Ward 7 Road Crater
    # CMP-SYN-012: Ward 4 Water Pipeline Rupture
    # CMP-SYN-017: Ward 9 Doctor Shortage
    # CMP-SYN-022: Ward 15 Transformer Fire
    sample_cids = {"CMP-SYN-001", "CMP-SYN-007", "CMP-SYN-012", "CMP-SYN-017", "CMP-SYN-022"}
    items = [p for p in processed_list if p.complaint_id in sample_cids]
    assert len(items) == 5

    clusterer = IssueClusterer()
    clusters = clusterer.cluster_complaints(items, raw_map)

    # All 5 disparate complaints should form distinct individual clusters
    assert len(clusters) == 5
    cluster_localities = {cl.locality for cl in clusters}
    assert {"Ward 12", "Ward 7", "Ward 4", "Ward 9", "Ward 15"} == cluster_localities


def test_same_ward_different_categories_separated(processed_sample_data):
    """Verify complaints in the same ward with distinct problems are not falsely merged."""
    processed_list, raw_map = processed_sample_data

    # In Ward 12:
    # CMP-SYN-001: School classrooms & water (Education)
    # CMP-SYN-026: Sewage overflowing near clinic (Water & Sanitation)
    # CMP-SYN-039: Park seating & public toilet (Water/Sanitation / Other)
    # CMP-SYN-049: Railway footbridge broken railings (Roads & Transport)
    ward12_diverse = [p for p in processed_list if p.complaint_id in {"CMP-SYN-001", "CMP-SYN-026", "CMP-SYN-049"}]
    assert len(ward12_diverse) == 3

    clusterer = IssueClusterer(similarity_threshold=0.45)
    clusters = clusterer.cluster_complaints(ward12_diverse, raw_map)

    # Should separate into 3 distinct clusters despite sharing Ward 12
    assert len(clusters) == 3
    cats = {c.category for c in clusters}
    assert ComplaintCategory.EDUCATION in cats
    assert ComplaintCategory.ROADS_AND_TRANSPORT in cats


def test_single_complaint_edge_case():
    """Verify a single complaint cleanly forms an individual cluster."""
    rec = ComplaintRecord(
        id="CMP-SOLO-1",
        source=ComplaintSource.DIRECT_WEB,
        original_text="Fallen tree blocking lane in Ward 3.",
        locality="Ward 3",
    )
    provider = MockAIProvider()
    processed = provider.process_complaint_full(rec)

    clusterer = IssueClusterer()
    clusters = clusterer.cluster_complaints([processed], {"CMP-SOLO-1": rec})

    assert len(clusters) == 1
    assert clusters[0].complaint_count == 1
    assert clusters[0].complaint_ids == ["CMP-SOLO-1"]
    assert clusters[0].locality == "Ward 3"
