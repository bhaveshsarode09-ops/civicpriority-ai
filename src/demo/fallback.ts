import {
  AnalyticsData,
  ComplaintRecord,
  IssueCluster,
  ProcessedComplaint,
  ClusterDetailResponse,
  ScoreBreakdown,
} from "../types/civic";
import { KAGGLE_ANALYTICS, KAGGLE_CLUSTERS } from "./kaggleDemoData";

export const DEMO_CLUSTERS: IssueCluster[] = KAGGLE_CLUSTERS as unknown as IssueCluster[];
export const DEMO_ANALYTICS: AnalyticsData = KAGGLE_ANALYTICS as unknown as AnalyticsData;

const demoComplaints = new Map<string, ComplaintRecord>();

function now() {
  return new Date().toISOString();
}

function classify(text: string) {
  const value = text.toLowerCase();
  if (/school|classroom|विद्यालय|शाळा|education/.test(value)) return "Education" as const;
  if (/water|पानी|पाणी|sanitation|sewage/.test(value)) return "Water and sanitation" as const;
  if (/road|pothole|सड़क|रस्ता|bridge/.test(value)) return "Roads and transport" as const;
  if (/hospital|medicine|health|स्वास्थ्य|आरोग्य/.test(value)) return "Healthcare" as const;
  return "Other" as const;
}

export function demoSubmitComplaint(input: {
  original_text: string;
  locality: string;
  source?: ComplaintRecord["source"];
  contact?: string;
}): { complaint: ComplaintRecord; processed: ProcessedComplaint } {
  const id = `DEMO-${Date.now()}`;
  const category = classify(input.original_text);
  const complaint: ComplaintRecord = {
    id,
    source: input.source ?? "direct_web",
    original_text: input.original_text.replace(/\b[6-9]\d{9}\b/g, "[PHONE_REDACTED]"),
    original_language: /[\u0900-\u097f]/.test(input.original_text) ? "hi" : "en",
    translated_text: input.original_text,
    submitted_at: now(),
    locality: input.locality,
    consent_obtained: true,
    citizen_contact_hash: input.contact ? "demo-contact-hash" : null,
    metadata: { mode: "static_demo", dataset: "Kaggle municipal benchmark" },
  };
  const processed: ProcessedComplaint = {
    complaint_id: id,
    language: complaint.original_language,
    translated_text: complaint.original_text,
    summary: `Demo triage: ${category} issue reported in ${input.locality}.`,
    category,
    subcategory: "Civic service request",
    location: input.locality,
    department: category === "Education" ? "Education Department" : "Municipal Services",
    severity_score: 78,
    urgency_score: 74,
    estimated_people_affected: 120,
    vulnerable_groups: category === "Education" ? ["Children"] : [],
    infrastructure_gap_score: 70,
    keywords: [category, input.locality],
    entities: [input.locality],
    ai_confidence: 0.82,
    requires_human_review: true,
    processing_errors: ["Static demo fallback used because the processing API was unavailable."],
    processed_at: now(),
  };
  demoComplaints.set(id, complaint);
  return { complaint, processed };
}

export function demoClusterDetails(clusterId: string): ClusterDetailResponse {
  const cluster = DEMO_CLUSTERS.find((item) => item.cluster_id === clusterId) ?? DEMO_CLUSTERS[0];
  const scoreBreakdown: ScoreBreakdown = {
    raw_severity: cluster.average_severity,
    raw_people_affected: cluster.estimated_people_affected,
    raw_urgency: cluster.average_urgency,
    raw_infrastructure_gap: cluster.infrastructure_gap_score,
    raw_complaint_count: cluster.complaint_count,
    normalized_people_score: Math.min(100, cluster.estimated_people_affected / 10),
    normalized_repeat_score: Math.min(100, cluster.complaint_count * 8),
    severity_contribution: cluster.average_severity * 0.3,
    people_contribution: Math.min(100, cluster.estimated_people_affected / 10) * 0.25,
    urgency_contribution: cluster.average_urgency * 0.2,
    infrastructure_contribution: cluster.infrastructure_gap_score * 0.15,
    repeat_contribution: Math.min(100, cluster.complaint_count * 8) * 0.1,
    total_priority_score: cluster.priority_score,
    priority_level: cluster.priority_level,
    fairness_warnings: cluster.fairness_warnings,
    explanation: cluster.explanation,
  };
  return { cluster, underlying_complaints: [], score_breakdown: scoreBreakdown };
}

export function demoUpdateCluster(clusterId: string, update: { status?: IssueCluster["status"]; assigned_department?: string; notes?: string }) {
  const cluster = DEMO_CLUSTERS.find((item) => item.cluster_id === clusterId) ?? DEMO_CLUSTERS[0];
  if (update.status) cluster.status = update.status;
  if (update.assigned_department) cluster.assigned_department = update.assigned_department;
  cluster.updated_at = now();
  return cluster;
}
