import React, { useState } from "react";
import {
  FileSpreadsheet,
  Upload,
  CheckCircle2,
  AlertCircle,
  FileText,
  MessageSquare,
  Share2,
} from "lucide-react";
import { submitBatch } from "../services/api";

interface BatchIngestViewProps {
  onBatchProcessed: () => void;
}

export const BatchIngestView: React.FC<BatchIngestViewProps> = ({ onBatchProcessed }) => {
  const [connectorType, setConnectorType] = useState<string>("text");
  const [payloadText, setPayloadText] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const sampleTranscripts = `Speaker 1 (Ward 12 Councilor): The primary school sanitation situation in Ward 12 is at a crisis point. Over 600 students have no running water.
Speaker 2 (Citizen Ramesh): Yes, we have submitted three written letters. The children are forced to bring water bottles from home or drink unboiled water. Please deploy a municipal water tanker.
Speaker 3 (Education Officer): We have noted the crisis and need the public works department to inspect the ruptured connection immediately.`;

  const samplePetition = `To: The Municipal Commissioner,
Subject: Urgent Road Safety Hazard in Ward 7

Respected Sir,
We, the residents and business owners of Ward 7, bring to your immediate notice the deep crater formed near the central market crossroad. Three motorbike accidents occurred in the last 48 hours alone. Heavy transport vehicles are stuck for hours causing massive traffic gridlock.

Please fill the craters with asphalt and install warning reflectors before serious fatalities occur.

Signed by 45 Ward 7 Residents. Contact: 9811223344`;

  const sampleSocialPosts = JSON.stringify(
    [
      {
        post_id: "TWT-109283",
        author_handle: "@ward15_citizens",
        text: "Transformer sparking violently near Ward 15 residential colony! 240 houses in complete blackout for 14 hours in summer heat. Elderly citizens suffering. Tagging @CityElectricityBoard help!",
        timestamp: new Date().toISOString(),
        locality: "Ward 15",
      },
    ],
    null,
    2
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!payloadText.trim()) return;

    setIsProcessing(true);
    setError(null);
    setResult(null);

    let parsedPayload: any = payloadText;
    if (connectorType === "social_media" || connectorType === "grievance_portal" || connectorType === "messaging") {
      try {
        parsedPayload = JSON.parse(payloadText);
      } catch {
        // use raw text if JSON parse fails
      }
    }

    try {
      const res = await submitBatch(connectorType, parsedPayload);
      setResult(res);
      onBatchProcessed();
    } catch (err: any) {
      setError(err.message || "Failed to process batch ingestion.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-600">
          <FileSpreadsheet className="w-4 h-4" />
          <span>Multi-Channel Batch Ingestion & Connectors</span>
        </div>
        <h2 className="text-xl font-bold text-slate-900">Ingest Citizen Grievance Datasets</h2>
        <p className="text-xs text-slate-500">
          The pipeline ingests complaints across diverse channels—town hall meeting audio transcripts, paper petition letters,
          social media grievance feeds, and structured CSV dumps.
        </p>

        {/* Quick Sample Buttons */}
        <div className="pt-2 flex flex-wrap gap-2 text-xs">
          <span className="text-[11px] font-semibold text-slate-400 self-center uppercase mr-1">
            Load Template:
          </span>
          <button
            type="button"
            onClick={() => {
              setConnectorType("transcript");
              setPayloadText(sampleTranscripts);
            }}
            className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer"
          >
            Ward 12 Town Hall Meeting (Transcript)
          </button>

          <button
            type="button"
            onClick={() => {
              setConnectorType("text");
              setPayloadText(samplePetition);
            }}
            className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer"
          >
            Ward 7 Resident Petition (Text/Letter)
          </button>

          <button
            type="button"
            onClick={() => {
              setConnectorType("social_media");
              setPayloadText(sampleSocialPosts);
            }}
            className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer"
          >
            Ward 15 Power Outage (Social Feed JSON)
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 pt-2">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Select Ingestion Channel Connector
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <button
                type="button"
                onClick={() => setConnectorType("transcript")}
                className={`p-2.5 rounded border text-left cursor-pointer transition ${
                  connectorType === "transcript"
                    ? "border-blue-500 bg-blue-50/50 text-blue-900 font-semibold"
                    : "border-slate-200 hover:bg-slate-50 text-slate-700"
                }`}
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <FileText className="w-3.5 h-3.5 text-blue-600" />
                  <span>Meeting Transcript</span>
                </div>
                <span className="text-[10px] text-slate-400 block">Speaker dialogs</span>
              </button>

              <button
                type="button"
                onClick={() => setConnectorType("text")}
                className={`p-2.5 rounded border text-left cursor-pointer transition ${
                  connectorType === "text"
                    ? "border-blue-500 bg-blue-50/50 text-blue-900 font-semibold"
                    : "border-slate-200 hover:bg-slate-50 text-slate-700"
                }`}
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <Upload className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Petition / Letter</span>
                </div>
                <span className="text-[10px] text-slate-400 block">Written grievances</span>
              </button>

              <button
                type="button"
                onClick={() => setConnectorType("social_media")}
                className={`p-2.5 rounded border text-left cursor-pointer transition ${
                  connectorType === "social_media"
                    ? "border-blue-500 bg-blue-50/50 text-blue-900 font-semibold"
                    : "border-slate-200 hover:bg-slate-50 text-slate-700"
                }`}
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <Share2 className="w-3.5 h-3.5 text-purple-600" />
                  <span>Social Monitor</span>
                </div>
                <span className="text-[10px] text-slate-400 block">Tweets / Public posts</span>
              </button>

              <button
                type="button"
                onClick={() => setConnectorType("messaging")}
                className={`p-2.5 rounded border text-left cursor-pointer transition ${
                  connectorType === "messaging"
                    ? "border-blue-500 bg-blue-50/50 text-blue-900 font-semibold"
                    : "border-slate-200 hover:bg-slate-50 text-slate-700"
                }`}
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  <MessageSquare className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Helpline Export</span>
                </div>
                <span className="text-[10px] text-slate-400 block">WhatsApp / SMS dumps</span>
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Raw Payload Content
            </label>
            <textarea
              rows={8}
              required
              value={payloadText}
              onChange={(e) => setPayloadText(e.target.value)}
              placeholder="Paste raw text or formatted data here..."
              className="w-full text-xs font-mono p-3 border border-slate-300 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded text-xs text-rose-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="flex items-center justify-end">
            <button
              type="submit"
              disabled={isProcessing || !payloadText.trim()}
              className="px-5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-xs transition flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>{isProcessing ? "Processing & Ingesting..." : "Ingest & Re-cluster"}</span>
            </button>
          </div>
        </form>
      </div>

      {result && (
        <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-5 shadow-xs space-y-2 animate-in fade-in-50">
          <div className="flex items-center gap-2 text-emerald-900 font-bold text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <span>Batch Processed & Re-Ranked Successfully</span>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-700 pt-1">
            <span>Accepted: <strong className="text-emerald-700 font-mono">{result.accepted}</strong></span>
            <span>·</span>
            <span>Rejected: <strong className="text-rose-700 font-mono">{result.rejected}</strong></span>
            <span>·</span>
            <span>Total Parsed: <strong className="text-slate-900 font-mono">{result.total}</strong></span>
          </div>
          {result.errors && result.errors.length > 0 && (
            <p className="text-xs text-rose-600 mt-2">Errors: {result.errors.join(", ")}</p>
          )}
        </div>
      )}
    </div>
  );
};
