import React, { useState, useEffect } from "react";
import {
  X,
  AlertTriangle,
  Building,
  CheckCircle2,
  Clock,
  FileText,
  Shield,
  Users,
  ChevronDown,
  Info,
  Calendar,
  Lock,
} from "lucide-react";
import {
  ClusterDetailResponse,
  IssueCluster,
  IssueStatus,
  UnderlyingComplaintItem,
} from "../types/civic";
import { fetchClusterDetails, updateCluster } from "../services/api";

interface IssueDetailModalProps {
  clusterId: string | null;
  onClose: () => void;
  onClusterUpdated: (updatedCluster: IssueCluster) => void;
}

export const IssueDetailModal: React.FC<IssueDetailModalProps> = ({
  clusterId,
  onClose,
  onClusterUpdated,
}) => {
  const [details, setDetails] = useState<ClusterDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Workflow update form state
  const [selectedStatus, setSelectedStatus] = useState<IssueStatus>("open");
  const [selectedDept, setSelectedDept] = useState<string>("");
  const [adminNotes, setAdminNotes] = useState<string>("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState(false);

  useEffect(() => {
    if (!clusterId) return;

    let mounted = true;
    setLoading(true);
    setError(null);

    fetchClusterDetails(clusterId)
      .then((data) => {
        if (!mounted) return;
        setDetails(data);
        setSelectedStatus(data.cluster.status);
        setSelectedDept(data.cluster.assigned_department || "");
        setAdminNotes(data.cluster.metadata?.admin_notes || "");
      })
      .catch((err) => {
        if (!mounted) return;
        setError(err.message || "Failed to load cluster details");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [clusterId]);

  if (!clusterId) return null;

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clusterId) return;

    setIsUpdating(true);
    setUpdateSuccess(false);

    try {
      const res = await updateCluster(clusterId, {
        status: selectedStatus,
        assigned_department: selectedDept,
        notes: adminNotes,
      });
      setDetails((prev) => (prev ? { ...prev, cluster: res.cluster } : null));
      onClusterUpdated(res.cluster);
      setUpdateSuccess(true);
      setTimeout(() => setUpdateSuccess(false), 3000);
    } catch (err: any) {
      alert(`Update failed: ${err.message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  const departments = [
    "Department of School Education",
    "Public Works Department (Roads)",
    "Municipal Water Supply & Drainage Board",
    "Primary Health & Family Welfare Office",
    "State Electricity Distribution Company",
    "Municipal Solid Waste Operations",
    "City Police & Traffic Division",
    "Municipal Rapid Response Taskforce",
  ];

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-3 sm:p-6 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-4xl w-full max-h-[92vh] flex flex-col overflow-hidden my-auto animate-in fade-in-50 zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-slate-900 text-white flex items-start justify-between gap-4 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
              <span>{details?.cluster.cluster_id || clusterId}</span>
              <span>·</span>
              <span>{details?.cluster.locality}</span>
              <span>·</span>
              <span className="text-blue-400 font-semibold">{details?.cluster.category}</span>
            </div>
            <h2 className="text-lg font-bold text-white mt-1">
              {details?.cluster.title || "Loading Issue Details..."}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {loading ? (
            <div className="space-y-4 py-8">
              <div className="h-6 bg-slate-200 rounded w-1/3 animate-pulse"></div>
              <div className="h-24 bg-slate-100 rounded animate-pulse"></div>
              <div className="h-32 bg-slate-100 rounded animate-pulse"></div>
            </div>
          ) : error || !details ? (
            <div className="p-8 text-center text-rose-600">
              <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-rose-500" />
              <p className="font-semibold">{error || "Failed to load cluster."}</p>
            </div>
          ) : (
            <>
              {/* Fairness Alert if triggered */}
              {details.cluster.fairness_warnings && details.cluster.fairness_warnings.length > 0 && (
                <div className="p-3.5 bg-amber-50 border border-amber-300 rounded-lg text-xs text-amber-950 flex items-start gap-2.5">
                  <Shield className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-amber-900">Demographic & Frequency Bias Protection: </span>
                    <span>{details.cluster.fairness_warnings.join(" ")}</span>
                  </div>
                </div>
              )}

              {/* Policy Recommendation Callout */}
              <div className="p-4 bg-blue-50/70 border border-blue-200 rounded-lg">
                <div className="flex items-center gap-2 text-xs font-bold text-blue-900 uppercase tracking-wide">
                  <Building className="w-4 h-4 text-blue-600" />
                  <span>Actionable Policy Recommendation</span>
                </div>
                <p className="text-sm font-medium text-blue-950 mt-1.5 leading-relaxed">
                  {details.cluster.recommendation}
                </p>
                <div className="mt-2.5 pt-2 border-t border-blue-200/60 text-xs text-blue-800/80 flex flex-wrap items-center gap-2">
                  <span className="font-semibold">Assigned Dept:</span>
                  <span>{details.cluster.assigned_department || "Unassigned"}</span>
                  <span>·</span>
                  <span className="font-semibold">Workflow Status:</span>
                  <span className="capitalize">{details.cluster.status.replace("_", " ")}</span>
                </div>
              </div>

              {/* Transparent Mathematical Score Breakdown */}
              <div className="border border-slate-200 rounded-lg p-5 bg-slate-50/50">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">
                      Transparent Priority Score Breakdown
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Multi-criteria policy formula verified across 5 dimensions
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-2xl font-bold tracking-tight text-slate-900">
                      {details.cluster.priority_score.toFixed(1)}
                    </span>
                    <span className="text-xs text-slate-400 font-mono"> / 100</span>
                    <div className="text-[11px] font-bold text-blue-600 uppercase">
                      {details.cluster.priority_level} Priority
                    </div>
                  </div>
                </div>

                {/* Granular Points Contribution Bars */}
                <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 pt-2">
                  {/* Severity */}
                  <div className="bg-white p-3 rounded border border-slate-200">
                    <div className="text-[11px] font-medium text-slate-500">Severity (30%)</div>
                    <div className="text-base font-bold text-slate-800 mt-0.5">
                      +{details.score_breakdown.severity_contribution.toFixed(1)} pts
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono mt-1">
                      Raw: {details.score_breakdown.raw_severity.toFixed(0)}/100
                    </div>
                  </div>

                  {/* People Affected (Log) */}
                  <div className="bg-white p-3 rounded border border-slate-200">
                    <div className="text-[11px] font-medium text-slate-500">Impact (25%)</div>
                    <div className="text-base font-bold text-slate-800 mt-0.5">
                      +{details.score_breakdown.people_contribution.toFixed(1)} pts
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono mt-1">
                      ~{details.score_breakdown.raw_people_affected.toLocaleString()} people
                    </div>
                  </div>

                  {/* Urgency */}
                  <div className="bg-white p-3 rounded border border-slate-200">
                    <div className="text-[11px] font-medium text-slate-500">Urgency (20%)</div>
                    <div className="text-base font-bold text-slate-800 mt-0.5">
                      +{details.score_breakdown.urgency_contribution.toFixed(1)} pts
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono mt-1">
                      Raw: {details.score_breakdown.raw_urgency.toFixed(0)}/100
                    </div>
                  </div>

                  {/* Infrastructure Gap */}
                  <div className="bg-white p-3 rounded border border-slate-200">
                    <div className="text-[11px] font-medium text-slate-500">Infra Gap (15%)</div>
                    <div className="text-base font-bold text-slate-800 mt-0.5">
                      +{details.score_breakdown.infrastructure_contribution.toFixed(1)} pts
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono mt-1">
                      Deficit: {details.score_breakdown.raw_infrastructure_gap.toFixed(0)}/100
                    </div>
                  </div>

                  {/* Repeat Volume */}
                  <div className="bg-white p-3 rounded border border-slate-200">
                    <div className="text-[11px] font-medium text-slate-500">Volume (10%)</div>
                    <div className="text-base font-bold text-slate-800 mt-0.5">
                      +{details.score_breakdown.repeat_contribution.toFixed(1)} pts
                    </div>
                    <div className="text-[10px] text-slate-400 font-mono mt-1">
                      {details.score_breakdown.raw_complaint_count} reports
                    </div>
                  </div>
                </div>

                <div className="mt-3.5 pt-3 border-t border-slate-200/80 text-xs text-slate-600 flex items-start gap-2">
                  <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                  <p>{details.cluster.explanation}</p>
                </div>
              </div>

              {/* Administrative Workflow & Department Assignment */}
              <div className="border border-slate-200 rounded-lg p-5 bg-white">
                <h3 className="text-sm font-bold text-slate-900 mb-1">
                  Administrative Triage & Department Dispatch
                </h3>
                <p className="text-xs text-slate-500 mb-4">
                  Update operational status, assign to the responsible authority, and log inspection notes.
                </p>

                <form onSubmit={handleUpdate} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Status Dropdown */}
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                        Workflow Status
                      </label>
                      <select
                        value={selectedStatus}
                        onChange={(e) => setSelectedStatus(e.target.value as IssueStatus)}
                        className="w-full text-xs py-2 px-3 border border-slate-300 rounded bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="open">Open (Awaiting Inspection)</option>
                        <option value="under_review">Under Review (Field Team Dispatched)</option>
                        <option value="in_progress">In Progress (Remediation Underway)</option>
                        <option value="resolved">Resolved (Inspection Verified)</option>
                      </select>
                    </div>

                    {/* Department Dropdown */}
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                        Responsible Department
                      </label>
                      <select
                        value={selectedDept}
                        onChange={(e) => setSelectedDept(e.target.value)}
                        className="w-full text-xs py-2 px-3 border border-slate-300 rounded bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="">-- Select Municipal Agency --</option>
                        {departments.map((dept) => (
                          <option key={dept} value={dept}>
                            {dept}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Notes Field */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                      Administrative Audit Notes & Action Log
                    </label>
                    <textarea
                      rows={2}
                      value={adminNotes}
                      onChange={(e) => setAdminNotes(e.target.value)}
                      placeholder="e.g., Water Tanker Unit #4 dispatched; site engineer contact details verified."
                      className="w-full text-xs p-2.5 border border-slate-300 rounded text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    />
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    {updateSuccess ? (
                      <span className="text-xs text-emerald-700 font-medium flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        <span>Workflow status and department updated successfully.</span>
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-400">
                        Changes persist directly to the municipal grievance database.
                      </span>
                    )}

                    <button
                      type="submit"
                      disabled={isUpdating}
                      className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded shadow-xs transition cursor-pointer disabled:opacity-50"
                    >
                      {isUpdating ? "Saving..." : "Save Status & Dispatch"}
                    </button>
                  </div>
                </form>
              </div>

              {/* Grouped Underlying Citizen Complaints */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-slate-900">
                    Consolidated Citizen Complaints ({details.underlying_complaints.length})
                  </h3>
                  <span className="text-xs text-slate-500">
                    Preserved from original reporting channels with automated PII masking
                  </span>
                </div>

                <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                  {details.underlying_complaints.map((item, i) => {
                    const raw = item.raw;
                    const proc = item.processed;

                    return (
                      <div
                        key={raw.id || i}
                        className="p-3.5 bg-white rounded-lg border border-slate-200 text-xs space-y-2 hover:border-slate-300 transition"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2 text-slate-500">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-slate-700">{raw.id}</span>
                            <span>·</span>
                            <span className="capitalize font-medium text-slate-800">
                              Channel: {raw.source.replace("_", " ")}
                            </span>
                            <span>·</span>
                            <span className="uppercase text-[10px] text-slate-400 font-mono">
                              Lang: {raw.original_language}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 text-slate-400 font-mono text-[11px]">
                            <Calendar className="w-3 h-3" />
                            <span>{new Date(raw.submitted_at).toLocaleDateString()}</span>
                          </div>
                        </div>

                        {/* Text */}
                        <div>
                          <p className="text-slate-800 font-medium leading-relaxed">
                            {raw.original_text}
                          </p>
                          {proc && proc.language !== "en" && (
                            <p className="mt-1 text-slate-500 italic bg-slate-50 p-2 rounded border border-slate-100">
                              <span className="font-semibold not-italic text-slate-600">English Translation: </span>
                              {proc.translated_text}
                            </p>
                          )}
                        </div>

                        {/* Privacy & Metadata badges */}
                        <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500">
                          <div className="flex items-center gap-2">
                            <span className="flex items-center gap-1 text-emerald-700 font-medium">
                              <Lock className="w-3 h-3 text-emerald-600" />
                              <span>PII Masked & Salted Hash</span>
                            </span>
                            {proc && (
                              <>
                                <span>·</span>
                                <span>Severity: {proc.severity_score.toFixed(0)}/100</span>
                                <span>·</span>
                                <span>Urgency: {proc.urgency_score.toFixed(0)}/100</span>
                              </>
                            )}
                          </div>

                          {raw.source_reference && (
                            <span className="font-mono text-slate-400 text-[10px]">
                              Ref: {raw.source_reference}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded hover:bg-slate-100 transition cursor-pointer"
          >
            Close Panel
          </button>
        </div>
      </div>
    </div>
  );
};
