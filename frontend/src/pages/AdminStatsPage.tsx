import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  Layers,
  Clock,
  CheckCircle,
  XCircle,
  Sparkles,
  Zap,
  TrendingUp,
} from "lucide-react";
import { apiService } from "../services/api";

export const AdminStatsPage: React.FC = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: () => apiService.getAdminStats(),
    refetchInterval: 10000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  const cards = [
    {
      label: "Total Assets",
      value: stats?.total_assets ?? 0,
      icon: Layers,
      color: "text-indigo-400",
      bg: "bg-indigo-500/10",
      border: "border-indigo-500/20",
    },
    {
      label: "Pending Moderation",
      value: stats?.pending_count ?? 0,
      icon: Clock,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      border: "border-amber-500/20",
    },
    {
      label: "Approved Assets",
      value: stats?.approved_count ?? 0,
      icon: CheckCircle,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/20",
    },
    {
      label: "Rejected Assets",
      value: stats?.rejected_count ?? 0,
      icon: XCircle,
      color: "text-rose-400",
      bg: "bg-rose-500/10",
      border: "border-rose-500/20",
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center space-x-3">
          <BarChart3 className="w-8 h-8 text-cyan-400" />
          <span>Platform Automation & Metrics</span>
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Real-time metrics on asset throughput, AI scene tagging coverage, and moderation decision turnaround times.
        </p>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((c, i) => (
          <div key={i} className={`glass-card rounded-3xl p-6 border ${c.border} space-y-4`}>
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{c.label}</span>
              <div className={`w-9 h-9 rounded-xl ${c.bg} flex items-center justify-center ${c.color}`}>
                <c.icon className="w-5 h-5" />
              </div>
            </div>
            <div className="text-3xl font-extrabold text-white font-mono tracking-tight">
              {c.value}
            </div>
          </div>
        ))}
      </div>

      {/* Automation Rates & Performance Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AI Tagging Coverage */}
        <div className="glass-card rounded-3xl p-6 space-y-4 border border-indigo-500/20">
          <div className="flex items-center space-x-2 text-indigo-400">
            <Sparkles className="w-5 h-5" />
            <h3 className="font-semibold text-white">AI Tag Coverage</h3>
          </div>
          <div className="text-4xl font-extrabold text-white font-mono">
            {stats?.tag_coverage_percentage ?? 0}%
          </div>
          <p className="text-xs text-slate-400">
            Proportion of ingested assets with at least one scene or object tag extracted by vision models.
          </p>
          <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
            <div
              className="bg-indigo-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${stats?.tag_coverage_percentage ?? 0}%` }}
            />
          </div>
        </div>

        {/* Automation Rate */}
        <div className="glass-card rounded-3xl p-6 space-y-4 border border-cyan-500/20">
          <div className="flex items-center space-x-2 text-cyan-400">
            <Zap className="w-5 h-5" />
            <h3 className="font-semibold text-white">Automation Rate</h3>
          </div>
          <div className="text-4xl font-extrabold text-white font-mono">
            {stats?.automation_rate ?? 0}%
          </div>
          <p className="text-xs text-slate-400">
            Percentage of assets with automated background tasks successfully finished without human intervention.
          </p>
          <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
            <div
              className="bg-cyan-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${stats?.automation_rate ?? 0}%` }}
            />
          </div>
        </div>

        {/* Average Time-To-Decision */}
        <div className="glass-card rounded-3xl p-6 space-y-4 border border-emerald-500/20">
          <div className="flex items-center space-x-2 text-emerald-400">
            <TrendingUp className="w-5 h-5" />
            <h3 className="font-semibold text-white">Average Decision Time</h3>
          </div>
          <div className="text-4xl font-extrabold text-white font-mono">
            {stats?.average_decision_time_seconds != null
              ? `${stats.average_decision_time_seconds}s`
              : "Insufficient data"}
          </div>
          <p className="text-xs text-slate-400">
            Average turnaround duration from asset upload to administrator review or automated disposition.
          </p>
        </div>
      </div>

      {/* UGC Intelligence Analytics Section */}
      <div className="space-y-4 pt-4 border-t border-slate-800">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <span>UGC Intelligence Analytics</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Deterministic quality distributions and automated routing analytics across {stats?.total_intelligence_analyzed ?? 0} analyzed assets.
            </p>
          </div>
          {stats?.total_intelligence_analyzed === 0 && (
            <span className="text-xs px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Insufficient data
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* 1. Average Quality Score */}
          <div className="glass-card rounded-3xl p-6 border border-slate-800 space-y-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
              UGC Quality
            </span>
            <div className="text-3xl font-extrabold text-white font-mono">
              {stats?.average_quality_score != null ? (
                <>
                  <span>{stats.average_quality_score}</span>
                  <span className="text-sm text-slate-400 font-sans ml-1">avg</span>
                </>
              ) : (
                <span className="text-sm font-normal text-slate-500 italic">Insufficient data</span>
              )}
            </div>
            <p className="text-[11px] text-slate-400">
              Deterministic average visual quality score calculated from resolution, aspect ratio, and framing signals.
            </p>
          </div>

          {/* 2. Auto-Approved % */}
          <div className="glass-card rounded-3xl p-6 border border-slate-800 space-y-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
              Automation
            </span>
            <div className="text-3xl font-extrabold text-emerald-400 font-mono">
              {stats?.auto_approved_percentage != null ? (
                `${stats.auto_approved_percentage}%`
              ) : (
                <span className="text-sm font-normal text-slate-500 italic">Insufficient data</span>
              )}
            </div>
            <p className="text-[11px] text-slate-400">
              Assets automatically approved by deterministic brand safety and confidence threshold criteria.
            </p>
          </div>

          {/* 3. Human Review % */}
          <div className="glass-card rounded-3xl p-6 border border-slate-800 space-y-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
              Human Review
            </span>
            <div className="text-3xl font-extrabold text-amber-400 font-mono">
              {stats?.human_review_percentage != null ? (
                `${stats.human_review_percentage}%`
              ) : (
                <span className="text-sm font-normal text-slate-500 italic">Insufficient data</span>
              )}
            </div>
            <p className="text-[11px] text-slate-400">
              Borderline or uncertain assets dispatched to moderation queue for human verification.
            </p>
          </div>

          {/* 4. Production Ready % */}
          <div className="glass-card rounded-3xl p-6 border border-slate-800 space-y-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
              Production Ready
            </span>
            <div className="text-3xl font-extrabold text-cyan-400 font-mono">
              {stats?.production_ready_percentage != null ? (
                `${stats.production_ready_percentage}%`
              ) : (
                <span className="text-sm font-normal text-slate-500 italic">Insufficient data</span>
              )}
            </div>
            <p className="text-[11px] text-slate-400">
              Assets scoring &ge; 80 in visual fidelity, meeting all omnichannel e-commerce production criteria.
            </p>
          </div>
        </div>

        {/* Most Common Review Reason Banner */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
          <span className="text-slate-400 font-medium">Most Common Review Reason:</span>
          <span className="text-slate-200 font-semibold max-w-lg truncate text-right">
            {stats?.most_common_review_reason || "Insufficient data"}
          </span>
        </div>
      </div>
    </div>
  );
};
