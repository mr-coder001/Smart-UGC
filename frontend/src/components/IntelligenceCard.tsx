import React, { useState } from "react";
import {
  Brain,
  ShieldCheck,
  Zap,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Sparkles,
  Layers,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import { AssetIntelligence, Asset } from "../types/asset";
import { WhyExplanationModal } from "./WhyExplanationModal";

interface IntelligenceCardProps {
  asset: Asset;
  onReanalyze?: () => void;
  isReanalyzing?: boolean;
}

export const IntelligenceCard: React.FC<IntelligenceCardProps> = ({
  asset,
  onReanalyze,
  isReanalyzing,
}) => {
  const intel = asset.intelligence;
  const [showHowCalculated, setShowHowCalculated] = useState(false);
  const [modalCategory, setModalCategory] = useState<
    "moderation" | "tags" | "crop" | "recommendations" | "quality" | null
  >(null);

  if (!intel) {
    return (
      <div className="glass-card rounded-3xl p-6 border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Brain className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">UGC Intelligence</h3>
          </div>
          <span className="text-[11px] text-amber-400/80 font-medium">Pending Analysis</span>
        </div>
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 text-center space-y-3">
          <p className="text-xs text-slate-400">Intelligence analysis not yet available for this asset.</p>
          {onReanalyze && (
            <button
              onClick={onReanalyze}
              disabled={isReanalyzing}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isReanalyzing ? "animate-spin" : ""}`} />
              <span>{isReanalyzing ? "Evaluating Intelligence..." : "Run Intelligence Analysis"}</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-400";
    if (score >= 60) return "text-cyan-400";
    if (score >= 40) return "text-amber-400";
    return "text-rose-400";
  };

  const getScoreProgressClass = (score: number) => {
    if (score >= 80) return "bg-emerald-500";
    if (score >= 60) return "bg-cyan-500";
    if (score >= 40) return "bg-amber-500";
    return "bg-rose-500";
  };

  const getRiskBadge = (risk: string) => {
    switch (risk?.toUpperCase()) {
      case "LOW":
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 whitespace-nowrap inline-block">Low Risk</span>;
      case "HIGH":
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 whitespace-nowrap inline-block">High Risk</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 whitespace-nowrap inline-block">Medium Risk</span>;
    }
  };

  const getDecisionBadge = (decision: string) => {
    switch (decision?.toUpperCase()) {
      case "AUTO_APPROVED":
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 whitespace-nowrap">
            <CheckCircle2 className="w-3 h-3 flex-shrink-0" />
            <span>Auto Approved</span>
          </span>
        );
      case "AUTO_REJECTED":
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 whitespace-nowrap">
            <AlertTriangle className="w-3 h-3 flex-shrink-0" />
            <span>Auto Rejected</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 whitespace-nowrap">
            <ShieldCheck className="w-3 h-3 flex-shrink-0" />
            <span>Human Review</span>
          </span>
        );
    }
  };

  const getChannelBadge = (decision: string) => {
    switch (decision?.toUpperCase()) {
      case "READY":
      case "RECOMMENDED":
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 whitespace-nowrap">READY</span>;
      case "REVIEW":
      case "ACCEPTABLE":
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 whitespace-nowrap">REVIEW</span>;
      default:
        return <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20 whitespace-nowrap">NOT RECOMMENDED</span>;
    }
  };

  return (
    <>
      <div className="glass-card rounded-3xl p-6 border-slate-800 space-y-6">
        {/* Header with Title and Reanalyze */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Brain className="w-4 h-4 text-indigo-400" />
            <h3 className="text-sm font-semibold text-white">UGC Intelligence</h3>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-[11px] text-slate-500 font-mono">v{intel.version}</span>
            {onReanalyze && (
              <button
                onClick={onReanalyze}
                disabled={isReanalyzing}
                title="Refresh Intelligence"
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition disabled:opacity-40"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isReanalyzing ? "animate-spin" : ""}`} />
              </button>
            )}
          </div>
        </div>

        {/* Top Summary Metric 2x2 Grid: Spacious and Clean */}
        <div className="grid grid-cols-2 gap-3">
          {/* Quality Score */}
          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between space-y-2">
            <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium">
              <span>Quality</span>
              <button
                onClick={() => setModalCategory("quality")}
                className="text-[10px] text-indigo-400 hover:text-indigo-300 font-medium hover:underline inline-flex items-center space-x-0.5"
              >
                <span>Why?</span>
              </button>
            </div>
            <div className="space-y-1.5 pt-1">
              <div className="flex items-baseline space-x-1">
                <span className={`text-2xl font-bold font-mono ${getScoreColor(intel.quality_score)}`}>
                  {intel.quality_score}
                </span>
                <span className="text-xs text-slate-500 font-mono">/100</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${getScoreProgressClass(intel.quality_score)}`}
                  style={{ width: `${Math.min(100, Math.max(0, intel.quality_score))}%` }}
                />
              </div>
              <span className="text-[10px] text-slate-400 font-medium block leading-tight truncate" title={intel.quality_rating}>
                {intel.quality_rating}
              </span>
            </div>
          </div>

          {/* Safety & Moderation */}
          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between space-y-2">
            <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium">
              <span>Safety</span>
              <button
                onClick={() => setModalCategory("moderation")}
                className="text-[10px] text-indigo-400 hover:text-indigo-300 font-medium hover:underline"
              >
                Why?
              </button>
            </div>
            <div className="space-y-1.5 pt-1">
              <div className="flex items-center space-x-1.5 text-slate-200 text-xs font-semibold">
                <ShieldCheck className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                <span className="truncate">
                  {asset.moderation_status === "APPROVED"
                    ? "Verified Safe"
                    : asset.moderation_status === "REJECTED"
                    ? "Rejected"
                    : "Pending Review"}
                </span>
              </div>
              <div className="flex items-center justify-between text-[10px] text-slate-400">
                <span>Confidence</span>
                <span className="font-mono text-slate-300">
                  {intel.review_confidence != null
                    ? `${(intel.review_confidence * 100).toFixed(0)}%`
                    : "Unavailable"}
                </span>
              </div>
              <div>{getRiskBadge(intel.review_risk)}</div>
            </div>
          </div>

          {/* Automation Decision */}
          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between space-y-2">
            <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium">
              <span>Automation</span>
              <button
                onClick={() => setModalCategory("moderation")}
                className="text-[10px] text-indigo-400 hover:text-indigo-300 font-medium hover:underline"
              >
                Why?
              </button>
            </div>
            <div className="space-y-1.5 pt-1">
              <div>{getDecisionBadge(intel.review_decision)}</div>
              <span className="text-[10px] text-slate-400 block leading-tight">
                {intel.review_decision === "AUTO_APPROVED"
                  ? "Bypassed manual review"
                  : "Manual review required"}
              </span>
            </div>
          </div>

          {/* Best Channel Affiliation */}
          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between space-y-2">
            <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium">
              <span>Best Use</span>
              <button
                onClick={() => setModalCategory("recommendations")}
                className="text-[10px] text-indigo-400 hover:text-indigo-300 font-medium hover:underline"
              >
                Why?
              </button>
            </div>
            <div className="space-y-1.5 pt-1">
              <span className="text-xs font-semibold text-white block leading-snug break-words">
                {intel.best_use || "Multi-format"}
              </span>
              <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 whitespace-nowrap">
                {intel.recommended_format || "Default"}
              </span>
            </div>
          </div>
        </div>

        {/* Visual Factors & 'How was this calculated?' */}
        <div className="p-4 rounded-2xl bg-slate-900/50 border border-slate-800/80 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300">Grounded Quality Factors</span>
            <button
              onClick={() => setShowHowCalculated(!showHowCalculated)}
              className="text-[11px] text-indigo-400 hover:text-indigo-300 transition flex items-center space-x-1"
            >
              <span>How was this calculated?</span>
              {showHowCalculated ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>

          <div className="space-y-2">
            {intel.quality_factors.map((f, idx) => (
              <div
                key={idx}
                className="flex items-start space-x-2.5 p-2.5 rounded-xl bg-slate-950/50 border border-slate-800/60"
              >
                <span
                  className={`mt-0.5 text-xs font-bold flex-shrink-0 ${
                    f.passed ? "text-emerald-400" : "text-amber-400"
                  }`}
                >
                  {f.passed ? "✓" : "⚠"}
                </span>
                <div className="min-w-0 flex-1 space-y-0.5">
                  <div className="flex items-center justify-between gap-1.5">
                    <span className="text-xs font-medium text-slate-200">{f.factor}</span>
                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded font-semibold whitespace-nowrap ${
                        f.passed
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      }`}
                    >
                      {f.passed ? "Passed" : "Warning"}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 leading-relaxed break-words">
                    {f.description}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Expandable Explanation of the Calculation */}
          {showHowCalculated && (
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 space-y-2 mt-2">
              <p className="font-semibold text-slate-200">Quality Scoring Algorithm Methodology:</p>
              <p className="leading-relaxed">
                The visual quality score (0–100) is evaluated deterministically from verified physical properties:
                Resolution & pixel count (max 35 pts), aspect ratio & framing suitability (max 20 pts), format encoding density (max 15 pts), AI Vision semantic confidence (max 15 pts), and brand safety validation (max 15 pts).
              </p>
              {intel.unavailable_signals && intel.unavailable_signals.length > 0 && (
                <div className="pt-2 text-[10px] text-slate-500 border-t border-slate-800/80 leading-relaxed">
                  <span className="font-semibold text-slate-400">Omitted Physical Metrics: </span>
                  {intel.unavailable_signals.join(", ")} (omitted as unmeasurable from raw web payloads without fabricating synthetic data).
                </div>
              )}
            </div>
          )}
        </div>

        {/* Multi-Channel Usage Recommendation Engine */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300">Channel Usage Recommendations</span>
            <button
              onClick={() => setModalCategory("recommendations")}
              className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
            >
              <span>Why Recommended?</span>
            </button>
          </div>

          <div className="space-y-2">
            {intel.usage_recommendations.map((rec, idx) => (
              <div
                key={idx}
                className="p-3 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition space-y-1.5"
              >
                <div className="flex flex-wrap items-center justify-between gap-1.5">
                  <span className="font-semibold text-slate-200 text-xs">{rec.channel}</span>
                  {getChannelBadge(rec.decision)}
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed break-words">{rec.reason}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Grounded Why Explanation Modal */}
      <WhyExplanationModal
        isOpen={!!modalCategory}
        onClose={() => setModalCategory(null)}
        title={
          modalCategory === "moderation"
            ? "Why This Moderation & Automation Decision?"
            : modalCategory === "tags"
            ? "Why These AI Tags?"
            : modalCategory === "crop"
            ? "Why This Smart Crop Framing?"
            : modalCategory === "quality"
            ? "Why This Quality Score?"
            : "Why These Channel Recommendations?"
        }
        category={modalCategory || "recommendations"}
        data={modalCategory ? intel.explanations[modalCategory] : undefined}
      />
    </>
  );
};
