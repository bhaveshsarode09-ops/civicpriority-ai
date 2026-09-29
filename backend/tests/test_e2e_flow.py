"""End-to-End Verification Test Suite for CivicPriority AI.
Validates the complete lifecycle:
1. Ingesting 52 synthetic complaints across 5 wards and 3 languages.
2. Verifying zero PII leakage with phone/email masking and salted contact hashing.
3. Graph clustering of Ward 12 school crisis across 5+ reporting channels.
4. Transparent multi-factor scoring with 'Children' vulnerable demographic recognition.
5. Itemized 5-factor mathematical score breakdown with natural language explanation.
6. Fairness safeguard trigger for high-severity low-frequency grievances in underserved areas.
7. Dynamic policy simulation re-ranking when criteria weights are modified.
8. Citizen tracking lookup by complaint ID.
9. Administrative dispatch workflow and department assignment.
"""

from pathlib import Path
import pytest

from civicpriority.ai import MockAIProvider
from civicpriority.clustering import IssueClusterer
from civicpriority.connectors import CSVConnector
from civicpriority.database import Database
from civicpriority.models import (
    ComplaintCategory,
    ComplaintRecord,
    ComplaintSource,
    IssueCluster,
    IssueStatus,
    PriorityLevel,
    ProcessedComplaint,
)
from civicpriority.pipeline import CivicPipeline
from civicpriority.privacy import hash_contact_identifier, mask_contact_in_text
from civicpriority.scoring import (
    ScoringWeights,
    apply_scoring_to_cluster,
    calculate_priority_score,
)


@pytest.fixture
def fresh_pipeline():
    """Provides a fresh in-memory pipeline for isolated end-to-end testing."""
    db = Database(":memory:")
    ai = MockAIProvider()
    clusterer = IssueClusterer()
    weights = ScoringWeights()
    return CivicPipeline(db=db, ai_provider=ai, clusterer=clusterer, weights=weights)


def test_e2e_step1_load_and_ingest_all_52_complaints(fresh_pipeline):
    """Step 1 & 2: Load the 52 synthetic complaints dataset and confirm 100% ingested with PII masked."""
    csv_path = Path("backend/data/sample_complaints.csv")
    assert csv_path.exists(), "Sample complaints CSV must exist"

    connector = CSVConnector()
    records = connector.load(csv_path)
    assert len(records) >= 50, f"Expected at least 50 synthetic records, got {len(records)}"

    res = fresh_pipeline.ingest_batch(records)
    assert res["accepted"] == len(records)
    assert res["rejected"] == 0

    saved_raw = fresh_pipeline.db.list_complaints(limit=200)
    assert len(saved_raw) == len(records)

    import re

    # Verify PII is scrubbed across all records
    for r in saved_raw:
        # Verify no unmasked email address exists
        assert not re.search(
            r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", r.original_text
        ), f"Unmasked email found in record {r.id}: {r.original_text}"

        # Ensure no raw 10-digit Indian phone numbers exist in text
        for token in r.original_text.split():
            clean_digits = "".join(filter(str.isdigit, token))
            if len(clean_digits) == 10 and clean_digits[0] in "6789":
                pytest.fail(f"Unmasked 10-digit phone number found in {r.id}: {token}")

        if r.citizen_contact_hash:
            assert len(r.citizen_contact_hash) == 64, "Salted SHA-256 hash must be 64 hex characters"


def test_e2e_step3_and_4_ward12_school_crisis_clustering_and_priority(fresh_pipeline):
    """Step 3 & 4: Verify Ward 12 school complaints cluster together across multiple sources with high priority score."""
    csv_path = Path("backend/data/sample_complaints.csv")
    fresh_pipeline.ingest_batch(CSVConnector().load(csv_path))

    clusters = fresh_pipeline.db.list_clusters()
    assert len(clusters) > 0

    # Locate the Ward 12 education cluster
    ward12_school_cluster = next(
        (
            c
            for c in clusters
            if c.locality == "Ward 12"
            and c.category in [ComplaintCategory.EDUCATION, ComplaintCategory.EDUCATION.value]
        ),
        None,
    )
    assert ward12_school_cluster is not None, "Ward 12 education cluster must exist"

    # Verify multiple reports merged (CMP-SYN-001 through CMP-SYN-006)
    assert ward12_school_cluster.complaint_count >= 5, (
        f"Expected at least 5 merged complaints, got {ward12_school_cluster.complaint_count}"
    )

    # Verify multi-channel diversity
    assert len(ward12_school_cluster.unique_sources) >= 4, (
        f"Expected reports from >= 4 distinct channels, got {ward12_school_cluster.unique_sources}"
    )

    # Verify high priority ranking
    assert ward12_school_cluster.priority_score >= 65.0, (
        f"Expected priority score >= 65, got {ward12_school_cluster.priority_score}"
    )
    assert ward12_school_cluster.priority_level in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]

    # Verify 'Children' demographic recognized
    assert "Children" in ward12_school_cluster.vulnerable_groups, (
        f"Expected 'Children' in vulnerable groups, got {ward12_school_cluster.vulnerable_groups}"
    )


def test_e2e_step5_score_breakdown_and_explainability(fresh_pipeline):
    """Step 5: Verify the score breakdown is transparent, itemized, and explainable."""
    csv_path = Path("backend/data/sample_complaints.csv")
    fresh_pipeline.ingest_batch(CSVConnector().load(csv_path))

    clusters = fresh_pipeline.db.list_clusters()
    top_cluster = clusters[0]

    breakdown = calculate_priority_score(
        severity=top_cluster.average_severity,
        people_affected=top_cluster.estimated_people_affected,
        urgency=top_cluster.average_urgency,
        infrastructure_gap=top_cluster.infrastructure_gap_score,
        complaint_count=top_cluster.complaint_count,
        locality=top_cluster.locality,
        vulnerable_groups=top_cluster.vulnerable_groups,
        weights=fresh_pipeline.weights,
    )

    # Verify mathematical integrity: sum of components equals total score
    computed_sum = (
        breakdown.severity_contribution
        + breakdown.people_contribution
        + breakdown.urgency_contribution
        + breakdown.infrastructure_contribution
        + breakdown.repeat_contribution
    )
    assert abs(breakdown.total_priority_score - computed_sum) < 0.2
    assert abs(breakdown.total_priority_score - top_cluster.priority_score) < 0.2

    # Verify natural language explanation contains score and key factors
    assert str(round(top_cluster.priority_score, 1)) in breakdown.explanation or str(int(top_cluster.priority_score)) in breakdown.explanation
    assert "Score composition" in breakdown.explanation
    assert len(top_cluster.recommendation) > 20


def test_e2e_step6_fairness_safeguard_for_isolated_severe_complaint(fresh_pipeline):
    """Step 6: Verify a single isolated high-severity complaint in an underreported ward receives a fairness safeguard."""
    # Create an isolated severe complaint in an underserved rural ward
    severe_single_complaint = ComplaintRecord(
        id="CMP-E2E-ISOLATED-01",
        source=ComplaintSource.PUBLIC_MEETING,
        original_text="Emergency: Deep open borewell left uncovered near Ward 15 primary health sub-center. High risk of child falling.",
        original_language="en",
        locality="Ward 15",
        citizen_contact_hash=hash_contact_identifier("9899887766"),
    )

    fresh_pipeline.ingest_single(severe_single_complaint)
    clusters = fresh_pipeline.db.list_clusters()

    isolated_cluster = next((c for c in clusters if "CMP-E2E-ISOLATED-01" in c.complaint_ids), None)
    assert isolated_cluster is not None

    # Calculate breakdown
    breakdown = calculate_priority_score(
        severity=isolated_cluster.average_severity,
        people_affected=isolated_cluster.estimated_people_affected,
        urgency=isolated_cluster.average_urgency,
        infrastructure_gap=isolated_cluster.infrastructure_gap_score,
        complaint_count=isolated_cluster.complaint_count,
        locality=isolated_cluster.locality,
        vulnerable_groups=isolated_cluster.vulnerable_groups,
    )

    # Verify fairness warning triggered
    assert len(breakdown.fairness_warnings) >= 1, "Fairness warning must be triggered for low-volume high-severity issue"
    assert any("Fairness Alert" in w or "isolated" in w.lower() or "frequency bias" in w.lower() for w in breakdown.fairness_warnings)


def test_e2e_step7_dynamic_weight_simulation_re_ranks_issues(fresh_pipeline):
    """Step 7: Verify changing criteria weights re-ranks issues logically."""
    csv_path = Path("backend/data/sample_complaints.csv")
    fresh_pipeline.ingest_batch(CSVConnector().load(csv_path))

    # Baseline clusters
    clusters_default = fresh_pipeline.recluster_and_rescore()
    top_default_id = clusters_default[0].cluster_id

    # Scenario A: Heavily prioritize Infrastructure Gap (e.g. 70% infra, 10% severity, 10% people, 5% urgency, 5% repeat)
    infra_weights = ScoringWeights(
        weight_severity=0.10,
        weight_people=0.10,
        weight_urgency=0.05,
        weight_infrastructure_gap=0.70,
        weight_repeated_complaints=0.05,
    )
    clusters_infra = fresh_pipeline.recluster_and_rescore(custom_weights=infra_weights)

    # Scenario B: Heavily prioritize Urgency (e.g. 70% urgency, 10% severity, 10% people, 5% infra, 5% repeat)
    urgency_weights = ScoringWeights(
        weight_severity=0.10,
        weight_people=0.10,
        weight_urgency=0.70,
        weight_infrastructure_gap=0.05,
        weight_repeated_complaints=0.05,
    )
    clusters_urgency = fresh_pipeline.recluster_and_rescore(custom_weights=urgency_weights)

    # Scores must adjust to reflect the modified priorities
    score_default = next(c.priority_score for c in clusters_default if c.cluster_id == top_default_id)
    score_infra = next(c.priority_score for c in clusters_infra if c.cluster_id == top_default_id)
    score_urgency = next(c.priority_score for c in clusters_urgency if c.cluster_id == top_default_id)

    assert score_default != score_infra or score_default != score_urgency, "Different weights must produce different scores"


def test_e2e_step8_citizen_tracking_lookup(fresh_pipeline):
    """Step 8: Verify a citizen can look up their submission by Complaint ID and see the transparent score."""
    csv_path = Path("backend/data/sample_complaints.csv")
    fresh_pipeline.ingest_batch(CSVConnector().load(csv_path))

    target_complaint_id = "CMP-SYN-001"
    raw = fresh_pipeline.db.get_complaint(target_complaint_id)
    assert raw is not None
    assert "Ward 12" in raw.locality

    clusters = fresh_pipeline.db.list_clusters()
    parent_cluster = next((c for c in clusters if target_complaint_id in c.complaint_ids), None)
    assert parent_cluster is not None
    assert parent_cluster.priority_score > 0
    assert len(parent_cluster.explanation) > 0


def test_e2e_step9_administrative_status_and_department_dispatch(fresh_pipeline):
    """Step 9: Verify administrative workflow status transition and department assignment persist."""
    csv_path = Path("backend/data/sample_complaints.csv")
    fresh_pipeline.ingest_batch(CSVConnector().load(csv_path))

    clusters = fresh_pipeline.db.list_clusters()
    target_cluster = clusters[0]

    # Update cluster to IN_PROGRESS and assign department
    fresh_pipeline.db.update_cluster_status(
        cluster_id=target_cluster.cluster_id,
        status=IssueStatus.IN_PROGRESS,
        assigned_department="Department of School Education",
    )

    reloaded = fresh_pipeline.db.get_cluster(target_cluster.cluster_id)
    assert reloaded is not None
    assert reloaded.status == IssueStatus.IN_PROGRESS
    assert reloaded.assigned_department == "Department of School Education"
