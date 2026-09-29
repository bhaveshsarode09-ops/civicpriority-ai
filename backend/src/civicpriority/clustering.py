"""Similarity calculation and issue clustering engine for CivicPriority AI.
Groups related citizen complaints across multiple channels into unified, actionable IssueClusters.
"""

import hashlib
import re
from typing import Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from civicpriority.models import (
    ComplaintCategory,
    ComplaintRecord,
    IssueCluster,
    IssueStatus,
    PriorityLevel,
    ProcessedComplaint,
    utc_now,
)


def normalize_text(text: str) -> str:
    """Normalize text for lexical matching and TF-IDF representation."""
    if not text:
        return ""
    # Lowercase and strip punctuation/symbols except spaces
    t = text.lower()
    t = re.sub(r"\[[a-z_]+\]", "", t)  # strip redaction tokens like [phone_redacted]
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


class IssueClusterer:
    """Groups processed complaints into cohesive clusters based on multi-dimensional similarity."""

    def __init__(
        self,
        similarity_threshold: float = 0.42,
        weight_text: float = 0.50,
        weight_locality: float = 0.30,
        weight_category: float = 0.20,
    ):
        self.similarity_threshold = similarity_threshold
        self.weight_text = weight_text
        self.weight_locality = weight_locality
        self.weight_category = weight_category

    def compute_similarity(
        self,
        c1: ProcessedComplaint,
        c2: ProcessedComplaint,
        text_sim: float,
    ) -> float:
        """Compute multi-dimensional similarity between two complaints."""
        # 1. Locality match
        loc1 = c1.location.strip().lower()
        loc2 = c2.location.strip().lower()
        if loc1 == loc2:
            loc_score = 1.0
        elif loc1 in loc2 or loc2 in loc1:
            loc_score = 0.8
        else:
            loc_score = 0.0

        # 2. Category match
        if c1.category == c2.category:
            cat_score = 1.0
        else:
            # Related categories (e.g. Education and Water if school drinking water is involved)
            c1_text = (c1.translated_text + " " + c1.summary).lower()
            c2_text = (c2.translated_text + " " + c2.summary).lower()
            if ("school" in c1_text or "classroom" in c1_text) and ("school" in c2_text or "classroom" in c2_text):
                cat_score = 0.8
            else:
                cat_score = 0.0

        # Composite score
        total_score = (
            self.weight_text * text_sim
            + self.weight_locality * loc_score
            + self.weight_category * cat_score
        )
        return total_score

    def cluster_complaints(
        self,
        processed_complaints: list[ProcessedComplaint],
        raw_complaints_map: Optional[dict[str, ComplaintRecord]] = None,
    ) -> list[IssueCluster]:
        """Cluster a list of processed complaints into synthesized IssueClusters."""
        if not processed_complaints:
            return []

        n = len(processed_complaints)
        if n == 1:
            return [self._create_cluster([processed_complaints[0]], 0, raw_complaints_map)]

        # Precompute text TF-IDF matrix
        texts = [normalize_text(c.translated_text + " " + c.summary) for c in processed_complaints]

        # Use TF-IDF with character and word n-grams for resilience against typos
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=2500)
        tfidf_matrix = vectorizer.fit_transform(texts)
        text_cosine_matrix = cosine_similarity(tfidf_matrix)

        # Build adjacency matrix
        adj = np.zeros((n, n), dtype=bool)
        for i in range(n):
            adj[i, i] = True
            for j in range(i + 1, n):
                score = self.compute_similarity(
                    processed_complaints[i],
                    processed_complaints[j],
                    float(text_cosine_matrix[i, j]),
                )
                if score >= self.similarity_threshold:
                    adj[i, j] = True
                    adj[j, i] = True

        # Find connected components (BFS / DFS)
        visited = set()
        components: list[list[int]] = []

        for i in range(n):
            if i not in visited:
                comp = []
                queue = [i]
                visited.add(i)
                while queue:
                    curr = queue.pop(0)
                    comp.append(curr)
                    for neighbor in range(n):
                        if adj[curr, neighbor] and neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(comp)

        # Build IssueCluster for each component
        clusters: list[IssueCluster] = []
        for idx, comp in enumerate(components):
            items = [processed_complaints[k] for k in comp]
            cluster = self._create_cluster(items, idx, raw_complaints_map)
            clusters.append(cluster)

        # Sort clusters by priority_score descending
        clusters.sort(key=lambda cl: cl.priority_score, reverse=True)
        return clusters

    def _create_cluster(
        self,
        items: list[ProcessedComplaint],
        cluster_idx: int,
        raw_complaints_map: Optional[dict[str, ComplaintRecord]] = None,
    ) -> IssueCluster:
        """Synthesize metrics and metadata for a cluster of complaints."""
        complaint_ids = [c.complaint_id for c in items]
        count = len(items)

        # Determine dominant locality and category
        locality_counts: dict[str, int] = {}
        for c in items:
            locality_counts[c.location] = locality_counts.get(c.location, 0) + 1
        dominant_locality = max(locality_counts, key=locality_counts.get)

        category_counts: dict[str, int] = {}
        for c in items:
            c_val = c.category.value if hasattr(c.category, "value") else str(c.category)
            category_counts[c_val] = category_counts.get(c_val, 0) + 1
        dominant_category_str = max(category_counts, key=category_counts.get)
        dominant_category = ComplaintCategory(dominant_category_str)

        # Unique sources
        unique_sources: set[str] = set()
        if raw_complaints_map:
            for cid in complaint_ids:
                if cid in raw_complaints_map:
                    src = raw_complaints_map[cid].source
                    unique_sources.add(src.value if hasattr(src, "value") else str(src))
        if not unique_sources:
            unique_sources = {"grievance_feed"}

        # Metrics aggregation
        avg_severity = float(np.mean([c.severity_score for c in items]))
        avg_urgency = float(np.mean([c.urgency_score for c in items]))
        avg_infra_gap = float(np.mean([c.infrastructure_gap_score for c in items]))
        max_affected = max([c.estimated_people_affected for c in items])

        # Vulnerable groups union
        vulnerable_set: set[str] = set()
        for c in items:
            vulnerable_set.update(c.vulnerable_groups)
        vulnerable_list = sorted(list(vulnerable_set))

        # Human review flag
        requires_review = any(c.requires_human_review for c in items) or any(c.ai_confidence < 0.70 for c in items)

        # Baseline priority computation (Refined further in Phase 6)
        # Log-scaled people affected + severity + urgency + volume
        people_factor = min(100.0, np.log10(max(10, max_affected)) * 25.0)
        volume_factor = min(100.0, count * 15.0)
        vulnerable_boost = 10.0 if vulnerable_list else 0.0

        raw_priority = (
            0.30 * avg_severity
            + 0.25 * people_factor
            + 0.20 * avg_urgency
            + 0.15 * avg_infra_gap
            + 0.10 * volume_factor
            + vulnerable_boost
        )
        priority_score = round(min(100.0, max(0.0, raw_priority)), 1)

        # Priority tier
        if priority_score >= 80.0:
            priority_level = PriorityLevel.CRITICAL
        elif priority_score >= 65.0:
            priority_level = PriorityLevel.HIGH
        elif priority_score >= 45.0:
            priority_level = PriorityLevel.MEDIUM
        else:
            priority_level = PriorityLevel.LOW

        # Generate cluster ID
        loc_slug = re.sub(r"[^a-zA-Z0-9]", "", dominant_locality).upper()
        cat_slug = dominant_category.value.split()[0].upper()
        cluster_id = f"CLU-{loc_slug}-{cat_slug}-{cluster_idx + 1:02d}"

        # Generate title and description
        top_complaint = max(items, key=lambda c: c.severity_score)
        title = self._generate_title(top_complaint, dominant_locality, count)
        description = self._generate_description(items, dominant_locality, dominant_category)
        recommendation = self._generate_recommendation(dominant_category, dominant_locality, vulnerable_list)
        explanation = (
            f"Clustered from {count} independent reports across {len(unique_sources)} source channels "
            f"({', '.join(sorted(list(unique_sources)))}). Severity: {avg_severity:.1f}/100, Urgency: {avg_urgency:.1f}/100, "
            f"Estimated affected: {max_affected:,}. Vulnerable groups: {', '.join(vulnerable_list) or 'None identified'}."
        )

        # Responsible department
        dept_counts: dict[str, int] = {}
        for c in items:
            dept_counts[c.department] = dept_counts.get(c.department, 0) + 1
        assigned_dept = max(dept_counts, key=dept_counts.get)

        return IssueCluster(
            cluster_id=cluster_id,
            title=title,
            description=description,
            category=dominant_category,
            locality=dominant_locality,
            complaint_ids=complaint_ids,
            complaint_count=count,
            unique_sources=sorted(list(unique_sources)),
            average_severity=round(avg_severity, 1),
            average_urgency=round(avg_urgency, 1),
            estimated_people_affected=max_affected,
            vulnerable_groups=vulnerable_list,
            infrastructure_gap_score=round(avg_infra_gap, 1),
            priority_score=priority_score,
            priority_level=priority_level,
            recommendation=recommendation,
            explanation=explanation,
            confidence=round(float(np.mean([c.ai_confidence for c in items])), 2),
            fairness_warnings=[],
            requires_human_review=requires_review,
            status=IssueStatus.OPEN,
            assigned_department=assigned_dept,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

    def _generate_title(self, top_complaint: ProcessedComplaint, locality: str, count: str) -> str:
        entities = top_complaint.entities
        subcat = top_complaint.subcategory or top_complaint.category.value
        if entities:
            return f"{subcat} crisis at {entities[0]} ({locality})"
        return f"{subcat} emergency in {locality}"

    def _generate_description(
        self,
        items: list[ProcessedComplaint],
        locality: str,
        category: ComplaintCategory,
    ) -> str:
        summaries = [c.summary for c in items[:3]]
        return f"Multiple reports received in {locality} regarding {category.value.lower()}. " + " ".join(summaries)

    def _generate_recommendation(
        self,
        category: ComplaintCategory,
        locality: str,
        vulnerable_groups: list[str],
    ) -> str:
        vuln_note = f" Prioritize safeguarding {', '.join(vulnerable_groups)}." if vulnerable_groups else ""
        if category == ComplaintCategory.EDUCATION:
            return f"Dispatch rapid education infrastructure inspection team to {locality}. Deploy emergency drinking water facility and modular classroom arrangements.{vuln_note}"
        elif category == ComplaintCategory.WATER_AND_SANITATION:
            return f"Order immediate isolation and repair of ruptured water mainline in {locality}. Provide emergency potable water tankers to affected households.{vuln_note}"
        elif category == ComplaintCategory.ROADS_AND_TRANSPORT:
            return f"Deploy emergency road repair unit to fill hazardous potholes and restore safe vehicular transit in {locality}. Install temporary hazard signage."
        elif category == ComplaintCategory.HEALTHCARE:
            return f"Depute temporary medical officer to {locality} primary health center and replenish emergency medicine stocks.{vuln_note}"
        elif category == ComplaintCategory.ELECTRICITY:
            return f"Install replacement distribution transformer in {locality} to restore power supply to residential colonies."
        return f"Initiate immediate field review by designated municipal engineering squad in {locality}.{vuln_note}"
