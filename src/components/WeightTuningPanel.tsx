import React, { useState } from "react";
import { Sliders, RefreshCw, RotateCcw, Info } from "lucide-react";
import { ScoringWeights } from "../types/civic";

interface WeightTuningPanelProps {
  weights: ScoringWeights;
  onApplyWeights: (weights: ScoringWeights) => Promise<void>;
  onResetWeights: () => void;
  isRecalculating: boolean;
}

export const WeightTuningPanel: React.FC<WeightTuningPanelProps> = ({
  weights,
  onApplyWeights,
  onResetWeights,
  isRecalculating,
}) => {
  const [localWeights, setLocalWeights] = useState<ScoringWeights>({ ...weights });
  const [isOpen, setIsOpen] = useState(false);

  const handleChange = (field: keyof ScoringWeights, val: number) => {
    setLocalWeights((prev) => ({
      ...prev,
      [field]: val,
    }));
  };

  const total =
    localWeights.weight_severity +
    localWeights.weight_people +
    localWeights.weight_urgency +
    localWeights.weight_infrastructure_gap +
    localWeights.weight_repeated_complaints;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onApplyWeights(localWeights);
  };

  const handleReset = () => {
    onResetWeights();
    setLocalWeights({
      weight_severity: 0.3,
      weight_people: 0.25,
      weight_urgency: 0.2,
      weight_infrastructure_gap: 0.15,
      weight_repeated_complaints: 0.1,
    });
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-xs">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-5 py-3.5 flex items-center justify-between text-left hover:bg-slate-50 transition cursor-pointer"
      >
        <div className="flex items-center gap-2.5">
          <Sliders className="w-4 h-4 text-blue-600" />
          <span className="text-sm font-semibold text-slate-800">
            Priority Formula Weight Configuration & Simulation
          </span>
          <span className="text-xs text-slate-500 hidden sm:inline">
            (Severity {Math.round(weights.weight_severity * 100)}% · People {Math.round(weights.weight_people * 100)}% · Urgency {Math.round(weights.weight_urgency * 100)}% · Infra {Math.round(weights.weight_infrastructure_gap * 100)}% · Repeat {Math.round(weights.weight_repeated_complaints * 100)}%)
          </span>
        </div>
        <span className="text-xs text-blue-600 font-medium">
          {isOpen ? "Collapse Controls ▲" : "Tune Weights ▼"}
        </span>
      </button>

      {isOpen && (
        <form onSubmit={handleSubmit} className="px-5 py-4 border-t border-slate-100 bg-slate-50/50">
          <div className="mb-4 text-xs text-slate-600 flex items-start gap-2 bg-blue-50/60 p-3 rounded border border-blue-200/60">
            <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-blue-900">Transparent Multi-Factor Prioritization Model</p>
              <p className="mt-0.5 text-blue-800/80">
                Adjust criteria weights to model municipal policy priorities. The logarithmic population scale protects
                critical community issues from being overshadowed by sheer density.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* 1. Severity */}
            <div className="bg-white p-3 rounded border border-slate-200">
              <div className="flex justify-between text-xs font-medium text-slate-700">
                <span>Issue Severity</span>
                <span className="font-mono font-bold text-blue-600">
                  {Math.round(localWeights.weight_severity * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.60"
                step="0.05"
                value={localWeights.weight_severity}
                onChange={(e) => handleChange("weight_severity", parseFloat(e.target.value))}
                className="w-full mt-2 accent-blue-600 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400 mt-1">Hazard level, health risks & life safety</p>
            </div>

            {/* 2. People Affected */}
            <div className="bg-white p-3 rounded border border-slate-200">
              <div className="flex justify-between text-xs font-medium text-slate-700">
                <span>People Affected (Log)</span>
                <span className="font-mono font-bold text-blue-600">
                  {Math.round(localWeights.weight_people * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.60"
                step="0.05"
                value={localWeights.weight_people}
                onChange={(e) => handleChange("weight_people", parseFloat(e.target.value))}
                className="w-full mt-2 accent-blue-600 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400 mt-1">Log-scaled demographic impact radius</p>
            </div>

            {/* 3. Urgency */}
            <div className="bg-white p-3 rounded border border-slate-200">
              <div className="flex justify-between text-xs font-medium text-slate-700">
                <span>Time Urgency</span>
                <span className="font-mono font-bold text-blue-600">
                  {Math.round(localWeights.weight_urgency * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.60"
                step="0.05"
                value={localWeights.weight_urgency}
                onChange={(e) => handleChange("weight_urgency", parseFloat(e.target.value))}
                className="w-full mt-2 accent-blue-600 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400 mt-1">Immediacy of needed intervention</p>
            </div>

            {/* 4. Infrastructure Gap */}
            <div className="bg-white p-3 rounded border border-slate-200">
              <div className="flex justify-between text-xs font-medium text-slate-700">
                <span>Infrastructure Gap</span>
                <span className="font-mono font-bold text-blue-600">
                  {Math.round(localWeights.weight_infrastructure_gap * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.60"
                step="0.05"
                value={localWeights.weight_infrastructure_gap}
                onChange={(e) => handleChange("weight_infrastructure_gap", parseFloat(e.target.value))}
                className="w-full mt-2 accent-blue-600 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400 mt-1">Historical deficit in civic assets</p>
            </div>

            {/* 5. Repeat Complaints */}
            <div className="bg-white p-3 rounded border border-slate-200">
              <div className="flex justify-between text-xs font-medium text-slate-700">
                <span>Repeat Volume</span>
                <span className="font-mono font-bold text-blue-600">
                  {Math.round(localWeights.weight_repeated_complaints * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0.05"
                max="0.40"
                step="0.05"
                value={localWeights.weight_repeated_complaints}
                onChange={(e) => handleChange("weight_repeated_complaints", parseFloat(e.target.value))}
                className="w-full mt-2 accent-blue-600 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400 mt-1">Volume across distinct channels</p>
            </div>
          </div>

          <div className="mt-4 flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-slate-200">
            <div className="text-xs text-slate-500">
              Raw Total:{" "}
              <span className={`font-mono font-semibold ${Math.abs(total - 1.0) < 0.05 ? "text-emerald-600" : "text-amber-600"}`}>
                {Math.round(total * 100)}%
              </span>{" "}
              <span className="text-slate-400">(Auto-normalizes to 100% on calculation)</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleReset}
                className="px-3 py-1.5 text-xs text-slate-600 hover:text-slate-900 border border-slate-300 rounded bg-white hover:bg-slate-50 transition cursor-pointer flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Reset Defaults</span>
              </button>
              <button
                type="submit"
                disabled={isRecalculating}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded shadow-xs transition cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRecalculating ? "animate-spin" : ""}`} />
                <span>{isRecalculating ? "Recalculating..." : "Recalculate Rankings"}</span>
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
};
