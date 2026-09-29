"""Pipeline Orchestrator for CivicPriority AI.
Connects ingestion, PII protection, AI analysis, clustering, scoring, and storage.
"""

from pathlib import Path
from typing import Optional
import logging

from civicpriority.ai import BaseAIProvider, MockAIProvider
from civicpriority.clustering import IssueClusterer
from civicpriority.connectors import CSVConnector
from civicpriority.database import Database
from civicpriority.models import (
    ComplaintRecord,
    IssueCluster,
    ProcessedComplaint,
)
from civicpriority.privacy import hash_contact_identifier, mask_contact_in_text, sanitize_text_for_ai
from civicpriority.scoring import ScoringWeights, apply_scoring_to_cluster

logger = logging.getLogger("civicpriority.pipeline")


class CivicPipeline:
    """End-to-end processing pipeline for municipal grievances."""

    def __init__(
        self,
        db: Optional[Database] = None,
        ai_provider: Optional[BaseAIProvider] = None,
        clusterer: Optional[IssueClusterer] = None,
        weights: Optional[ScoringWeights] = None,
    ):
        self.db = db or Database()
        self.ai_provider = ai_provider or MockAIProvider()
        self.clusterer = clusterer or IssueClusterer()
        self.weights = weights or ScoringWeights()

    def seed_initial_data_if_empty(self, csv_path: Optional[Path] = None) -> int:
        """Seed initial synthetic dataset if database has zero complaints."""
        existing = self.db.list_complaints()
        if existing:
            return len(existing)

        target_path = csv_path or Path("backend/data/sample_complaints.csv")
        if not target_path.exists():
            logger.warning("Seed CSV not found at %s", target_path)
            return 0

        connector = CSVConnector()
        records = connector.load(target_path)
        logger.info("Loaded %d records from %s", len(records), target_path)

        # Ingest and process all seed records
        self.ingest_batch(records)
        return len(records)

    def ingest_single(self, record: ComplaintRecord) -> tuple[ComplaintRecord, ProcessedComplaint]:
        """Ingest and process a single complaint, masking PII and persisting to DB."""
        # 1. Privacy & PII protection
        record.original_text = mask_contact_in_text(record.original_text)
        if record.citizen_contact_hash is None and record.metadata.get("contact"):
            record.citizen_contact_hash = hash_contact_identifier(str(record.metadata.get("contact")))

        # 2. AI Processing
        processed = self.ai_provider.process_complaint_full(record)

        # 3. Persistence
        self.db.save_complaint(record)
        self.db.save_processed(processed)

        # 4. Trigger re-clustering and scoring
        self.recluster_and_rescore()

        return record, processed

    def ingest_batch(self, records: list[ComplaintRecord]) -> dict[str, int]:
        """Ingest a batch of records, processing and clustering them."""
        accepted = 0
        rejected = 0

        processed_batch: list[ProcessedComplaint] = []
        for r in records:
            try:
                r.original_text = mask_contact_in_text(r.original_text)
                processed = self.ai_provider.process_complaint_full(r)

                self.db.save_complaint(r)
                self.db.save_processed(processed)
                processed_batch.append(processed)
                accepted += 1
            except Exception as e:
                logger.error("Failed to ingest record %s: %s", r.id, e)
                rejected += 1

        if accepted > 0:
            self.recluster_and_rescore()

        return {"accepted": accepted, "rejected": rejected, "total": len(records)}

    def recluster_and_rescore(self, custom_weights: Optional[ScoringWeights] = None) -> list[IssueCluster]:
        """Re-runs graph clustering on all processed complaints and updates scores."""
        all_raw = self.db.list_complaints()
        all_processed = self.db.list_processed()

        if not all_processed:
            return []

        raw_map = {r.id: r for r in all_raw}
        weights_to_use = custom_weights or self.weights

        # 1. Cluster complaints
        raw_clusters = self.clusterer.cluster_complaints(all_processed, raw_map)

        # 2. Apply transparent scoring and fairness checks
        final_clusters = [apply_scoring_to_cluster(cl, weights_to_use) for cl in raw_clusters]

        # 3. Sort by priority score descending
        final_clusters.sort(key=lambda c: c.priority_score, reverse=True)

        # 4. Persist to DB
        for cl in final_clusters:
            # Preserve existing administrative status/notes if cluster previously existed
            existing = self.db.get_cluster(cl.cluster_id)
            if existing:
                cl.status = existing.status
                cl.assigned_department = existing.assigned_department or cl.assigned_department
            self.db.save_cluster(cl)

        return final_clusters
