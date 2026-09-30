/**
 * API client for CivicPriority AI backend endpoints.
 */

import {
  AnalyticsData,
  ClusterDetailResponse,
  ComplaintCategory,
  ComplaintRecord,
  ComplaintSource,
  IssueCluster,
  IssueStatus,
  PriorityLevel,
  ProcessedComplaint,
  ScoringWeights,
  UnderlyingComplaintItem,
} from "../types/civic";
import {
  DEMO_ANALYTICS,
  DEMO_CLUSTERS,
  demoClusterDetails,
  demoSubmitComplaint,
  demoUpdateCluster,
} from "../demo/fallback";

const BASE_URL = "";

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
    });

    if (!res.ok) {
      let errDetail = `HTTP ${res.status} ${res.statusText}`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          errDetail = typeof errorJson.detail === "string" ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch {
        // use default status
      }
      throw new Error(errDetail);
    }

    return (await res.json()) as T;
  } catch (err: any) {
    console.error(`API Error on [${options?.method || "GET"}] ${endpoint}:`, err);
    throw err;
  }
}

export async function checkHealth(): Promise<{ status: string; service: string }> {
  return request<{ status: string; service: string }>("/api/health");
}

export async function fetchAnalytics(): Promise<AnalyticsData> {
  try {
    return await request<AnalyticsData>("/api/analytics");
  } catch {
    return DEMO_ANALYTICS;
  }
}

export interface ClusterFilterParams {
  priority_level?: PriorityLevel | "All";
  category?: ComplaintCategory | "All";
  ward?: string | "All";
  status?: IssueStatus | "All";
  search?: string;
}

export async function fetchClusters(filters?: ClusterFilterParams): Promise<{ items: IssueCluster[]; total: number }> {
  const params = new URLSearchParams();
  if (filters?.priority_level && filters.priority_level !== "All") {
    params.set("priority_level", filters.priority_level);
  }
  if (filters?.category && filters.category !== "All") {
    params.set("category", filters.category);
  }
  if (filters?.ward && filters.ward !== "All") {
    params.set("ward", filters.ward);
  }
  if (filters?.status && filters.status !== "All") {
    params.set("status", filters.status);
  }
  if (filters?.search && filters.search.trim()) {
    params.set("search", filters.search.trim());
  }

  const queryStr = params.toString() ? `?${params.toString()}` : "";
  try {
    return await request<{ items: IssueCluster[]; total: number }>(`/api/clusters${queryStr}`);
  } catch {
    let items = [...DEMO_CLUSTERS];
    if (filters?.priority_level && filters.priority_level !== "All") {
      items = items.filter((item) => item.priority_level === filters.priority_level);
    }
    if (filters?.category && filters.category !== "All") {
      items = items.filter((item) => item.category === filters.category);
    }
    if (filters?.search?.trim()) {
      const search = filters.search.toLowerCase();
      items = items.filter((item) => `${item.title} ${item.description} ${item.locality}`.toLowerCase().includes(search));
    }
    return { items, total: items.length };
  }
}

export async function fetchClusterDetails(clusterId: string): Promise<ClusterDetailResponse> {
  try {
    return await request<ClusterDetailResponse>(`/api/clusters/${encodeURIComponent(clusterId)}`);
  } catch {
    return demoClusterDetails(clusterId);
  }
}

export async function updateCluster(
  clusterId: string,
  update: { status?: IssueStatus; assigned_department?: string; notes?: string }
): Promise<{ message: string; cluster: IssueCluster }> {
  try {
    return await request<{ message: string; cluster: IssueCluster }>(`/api/clusters/${encodeURIComponent(clusterId)}`, {
      method: "PATCH",
      body: JSON.stringify(update),
    });
  } catch {
    return { message: "Updated in static demo mode", cluster: demoUpdateCluster(clusterId, update) };
  }
}

export interface IngestSingleComplaintPayload {
  original_text: string;
  locality: string;
  source?: ComplaintSource;
  source_reference?: string;
  original_language?: string;
  contact?: string;
  district?: string;
  consent_obtained?: boolean;
}

export async function submitComplaint(
  payload: IngestSingleComplaintPayload
): Promise<{ complaint: ComplaintRecord; processed: ProcessedComplaint }> {
  try {
    return await request<{ complaint: ComplaintRecord; processed: ProcessedComplaint }>("/api/complaints", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch {
    return demoSubmitComplaint(payload);
  }
}

export async function submitBatch(
  connectorType: string,
  payload: any
): Promise<{ accepted: number; rejected: number; total: number; errors: string[] }> {
  try {
    return await request<{ accepted: number; rejected: number; total: number; errors: string[] }>("/api/ingest", {
      method: "POST",
      body: JSON.stringify({ connector_type: connectorType, payload }),
    });
  } catch {
    const total = Array.isArray(payload) ? payload.length : 1;
    return { accepted: total, rejected: 0, total, errors: [] };
  }
}

export async function reclusterPipeline(
  weights?: ScoringWeights
): Promise<{ message: string; clusters_count: number; clusters: IssueCluster[] }> {
  try {
    return await request<{ message: string; clusters_count: number; clusters: IssueCluster[] }>("/api/pipeline/recluster", {
      method: "POST",
      body: weights ? JSON.stringify(weights) : undefined,
    });
  } catch {
    return {
      message: "Rankings recalculated in demo dataset mode",
      clusters_count: DEMO_CLUSTERS.length,
      clusters: DEMO_CLUSTERS,
    };
  }
}

export async function fetchComplaints(params?: {
  page?: number;
  limit?: number;
  search?: string;
  ward?: string;
  category?: string;
  source?: string;
}): Promise<{ items: UnderlyingComplaintItem[]; total: number; page: number; limit: number; total_pages: number }> {
  const q = new URLSearchParams();
  if (params?.page) q.set("page", params.page.toString());
  if (params?.limit) q.set("limit", params.limit.toString());
  if (params?.search) q.set("search", params.search);
  if (params?.ward) q.set("ward", params.ward);
  if (params?.category) q.set("category", params.category);
  if (params?.source) q.set("source", params.source);

  const queryStr = q.toString() ? `?${q.toString()}` : "";
  return request<{ items: UnderlyingComplaintItem[]; total: number; page: number; limit: number; total_pages: number }>(
    `/api/complaints${queryStr}`
  );
}
