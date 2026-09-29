"""SQLite database management and persistence layer for CivicPriority AI.
Provides clean roundtrip persistence for ComplaintRecord, ProcessedComplaint, and IssueCluster.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from civicpriority.models import (
    ComplaintCategory,
    ComplaintRecord,
    ComplaintSource,
    IssueCluster,
    IssueStatus,
    PriorityLevel,
    ProcessedComplaint,
)


class Database:
    """Manages SQLite connection and CRUD operations for civic data."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._shared_conn: Optional[sqlite3.Connection] = None
        if db_path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:")
            self._shared_conn.row_factory = sqlite3.Row
        else:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_complaints (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                source_reference TEXT,
                original_text TEXT NOT NULL,
                original_language TEXT NOT NULL,
                translated_text TEXT,
                submitted_at TEXT NOT NULL,
                locality TEXT NOT NULL,
                district TEXT,
                state TEXT,
                latitude REAL,
                longitude REAL,
                attachment_paths TEXT,
                citizen_contact_hash TEXT,
                consent_obtained INTEGER NOT NULL DEFAULT 1,
                metadata TEXT
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_complaints (
                complaint_id TEXT PRIMARY KEY,
                language TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                summary TEXT NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                location TEXT NOT NULL,
                department TEXT NOT NULL,
                severity_score REAL NOT NULL,
                urgency_score REAL NOT NULL,
                estimated_people_affected INTEGER NOT NULL,
                vulnerable_groups TEXT,
                infrastructure_gap_score REAL NOT NULL,
                keywords TEXT,
                entities TEXT,
                ai_confidence REAL NOT NULL,
                requires_human_review INTEGER NOT NULL,
                processing_errors TEXT,
                processed_at TEXT NOT NULL,
                FOREIGN KEY (complaint_id) REFERENCES raw_complaints(id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS issue_clusters (
                cluster_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                locality TEXT NOT NULL,
                complaint_ids TEXT NOT NULL,
                complaint_count INTEGER NOT NULL,
                unique_sources TEXT,
                average_severity REAL NOT NULL,
                average_urgency REAL NOT NULL,
                estimated_people_affected INTEGER NOT NULL,
                vulnerable_groups TEXT,
                infrastructure_gap_score REAL NOT NULL,
                priority_score REAL NOT NULL,
                priority_level TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                explanation TEXT NOT NULL,
                confidence REAL NOT NULL,
                fairness_warnings TEXT,
                requires_human_review INTEGER NOT NULL,
                status TEXT NOT NULL,
                assigned_department TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """)
            conn.commit()

    # --- Raw Complaints ---

    def save_raw_complaint(self, record: ComplaintRecord) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO raw_complaints (
                id, source, source_reference, original_text, original_language,
                translated_text, submitted_at, locality, district, state,
                latitude, longitude, attachment_paths, citizen_contact_hash,
                consent_obtained, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id,
                record.source,
                record.source_reference,
                record.original_text,
                record.original_language,
                record.translated_text,
                record.submitted_at.isoformat(),
                record.locality,
                record.district,
                record.state,
                record.latitude,
                record.longitude,
                json.dumps(record.attachment_paths),
                record.citizen_contact_hash,
                1 if record.consent_obtained else 0,
                json.dumps(record.metadata),
            ))
            conn.commit()

    def get_raw_complaint(self, complaint_id: str) -> Optional[ComplaintRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM raw_complaints WHERE id = ?", (complaint_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return ComplaintRecord(
                id=row["id"],
                source=ComplaintSource(row["source"]),
                source_reference=row["source_reference"],
                original_text=row["original_text"],
                original_language=row["original_language"],
                translated_text=row["translated_text"],
                submitted_at=datetime.fromisoformat(row["submitted_at"]),
                locality=row["locality"],
                district=row["district"],
                state=row["state"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                attachment_paths=json.loads(row["attachment_paths"] or "[]"),
                citizen_contact_hash=row["citizen_contact_hash"],
                consent_obtained=bool(row["consent_obtained"]),
                metadata=json.loads(row["metadata"] or "{}"),
            )

    def list_raw_complaints(self, limit: int = 100, offset: int = 0) -> list[ComplaintRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM raw_complaints ORDER BY submitted_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                results.append(ComplaintRecord(
                    id=row["id"],
                    source=ComplaintSource(row["source"]),
                    source_reference=row["source_reference"],
                    original_text=row["original_text"],
                    original_language=row["original_language"],
                    translated_text=row["translated_text"],
                    submitted_at=datetime.fromisoformat(row["submitted_at"]),
                    locality=row["locality"],
                    district=row["district"],
                    state=row["state"],
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    attachment_paths=json.loads(row["attachment_paths"] or "[]"),
                    citizen_contact_hash=row["citizen_contact_hash"],
                    consent_obtained=bool(row["consent_obtained"]),
                    metadata=json.loads(row["metadata"] or "{}"),
                ))
            return results

    # --- Processed Complaints ---

    def save_processed_complaint(self, processed: ProcessedComplaint) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO processed_complaints (
                complaint_id, language, translated_text, summary, category,
                subcategory, location, department, severity_score, urgency_score,
                estimated_people_affected, vulnerable_groups, infrastructure_gap_score,
                keywords, entities, ai_confidence, requires_human_review,
                processing_errors, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                processed.complaint_id,
                processed.language,
                processed.translated_text,
                processed.summary,
                processed.category,
                processed.subcategory,
                processed.location,
                processed.department,
                processed.severity_score,
                processed.urgency_score,
                processed.estimated_people_affected,
                json.dumps(processed.vulnerable_groups),
                processed.infrastructure_gap_score,
                json.dumps(processed.keywords),
                json.dumps(processed.entities),
                processed.ai_confidence,
                1 if processed.requires_human_review else 0,
                json.dumps(processed.processing_errors),
                processed.processed_at.isoformat(),
            ))
            conn.commit()

    def get_processed_complaint(self, complaint_id: str) -> Optional[ProcessedComplaint]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM processed_complaints WHERE complaint_id = ?", (complaint_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return ProcessedComplaint(
                complaint_id=row["complaint_id"],
                language=row["language"],
                translated_text=row["translated_text"],
                summary=row["summary"],
                category=ComplaintCategory(row["category"]),
                subcategory=row["subcategory"],
                location=row["location"],
                department=row["department"],
                severity_score=row["severity_score"],
                urgency_score=row["urgency_score"],
                estimated_people_affected=row["estimated_people_affected"],
                vulnerable_groups=json.loads(row["vulnerable_groups"] or "[]"),
                infrastructure_gap_score=row["infrastructure_gap_score"],
                keywords=json.loads(row["keywords"] or "[]"),
                entities=json.loads(row["entities"] or "[]"),
                ai_confidence=row["ai_confidence"],
                requires_human_review=bool(row["requires_human_review"]),
                processing_errors=json.loads(row["processing_errors"] or "[]"),
                processed_at=datetime.fromisoformat(row["processed_at"]),
            )

    def list_processed_complaints(self, limit: int = 1000, offset: int = 0) -> list[ProcessedComplaint]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM processed_complaints ORDER BY processed_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                results.append(ProcessedComplaint(
                    complaint_id=row["complaint_id"],
                    language=row["language"],
                    translated_text=row["translated_text"],
                    summary=row["summary"],
                    category=ComplaintCategory(row["category"]),
                    subcategory=row["subcategory"],
                    location=row["location"],
                    department=row["department"],
                    severity_score=row["severity_score"],
                    urgency_score=row["urgency_score"],
                    estimated_people_affected=row["estimated_people_affected"],
                    vulnerable_groups=json.loads(row["vulnerable_groups"] or "[]"),
                    infrastructure_gap_score=row["infrastructure_gap_score"],
                    keywords=json.loads(row["keywords"] or "[]"),
                    entities=json.loads(row["entities"] or "[]"),
                    ai_confidence=row["ai_confidence"],
                    requires_human_review=bool(row["requires_human_review"]),
                    processing_errors=json.loads(row["processing_errors"] or "[]"),
                    processed_at=datetime.fromisoformat(row["processed_at"]),
                ))
            return results

    # Convenience method aliases
    def save_complaint(self, record: ComplaintRecord) -> None:
        self.save_raw_complaint(record)

    def get_complaint(self, complaint_id: str) -> Optional[ComplaintRecord]:
        return self.get_raw_complaint(complaint_id)

    def list_complaints(self, limit: int = 1000, offset: int = 0) -> list[ComplaintRecord]:
        return self.list_raw_complaints(limit=limit, offset=offset)

    def save_processed(self, processed: ProcessedComplaint) -> None:
        self.save_processed_complaint(processed)

    def get_processed(self, complaint_id: str) -> Optional[ProcessedComplaint]:
        return self.get_processed_complaint(complaint_id)

    def list_processed(self, limit: int = 1000, offset: int = 0) -> list[ProcessedComplaint]:
        return self.list_processed_complaints(limit=limit, offset=offset)

    # --- Issue Clusters ---

    def save_cluster(self, cluster: IssueCluster) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO issue_clusters (
                cluster_id, title, description, category, locality,
                complaint_ids, complaint_count, unique_sources, average_severity,
                average_urgency, estimated_people_affected, vulnerable_groups,
                infrastructure_gap_score, priority_score, priority_level,
                recommendation, explanation, confidence, fairness_warnings,
                requires_human_review, status, assigned_department,
                metadata, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cluster.cluster_id,
                cluster.title,
                cluster.description,
                cluster.category,
                cluster.locality,
                json.dumps(cluster.complaint_ids),
                cluster.complaint_count,
                json.dumps(cluster.unique_sources),
                cluster.average_severity,
                cluster.average_urgency,
                cluster.estimated_people_affected,
                json.dumps(cluster.vulnerable_groups),
                cluster.infrastructure_gap_score,
                cluster.priority_score,
                cluster.priority_level,
                cluster.recommendation,
                cluster.explanation,
                cluster.confidence,
                json.dumps(cluster.fairness_warnings),
                1 if cluster.requires_human_review else 0,
                cluster.status,
                cluster.assigned_department,
                json.dumps(cluster.metadata),
                cluster.created_at.isoformat(),
                cluster.updated_at.isoformat(),
            ))
            conn.commit()

    def get_cluster(self, cluster_id: str) -> Optional[IssueCluster]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM issue_clusters WHERE cluster_id = ?", (cluster_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_cluster(row)

    def list_clusters(
        self,
        category: Optional[str] = None,
        locality: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[IssueCluster]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM issue_clusters WHERE 1=1"
            params: list[Any] = []
            if category:
                query += " AND category = ?"
                params.append(category)
            if locality:
                query += " AND locality = ?"
                params.append(locality)
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY priority_score DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            return [self._row_to_cluster(row) for row in cursor.fetchall()]

    def update_cluster_status(
        self,
        cluster_id: str,
        status: IssueStatus,
        assigned_department: Optional[str] = None,
    ) -> Optional[IssueCluster]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            if assigned_department is not None:
                cursor.execute(
                    "UPDATE issue_clusters SET status = ?, assigned_department = ?, updated_at = ? WHERE cluster_id = ?",
                    (status.value if isinstance(status, IssueStatus) else status, assigned_department, now, cluster_id),
                )
            else:
                cursor.execute(
                    "UPDATE issue_clusters SET status = ?, updated_at = ? WHERE cluster_id = ?",
                    (status.value if isinstance(status, IssueStatus) else status, now, cluster_id),
                )
            conn.commit()
        return self.get_cluster(cluster_id)

    def _row_to_cluster(self, row: sqlite3.Row) -> IssueCluster:
        return IssueCluster(
            cluster_id=row["cluster_id"],
            title=row["title"],
            description=row["description"],
            category=ComplaintCategory(row["category"]),
            locality=row["locality"],
            complaint_ids=json.loads(row["complaint_ids"]),
            complaint_count=row["complaint_count"],
            unique_sources=json.loads(row["unique_sources"] or "[]"),
            average_severity=row["average_severity"],
            average_urgency=row["average_urgency"],
            estimated_people_affected=row["estimated_people_affected"],
            vulnerable_groups=json.loads(row["vulnerable_groups"] or "[]"),
            infrastructure_gap_score=row["infrastructure_gap_score"],
            priority_score=row["priority_score"],
            priority_level=PriorityLevel(row["priority_level"]),
            recommendation=row["recommendation"],
            explanation=row["explanation"],
            confidence=row["confidence"],
            fairness_warnings=json.loads(row["fairness_warnings"] or "[]"),
            requires_human_review=bool(row["requires_human_review"]),
            status=IssueStatus(row["status"]),
            assigned_department=row["assigned_department"],
            metadata=json.loads(row["metadata"] or "{}") if "metadata" in row.keys() and row["metadata"] else {},
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
