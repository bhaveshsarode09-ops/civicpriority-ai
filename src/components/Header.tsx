import React from "react";
import { AlertTriangle, BarChart3, Database, FileSpreadsheet, Eye, PlusCircle, ShieldCheck } from "lucide-react";

export type ActiveTab = "policy" | "public" | "intake" | "explorer" | "batch";

interface HeaderProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  isBackendHealthy: boolean;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  isBackendHealthy,
  onRefresh,
  isRefreshing,
}) => {
  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white">
      {/* Top Disclaimer Banner */}
      <div className="bg-amber-950/80 border-b border-amber-800/60 px-4 py-1.5 text-xs text-amber-200/90 flex items-center justify-between">
        <div className="max-w-7xl mx-auto w-full flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span className="font-medium tracking-wide">
            DEMONSTRATION SYSTEM: Uses synthetic data. Not connected to live municipal dispatch.
          </span>
          <span className="hidden md:inline text-amber-300/60">·</span>
          <span className="hidden md:inline text-amber-300/80">
            Automated PII redaction and salted contact hashing active.
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-slate-400 font-mono text-[11px]">Engine v1.0</span>
        </div>
      </div>

      {/* Main Header Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center shadow-md shadow-blue-500/20 text-white font-bold text-lg">
              CP
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white">CivicPriority AI</h1>
                <span className="text-xs bg-blue-950 text-blue-300 border border-blue-800/80 px-2 py-0.5 rounded font-medium">
                  Municipal Triage
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                From Citizen Voice to Government Action — Multilingual grievance clustering & transparent policy prioritization
              </p>
            </div>
          </div>

          {/* Quick Actions & System Status */}
          <div className="flex items-center gap-3 self-end md:self-auto">
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="text-xs px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <Database className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-blue-400" : "text-slate-400"}`} />
              <span>{isRefreshing ? "Syncing..." : "Sync Database"}</span>
            </button>
            <div
              className={`text-xs px-2.5 py-1 rounded border flex items-center gap-1.5 ${
                isBackendHealthy
                  ? "bg-emerald-950/60 border-emerald-800/80 text-emerald-300"
                  : "bg-rose-950/60 border-rose-800/80 text-rose-300"
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
                  <span>{isBackendHealthy ? "Core Active" : "Demo Dataset Active"}</span>
            </div>
          </div>
        </div>

        {/* Primary Navigation Tabs */}
        <nav className="flex items-center gap-1 mt-6 border-b border-slate-800/80 overflow-x-auto pb-px">
          <button
            onClick={() => onTabChange("policy")}
            className={`px-3.5 py-2 text-sm font-medium transition-colors border-b-2 flex items-center gap-2 cursor-pointer shrink-0 ${
              activeTab === "policy"
                ? "border-blue-500 text-white bg-slate-800/40 rounded-t"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <span>Policy Dashboard</span>
          </button>

          <button
            onClick={() => onTabChange("public")}
            className={`px-3.5 py-2 text-sm font-medium transition-colors border-b-2 flex items-center gap-2 cursor-pointer shrink-0 ${
              activeTab === "public"
                ? "border-blue-500 text-white bg-slate-800/40 rounded-t"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            <Eye className="w-4 h-4 text-emerald-400" />
            <span>Public Transparency View</span>
          </button>

          <button
            onClick={() => onTabChange("intake")}
            className={`px-3.5 py-2 text-sm font-medium transition-colors border-b-2 flex items-center gap-2 cursor-pointer shrink-0 ${
              activeTab === "intake"
                ? "border-blue-500 text-white bg-slate-800/40 rounded-t"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            <PlusCircle className="w-4 h-4 text-indigo-400" />
            <span>Citizen Grievance Intake</span>
          </button>

          <button
            onClick={() => onTabChange("explorer")}
            className={`px-3.5 py-2 text-sm font-medium transition-colors border-b-2 flex items-center gap-2 cursor-pointer shrink-0 ${
              activeTab === "explorer"
                ? "border-blue-500 text-white bg-slate-800/40 rounded-t"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            <Database className="w-4 h-4 text-purple-400" />
            <span>Complaint Records Explorer</span>
          </button>

          <button
            onClick={() => onTabChange("batch")}
            className={`px-3.5 py-2 text-sm font-medium transition-colors border-b-2 flex items-center gap-2 cursor-pointer shrink-0 ${
              activeTab === "batch"
                ? "border-blue-500 text-white bg-slate-800/40 rounded-t"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
            }`}
          >
            <FileSpreadsheet className="w-4 h-4 text-amber-400" />
            <span>Batch & Channel Ingest</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
