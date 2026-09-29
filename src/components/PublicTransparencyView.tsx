import React, { useState } from "react";
import {
  Search,
  CheckCircle,
  HelpCircle,
  Shield,
  Eye,
  Building,
  TrendingUp,
  Clock,
  Layers,
} from "lucide-react";
import { IssueCluster, PriorityLevel } from "../types/civic";

interface PublicTransparencyViewProps {
  clusters: IssueCluster[];
  onSelectCluster: (cluster: IssueCluster) => void;
}

export const PublicTransparencyView: React.FC<PublicTransparencyViewProps> = ({
  clusters,
  onSelectCluster,
}) => {
  const [trackingId, setTrackingId] = useState("");
  const [matchedCluster, setMatchedCluster] = useState<IssueCluster | null>(null);
  const [searchAttempted, setSearchAttempted] = useState(false);

  const handleTrack = (e: React.FormEvent) => {
    e.preventDefault();
    const query = trackingId.trim().toUpperCase();
    if (!query) return;

    setSearchAttempted(true);
    // Find cluster where query matches cluster_id or any complaint_id
    const found = clusters.find(
      (c) =>
        c.cluster_id.toUpperCase().includes(query) ||
        c.complaint_ids.some((cid) => cid.toUpperCase().includes(query))
    );
    setMatchedCluster(found || null);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Banner / Civic Commitment */}
      <div className="bg-gradient-to-r from-blue-900 via-slate-900 to-indigo-950 text-white p-6 sm:p-8 rounded-xl shadow-xs">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-300 mb-2">
          <Eye className="w-4 h-4 text-emerald-400" />
          <span>Open Governance & Citizen Accountability</span>
        </div>
        <h2 className="text-2xl font-bold tracking-tight">Public Grievance Prioritization Portal</h2>
        <p className="mt-2 text-sm text-slate-300 max-w-2xl leading-relaxed">
          The municipality allocates public repair crews and budget using an open, transparent multi-criteria formula.
          Decisions are never made in secret or skewed by vocal special interests. Every grievance is analyzed on merit,
          urgency, public health risk, and historical infrastructure deficit.
        </p>
      </div>

      {/* Citizen Submission Tracking Tool */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase tracking-wide">
          <Search className="w-4 h-4 text-blue-600" />
          <span>Track Your Grievance Status & Public Impact</span>
        </div>
        <p className="text-xs text-slate-500">
          Enter your Complaint ID (e.g., <code className="font-mono bg-slate-100 px-1 py-0.5 rounded">CMP-SYN-001</code>)
          or Cluster ID to verify how your voice contributed to municipal planning.
        </p>

        <form onSubmit={handleTrack} className="flex gap-2">
          <input
            type="text"
            placeholder="Enter Complaint ID (e.g. CMP-SYN-001, CMP-SYN-007)..."
            value={trackingId}
            onChange={(e) => setTrackingId(e.target.value)}
            className="flex-1 text-xs px-3.5 py-2 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-xs transition cursor-pointer"
          >
            Track Grievance
          </button>
        </form>

        {searchAttempted && matchedCluster && (
          <div className="p-4 bg-emerald-50/70 border border-emerald-200 rounded-lg text-xs space-y-2 animate-in fade-in-50">
            <div className="flex items-center justify-between">
              <span className="font-bold text-emerald-900 flex items-center gap-1.5">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                <span>Found! Consolidated into Municipal Action Cluster:</span>
              </span>
              <span className="font-mono text-emerald-800 font-bold bg-white px-2 py-0.5 rounded border border-emerald-200">
                {matchedCluster.cluster_id}
              </span>
            </div>
            <p className="font-semibold text-slate-800 text-sm">{matchedCluster.title}</p>
            <p className="text-slate-600">{matchedCluster.explanation}</p>
            <div className="pt-2 flex items-center justify-between border-t border-emerald-200/60">
              <span className="text-emerald-800 font-medium">
                Current Status: <span className="capitalize">{matchedCluster.status.replace("_", " ")}</span>
              </span>
              <button
                onClick={() => onSelectCluster(matchedCluster)}
                className="text-blue-600 font-semibold hover:underline cursor-pointer"
              >
                View Full Score Breakdown & Action Plan &rarr;
              </button>
            </div>
          </div>
        )}

        {searchAttempted && !matchedCluster && (
          <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
            No active cluster found for tracking ID &ldquo;{trackingId}&rdquo;. Try <button type="button" onClick={() => { setTrackingId("CMP-SYN-001"); }} className="underline font-mono">CMP-SYN-001</button> (Ward 12 school).
          </div>
        )}
      </div>

      {/* The 5 Pillars of Prioritization Explained */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-blue-600" />
          <span>How Municipal Priorities Are Objectively Scored</span>
        </h3>
        <p className="text-xs text-slate-500">
          To ensure fairness across all neighborhoods regardless of household income or smartphone access, the system
          balances five distinct criteria:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 pt-2 text-xs">
          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
            <span className="font-bold text-slate-900 block">1. Severity (30%)</span>
            <p className="text-slate-600 leading-relaxed text-[11px]">
              Direct physical risk, contamination of drinking water, structural collapse, or school shutdown.
            </p>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
            <span className="font-bold text-slate-900 block">2. Population (25%)</span>
            <p className="text-slate-600 leading-relaxed text-[11px]">
              Estimated affected citizens using a logarithmic scale to protect small communities from being drowned out.
            </p>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
            <span className="font-bold text-slate-900 block">3. Urgency (20%)</span>
            <p className="text-slate-600 leading-relaxed text-[11px]">
              Time-criticality—rapid response prevents minor water leaks from triggering road cave-ins.
            </p>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
            <span className="font-bold text-slate-900 block">4. Infra Deficit (15%)</span>
            <p className="text-slate-600 leading-relaxed text-[11px]">
              Historical lack of municipal investment in underserved wards is compensated to promote spatial equity.
            </p>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
            <span className="font-bold text-slate-900 block">5. Multi-Source (10%)</span>
            <p className="text-slate-600 leading-relaxed text-[11px]">
              Validation across town halls, letters, and mobile reports confirms community consensus.
            </p>
          </div>
        </div>
      </div>

      {/* Top Public Priorities Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">Current Top Public Priorities</h3>
            <p className="text-xs text-slate-500 mt-0.5">Ranked in real-time according to verified civic impact</p>
          </div>
          <span className="text-xs text-slate-400 font-mono">Showing Top {Math.min(10, clusters.length)}</span>
        </div>

        <div className="divide-y divide-slate-100 text-xs">
          {clusters.slice(0, 10).map((cl, i) => (
            <div
              key={cl.cluster_id}
              onClick={() => onSelectCluster(cl)}
              className="p-4 hover:bg-slate-50 transition cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-3"
            >
              <div className="space-y-1 flex-1">
                <div className="flex items-center gap-2 text-slate-400">
                  <span className="font-bold text-slate-800">#{i + 1}</span>
                  <span>·</span>
                  <span className="font-semibold text-slate-700">{cl.locality}</span>
                  <span>·</span>
                  <span className="text-slate-500">{cl.category}</span>
                  <span>·</span>
                  <span>~{cl.estimated_people_affected.toLocaleString()} affected</span>
                </div>
                <h4 className="font-bold text-slate-900 text-sm">{cl.title}</h4>
                <p className="text-slate-500 line-clamp-1">{cl.recommendation}</p>
              </div>

              <div className="flex items-center gap-4 shrink-0 sm:text-right">
                <div>
                  <span className="text-xs font-semibold text-blue-600 block">
                    {cl.priority_level} Priority
                  </span>
                  <span className="font-bold text-slate-800 font-mono text-base">
                    {cl.priority_score.toFixed(1)} / 100
                  </span>
                </div>
                <span className="text-xs px-2.5 py-1 rounded bg-slate-100 font-medium capitalize text-slate-700">
                  {cl.status.replace("_", " ")}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
