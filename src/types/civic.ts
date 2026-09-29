/**
 * TypeScript types and interfaces for CivicPriority AI.
 */

export type PriorityLevel = "Critical" | "High" | "Medium" | "Low";

export type IssueStatus = "open" | "under_review" | "in_progress" | "resolved";

export type ComplaintCategory =
  | "Education"
  | "Water and sanitation"
  | "Roads and transport"
  | "Healthcare"
  | "Electricity"
  | "Waste management"
  | "Public safety"
  | "Housing"
  | "Social welfare"
  | "Environment"
  | "Other";

export type ComplaintSource =
  | "public_meeting"
  | "direct_web"
  | "messaging"
  | "letter_pdf"
  | "social_media"
  | "grievance_portal";

export interface ComplaintRecord {
  id: string;
  source: ComplaintSource;
  source_reference?: string | null;
  original_text: string;
  original_language: string;
  translated_text?: string | null;
  submitted_at: string;
  locality: string;
  district?: string | null;
  state?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  attachment_paths?: string[];
  citizen_contact_hash?: string | null;
  consent_obtained: boolean;
  metadata?: Record<string, any>;
}

export interface ProcessedComplaint {
  complaint_id: string;
  language: string;
  translated_text: string;
  summary: string;
  category: ComplaintCategory;
  subcategory?: string | null;
  location: string;
  department: string;
  severity_score: number;
  urgency_score: number;
  estimated_people_affected: number;
  vulnerable_groups: string[];
  infrastructure_gap_score: number;
  keywords: string[];
  entities: string[];
  ai_confidence: number;
  requires_human_review: boolean;
  processing_errors: string[];
  processed_at: string;
}

export interface IssueCluster {
  cluster_id: string;
  title: string;
  description: string;
  category: ComplaintCategory;
  locality: string;
  complaint_ids: string[];
  complaint_count: number;
  unique_sources: string[];
  average_severity: number;
  average_urgency: number;
  estimated_people_affected: number;
  vulnerable_groups: string[];
  infrastructure_gap_score: number;
  priority_score: number;
  priority_level: PriorityLevel;
  recommendation: string;
  explanation: string;
  confidence: number;
  fairness_warnings: string[];
  requires_human_review: boolean;
  status: IssueStatus;
  assigned_department?: string | null;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ScoreBreakdown {
  raw_severity: number;
  raw_people_affected: number;
  raw_urgency: number;
  raw_infrastructure_gap: number;
  raw_complaint_count: number;
  normalized_people_score: number;
  normalized_repeat_score: number;
  severity_contribution: number;
  people_contribution: number;
  urgency_contribution: number;
  infrastructure_contribution: number;
  repeat_contribution: number;
  total_priority_score: number;
  priority_level: PriorityLevel;
  fairness_warnings: string[];
  explanation: string;
}

export interface UnderlyingComplaintItem {
  raw: ComplaintRecord;
  processed: ProcessedComplaint | null;
}

export interface ClusterDetailResponse {
  cluster: IssueCluster;
  underlying_complaints: UnderlyingComplaintItem[];
  score_breakdown: ScoreBreakdown;
}

export interface AnalyticsData {
  total_complaints: number;
  total_clusters: number;
  critical_issues_count: number;
  high_issues_count: number;
  by_category: Record<string, number>;
  by_ward: Record<string, number>;
  by_language: Record<string, number>;
  by_source: Record<string, number>;
  by_priority_level: Record<string, number>;
  vulnerable_groups_distribution: Record<string, number>;
  top_priority_clusters: IssueCluster[];
}

export interface ScoringWeights {
  weight_severity: number;
  weight_people: number;
  weight_urgency: number;
  weight_infrastructure_gap: number;
  weight_repeated_complaints: number;
}
