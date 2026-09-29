import React, { useState, useMemo } from "react";
import {
  Send,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Lock,
  Globe,
  Mic,
  FileText,
} from "lucide-react";
import { ComplaintCategory, ComplaintSource } from "../types/civic";
import { submitComplaint } from "../services/api";

interface GrievanceIntakeViewProps {
  onComplaintSubmitted: () => void;
}

export const GrievanceIntakeView: React.FC<GrievanceIntakeViewProps> = ({
  onComplaintSubmitted,
}) => {
  const [complaintText, setComplaintText] = useState("");
  const [locality, setLocality] = useState("Ward 12");
  const [customLocality, setCustomLocality] = useState("");
  const [source, setSource] = useState<ComplaintSource>("direct_web");
  const [contactInfo, setContactInfo] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Client-side real-time preview of PII scrubbing
  const maskedPreview = useMemo(() => {
    if (!complaintText) return "";
    let s = complaintText;
    // Mask emails
    s = s.replace(/[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/g, "[EMAIL_REDACTED]");
    // Mask phones
    s = s.replace(/(?:\+91[\-\s]?)?[6-9]\d{9}/g, "[PHONE_REDACTED]");
    s = s.replace(/\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b/g, "[PHONE_REDACTED]");
    return s;
  }, [complaintText]);

  const hasPiiDetected = complaintText !== maskedPreview;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!complaintText.trim()) return;

    setIsSubmitting(true);
    setError(null);
    setResult(null);

    const activeLocality = locality === "Custom" ? customLocality.trim() : locality;

    try {
      const res = await submitComplaint({
        original_text: complaintText.trim(),
        locality: activeLocality || "Ward 12",
        source: source,
        contact: contactInfo.trim() || undefined,
        consent_obtained: true,
      });

      setResult(res);
      setComplaintText("");
      setContactInfo("");
      onComplaintSubmitted();
    } catch (err: any) {
      setError(err.message || "Failed to process complaint.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickFill = (text: string, loc: string, src: ComplaintSource, contact: string) => {
    setComplaintText(text);
    setLocality(loc);
    setSource(src);
    setContactInfo(contact);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-600 mb-1">
          <ShieldCheck className="w-4 h-4" />
          <span>Multilingual Citizen Grievance Intake</span>
        </div>
        <h2 className="text-xl font-bold text-slate-900">Submit or Ingest Citizen Complaint</h2>
        <p className="text-xs text-slate-500 mt-1">
          Supports Hindi (हिंदी), Marathi (मराठी), and English. Automated privacy protection redacts citizen phone
          numbers and emails before triage.
        </p>

        {/* Quick Demo Pre-fill Pills */}
        <div className="mt-4 pt-3 border-t border-slate-100">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide block mb-2">
            Sample Grievance Scenarios (Click to test):
          </span>
          <div className="flex flex-wrap gap-2 text-xs">
            <button
              type="button"
              onClick={() =>
                handleQuickFill(
                  "वार्ड 12 के प्राथमिक विद्यालय में पीने का पानी नहीं है और शौचालय टूटे हुए हैं। कृपया मदद करें, फोन: 9823456789",
                  "Ward 12",
                  "messaging",
                  "9823456789"
                )
              }
              className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer"
            >
              School Sanitation (Hindi)
            </button>

            <button
              type="button"
              onClick={() =>
                handleQuickFill(
                  "वॉर्ड 7 मुख्य रस्त्यावर मोठा खड्डा पडला आहे. 3 दुचाकी चालक पडले. संपर्क: 9811223344",
                  "Ward 7",
                  "direct_web",
                  "9811223344"
                )
              }
              className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer"
            >
              Road Crater Accident (Marathi)
            </button>

            <button
              type="button"
              onClick={() =>
                handleQuickFill(
                  "Main water pipeline burst near Ward 4 health dispensary. Sewage mixing with drinking water line. Emergency contact: rahul.verma@example.com or 9845012345.",
                  "Ward 4",
                  "public_meeting",
                  "9845012345"
                )
              }
              className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer"
            >
              Water Pipeline Contamination (English)
            </button>
          </div>
        </div>

        {/* Ingestion Form */}
        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Locality */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Ward / Locality
              </label>
              <select
                value={locality}
                onChange={(e) => setLocality(e.target.value)}
                className="w-full text-xs py-2 px-3 border border-slate-300 rounded bg-white text-slate-800 focus:ring-1 focus:ring-blue-500"
              >
                <option value="Ward 12">Ward 12</option>
                <option value="Ward 7">Ward 7</option>
                <option value="Ward 4">Ward 4</option>
                <option value="Ward 9">Ward 9</option>
                <option value="Ward 15">Ward 15</option>
                <option value="Custom">Custom Locality...</option>
              </select>
              {locality === "Custom" && (
                <input
                  type="text"
                  placeholder="Enter locality name..."
                  value={customLocality}
                  onChange={(e) => setCustomLocality(e.target.value)}
                  className="w-full mt-2 text-xs py-1.5 px-3 border border-slate-300 rounded"
                  required
                />
              )}
            </div>

            {/* Ingestion Channel */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Channel / Source
              </label>
              <select
                value={source}
                onChange={(e) => setSource(e.target.value as ComplaintSource)}
                className="w-full text-xs py-2 px-3 border border-slate-300 rounded bg-white text-slate-800 focus:ring-1 focus:ring-blue-500"
              >
                <option value="direct_web">Direct Citizen Web Portal</option>
                <option value="messaging">WhatsApp / SMS Helpline</option>
                <option value="public_meeting">Public Meeting / Town Hall</option>
                <option value="letter_pdf">Citizen Petition / Letter</option>
                <option value="social_media">Social Media Monitor</option>
                <option value="grievance_portal">Central Grievance Portal</option>
              </select>
            </div>

            {/* Citizen Contact (Optional) */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Citizen Phone / Email (Optional)
              </label>
              <input
                type="text"
                placeholder="Will be hashed & salted immediately"
                value={contactInfo}
                onChange={(e) => setContactInfo(e.target.value)}
                className="w-full text-xs py-2 px-3 border border-slate-300 rounded bg-white text-slate-800 focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Grievance Text Area */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Complaint Description (In English, Hindi, or Marathi)
            </label>
            <textarea
              rows={4}
              required
              value={complaintText}
              onChange={(e) => setComplaintText(e.target.value)}
              placeholder="Describe the municipal grievance in detail (e.g. broken transformer, collapsed water pipeline, lack of teachers, open drain)..."
              className="w-full text-xs p-3 border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Real-time PII Scrubbing Live Preview Box */}
          {complaintText.trim() && (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Real-Time PII Masking Preview:</span>
                </span>
                {hasPiiDetected ? (
                  <span className="text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    Sensitive Contact Redacted
                  </span>
                ) : (
                  <span className="text-[11px] text-slate-400">No contact numbers detected in text</span>
                )}
              </div>
              <p className="font-mono text-slate-600 bg-white p-2.5 rounded border border-slate-200 leading-relaxed text-[11px]">
                {maskedPreview}
              </p>
            </div>
          )}

          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded text-xs text-rose-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Globe className="w-3.5 h-3.5" />
              <span>Automatic language detection & translation included</span>
            </span>

            <button
              type="submit"
              disabled={isSubmitting || !complaintText.trim()}
              className="px-5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-xs transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{isSubmitting ? "Processing Triage..." : "Submit & Auto-Triage"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Result Card */}
      {result && (
        <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-5 shadow-xs space-y-4 animate-in fade-in-50 duration-200">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              <span>Complaint Ingested & Triaged Successfully</span>
            </div>
            <span className="font-mono text-xs font-bold text-slate-600 bg-white px-2 py-1 rounded border border-slate-200">
              {result.complaint.id}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
            <div className="bg-white p-3 rounded border border-emerald-200/80">
              <span className="text-slate-400 block text-[11px]">Category</span>
              <span className="font-semibold text-slate-900 mt-0.5 block">
                {result.processed.category}
              </span>
            </div>

            <div className="bg-white p-3 rounded border border-emerald-200/80">
              <span className="text-slate-400 block text-[11px]">Severity / Urgency</span>
              <span className="font-semibold text-slate-900 mt-0.5 block">
                {result.processed.severity_score.toFixed(0)} / {result.processed.urgency_score.toFixed(0)}
              </span>
            </div>

            <div className="bg-white p-3 rounded border border-emerald-200/80">
              <span className="text-slate-400 block text-[11px]">Detected Language</span>
              <span className="font-semibold text-slate-900 mt-0.5 block uppercase">
                {result.processed.language}
              </span>
            </div>

            <div className="bg-white p-3 rounded border border-emerald-200/80">
              <span className="text-slate-400 block text-[11px]">Vulnerable Groups</span>
              <span className="font-semibold text-indigo-700 mt-0.5 block">
                {result.processed.vulnerable_groups.join(", ") || "None"}
              </span>
            </div>
          </div>

          <div className="bg-white p-3.5 rounded border border-emerald-200/80 text-xs space-y-1">
            <span className="font-bold text-slate-700">English Synthesis & Summary:</span>
            <p className="text-slate-600 leading-relaxed">{result.processed.summary}</p>
          </div>
        </div>
      )}
    </div>
  );
};
