import React from "react";
import { AlertCircle, CheckCircle2, Clock, Inbox, TrendingUp } from "lucide-react";
import { AnalyticsData } from "../types/civic";

interface MetricCardsProps {
  analytics: AnalyticsData | null;
  loading: boolean;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ analytics, loading }) => {
  if (loading || !analytics) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white p-5 rounded-lg border border-slate-200 animate-pulse h-28">
            <div className="h-4 bg-slate-100 rounded w-1/2 mb-3"></div>
            <div className="h-8 bg-slate-200 rounded w-1/3"></div>
          </div>
        ))}
      </div>
    );
  }

  const criticalCount = analytics.critical_issues_count || 0;
  const highCount = analytics.high_issues_count || 0;
  const underReviewCount =
    (analytics.by_priority_level && analytics.by_priority_level["High"]) || 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Total Complaints */}
      <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs transition hover:border-slate-300">
        <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider">
          <span>Total Ingested Grievances</span>
          <Inbox className="w-4 h-4 text-blue-600" />
        </div>
        <div className="mt-2.5 flex items-baseline gap-2">
          <span className="text-3xl font-bold tracking-tight text-slate-900">{analytics.total_complaints}</span>
          <span className="text-xs text-slate-500">across 6 channels</span>
        </div>
        <div className="mt-2 text-xs text-slate-500 flex items-center gap-1.5">
          <span className="text-emerald-700 font-medium">100% PII Redacted</span>
          <span>·</span>
          <span>3 Languages</span>
        </div>
      </div>

      {/* 2. Consolidated Issues */}
      <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs transition hover:border-slate-300">
        <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider">
          <span>Clustered Policy Issues</span>
          <TrendingUp className="w-4 h-4 text-indigo-600" />
        </div>
        <div className="mt-2.5 flex items-baseline gap-2">
          <span className="text-3xl font-bold tracking-tight text-slate-900">{analytics.total_clusters}</span>
          <span className="text-xs text-slate-500">synthesized clusters</span>
        </div>
        <div className="mt-2 text-xs text-slate-500 flex items-center gap-1.5">
          <span>TF-IDF + Ward Match</span>
          <span>·</span>
          <span>No duplicate effort</span>
        </div>
      </div>

      {/* 3. Critical Emergencies */}
      <div className="bg-white p-5 rounded-lg border border-rose-200/80 bg-rose-50/20 shadow-xs transition hover:border-rose-300">
        <div className="flex items-center justify-between text-rose-800 text-xs font-semibold uppercase tracking-wider">
          <span>Critical Emergencies</span>
          <AlertCircle className="w-4 h-4 text-rose-600" />
        </div>
        <div className="mt-2.5 flex items-baseline gap-2">
          <span className="text-3xl font-bold tracking-tight text-rose-700">{criticalCount}</span>
          <span className="text-xs text-rose-600/90 font-medium">Score &ge; 80 / 100</span>
        </div>
        <div className="mt-2 text-xs text-rose-700/80 flex items-center gap-1.5 font-medium">
          <span>Immediate dispatch recommended</span>
        </div>
      </div>

      {/* 4. High & Under Review */}
      <div className="bg-white p-5 rounded-lg border border-amber-200/80 bg-amber-50/20 shadow-xs transition hover:border-amber-300">
        <div className="flex items-center justify-between text-amber-800 text-xs font-semibold uppercase tracking-wider">
          <span>High Priority & Review</span>
          <Clock className="w-4 h-4 text-amber-600" />
        </div>
        <div className="mt-2.5 flex items-baseline gap-2">
          <span className="text-3xl font-bold tracking-tight text-amber-800">{highCount}</span>
          <span className="text-xs text-amber-700/90 font-medium">Score 65–79 / 100</span>
        </div>
        <div className="mt-2 text-xs text-amber-700/80 flex items-center gap-1.5">
          <span>Fairness safeguards active</span>
        </div>
      </div>
    </div>
  );
};
