import React, { useState, useEffect, useCallback } from "react";
import { Header, ActiveTab } from "./components/Header";
import { MetricCards } from "./components/MetricCards";
import { WeightTuningPanel } from "./components/WeightTuningPanel";
import { ClusterList } from "./components/ClusterList";
import { IssueDetailModal } from "./components/IssueDetailModal";
import { GrievanceIntakeView } from "./components/GrievanceIntakeView";
import { PublicTransparencyView } from "./components/PublicTransparencyView";
import { ComplaintsExplorerView } from "./components/ComplaintsExplorerView";
import { BatchIngestView } from "./components/BatchIngestView";
import {
  AnalyticsData,
  IssueCluster,
  ScoringWeights,
} from "./types/civic";
import {
  checkHealth,
  ClusterFilterParams,
  fetchAnalytics,
  fetchClusters,
  reclusterPipeline,
} from "./services/api";

const DEFAULT_WEIGHTS: ScoringWeights = {
  weight_severity: 0.3,
  weight_people: 0.25,
  weight_urgency: 0.2,
  weight_infrastructure_gap: 0.15,
  weight_repeated_complaints: 0.1,
};

export default function App() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("policy");
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [clusters, setClusters] = useState<IssueCluster[]>([]);
  const [filters, setFilters] = useState<ClusterFilterParams>({
    priority_level: "All",
    category: "All",
    ward: "All",
    status: "All",
    search: "",
  });
  const [selectedCluster, setSelectedCluster] = useState<IssueCluster | null>(null);
  const [weights, setWeights] = useState<ScoringWeights>(DEFAULT_WEIGHTS);
  const [isBackendHealthy, setIsBackendHealthy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isRecalculating, setIsRecalculating] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [healthRes, analyticsRes, clustersRes] = await Promise.all([
        checkHealth().catch(() => ({ status: "offline", service: "none" })),
        fetchAnalytics().catch(() => null),
        fetchClusters(filters).catch(() => ({ items: [], total: 0 })),
      ]);

      setIsBackendHealthy(healthRes.status === "healthy");
      if (analyticsRes) setAnalytics(analyticsRes);
      if (clustersRes) setClusters(clustersRes.items);
    } catch (err) {
      console.error("Failed to load initial civic data:", err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [filters]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadData();
  };

  const handleApplyWeights = async (newWeights: ScoringWeights) => {
    setIsRecalculating(true);
    try {
      const res = await reclusterPipeline(newWeights);
      setWeights(newWeights);
      setClusters(res.clusters);
      const updatedAnalytics = await fetchAnalytics();
      setAnalytics(updatedAnalytics);
    } catch (err) {
      console.error("Weight recalculation failed:", err);
      alert("Recalculation failed. Please check backend connection.");
    } finally {
      setIsRecalculating(false);
    }
  };

  const handleResetWeights = async () => {
    await handleApplyWeights(DEFAULT_WEIGHTS);
  };

  const handleClusterUpdated = (updated: IssueCluster) => {
    setClusters((prev) =>
      prev.map((c) => (c.cluster_id === updated.cluster_id ? updated : c))
    );
    fetchAnalytics().then(setAnalytics).catch(console.error);
  };

  return (
    <div className="min-h-screen bg-slate-100/70 text-slate-900 flex flex-col font-sans">
      {/* Universal Header with Navigation */}
      <Header
        activeTab={activeTab}
        onTabChange={setActiveTab}
        isBackendHealthy={isBackendHealthy}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === "policy" && (
          <div className="space-y-6">
            {/* Executive Metric Cards */}
            <MetricCards analytics={analytics} loading={loading} />

            {/* Weight Tuning Simulation Panel */}
            <WeightTuningPanel
              weights={weights}
              onApplyWeights={handleApplyWeights}
              onResetWeights={handleResetWeights}
              isRecalculating={isRecalculating}
            />

            {/* Prioritized Issues List */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h2 className="text-base font-bold text-slate-900">
                    Prioritized Civic Action Clusters
                  </h2>
                  <p className="text-xs text-slate-500">
                    Grouped by similarity across 6 channels · Ranked by transparent multi-criteria impact formula
                  </p>
                </div>
                <span className="text-xs text-slate-500 font-medium">
                  {clusters.length} {clusters.length === 1 ? "issue" : "issues"} active
                </span>
              </div>

              <ClusterList
                clusters={clusters}
                loading={loading}
                filters={filters}
                onFilterChange={setFilters}
                onSelectCluster={setSelectedCluster}
                selectedClusterId={selectedCluster?.cluster_id}
              />
            </div>
          </div>
        )}

        {activeTab === "public" && (
          <PublicTransparencyView
            clusters={clusters}
            onSelectCluster={(cluster) => {
              setSelectedCluster(cluster);
            }}
          />
        )}

        {activeTab === "intake" && (
          <GrievanceIntakeView
            onComplaintSubmitted={async () => {
              await loadData();
            }}
          />
        )}

        {activeTab === "explorer" && <ComplaintsExplorerView />}

        {activeTab === "batch" && (
          <BatchIngestView
            onBatchProcessed={async () => {
              await loadData();
              setActiveTab("policy");
            }}
          />
        )}
      </main>

      {/* Full Explainability & Workflow Modal */}
      {selectedCluster && (
        <IssueDetailModal
          clusterId={selectedCluster.cluster_id}
          onClose={() => setSelectedCluster(null)}
          onClusterUpdated={handleClusterUpdated}
        />
      )}

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 mt-12 py-6 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-700">CivicPriority AI</span>
            <span>·</span>
            <span>Open Civic Decision Support System</span>
            <span>·</span>
            <span className="text-slate-400">Ward 4, 7, 9, 12, 15 Pilot Coverage</span>
          </div>

          <div className="text-slate-400 text-center sm:text-right">
            DEMONSTRATION SYSTEM: Uses Kaggle benchmark data for simulation. Not connected to live municipal dispatch.
          </div>
        </div>
      </footer>
    </div>
  );
}
