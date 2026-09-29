import React, { useState, useEffect } from "react";
import { Search, Database, Calendar, ShieldCheck, Filter, ChevronLeft, ChevronRight } from "lucide-react";
import { UnderlyingComplaintItem } from "../types/civic";
import { fetchComplaints } from "../services/api";

export const ComplaintsExplorerView: React.FC = () => {
  const [complaints, setComplaints] = useState<UnderlyingComplaintItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  // Filters
  const [search, setSearch] = useState("");
  const [selectedWard, setSelectedWard] = useState("All");
  const [selectedSource, setSelectedSource] = useState("All");

  const loadData = async (targetPage = page) => {
    setLoading(true);
    try {
      const res = await fetchComplaints({
        page: targetPage,
        limit: 15,
        search: search.trim() || undefined,
        ward: selectedWard !== "All" ? selectedWard : undefined,
        source: selectedSource !== "All" ? selectedSource : undefined,
      });
      setComplaints(res.items);
      setTotalPages(res.total_pages);
      setTotal(res.total);
      setPage(res.page);
    } catch (err) {
      console.error("Failed to load complaints:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(1);
  }, [selectedWard, selectedSource]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadData(1);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Citizen Grievance Records Explorer</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Browse raw complaints, automated English translations, and PII-redacted citizen submissions
            </p>
          </div>
          <span className="text-xs font-mono bg-slate-100 text-slate-600 px-3 py-1 rounded border border-slate-200">
            Total Records: {total}
          </span>
        </div>

        {/* Toolbar */}
        <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
          <div className="sm:col-span-2 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search keyword (e.g. पानी, road, transformer, school)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <select
              value={selectedWard}
              onChange={(e) => setSelectedWard(e.target.value)}
              className="w-full py-2 px-3 border border-slate-300 rounded bg-white text-slate-800"
            >
              <option value="All">All Wards</option>
              <option value="Ward 12">Ward 12</option>
              <option value="Ward 7">Ward 7</option>
              <option value="Ward 4">Ward 4</option>
              <option value="Ward 9">Ward 9</option>
              <option value="Ward 15">Ward 15</option>
            </select>
          </div>

          <div>
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="w-full py-2 px-3 border border-slate-300 rounded bg-white text-slate-800"
            >
              <option value="All">All Channels</option>
              <option value="public_meeting">Public Meeting</option>
              <option value="direct_web">Direct Web</option>
              <option value="messaging">WhatsApp / SMS</option>
              <option value="letter_pdf">Citizen Letter</option>
              <option value="social_media">Social Media</option>
              <option value="grievance_portal">Central Portal</option>
            </select>
          </div>
        </form>
      </div>

      {/* List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="bg-white p-4 rounded-lg border border-slate-200 animate-pulse h-24"></div>
          ))}
        </div>
      ) : complaints.length === 0 ? (
        <div className="bg-white p-12 text-center rounded-lg border border-slate-200 text-xs text-slate-500">
          No records match your query.
        </div>
      ) : (
        <div className="space-y-2.5">
          {complaints.map((item) => {
            const raw = item.raw;
            const proc = item.processed;

            return (
              <div
                key={raw.id}
                className="bg-white p-4 rounded-lg border border-slate-200 hover:border-slate-300 transition text-xs space-y-2"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 text-slate-500">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-slate-800">{raw.id}</span>
                    <span>·</span>
                    <span className="font-semibold text-slate-700">{raw.locality}</span>
                    <span>·</span>
                    <span className="capitalize text-slate-600 font-medium">
                      {raw.source.replace("_", " ")}
                    </span>
                    <span>·</span>
                    <span className="uppercase text-[10px] font-mono text-slate-400">
                      Lang: {raw.original_language}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-slate-400 font-mono text-[11px]">
                    <Calendar className="w-3 h-3" />
                    <span>{new Date(raw.submitted_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <p className="text-slate-900 font-medium leading-relaxed">{raw.original_text}</p>

                {proc && proc.language !== "en" && (
                  <p className="text-slate-600 bg-slate-50 p-2 rounded border border-slate-100 italic">
                    <span className="font-semibold text-slate-700 not-italic">English Translation: </span>
                    {proc.translated_text}
                  </p>
                )}

                <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500">
                  <div className="flex items-center gap-2">
                    <span className="text-emerald-700 font-medium flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3 text-emerald-600" />
                      <span>Contact Hash: {raw.citizen_contact_hash ? raw.citizen_contact_hash.slice(0, 12) + "..." : "None"}</span>
                    </span>
                    {proc && (
                      <>
                        <span>·</span>
                        <span className="font-semibold text-slate-700">{proc.category}</span>
                        <span>·</span>
                        <span>Severity: {proc.severity_score.toFixed(0)}/100</span>
                        <span>·</span>
                        <span>Urgency: {proc.urgency_score.toFixed(0)}/100</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination Bar */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between bg-white px-4 py-3 rounded-lg border border-slate-200 text-xs">
          <span className="text-slate-500">
            Page {page} of {totalPages} ({total} complaints total)
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => loadData(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded border border-slate-300 text-slate-700 disabled:opacity-40 cursor-pointer flex items-center gap-1 hover:bg-slate-50"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>
            <button
              onClick={() => loadData(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded border border-slate-300 text-slate-700 disabled:opacity-40 cursor-pointer flex items-center gap-1 hover:bg-slate-50"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
