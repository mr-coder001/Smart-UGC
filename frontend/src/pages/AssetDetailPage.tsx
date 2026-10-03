import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Copy,
  Check,
  X,
  Sparkles,
  Sliders,
  Crop,
  Layers,
  Download,
  ShieldCheck,
  Clock,
  HelpCircle,
  AlertCircle,
} from "lucide-react";
import { apiService } from "../services/api";
import { IntelligenceCard } from "../components/IntelligenceCard";
import { PipelineTimeline } from "../components/PipelineTimeline";
import { WhyExplanationModal } from "../components/WhyExplanationModal";

export const AssetDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const [activePreset, setActivePreset] = useState<"delivery" | "thumbnail" | "square" | "landscape" | "portrait">("delivery");
  const [bgRemoval, setBgRemoval] = useState(false);
  const [customWidth, setCustomWidth] = useState<number | "">("");
  const [customHeight, setCustomHeight] = useState<number | "">("");
  const [cropMode, setCropMode] = useState("fill");
  const [copied, setCopied] = useState(false);
  const [isReanalyzing, setIsReanalyzing] = useState(false);
  const [whyCategory, setWhyCategory] = useState<"moderation" | "tags" | "crop" | "recommendations" | "quality" | null>(null);
  const [imageError, setImageError] = useState(false);

  const { data: asset, isLoading, isError, refetch } = useQuery({
    queryKey: ["asset", id],
    queryFn: () => apiService.getAssetById(id!),
    enabled: !!id,
  });

  const handleReanalyze = async () => {
    if (!id) return;
    setIsReanalyzing(true);
    try {
      await apiService.reanalyzeAsset(id);
      await refetch();
    } catch (e) {
      console.error("Failed to reanalyze asset intelligence:", e);
    } finally {
      setIsReanalyzing(false);
    }
  };

  const queryClient = useQueryClient();

  const approveMutation = useMutation({
    mutationFn: () => apiService.approveAsset(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["asset", id] });
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      queryClient.invalidateQueries({ queryKey: ["admin-assets"] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (reason: string) => apiService.rejectAsset(id!, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["asset", id] });
      queryClient.invalidateQueries({ queryKey: ["assets"] });
      queryClient.invalidateQueries({ queryKey: ["admin-assets"] });
    },
  });

  // Query custom on-demand transformation URL when toggles change
  const { data: transformData } = useQuery({
    queryKey: ["transform", id, activePreset, bgRemoval, customWidth, customHeight, cropMode],
    queryFn: () =>
      apiService.transformAsset(id!, {
        width: typeof customWidth === "number" ? customWidth : undefined,
        height: typeof customHeight === "number" ? customHeight : undefined,
        crop: cropMode,
        background_removal: bgRemoval,
      }),
    enabled: !!id && (bgRemoval || !!customWidth || !!customHeight),
  });

  // Reset image error state whenever activePreset or parameters change (called unconditionally at top level)
  useEffect(() => {
    setImageError(false);
  }, [id, activePreset, bgRemoval, customWidth, customHeight, cropMode]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
      </div>
    );
  }

  if (isError || !asset) {
    return (
      <div className="glass-card rounded-3xl p-12 text-center max-w-md mx-auto space-y-4">
        <p className="text-rose-400 font-semibold">Asset Not Found</p>
        <p className="text-slate-400 text-xs">The requested image asset does not exist or has been removed.</p>
        <Link to="/" className="inline-block px-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300">
          Back to Gallery
        </Link>
      </div>
    );
  }

  // Determine current active preview image URL
  let currentImageUrl = asset.presets?.[activePreset] || asset.cloudinary_url || "";
  if (transformData?.transformation_url) {
    currentImageUrl = transformData.transformation_url;
  }

  const handleCopyUrl = () => {
    navigator.clipboard.writeText(currentImageUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8">
      {/* Top Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link
          to="/"
          className="inline-flex items-center space-x-2 text-xs font-medium text-slate-400 hover:text-slate-200 transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Catalog</span>
        </Link>

        <div className="flex items-center space-x-2.5">
          {asset.intelligence && (
            <button
              onClick={() => setWhyCategory("moderation")}
              className="inline-flex items-center space-x-1 px-3 py-1 rounded-full text-xs font-medium bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition"
            >
              <HelpCircle className="w-3.5 h-3.5 text-indigo-400" />
              <span>Why this decision?</span>
            </button>
          )}
          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold border ${
              asset.status === "APPROVED"
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                : asset.status === "REJECTED"
                ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                : "bg-amber-500/10 text-amber-400 border-amber-500/30"
            }`}
          >
            {asset.status}
          </span>
        </div>
      </div>

      {/* Pending Moderation Action Banner */}
      {asset.status === "PENDING" && (
        <div className="p-4 sm:p-5 rounded-3xl glass-card border border-amber-500/30 bg-amber-500/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-fade-in shadow-xl shadow-amber-500/5">
          <div className="flex items-center space-x-3.5">
            <div className="w-10 h-10 rounded-2xl bg-amber-500/15 border border-amber-500/30 text-amber-400 flex items-center justify-center flex-shrink-0 shadow-inner">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white">Pending Moderation Review</h4>
              <p className="text-xs text-slate-400 mt-0.5">
                This asset is awaiting moderation. You can approve or reject it right here, or manage it in the full Moderation Queue.
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2.5 self-end sm:self-auto flex-shrink-0">
            <Link
              to="/admin/moderation"
              className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs font-medium transition"
            >
              Queue
            </Link>
            <button
              disabled={approveMutation.isPending}
              onClick={() => approveMutation.mutate()}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-600/30 transition flex items-center space-x-1.5 disabled:opacity-50"
            >
              <Check className="w-3.5 h-3.5" />
              <span>{approveMutation.isPending ? "Approving..." : "Approve Asset"}</span>
            </button>
            <button
              disabled={rejectMutation.isPending}
              onClick={() => {
                const reason = window.prompt("Enter rejection reason:", "Content policy violation");
                if (reason) rejectMutation.mutate(reason);
              }}
              className="px-3.5 py-2 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/30 text-rose-300 text-xs font-semibold transition flex items-center space-x-1.5 disabled:opacity-50"
            >
              <X className="w-3.5 h-3.5" />
              <span>Reject</span>
            </button>
          </div>
        </div>
      )}

      {/* Main Grid: Viewer + Transformation Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Image Canvas Preview */}
        <div className="lg:col-span-8 space-y-4">
          <div className="glass-card rounded-3xl p-4 sm:p-6 overflow-hidden flex items-center justify-center min-h-[450px] bg-slate-950/60 border-slate-800/80 relative">
            {imageError ? (
              <div className="flex flex-col items-center justify-center p-8 text-center space-y-3 bg-slate-900/50 rounded-2xl border border-slate-800/80 max-w-sm">
                <div className="w-12 h-12 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center">
                  <AlertCircle className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <p className="text-xs font-bold tracking-wider text-rose-400 uppercase">Image Unavailable</p>
                  <p className="text-xs text-slate-300 font-mono break-all">{asset.original_filename}</p>
                </div>
                <p className="text-[11px] text-slate-500">
                  Cloudinary image could not be loaded directly by the browser.
                </p>
              </div>
            ) : (
              <img
                src={currentImageUrl}
                alt={asset.original_filename}
                onError={() => {
                  console.warn("Asset image failed to load from:", currentImageUrl);
                  setImageError(true);
                }}
                className="max-h-[550px] w-auto object-contain rounded-2xl shadow-2xl transition-all duration-300"
              />
            )}

            {/* Floating quick actions */}
            <div className="absolute top-4 right-4 flex items-center space-x-2">
              <button
                onClick={handleCopyUrl}
                className="px-3 py-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-700/60 text-slate-200 text-xs font-medium backdrop-blur-md transition flex items-center space-x-1.5 shadow-lg"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? "Copied" : "Copy URL"}</span>
              </button>
              <a
                href={currentImageUrl}
                target="_blank"
                rel="noreferrer"
                download
                className="p-1.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-slate-700/60 text-slate-200 text-xs backdrop-blur-md transition shadow-lg"
              >
                <Download className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* Subject-Aware Preset Chips */}
          <div className="glass-card rounded-2xl p-4 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-slate-400 font-medium mr-2 flex items-center space-x-1">
                  <Crop className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Smart Presets (g_auto):</span>
                </span>

                {(
                  [
                    { id: "delivery", label: "Optimized Original" },
                    { id: "thumbnail", label: "Thumbnail (300×300)" },
                    { id: "square", label: "Square (1080×1080)" },
                    { id: "landscape", label: "Landscape (1600×900)" },
                    { id: "portrait", label: "Portrait (1080×1350)" },
                  ] as const
                ).map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => {
                      setActivePreset(preset.id);
                      setCustomWidth("");
                      setCustomHeight("");
                    }}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium transition ${
                      activePreset === preset.id && !customWidth && !customHeight
                        ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                        : "bg-slate-900/80 text-slate-300 border border-slate-800 hover:bg-slate-800"
                    }`}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>

              {asset.intelligence && (
                <button
                  onClick={() => setWhyCategory("crop")}
                  className="text-xs text-indigo-400 hover:text-indigo-300 inline-flex items-center space-x-1"
                >
                  <HelpCircle className="w-3.5 h-3.5" />
                  <span>Why this crop?</span>
                </button>
              )}
            </div>
          </div>

          {/* Pipeline Decision Timeline */}
          {asset.intelligence?.pipeline_timeline && (
            <PipelineTimeline stages={asset.intelligence.pipeline_timeline} />
          )}
        </div>

        {/* Right Column: UGC Intelligence, Custom Transformation & AI Metadata */}
        <div className="lg:col-span-4 space-y-6">
          {/* UGC Intelligence Card */}
          <IntelligenceCard
            asset={asset}
            onReanalyze={handleReanalyze}
            isReanalyzing={isReanalyzing}
          />

          {/* Custom On-Demand Transformations */}
          <div className="glass-card rounded-3xl p-6 space-y-5">
            <div className="flex items-center space-x-2 text-sm font-semibold text-white border-b border-slate-800 pb-3">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <span>On-Demand Transformations</span>
            </div>

            {/* AI Background Removal Toggle */}
            <div className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800">
              <div>
                <span className="text-xs font-semibold text-slate-200 block">AI Background Removal</span>
                <span className="text-[11px] text-slate-500">Cloudinary on-the-fly cutout</span>
              </div>
              <button
                onClick={() => setBgRemoval(!bgRemoval)}
                className={`w-11 h-6 rounded-full transition-colors relative flex items-center p-0.5 ${
                  bgRemoval ? "bg-indigo-600" : "bg-slate-800"
                }`}
              >
                <div
                  className={`w-5 h-5 rounded-full bg-white transition-transform ${
                    bgRemoval ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>

            {/* Custom Width & Height */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-medium text-slate-400 block mb-1">Width (px)</label>
                <input
                  type="number"
                  placeholder="e.g. 800"
                  value={customWidth}
                  onChange={(e) => setCustomWidth(e.target.value ? Number(e.target.value) : "")}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="text-[11px] font-medium text-slate-400 block mb-1">Height (px)</label>
                <input
                  type="number"
                  placeholder="e.g. 600"
                  value={customHeight}
                  onChange={(e) => setCustomHeight(e.target.value ? Number(e.target.value) : "")}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            {/* Crop Mode Selection */}
            <div>
              <label className="text-[11px] font-medium text-slate-400 block mb-1">Crop Mode</label>
              <select
                value={cropMode}
                onChange={(e) => setCropMode(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="fill">fill (Subject-aware fill)</option>
                <option value="scale">scale (Fit without cropping)</option>
                <option value="thumb">thumb (Face / Subject thumbnail)</option>
                <option value="crop">crop (Direct coordinate crop)</option>
              </select>
            </div>
          </div>

          {/* AI Vision Tags Card */}
          <div className="glass-card rounded-3xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2 text-sm font-semibold text-white">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span>AI Vision Scene Tags</span>
              </div>
              {asset.intelligence && (
                <button
                  onClick={() => setWhyCategory("tags")}
                  className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
                >
                  <HelpCircle className="w-3.5 h-3.5" />
                  <span>Why these tags?</span>
                </button>
              )}
            </div>

            {asset.tags && asset.tags.length > 0 ? (
              <div className="space-y-2">
                {asset.tags.map((tag) => (
                  <div
                    key={tag.id}
                    className="flex items-center justify-between p-2 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs"
                  >
                    <span className="font-medium text-slate-300">#{tag.tag}</span>
                    {tag.confidence !== null && tag.confidence !== undefined ? (
                      <span className="font-mono text-cyan-400 font-semibold">
                        {(tag.confidence * 100).toFixed(0)}%
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-400 font-mono">
                        Unavailable
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500">No automated vision tags detected from provider.</p>
            )}
          </div>

          {/* Asset Metadata Card */}
          <div className="glass-card rounded-3xl p-6 space-y-3 text-xs">
            <div className="text-sm font-semibold text-white border-b border-slate-800 pb-2">
              Metadata
            </div>
            <div className="flex justify-between py-1 text-slate-400">
              <span>Original Filename</span>
              <span className="text-slate-200 font-medium truncate max-w-[180px]">{asset.original_filename}</span>
            </div>
            <div className="flex justify-between py-1 text-slate-400">
              <span>MIME Type</span>
              <span className="font-mono text-slate-300">{asset.mime_type}</span>
            </div>
            <div className="flex justify-between py-1 text-slate-400">
              <span>File Size</span>
              <span className="font-mono text-slate-300">{(asset.file_size / 1024).toFixed(1)} KB</span>
            </div>
            {asset.width && asset.height && (
              <div className="flex justify-between py-1 text-slate-400">
                <span>Dimensions</span>
                <span className="font-mono text-slate-300">{asset.width} × {asset.height} px</span>
              </div>
            )}
            <div className="flex justify-between py-1 text-slate-400">
              <span>Public ID</span>
              <span className="font-mono text-slate-300 truncate max-w-[160px]">{asset.public_id}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Grounded Why Explanation Modal */}
      <WhyExplanationModal
        isOpen={!!whyCategory}
        onClose={() => setWhyCategory(null)}
        title={
          whyCategory === "moderation"
            ? "Why This Moderation & Automation Decision?"
            : whyCategory === "tags"
            ? "Why These AI Tags?"
            : whyCategory === "crop"
            ? "Why This Smart Crop Framing?"
            : whyCategory === "quality"
            ? "Why This Quality Score?"
            : "Why These Channel Recommendations?"
        }
        category={whyCategory || "moderation"}
        data={asset.intelligence && whyCategory ? asset.intelligence.explanations[whyCategory] : undefined}
      />
    </div>
  );
};
