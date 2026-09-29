"""Integration tests for Phase 7 FastAPI REST API Layer.
"""

from fastapi.testclient import TestClient
import pytest

from civicpriority.api import app, get_pipeline
from civicpriority.models import ComplaintCategory, IssueStatus, PriorityLevel


@pytest.fixture(scope="module")
def client():
    # Ensure sample complaints are loaded
    pipe = get_pipeline()
    pipe.seed_initial_data_if_empty()
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    """Verify health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "CivicPriority AI" in data["service"]


def test_ingest_single_complaint_masks_contact(client):
    """Verify POST /api/complaints masks contact and returns processed analysis."""
    payload = {
        "original_text": "Emergency: Collapsed sewer cover in Ward 7. Call 9876543210 immediately.",
        "locality": "Ward 7",
        "contact": "9876543210",
        "district": "Central District",
    }
    response = client.post("/api/complaints", json=payload)
    assert response.status_code == 201
    data = response.json()

    # Raw complaint checks
    complaint = data["complaint"]
    assert complaint["id"].startswith("CMP-")
    assert "[PHONE_REDACTED]" in complaint["original_text"]
    assert "9876543210" not in complaint["original_text"]
    assert complaint["citizen_contact_hash"] is not None

    # Processed complaint checks
    proc = data["processed"]
    assert proc["complaint_id"] == complaint["id"]
    assert proc["severity_score"] >= 60.0
    assert proc["category"] in [ComplaintCategory.WATER_AND_SANITATION.value, ComplaintCategory.ROADS_AND_TRANSPORT.value]


def test_batch_ingest_text(client):
    """Verify POST /api/ingest parses text representation."""
    text_payload = """
    Locality: Ward 15
    Subject: Broken Electric Pole
    Live wire hanging near primary school playground. Dangerous hazard. Call 9811223344.
    """
    response = client.post("/api/ingest", json={"connector_type": "text", "payload": text_payload})
    assert response.status_code == 200
    data = response.json()
    assert data["accepted"] >= 1
    assert data["rejected"] == 0


def test_list_complaints_with_filtering_and_search(client):
    """Verify GET /api/complaints supports pagination, search, and ward filtering."""
    # 1. Basic pagination
    res = client.get("/api/complaints?page=1&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) <= 10
    assert data["total"] >= 50

    # 2. Ward filter
    res_w12 = client.get("/api/complaints?ward=Ward 12")
    assert res_w12.status_code == 200
    w12_data = res_w12.json()
    assert all("Ward 12" in item["raw"]["locality"] for item in w12_data["items"])

    # 3. Search filter (searching Hindi text keyword)
    res_search = client.get("/api/complaints?search=स्कूल")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert len(search_data["items"]) >= 1


def test_list_clusters_prioritization(client):
    """Verify GET /api/clusters returns prioritized issues sorted descending by score."""
    res = client.get("/api/clusters")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    items = data["items"]

    # Verify descending score sorting
    scores = [c["priority_score"] for c in items]
    assert scores == sorted(scores, reverse=True)

    # Verify Ward 12 school cluster exists in top clusters
    w12_cluster = next((c for c in items if "Ward 12" in c["locality"] and "Education" in c["category"]), None)
    assert w12_cluster is not None
    assert w12_cluster["complaint_count"] >= 4
    assert "Children" in w12_cluster["vulnerable_groups"]


def test_get_cluster_details_with_breakdown(client):
    """Verify GET /api/clusters/{id} returns underlying complaints and score breakdown."""
    # Fetch first cluster
    list_res = client.get("/api/clusters")
    first_cluster_id = list_res.json()["items"][0]["cluster_id"]

    res = client.get(f"/api/clusters/{first_cluster_id}")
    assert res.status_code == 200
    data = res.json()

    # Structure checks
    assert data["cluster"]["cluster_id"] == first_cluster_id
    assert len(data["underlying_complaints"]) >= 1

    # Score breakdown verification
    breakdown = data["score_breakdown"]
    assert "severity_contribution" in breakdown
    assert "people_contribution" in breakdown
    assert "urgency_contribution" in breakdown
    assert "infrastructure_contribution" in breakdown
    assert "repeat_contribution" in breakdown
    assert "explanation" in breakdown


def test_patch_cluster_status_and_assignment(client):
    """Verify PATCH /api/clusters/{id} updates administrative state."""
    list_res = client.get("/api/clusters")
    target_id = list_res.json()["items"][0]["cluster_id"]

    update_payload = {
        "status": IssueStatus.UNDER_REVIEW.value,
        "assigned_department": "Municipal Rapid Response Taskforce",
        "notes": "Site inspection scheduled for 10:00 AM tomorrow.",
    }
    patch_res = client.patch(f"/api/clusters/{target_id}", json=update_payload)
    assert patch_res.status_code == 200
    updated = patch_res.json()["cluster"]

    assert updated["status"] == IssueStatus.UNDER_REVIEW.value
    assert updated["assigned_department"] == "Municipal Rapid Response Taskforce"
    assert updated["metadata"]["admin_notes"] == "Site inspection scheduled for 10:00 AM tomorrow."


def test_get_analytics_summary(client):
    """Verify GET /api/analytics returns multi-channel grievance intelligence."""
    res = client.get("/api/analytics")
    assert res.status_code == 200
    data = res.json()

    assert data["total_complaints"] >= 50
    assert data["total_clusters"] >= 5
    assert len(data["by_ward"]) >= 5
    assert len(data["by_category"]) >= 5
    assert "hi" in data["by_language"]
    assert "en" in data["by_language"]
    assert "public_meeting" in data["by_source"]
    assert "Children" in data["vulnerable_groups_distribution"]
    assert len(data["top_priority_clusters"]) >= 1


def test_recluster_endpoint(client):
    """Verify POST /api/pipeline/recluster recomputes cluster rankings."""
    weights_payload = {
        "weight_severity": 0.40,
        "weight_people": 0.20,
        "weight_urgency": 0.20,
        "weight_infrastructure_gap": 0.10,
        "weight_repeated_complaints": 0.10,
    }
    res = client.post("/api/pipeline/recluster", json=weights_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["clusters_count"] > 0
    assert len(data["clusters"]) == data["clusters_count"]
