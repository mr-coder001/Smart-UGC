import React from "react";
import { CheckCircle2, Clock, XCircle, AlertCircle, ArrowRight } from "lucide-react";
import { TimelineStage } from "../types/asset";

interface PipelineTimelineProps {
  stages?: TimelineStage[];
}

export const PipelineTimeline: React.FC<PipelineTimelineProps> = ({ stages }) => {
  if (!stages || stages.length === 0) {
    return null;
  }

  const formatDuration = (ms?: number) => {
    if (ms === undefined || ms === null) return null;
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const getStageIcon = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
      case "FAILED":
        return <XCircle className="w-3.5 h-3.5 text-rose-400" />;
      case "PROCESSING":
        return <div className="w-3.5 h-3.5 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin" />;
      default:
        return <Clock className="w-3.5 h-3.5 text-amber-400" />;
    }
  };

  const getStageBadgeClass = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "FAILED":
        return "bg-rose-500/10 text-rose-400 border-rose-500/20";
      case "PROCESSING":
        return "bg-indigo-500/10 text-indigo-400 border-indigo-500/20";
      default:
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    }
  };

  return (
    <div className="glass-card rounded-3xl p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <Clock className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-white">Pipeline Decision Timeline</h3>
        </div>
        <span className="text-[11px] text-slate-500 font-mono">Real-time Stage Latencies</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
        {stages.map((stg, idx) => {
          const durationLabel = formatDuration(stg.duration_ms);

          return (
            <div
              key={idx}
              className="p-3 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex flex-col justify-between space-y-2 relative group hover:border-slate-700 transition"
              title={stg.details}
            >
              <div className="flex items-start justify-between gap-1">
                <span className="text-[11px] font-bold text-slate-300 tracking-wider break-words leading-tight">
                  {stg.stage.replace(/_/g, " ")}
                </span>
                <span className="flex-shrink-0 mt-0.5">{getStageIcon(stg.status)}</span>
              </div>

              <div className="flex items-center justify-between pt-1 gap-1">
                <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium whitespace-nowrap ${getStageBadgeClass(stg.status)}`}>
                  {stg.status === "COMPLETED" ? "Complete" : stg.status === "FAILED" ? "Failed" : "Pending"}
                </span>

                {durationLabel ? (
                  <span className="text-[11px] font-mono text-cyan-400 font-semibold whitespace-nowrap">
                    {durationLabel}
                  </span>
                ) : (
                  <span className="text-[10px] text-slate-500 italic">Ready</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
