import React from "react";
import {
  AlertTriangle,
  ChevronRight,
  Filter,
  Search,
  Users,
  Building2,
  ShieldAlert,
} from "lucide-react";
import {
  ComplaintCategory,
  IssueCluster,
  IssueStatus,
  PriorityLevel,
} from "../types/civic";
import { ClusterFilterParams } from "../services/api";

interface ClusterListProps {
  clusters: IssueCluster[];
  loading: boolean;
  filters: ClusterFilterParams;
  onFilterChange: (filters: ClusterFilterParams) => void;
  onSelectCluster: (cluster: IssueCluster) => void;
  selectedClusterId?: string;
}

const CATEGORIES: ComplaintCategory[] = [
  "Education",
  "Water and sanitation",
  "Roads and transport",
  "Healthcare",
  "Electricity",
  "Waste management",
  "Public safety",
  "Housing",
  "Social welfare",
  "Environment",
  "Other",
];

const WARDS = ["Ward 4", "Ward 7", "Ward 9", "Ward 12", "Ward 15"];

export const ClusterList: React.FC<ClusterListProps> = ({
  clusters,
  loading,
  filters,
  onFilterChange,
  onSelectCluster,
  selectedClusterId,
}) => {
  const getPriorityStyle = (level: PriorityLevel) => {
    switch (level) {
      case "Critical":
        return {
          barBg: "bg-rose-600",
          text: "text-rose-700 font-bold",
          border: "border-l-rose-500",
        };
      case "High":
        return {
          barBg: "bg-amber-500",
          text: "text-amber-700 font-bold",
          border: "border-l-amber-500",
        };
      case "Medium":
        return {
          barBg: "bg-blue-600",
          text: "text-blue-700 font-semibold",
          border: "border-l-blue-500",
        };
      case "Low":
        return {
          barBg: "bg-slate-400",
          text: "text-slate-600 font-medium",
          border: "border-l-slate-400",
        };
    }
  };

  const getStatusLabel = (status: IssueStatus) => {
    switch (status) {
      case "open":
        return "Open";
      case "under_review":
        return "Under Review";
      case "in_progress":
        return "In Progress";
      case "resolved":
        return "Resolved";
      default:
        return status;
    }
  };

  return (
    <div className="space-y-4">
      {/* Filtering Toolbar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs space-y-3">
        <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
          {/* Search bar */}
          <div className="relative w-full md:w-96">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by school, road, ward, issue..."
              value={filters.search || ""}
              onChange={(e) => onFilterChange({ ...filters, search: e.target.value })}
              className="w-full pl-9 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 border border-slate-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Segmented Priority Filter Controls */}
          <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-lg text-xs self-start md:self-auto overflow-x-auto">
            <button
              onClick={() => onFilterChange({ ...filters, priority_level: "All" })}
              className={`px-3 py-1 font-medium rounded transition cursor-pointer ${
                !filters.priority_level || filters.priority_level === "All"
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              All Priorities
            </button>
            <button
              onClick={() => onFilterChange({ ...filters, priority_level: "Critical" })}
              className={`px-3 py-1 font-medium rounded transition cursor-pointer ${
                filters.priority_level === "Critical"
                  ? "bg-rose-600 text-white shadow-xs"
                  : "text-rose-700 hover:bg-rose-50"
              }`}
            >
              Critical
            </button>
            <button
              onClick={() => onFilterChange({ ...filters, priority_level: "High" })}
              className={`px-3 py-1 font-medium rounded transition cursor-pointer ${
                filters.priority_level === "High"
                  ? "bg-amber-600 text-white shadow-xs"
                  : "text-amber-800 hover:bg-amber-50"
              }`}
            >
              High
            </button>
            <button
              onClick={() => onFilterChange({ ...filters, priority_level: "Medium" })}
              className={`px-3 py-1 font-medium rounded transition cursor-pointer ${
                filters.priority_level === "Medium"
                  ? "bg-blue-600 text-white shadow-xs"
                  : "text-blue-700 hover:bg-blue-50"
              }`}
            >
              Medium
            </button>
          </div>
        </div>

        {/* Dropdowns for Ward, Category, and Workflow Status */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-slate-100 text-xs">
          {/* Ward Selector */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 mb-1">Ward / Locality</label>
            <select
              value={filters.ward || "All"}
              onChange={(e) => onFilterChange({ ...filters, ward: e.target.value })}
              className="w-full py-1.5 px-2.5 border border-slate-300 rounded bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="All">All Municipal Wards</option>
              {WARDS.map((w) => (
                <option key={w} value={w}>
                  {w}
                </option>
              ))}
            </select>
          </div>

          {/* Category Selector */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 mb-1">Issue Category</label>
            <select
              value={filters.category || "All"}
              onChange={(e) => onFilterChange({ ...filters, category: e.target.value as any })}
              className="w-full py-1.5 px-2.5 border border-slate-300 rounded bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="All">All Categories</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Status Selector */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 mb-1">Administrative Status</label>
            <select
              value={filters.status || "All"}
              onChange={(e) => onFilterChange({ ...filters, status: e.target.value as any })}
              className="w-full py-1.5 px-2.5 border border-slate-300 rounded bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="All">All Statuses</option>
              <option value="open">Open</option>
              <option value="under_review">Under Review</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>
        </div>
      </div>

      {/* Cluster Items List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white p-5 rounded-lg border border-slate-200 animate-pulse h-36">
              <div className="h-5 bg-slate-200 rounded w-1/3 mb-2"></div>
              <div className="h-4 bg-slate-100 rounded w-2/3 mb-3"></div>
              <div className="h-4 bg-slate-100 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : clusters.length === 0 ? (
        <div className="bg-white p-12 text-center rounded-lg border border-slate-200">
          <Filter className="w-8 h-8 text-slate-400 mx-auto mb-2" />
          <h3 className="text-sm font-semibold text-slate-800">No matching civic issues</h3>
          <p className="text-xs text-slate-500 mt-1">Try resetting the ward, category, or search filters.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {clusters.map((cluster, idx) => {
            const priority = getPriorityStyle(cluster.priority_level);
            const isSelected = selectedClusterId === cluster.cluster_id;

            return (
              <div
                key={cluster.cluster_id}
                onClick={() => onSelectCluster(cluster)}
                className={`bg-white rounded-lg border transition-all cursor-pointer overflow-hidden border-l-4 ${
                  priority.border
                } ${
                  isSelected
                    ? "ring-2 ring-blue-500 border-slate-300 shadow-md"
                    : "border-slate-200 hover:border-slate-300 hover:shadow-xs"
                }`}
              >
                <div className="p-5">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    {/* Title and metadata */}
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2 flex-wrap text-xs text-slate-500">
                        <span className="font-mono text-slate-400">#{idx + 1}</span>
                        <span>·</span>
                        <span className="font-semibold text-slate-800">{cluster.locality}</span>
                        <span>·</span>
                        <span className="text-slate-600 font-medium">{cluster.category}</span>
                        <span>·</span>
                        <span className="text-slate-500">Status: {getStatusLabel(cluster.status)}</span>
                      </div>

                      <h3 className="text-base font-bold text-slate-900 group-hover:text-blue-600 transition">
                        {cluster.title}
                      </h3>

                      <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                        {cluster.description}
                      </p>
                    </div>

                    {/* Priority score card */}
                    <div className="sm:text-right shrink-0">
                      <div className="flex sm:flex-col items-center sm:items-end justify-between gap-2">
                        <span className={`text-xs uppercase tracking-wider ${priority.text}`}>
                          {cluster.priority_level} Priority
                        </span>
                        <div className="flex items-baseline gap-1">
                          <span className="text-2xl font-bold tracking-tight text-slate-900">
                            {cluster.priority_score.toFixed(1)}
                          </span>
                          <span className="text-xs text-slate-400 font-mono">/100</span>
                        </div>
                      </div>

                      {/* Mini Score Bar */}
                      <div className="w-24 h-1.5 bg-slate-100 rounded-full mt-1.5 overflow-hidden ml-auto">
                        <div
                          className={`h-full rounded-full ${priority.barBg}`}
                          style={{ width: `${Math.min(100, cluster.priority_score)}%` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Fairness alert banner if triggered */}
                  {cluster.fairness_warnings && cluster.fairness_warnings.length > 0 && (
                    <div className="mt-3.5 p-2.5 bg-amber-50 border border-amber-200/80 rounded text-xs text-amber-900 flex items-start gap-2">
                      <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold text-amber-950">Fairness Safeguard Active: </span>
                        <span>{cluster.fairness_warnings[0]}</span>
                      </div>
                    </div>
                  )}

                  {/* Footer metadata line - ZERO-PILL DISCIPLINE */}
                  <div className="mt-3.5 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium text-slate-700">
                        {cluster.complaint_count} {cluster.complaint_count === 1 ? "report" : "consolidated reports"}
                      </span>
                      <span>·</span>
                      <span>{cluster.unique_sources.length} sources ({cluster.unique_sources.join(", ")})</span>
                      <span>·</span>
                      <span className="flex items-center gap-1">
                        <Users className="w-3 h-3 text-slate-400" />
                        <span>~{cluster.estimated_people_affected.toLocaleString()} affected</span>
                      </span>
                      {cluster.vulnerable_groups.length > 0 && (
                        <>
                          <span>·</span>
                          <span className="text-indigo-700 font-medium">
                            Vulnerable: {cluster.vulnerable_groups.join(", ")}
                          </span>
                        </>
                      )}
                    </div>

                    <div className="flex items-center gap-1 text-blue-600 font-medium text-xs ml-auto">
                      <span>View Full Breakdown</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
