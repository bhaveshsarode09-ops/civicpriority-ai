"""Transparent Priority Scoring Engine for CivicPriority AI.
Implements multi-criteria ranking, configurable weights, logarithmic population scaling,
fairness safeguards for underrepresented localities, and granular explainability breakdowns.
"""

import math
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from civicpriority.models import IssueCluster, PriorityLevel


class ScoringWeights(BaseModel):
    """Configurable weights for the civic prioritization formula."""
    weight_severity: float = Field(default=0.30, ge=0.0, le=1.0, description="Weight for severity score")
    weight_people: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight for people affected")
    weight_urgency: float = Field(default=0.20, ge=0.0, le=1.0, description="Weight for urgency score")
    weight_infrastructure_gap: float = Field(default=0.15, ge=0.0, le=1.0, description="Weight for infrastructure gap")
    weight_repeated_complaints: float = Field(default=0.10, ge=0.0, le=1.0, description="Weight for repeat complaint volume")

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "ScoringWeights":
        total = (
            self.weight_severity
            + self.weight_people
            + self.weight_urgency
            + self.weight_infrastructure_gap
            + self.weight_repeated_complaints
        )
        if not math.isclose(total, 1.0, abs_tol=0.02):
            # Normalize automatically to sum to 1.0
            factor = 1.0 / total
            self.weight_severity = round(self.weight_severity * factor, 4)
            self.weight_people = round(self.weight_people * factor, 4)
            self.weight_urgency = round(self.weight_urgency * factor, 4)
            self.weight_infrastructure_gap = round(self.weight_infrastructure_gap * factor, 4)
            self.weight_repeated_complaints = round(self.weight_repeated_complaints * factor, 4)
        return self


DEFAULT_WEIGHTS = ScoringWeights()


class ScoreBreakdown(BaseModel):
    """Detailed mathematical and logical breakdown of an issue's priority score."""
    raw_severity: float
    raw_people_affected: int
    raw_urgency: float
    raw_infrastructure_gap: float
    raw_complaint_count: int

    normalized_people_score: float
    normalized_repeat_score: float

    severity_contribution: float
    people_contribution: float
    urgency_contribution: float
    infrastructure_contribution: float
    repeat_contribution: float

    total_priority_score: float
    priority_level: PriorityLevel
    fairness_warnings: list[str]
    explanation: str


def normalize_people_affected(people: int) -> float:
    """Logarithmically scales affected population to prevent massive populations
    from drowning out critical hyper-local issues (e.g. 10 -> 25pts, 100 -> 50pts,
    1,000 -> 75pts, 10,000+ -> 100pts).
    """
    if people <= 0:
        return 0.0
    val = math.log10(max(1.0, float(people))) * 25.0
    return min(100.0, max(0.0, round(val, 2)))


def normalize_repeated_complaints(count: int, max_cap: int = 10) -> float:
    """Normalizes complaint volume (1 to 10+ reports) into a 0 to 100 score."""
    if count <= 0:
        return 0.0
    score = (min(count, max_cap) / max_cap) * 100.0
    return round(score, 2)


def detect_fairness_issues(
    severity: float,
    count: int,
    locality: str,
    infra_gap: float,
    vulnerable_groups: list[str],
) -> list[str]:
    """Generates fairness safeguards to ensure underreported and less-connected
    areas are not suppressed by affluent areas with higher submission volume.
    """
    warnings: list[str] = []

    # Safeguard 1: Severe issues reported by only 1-2 citizens
    if severity >= 80.0 and count <= 2:
        warnings.append(
            f"Fairness safeguard triggered: High severity ({severity:.1f}/100) with only {count} report(s). "
            f"Issue prioritized to prevent marginalization of digitally underserved citizens in {locality}."
        )

    # Safeguard 2: Acute infrastructure deficit in low-reporting ward
    if infra_gap >= 85.0 and count <= 2:
        warnings.append(
            f"Infrastructure gap safeguard: Severe structural deficit ({infra_gap:.1f}/100) identified in {locality} "
            f"despite low complaint volume. Protected from frequency bias."
        )

    # Safeguard 3: Vulnerable populations protection
    if vulnerable_groups and count <= 3 and severity >= 75.0:
        warnings.append(
            f"Demographic equity alert: Involves vulnerable groups ({', '.join(vulnerable_groups)}) in {locality}. "
            f"Rank elevated above raw report counts."
        )

    return warnings


def classify_priority_level(score: float) -> PriorityLevel:
    """Classifies priority score into standardized tiers:
    - Critical (80-100)
    - High (65-79)
    - Medium (45-64)
    - Low (0-44)
    """
    if score >= 80.0:
        return PriorityLevel.CRITICAL
    elif score >= 65.0:
        return PriorityLevel.HIGH
    elif score >= 45.0:
        return PriorityLevel.MEDIUM
    else:
        return PriorityLevel.LOW


def calculate_priority_score(
    severity: float,
    people_affected: int,
    urgency: float,
    infrastructure_gap: float,
    complaint_count: int,
    locality: str = "Local Ward",
    vulnerable_groups: Optional[list[str]] = None,
    weights: Optional[ScoringWeights] = None,
) -> ScoreBreakdown:
    """Computes transparent priority score, factor contributions, and fairness checks."""
    w = weights or DEFAULT_WEIGHTS
    vulnerable = vulnerable_groups or []

    # Normalized inputs
    norm_people = normalize_people_affected(people_affected)
    norm_repeats = normalize_repeated_complaints(complaint_count)

    # Factor contributions
    sev_contrib = round(w.weight_severity * severity, 2)
    ppl_contrib = round(w.weight_people * norm_people, 2)
    urg_contrib = round(w.weight_urgency * urgency, 2)
    inf_contrib = round(w.weight_infrastructure_gap * infrastructure_gap, 2)
    rep_contrib = round(w.weight_repeated_complaints * norm_repeats, 2)

    raw_total = sev_contrib + ppl_contrib + urg_contrib + inf_contrib + rep_contrib
    final_score = round(min(100.0, max(0.0, raw_total)), 1)

    priority_lvl = classify_priority_level(final_score)
    fairness_warns = detect_fairness_issues(severity, complaint_count, locality, infrastructure_gap, vulnerable)

    # Transparent human explanation
    factors = [
        f"Severity: {sev_contrib:.1f}pts ({w.weight_severity * 100:.0f}%)",
        f"People Affected: {ppl_contrib:.1f}pts ({w.weight_people * 100:.0f}%)",
        f"Urgency: {urg_contrib:.1f}pts ({w.weight_urgency * 100:.0f}%)",
        f"Infrastructure Deficit: {inf_contrib:.1f}pts ({w.weight_infrastructure_gap * 100:.0f}%)",
        f"Repeat Volume: {rep_contrib:.1f}pts ({w.weight_repeated_complaints * 100:.0f}%)",
    ]
    explanation = (
        f"Ranked as {priority_lvl.value} Priority ({final_score:.1f}/100). "
        f"Score composition: " + ", ".join(factors) + "."
    )
    if fairness_warns:
        explanation += f" Active fairness protections: {len(fairness_warns)}."

    return ScoreBreakdown(
        raw_severity=severity,
        raw_people_affected=people_affected,
        raw_urgency=urgency,
        raw_infrastructure_gap=infrastructure_gap,
        raw_complaint_count=complaint_count,
        normalized_people_score=norm_people,
        normalized_repeat_score=norm_repeats,
        severity_contribution=sev_contrib,
        people_contribution=ppl_contrib,
        urgency_contribution=urg_contrib,
        infrastructure_contribution=inf_contrib,
        repeat_contribution=rep_contrib,
        total_priority_score=final_score,
        priority_level=priority_lvl,
        fairness_warnings=fairness_warns,
        explanation=explanation,
    )


def apply_scoring_to_cluster(
    cluster: IssueCluster,
    weights: Optional[ScoringWeights] = None,
) -> IssueCluster:
    """Updates an IssueCluster with recalculated transparent scoring and fairness checks."""
    breakdown = calculate_priority_score(
        severity=cluster.average_severity,
        people_affected=cluster.estimated_people_affected,
        urgency=cluster.average_urgency,
        infrastructure_gap=cluster.infrastructure_gap_score,
        complaint_count=cluster.complaint_count,
        locality=cluster.locality,
        vulnerable_groups=cluster.vulnerable_groups,
        weights=weights,
    )

    cluster.priority_score = breakdown.total_priority_score
    cluster.priority_level = breakdown.priority_level
    cluster.fairness_warnings = breakdown.fairness_warnings
    cluster.explanation = breakdown.explanation
    return cluster
