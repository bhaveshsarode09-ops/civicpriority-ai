"""Data models for CivicPriority AI.
Defines Pydantic models, enums, validation rules, and serialization helpers.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ComplaintSource(str, Enum):
    """Authorized complaint sources supported by CivicPriority AI."""
    DIRECT_WEB = "direct_web"
    PUBLIC_MEETING = "public_meeting"
    LETTER_PDF = "letter_pdf"
    SOCIAL_MEDIA = "social_media"
    GRIEVANCE_PORTAL = "grievance_portal"
    MESSAGING = "messaging"
    VOICE_TRANSCRIPT = "voice_transcript"
    CSV = "csv"


class ComplaintCategory(str, Enum):
    """Configurable civic complaint categories."""
    ROADS_AND_TRANSPORT = "Roads and transport"
    WATER_AND_SANITATION = "Water and sanitation"
    EDUCATION = "Education"
    HEALTHCARE = "Healthcare"
    AGRICULTURE = "Agriculture"
    ELECTRICITY = "Electricity"
    POLLUTION_AND_ENVIRONMENT = "Pollution and environment"
    PUBLIC_SAFETY = "Public safety"
    HOUSING = "Housing"
    DIGITAL_PUBLIC_INFRASTRUCTURE = "Digital public infrastructure"
    OTHER = "Other"


class PriorityLevel(str, Enum):
    """Categorical ranking for policymakers."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class IssueStatus(str, Enum):
    """Administrative workflow status for policymakers."""
    OPEN = "Open"
    UNDER_REVIEW = "Under Review"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class ComplaintRecord(BaseModel):
    """Raw or normalized complaint record ingested from any supported source."""
    model_config = ConfigDict(use_enum_values=True)

    id: str = Field(..., description="Unique complaint identifier (e.g. CMP-2026-0001)")
    source: ComplaintSource = Field(..., description="Channel from which the complaint was received")
    source_reference: Optional[str] = Field(None, description="External reference ID (e.g., tweet id, meeting minute line, grievance token)")
    original_text: str = Field(..., min_length=3, description="Original verbatim text as submitted by citizen")
    original_language: str = Field(default="en", description="Detected or declared ISO language code (e.g., 'hi', 'en', 'mr')")
    translated_text: Optional[str] = Field(None, description="Standardized English translation for pipeline analysis")
    submitted_at: datetime = Field(default_factory=utc_now, description="Timestamp of submission")
    locality: str = Field(..., min_length=1, description="Ward, village, neighborhood, or sector")
    district: Optional[str] = Field(None, description="Administrative district name")
    state: Optional[str] = Field(None, description="State or province")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Optional GPS latitude")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Optional GPS longitude")
    attachment_paths: list[str] = Field(default_factory=list, description="Associated media or document attachments")
    citizen_contact_hash: Optional[str] = Field(None, description="Salted SHA-256 hash of citizen contact info (phone/email)")
    consent_obtained: bool = Field(default=True, description="Whether citizen consent was granted for grievance processing")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Arbitrary source-specific metadata")

    @field_validator("id")
    @classmethod
    def validate_id_not_empty(cls, v: str) -> str:
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("Complaint id cannot be empty.")
        return v_stripped

    @field_validator("original_text")
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        v_stripped = v.strip()
        if len(v_stripped) < 3:
            raise ValueError("Complaint text must contain at least 3 characters.")
        return v_stripped


class ProcessedComplaint(BaseModel):
    """Structured analytical record produced by the ML and AI pipeline."""
    model_config = ConfigDict(use_enum_values=True)

    complaint_id: str = Field(..., description="ID matching the raw ComplaintRecord")
    language: str = Field(..., description="Detected language code")
    translated_text: str = Field(..., description="Normalized English translation")
    summary: str = Field(..., description="Concise one-sentence synthesis of the complaint")
    category: ComplaintCategory = Field(..., description="Assigned primary category")
    subcategory: Optional[str] = Field(None, description="Finer-grained sub-classification")
    location: str = Field(..., description="Normalized locality or geographic descriptor")
    department: str = Field(..., description="Primary responsible government department")
    severity_score: float = Field(..., ge=0.0, le=100.0, description="Severity score (0-100)")
    urgency_score: float = Field(..., ge=0.0, le=100.0, description="Urgency score (0-100)")
    estimated_people_affected: int = Field(default=1, ge=0, description="Estimated count of impacted individuals")
    vulnerable_groups: list[str] = Field(default_factory=list, description="Vulnerable groups identified (e.g., children, elderly, patients)")
    infrastructure_gap_score: float = Field(default=50.0, ge=0.0, le=100.0, description="Severity of missing/damaged public infrastructure (0-100)")
    keywords: list[str] = Field(default_factory=list, description="Extracted domain keywords")
    entities: list[str] = Field(default_factory=list, description="Extracted named entities (schools, hospitals, road names)")
    ai_confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Model confidence score (0.0 to 1.0)")
    requires_human_review: bool = Field(default=False, description="Flag indicating human triage needed due to ambiguity or sensitive content")
    processing_errors: list[str] = Field(default_factory=list, description="Non-fatal warnings or processing logs")
    processed_at: datetime = Field(default_factory=utc_now, description="Processing timestamp")

    @field_validator("complaint_id")
    @classmethod
    def validate_complaint_id(cls, v: str) -> str:
        v_stripped = v.strip()
        if not v_stripped:
            raise ValueError("complaint_id cannot be blank.")
        return v_stripped


class IssueCluster(BaseModel):
    """Ranked issue cluster synthesizing multiple complaints into a single policy priority."""
    model_config = ConfigDict(use_enum_values=True)

    cluster_id: str = Field(..., description="Unique cluster identifier (e.g. CLU-WARD12-EDU-01)")
    title: str = Field(..., description="Actionable title for government policymakers")
    description: str = Field(..., description="Synthesized description of the underlying problem")
    category: ComplaintCategory = Field(..., description="Primary civic category")
    locality: str = Field(..., description="Locality or ward")
    complaint_ids: list[str] = Field(..., min_length=1, description="List of grouped complaint IDs")
    complaint_count: int = Field(..., ge=1, description="Total complaints in this cluster")
    unique_sources: list[str] = Field(default_factory=list, description="Distinct reporting channels (e.g., web, meeting, sms)")
    average_severity: float = Field(..., ge=0.0, le=100.0, description="Aggregated average severity (0-100)")
    average_urgency: float = Field(..., ge=0.0, le=100.0, description="Aggregated average urgency (0-100)")
    estimated_people_affected: int = Field(default=1, ge=0, description="Estimated total affected population")
    vulnerable_groups: list[str] = Field(default_factory=list, description="Aggregated vulnerable demographics")
    infrastructure_gap_score: float = Field(default=50.0, ge=0.0, le=100.0, description="Infrastructure deficit metric (0-100)")
    priority_score: float = Field(..., ge=0.0, le=100.0, description="Transparent computed priority score (0-100)")
    priority_level: PriorityLevel = Field(..., description="Categorical priority tier")
    recommendation: str = Field(..., description="Concrete, actionable policy recommendation")
    explanation: str = Field(..., description="Human-readable transparent explanation of the rank")
    confidence: float = Field(default=0.90, ge=0.0, le=1.0, description="Cluster-level confidence score")
    fairness_warnings: list[str] = Field(default_factory=list, description="Fairness alerts (e.g. low-frequency high-severity alerts)")
    requires_human_review: bool = Field(default=False, description="Flag for manual oversight")
    status: IssueStatus = Field(default=IssueStatus.OPEN, description="Administrative workflow status")
    assigned_department: Optional[str] = Field(None, description="Designated municipal or state agency")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Administrative metadata, notes, and audit history")
    created_at: datetime = Field(default_factory=utc_now, description="Cluster creation timestamp")
    updated_at: datetime = Field(default_factory=utc_now, description="Last updated timestamp")

    @model_validator(mode="after")
    def sync_complaint_count(self) -> "IssueCluster":
        """Ensure complaint_count matches the length of complaint_ids if not explicitly aligned."""
        if len(self.complaint_ids) != self.complaint_count:
            self.complaint_count = len(self.complaint_ids)
        return self
