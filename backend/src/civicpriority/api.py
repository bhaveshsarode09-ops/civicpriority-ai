"""FastAPI Application for CivicPriority AI.
Exposes REST endpoints for complaint ingestion, listing, clustering, transparent scoring,
issue lifecycle updates, and civic grievance analytics.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from civicpriority.ai import GeminiProvider, MockAIProvider
from civicpriority.connectors import (
    CSVConnector,
    GrievancePortalMockConnector,
    MessagingMockConnector,
    SocialMediaMockConnector,
    TextFileConnector,
    TranscriptConnector,
)
from civicpriority.database import Database
from civicpriority.models import (
    ComplaintCategory,
    ComplaintRecord,
    ComplaintSource,
    IssueCluster,
    IssueStatus,
    PriorityLevel,
    ProcessedComplaint,
    utc_now,
)
from civicpriority.pipeline import CivicPipeline
from civicpriority.privacy import hash_contact_identifier, mask_contact_in_text
from civicpriority.scoring import (
    ScoreBreakdown,
    ScoringWeights,
    calculate_priority_score,
)

# Global pipeline instance
pipeline: Optional[CivicPipeline] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline
    db_path = Path("backend/data/civic_priority.sqlite3")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = Database(str(db_path))
    # Default to fast, deterministic MockAIProvider for bulk responsiveness; GeminiProvider ready on demand
    ai = MockAIProvider()
    pipeline = CivicPipeline(db=db, ai_provider=ai)
    # Automatically seed initial sample dataset if DB is empty
    count = pipeline.seed_initial_data_if_empty()
    print(f"CivicPriority AI pipeline initialized. Seeded/Available records: {count}")
    yield


app = FastAPI(
    title="CivicPriority AI API",
    description="Multilingual Civic Issue Triage, Clustering, and Transparent Priority Ranking",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend Vite dev server (port 3000) and previews
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_pipeline() -> CivicPipeline:
    global pipeline
    if pipeline is None:
        db_path = Path("backend/data/civic_priority.sqlite3")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db = Database(str(db_path))
        pipeline = CivicPipeline(db=db)
        pipeline.seed_initial_data_if_empty()
    return pipeline


# ==========================================
# Request & Response Schemas
# ==========================================

class SingleComplaintRequest(BaseModel):
    original_text: str = Field(min_length=3, description="Citizen complaint text")
    locality: str = Field(description="Ward, neighborhood, or village name")
    source: Optional[ComplaintSource] = ComplaintSource.DIRECT_WEB
    source_reference: Optional[str] = None
    original_language: Optional[str] = "en"
    contact: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    consent_obtained: bool = True
    metadata: Optional[dict[str, Any]] = None


class BatchIngestRequest(BaseModel):
    connector_type: str = Field(description="csv, text, transcript, social_media, grievance_portal, messaging")
    payload: Any = Field(description="String text, CSV content, or JSON payload")


class UpdateClusterRequest(BaseModel):
    status: Optional[IssueStatus] = None
    assigned_department: Optional[str] = None
    notes: Optional[str] = None


# ==========================================
# Endpoints
# ==========================================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CivicPriority AI Engine",
        "timestamp": utc_now().isoformat(),
    }


@app.post("/api/complaints", status_code=status.HTTP_201_CREATED)
def ingest_single_complaint(body: SingleComplaintRequest):
    """Ingest a single citizen grievance with automatic PII masking and instant AI processing."""
    pipe = get_pipeline()

    # Mask contact info in text
    masked_text = mask_contact_in_text(body.original_text)
    contact_hash = hash_contact_identifier(body.contact) if body.contact else None

    # Safe source string
    src_val = body.source.value if hasattr(body.source, "value") else str(body.source)
    cid = f"CMP-{src_val[:3].upper()}-{len(pipe.db.list_complaints()) + 1:04d}"

    record = ComplaintRecord(
        id=cid,
        source=body.source,
        source_reference=body.source_reference,
        original_text=masked_text,
        original_language=body.original_language or "en",
        submitted_at=utc_now(),
        locality=body.locality,
        district=body.district,
        state=body.state,
        latitude=body.latitude,
        longitude=body.longitude,
        citizen_contact_hash=contact_hash,
        consent_obtained=body.consent_obtained,
        metadata=body.metadata or {},
    )

    rec, processed = pipe.ingest_single(record)
    return {
        "complaint": rec.model_dump(),
        "processed": processed.model_dump(),
    }


@app.post("/api/ingest")
def batch_ingest(body: BatchIngestRequest):
    """Batch ingest records from any supported connector type."""
    pipe = get_pipeline()
    ctype = body.connector_type.lower().strip()
    records: list[ComplaintRecord] = []
    errors: list[str] = []

    try:
        if ctype == "csv":
            connector = CSVConnector()
            records = connector.load(body.payload)
        elif ctype == "text":
            connector = TextFileConnector()
            records = connector.load(str(body.payload))
        elif ctype == "transcript":
            connector = TranscriptConnector()
            records = connector.load(str(body.payload))
        elif ctype == "social_media":
            connector = SocialMediaMockConnector()
            records = connector.load(body.payload)
        elif ctype == "grievance_portal":
            connector = GrievancePortalMockConnector()
            records = connector.load(body.payload)
        elif ctype == "messaging":
            connector = MessagingMockConnector()
            records = connector.load(body.payload)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported connector type: {ctype}")
    except Exception as e:
        errors.append(str(e))
        return {
            "accepted": 0,
            "rejected": 0,
            "total": 0,
            "errors": errors,
        }

    res = pipe.ingest_batch(records)
    return {
        "accepted": res["accepted"],
        "rejected": res["rejected"],
        "total": res["total"],
        "errors": errors,
    }


@app.get("/api/complaints")
def list_complaints(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = None,
    ward: Optional[str] = None,
    category: Optional[str] = None,
    language: Optional[str] = None,
    source: Optional[str] = None,
):
    """List complaints with pagination and multi-field filters."""
    pipe = get_pipeline()
    raw_list = pipe.db.list_complaints()
    proc_map = {p.complaint_id: p for p in pipe.db.list_processed()}

    filtered = []
    search_lower = search.lower().strip() if search else None
    ward_lower = ward.lower().strip() if ward else None
    cat_lower = category.lower().strip() if category else None
    lang_lower = language.lower().strip() if language else None
    src_lower = source.lower().strip() if source else None

    for r in raw_list:
        p = proc_map.get(r.id)

        # Filters
        r_src = r.source.value if hasattr(r.source, "value") else str(r.source)
        if ward_lower and ward_lower not in r.locality.lower():
            continue
        if lang_lower and r.original_language.lower() != lang_lower:
            continue
        if src_lower and r_src.lower() != src_lower:
            continue
        if cat_lower and p:
            p_cat = p.category.value if hasattr(p.category, "value") else str(p.category)
            if cat_lower not in p_cat.lower():
                continue

        if search_lower:
            match_text = (
                r.original_text.lower()
                + " "
                + (p.translated_text.lower() if p else "")
                + " "
                + r.locality.lower()
                + " "
                + r.id.lower()
            )
            if search_lower not in match_text:
                continue

        filtered.append({
            "raw": r.model_dump(),
            "processed": p.model_dump() if p else None,
        })

    # Sort newest first
    filtered.sort(key=lambda item: item["raw"]["submitted_at"], reverse=True)

    total = len(filtered)
    start = (page - 1) * limit
    end = start + limit
    items = filtered[start:end]

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
    }


@app.get("/api/clusters")
def list_clusters(
    priority_level: Optional[str] = None,
    category: Optional[str] = None,
    ward: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
):
    """Return prioritized issues sorted by priority score, with filters."""
    pipe = get_pipeline()
    clusters = pipe.db.list_clusters()

    # Recluster if empty
    if not clusters:
        clusters = pipe.recluster_and_rescore()

    filtered = []
    p_lvl_lower = priority_level.lower().strip() if priority_level else None
    cat_lower = category.lower().strip() if category else None
    ward_lower = ward.lower().strip() if ward else None
    stat_lower = status.lower().strip() if status else None
    search_lower = search.lower().strip() if search else None

    for cl in clusters:
        cl_plvl = cl.priority_level.value if hasattr(cl.priority_level, "value") else str(cl.priority_level)
        cl_cat = cl.category.value if hasattr(cl.category, "value") else str(cl.category)
        cl_stat = cl.status.value if hasattr(cl.status, "value") else str(cl.status)

        if p_lvl_lower and cl_plvl.lower() != p_lvl_lower:
            continue
        if cat_lower and cat_lower not in cl_cat.lower():
            continue
        if ward_lower and ward_lower not in cl.locality.lower():
            continue
        if stat_lower and cl_stat.lower() != stat_lower:
            continue
        if search_lower:
            text = (cl.title + " " + cl.description + " " + cl.locality).lower()
            if search_lower not in text:
                continue
        filtered.append(cl)

    # Sort descending by priority score
    filtered.sort(key=lambda c: c.priority_score, reverse=True)
    return {
        "items": [c.model_dump() for c in filtered],
        "total": len(filtered),
    }


@app.get("/api/clusters/{cluster_id}")
def get_cluster_details(cluster_id: str):
    """Return full detailed view of an issue cluster, including all underlying complaints
    and transparent mathematical factor breakdown.
    """
    pipe = get_pipeline()
    cluster = pipe.db.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

    # Fetch underlying complaints
    underlying = []
    for cid in cluster.complaint_ids:
        raw = pipe.db.get_complaint(cid)
        proc = pipe.db.get_processed(cid)
        if raw:
            underlying.append({
                "raw": raw.model_dump(),
                "processed": proc.model_dump() if proc else None,
            })

    # Compute explicit score breakdown
    breakdown = calculate_priority_score(
        severity=cluster.average_severity,
        people_affected=cluster.estimated_people_affected,
        urgency=cluster.average_urgency,
        infrastructure_gap=cluster.infrastructure_gap_score,
        complaint_count=cluster.complaint_count,
        locality=cluster.locality,
        vulnerable_groups=cluster.vulnerable_groups,
        weights=pipe.weights,
    )

    return {
        "cluster": cluster.model_dump(),
        "underlying_complaints": underlying,
        "score_breakdown": breakdown.model_dump(),
    }


@app.patch("/api/clusters/{cluster_id}")
def update_cluster(cluster_id: str, body: UpdateClusterRequest):
    """Update issue status (open, investigating, in_progress, resolved), assign department, or add notes."""
    pipe = get_pipeline()
    cluster = pipe.db.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

    if body.status is not None:
        cluster.status = body.status
    if body.assigned_department is not None:
        cluster.assigned_department = body.assigned_department
    if body.notes is not None:
        cluster.metadata["admin_notes"] = body.notes

    cluster.updated_at = utc_now()
    pipe.db.save_cluster(cluster)

    return {
        "message": "Cluster updated successfully",
        "cluster": cluster.model_dump(),
    }


@app.get("/api/analytics")
def get_analytics():
    """Summary statistics across the entire grievance database."""
    pipe = get_pipeline()
    raw_list = pipe.db.list_complaints()
    proc_list = pipe.db.list_processed()
    clusters = pipe.db.list_clusters()

    if not clusters and proc_list:
        clusters = pipe.recluster_and_rescore()

    by_category: dict[str, int] = {}
    by_ward: dict[str, int] = {}
    by_language: dict[str, int] = {}
    by_source: dict[str, int] = {}
    vulnerable_dist: dict[str, int] = {}

    for r in raw_list:
        by_ward[r.locality] = by_ward.get(r.locality, 0) + 1
        by_language[r.original_language] = by_language.get(r.original_language, 0) + 1
        src_val = r.source.value if hasattr(r.source, "value") else str(r.source)
        by_source[src_val] = by_source.get(src_val, 0) + 1

    for p in proc_list:
        cat_str = p.category.value if hasattr(p.category, "value") else str(p.category)
        by_category[cat_str] = by_category.get(cat_str, 0) + 1
        for vg in p.vulnerable_groups:
            vulnerable_dist[vg] = vulnerable_dist.get(vg, 0) + 1

    by_priority: dict[str, int] = {
        PriorityLevel.CRITICAL.value: 0,
        PriorityLevel.HIGH.value: 0,
        PriorityLevel.MEDIUM.value: 0,
        PriorityLevel.LOW.value: 0,
    }
    for cl in clusters:
        lvl = cl.priority_level.value if hasattr(cl.priority_level, "value") else str(cl.priority_level)
        by_priority[lvl] = by_priority.get(lvl, 0) + 1

    # Top priority issues
    sorted_clusters = sorted(clusters, key=lambda c: c.priority_score, reverse=True)
    top_clusters = [c.model_dump() for c in sorted_clusters[:5]]

    return {
        "total_complaints": len(raw_list),
        "total_clusters": len(clusters),
        "critical_issues_count": by_priority.get(PriorityLevel.CRITICAL.value, 0),
        "high_issues_count": by_priority.get(PriorityLevel.HIGH.value, 0),
        "by_category": by_category,
        "by_ward": by_ward,
        "by_language": by_language,
        "by_source": by_source,
        "by_priority_level": by_priority,
        "vulnerable_groups_distribution": vulnerable_dist,
        "top_priority_clusters": top_clusters,
    }


@app.post("/api/pipeline/recluster")
def recluster_pipeline(weights: Optional[ScoringWeights] = None):
    """Re-runs clustering and scoring on demand or with updated weights."""
    pipe = get_pipeline()
    if weights:
        pipe.weights = weights
    clusters = pipe.recluster_and_rescore(custom_weights=weights)
    return {
        "message": "Re-clustering completed",
        "clusters_count": len(clusters),
        "clusters": [c.model_dump() for c in clusters],
    }
