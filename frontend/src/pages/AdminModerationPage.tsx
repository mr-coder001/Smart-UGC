import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck, Check, X, AlertTriangle, RefreshCw, Eye } from "lucide-react";
import { apiService } from "../services/api";
import { Asset } from "../types/asset";

export const AdminModerationPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [activeTab, setActiveTab] = useState<"PENDING" | "APPROVED" | "REJECTED">("PENDING");

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["admin-assets", activeTab],
    queryFn: () => apiService.getAdminAssets({ status: activeTab, page_size: 20 }),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => apiService.approveAsset(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-assets"] });
      queryClient.invalidateQueries({ queryKey: ["admin-stats"] });
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      setSelectedAsset(null);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      apiService.rejectAsset(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-assets"] });
      queryClient.invalidateQueries({ queryKey: ["admin-stats"] });
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      setSelectedAsset(null);
      setRejectionReason("");
    },
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center space-x-3">
            <ShieldCheck className="w-8 h-8 text-indigo-400" />
            <span>Admin Moderation Queue</span>
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Review uploaded assets, inspect AI confidence scores, approve compliant images, or reject with reasons.
          </p>
        </div>

        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="self-start sm:self-auto inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs font-medium hover:bg-slate-800 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? "animate-spin" : ""}`} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 space-x-6 text-sm">
        {(["PENDING", "APPROVED", "REJECTED"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 font-semibold transition relative ${
              activeTab === tab
                ? "text-indigo-400 border-b-2 border-indigo-500"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab} Queue
          </button>
        ))}
      </div>

      {/* Grid of Moderation Cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="glass-card rounded-2xl h-80 animate-pulse bg-slate-900/50" />
          ))}
        </div>
      ) : data?.items?.length === 0 ? (
        <div className="glass-card rounded-3xl p-16 text-center max-w-md mx-auto space-y-3">
          <ShieldCheck className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-white">No assets in {activeTab} queue</h3>
          <p className="text-xs text-slate-400">All submissions have been reviewed.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data?.items?.map((asset: Asset) => (
            <div
              key={asset.id}
              className="glass-card rounded-2xl overflow-hidden border border-slate-800/80 flex flex-col justify-between"
            >
              <div>
                <div className="relative h-56 bg-slate-950 overflow-hidden">
                  <img
                    src={asset.presets?.thumbnail || asset.cloudinary_url || ""}
                    alt={asset.original_filename}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-2.5 right-2.5">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider backdrop-blur-md border ${
                        asset.status === "PENDING"
                          ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                          : asset.status === "APPROVED"
                          ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                          : "bg-rose-500/20 text-rose-300 border-rose-500/40"
                      }`}
                    >
                      {asset.status}
                    </span>
                  </div>
                </div>

                <div className="p-4 space-y-3">
                  <h4 className="font-semibold text-sm text-slate-200 truncate">
                    {asset.original_filename}
                  </h4>

                  {/* AI Tags Preview */}
                  {asset.tags && asset.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {asset.tags.map((t) => (
                        <span
                          key={t.id}
                          className="px-2 py-0.5 rounded text-[10px] bg-slate-900 border border-slate-800 text-slate-300 font-mono"
                        >
                          {t.tag}{t.confidence != null ? ` (${(t.confidence * 100).toFixed(0)}%)` : ""}
                        </span>
                      ))}
                    </div>
                  )}

                  {asset.moderation_reason && (
                    <p className="text-[11px] text-slate-400 italic">
                      Reason: {asset.moderation_reason}
                    </p>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="p-4 pt-0 grid grid-cols-2 gap-2">
                <button
                  disabled={approveMutation.isPending || asset.status === "APPROVED"}
                  onClick={() => approveMutation.mutate(asset.public_id)}
                  className="py-2 px-3 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/30 text-emerald-300 text-xs font-semibold flex items-center justify-center space-x-1.5 transition disabled:opacity-40"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Approve</span>
                </button>
                <button
                  disabled={rejectMutation.isPending || asset.status === "REJECTED"}
                  onClick={() => setSelectedAsset(asset)}
                  className="py-2 px-3 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/30 text-rose-300 text-xs font-semibold flex items-center justify-center space-x-1.5 transition disabled:opacity-40"
                >
                  <X className="w-3.5 h-3.5" />
                  <span>Reject</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Reject Modal */}
      {selectedAsset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
          <div className="glass-card rounded-3xl p-6 max-w-md w-full space-y-4 border border-rose-500/30 shadow-2xl">
            <div className="flex items-center space-x-2 text-rose-400">
              <AlertTriangle className="w-5 h-5" />
              <h3 className="font-semibold text-white">Reject Asset</h3>
            </div>
            <p className="text-xs text-slate-300">
              Provide a rejection reason for <span className="font-mono text-cyan-300">{selectedAsset.original_filename}</span>.
            </p>
            <textarea
              rows={3}
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="e.g. Inappropriate content, poor resolution, copyright infringement..."
              className="w-full p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-rose-500"
            />
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setSelectedAsset(null)}
                className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs"
              >
                Cancel
              </button>
              <button
                disabled={rejectMutation.isPending}
                onClick={() =>
                  rejectMutation.mutate({
                    id: selectedAsset.public_id,
                    reason: rejectionReason || "Policy violation",
                  })
                }
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
