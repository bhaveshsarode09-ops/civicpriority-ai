"""Unit tests for Phase 6 Transparent Priority Scoring Engine.
"""

import pytest

from civicpriority.models import ComplaintCategory, IssueCluster, IssueStatus, PriorityLevel
from civicpriority.scoring import (
    DEFAULT_WEIGHTS,
    ScoreBreakdown,
    ScoringWeights,
    apply_scoring_to_cluster,
    calculate_priority_score,
    classify_priority_level,
    normalize_people_affected,
    normalize_repeated_complaints,
)


def test_log_normalization_people():
    """Verify logarithmic normalization of people affected."""
    assert normalize_people_affected(0) == 0.0
    assert normalize_people_affected(1) == 0.0  # log10(1) = 0
    assert normalize_people_affected(10) == 25.0  # log10(10)*25 = 25
    assert normalize_people_affected(100) == 50.0  # log10(100)*25 = 50
    assert normalize_people_affected(1000) == 75.0  # log10(1000)*25 = 75
    assert normalize_people_affected(10000) == 100.0  # log10(10000)*25 = 100
    assert normalize_people_affected(100000) == 100.0  # capped at 100


def test_core_formula_calculation():
    """Verify priority score matches the defined multi-criteria weights."""
    # Test inputs
    severity = 80.0
    people = 1000  # norm = 75.0
    urgency = 70.0
    infra_gap = 60.0
    repeats = 5  # norm = 50.0

    breakdown = calculate_priority_score(
        severity=severity,
        people_affected=people,
        urgency=urgency,
        infrastructure_gap=infra_gap,
        complaint_count=repeats,
        locality="Ward 12",
    )

    # 0.30 * 80.0 = 24.0
    assert breakdown.severity_contribution == 24.0
    # 0.25 * 75.0 = 18.75
    assert breakdown.people_contribution == 18.75
    # 0.20 * 70.0 = 14.0
    assert breakdown.urgency_contribution == 14.0
    # 0.15 * 60.0 = 9.0
    assert breakdown.infrastructure_contribution == 9.0
    # 0.10 * 50.0 = 5.0
    assert breakdown.repeat_contribution == 5.0

    # Total = 24.0 + 18.75 + 14.0 + 9.0 + 5.0 = 70.75 -> rounded to 70.8
    assert breakdown.total_priority_score == 70.8
    assert breakdown.priority_level == PriorityLevel.HIGH


def test_configurable_weights():
    """Verify customization of weights alters factor contributions."""
    custom_weights = ScoringWeights(
        weight_severity=0.50,
        weight_people=0.10,
        weight_urgency=0.20,
        weight_infrastructure_gap=0.10,
        weight_repeated_complaints=0.10,
    )
    breakdown = calculate_priority_score(
        severity=90.0,
        people_affected=100,  # norm = 50.0
        urgency=80.0,
        infrastructure_gap=50.0,
        complaint_count=2,  # norm = 20.0
        weights=custom_weights,
    )
    # Severity weight 0.50 * 90 = 45.0
    assert breakdown.severity_contribution == 45.0
    # Total priority
    expected_total = (
        0.50 * 90.0 + 0.10 * 50.0 + 0.20 * 80.0 + 0.10 * 50.0 + 0.10 * 20.0
    )
    assert breakdown.total_priority_score == round(expected_total, 1)


def test_fairness_warning_for_high_severity_low_count():
    """Verify that a severe issue reported by only 1 citizen triggers a fairness safeguard
    to protect against frequency bias in digitally underserved wards.
    """
    breakdown = calculate_priority_score(
        severity=92.0,  # High severity >= 80
        people_affected=300,
        urgency=85.0,
        infrastructure_gap=88.0,
        complaint_count=1,  # Only 1 report
        locality="Rural Ward 18",
        vulnerable_groups=["Elderly"],
    )
    assert len(breakdown.fairness_warnings) >= 1
    warnings_text = " ".join(breakdown.fairness_warnings)
    assert "Fairness safeguard triggered" in warnings_text
    assert "digitally underserved" in warnings_text
    assert "Rural Ward 18" in warnings_text


def test_priority_tier_classification():
    """Verify priority tier classifications: Critical, High, Medium, Low."""
    assert classify_priority_level(85.0) == PriorityLevel.CRITICAL
    assert classify_priority_level(80.0) == PriorityLevel.CRITICAL
    assert classify_priority_level(79.9) == PriorityLevel.HIGH
    assert classify_priority_level(65.0) == PriorityLevel.HIGH
    assert classify_priority_level(64.9) == PriorityLevel.MEDIUM
    assert classify_priority_level(45.0) == PriorityLevel.MEDIUM
    assert classify_priority_level(44.9) == PriorityLevel.LOW
    assert classify_priority_level(20.0) == PriorityLevel.LOW


def test_apply_scoring_to_cluster():
    """Verify apply_scoring_to_cluster updates cluster priority, level, and warnings."""
    cluster = IssueCluster(
        cluster_id="CLU-TEST-01",
        title="Test Cluster",
        description="Test description",
        category=ComplaintCategory.WATER_AND_SANITATION,
        locality="Ward 4",
        complaint_ids=["CMP-1", "CMP-2"],
        complaint_count=2,
        unique_sources=["direct_web"],
        average_severity=88.0,
        average_urgency=82.0,
        estimated_people_affected=1200,
        vulnerable_groups=["Children"],
        infrastructure_gap_score=90.0,
        priority_score=0.0,
        priority_level=PriorityLevel.LOW,
        recommendation="Fix leak",
        explanation="Old explanation",
        confidence=0.95,
        status=IssueStatus.OPEN,
    )

    updated = apply_scoring_to_cluster(cluster)
    assert updated.priority_score > 75.0
    assert updated.priority_level in [PriorityLevel.CRITICAL, PriorityLevel.HIGH]
    assert len(updated.fairness_warnings) >= 1  # 2 reports with severity 88 triggers warning
    assert "Severity:" in updated.explanation
    assert "People Affected:" in updated.explanation
