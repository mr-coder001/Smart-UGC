import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Search, Tag, Sparkles, Filter, SlidersHorizontal, ArrowUpDown, Brain, CheckCircle2, ShieldAlert } from "lucide-react";
import { apiService } from "../services/api";
import { Asset } from "../types/asset";

export const GalleryPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [qualityTier, setQualityTier] = useState<string>("all");
  const [reviewDecision, setReviewDecision] = useState<string>("all");
  const [recommendedUse, setRecommendedUse] = useState<string>("all");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useQuery({
    queryKey: [
      "assets",
      searchQuery,
      selectedTag,
      qualityTier,
      reviewDecision,
      recommendedUse,
      sortBy,
      sortOrder,
      page,
    ],
    queryFn: () =>
      apiService.getAssets({
        query: searchQuery || undefined,
        tag: selectedTag || undefined,
        quality_tier: qualityTier !== "all" ? qualityTier : undefined,
        review_decision: reviewDecision !== "all" ? reviewDecision : undefined,
        recommended_use: recommendedUse !== "all" ? recommendedUse : undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: 12,
      }),
  });

  const hasActiveFilters =
    selectedTag !== null ||
    qualityTier !== "all" ||
    reviewDecision !== "all" ||
    recommendedUse !== "all" ||
    searchQuery.trim().length > 0;

  const resetFilters = () => {
    setSelectedTag(null);
    setQualityTier("all");
    setReviewDecision("all");
    setRecommendedUse("all");
    setSearchQuery("");
    setPage(1);
  };

  return (
    <div className="space-y-8">
      {/* Hero / Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Asset Catalog
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Explore approved assets evaluated with deterministic UGC intelligence, visual quality scoring, and channel recommendations.
          </p>
        </div>

        {/* Action button */}
        <Link
          to="/upload"
          className="self-start md:self-auto inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-medium shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02]"
        >
          <Sparkles className="w-4 h-4 text-cyan-200" />
          <span>Upload Image</span>
        </Link>
      </div>

      {/* Filter / Search Bar */}
      <div className="glass-card rounded-2xl p-4 space-y-3">
        <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
          <div className="relative w-full md:w-96">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              placeholder="Search by filename or tag..."
              className="w-full pl-10 pr-4 py-2 bg-slate-900/80 border border-slate-700/60 rounded-xl text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2 w-full md:w-auto justify-end">
            {/* Tag Filter Reset if active */}
            {selectedTag && (
              <button
                onClick={() => setSelectedTag(null)}
                className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-indigo-500/20 text-indigo-300 text-xs border border-indigo-500/40 hover:bg-indigo-500/30 transition"
              >
                <span>Tag: {selectedTag}</span>
                <span className="font-bold ml-1">×</span>
              </button>
            )}

            {/* Quality Tier Dropdown */}
            <div className="flex items-center space-x-1 text-xs text-slate-400">
              <select
                value={qualityTier}
                onChange={(e) => {
                  setQualityTier(e.target.value);
                  setPage(1);
                }}
                className="bg-slate-900 border border-slate-700/60 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="all">All Quality Tiers</option>
                <option value="high">High Quality (80–100)</option>
                <option value="medium">Medium Quality (50–79)</option>
                <option value="low">Low Quality (&lt;50)</option>
              </select>
            </div>

            {/* Review Decision Dropdown */}
            <div className="flex items-center space-x-1 text-xs text-slate-400">
              <select
                value={reviewDecision}
                onChange={(e) => {
                  setReviewDecision(e.target.value);
                  setPage(1);
                }}
                className="bg-slate-900 border border-slate-700/60 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="all">All Automation Decisions</option>
                <option value="AUTO_APPROVED">Auto Approved</option>
                <option value="HUMAN_REVIEW">Human Review</option>
              </select>
            </div>

            {/* Recommended Channel Dropdown */}
            <div className="flex items-center space-x-1 text-xs text-slate-400">
              <select
                value={recommendedUse}
                onChange={(e) => {
                  setRecommendedUse(e.target.value);
                  setPage(1);
                }}
                className="bg-slate-900 border border-slate-700/60 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="all">All Channel Uses</option>
                <option value="Product Card">Product Card</option>
                <option value="Website Hero">Website Hero</option>
                <option value="Social Feed">Social Feed</option>
                <option value="Story / Vertical">Story / Vertical</option>
                <option value="Marketplace Listing">Marketplace Listing</option>
              </select>
            </div>

            {/* Sort Dropdown */}
            <div className="flex items-center space-x-1 text-xs text-slate-400">
              <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [sb, so] = e.target.value.split("-");
                  setSortBy(sb);
                  setSortOrder(so as "asc" | "desc");
                }}
                className="bg-slate-900 border border-slate-700/60 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="created_at-desc">Newest First</option>
                <option value="created_at-asc">Oldest First</option>
                <option value="file_size-desc">Largest Size</option>
                <option value="file_size-asc">Smallest Size</option>
              </select>
            </div>

            {hasActiveFilters && (
              <button
                onClick={resetFilters}
                className="px-2.5 py-1.5 text-xs text-rose-400 hover:text-rose-300 transition"
              >
                Reset
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Gallery Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="glass-card rounded-2xl overflow-hidden animate-pulse">
              <div className="w-full h-52 bg-slate-800" />
              <div className="p-4 space-y-3">
                <div className="h-4 bg-slate-800 rounded w-3/4" />
                <div className="h-3 bg-slate-800 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : isError ? (
        <div className="glass-card rounded-2xl p-12 text-center max-w-md mx-auto">
          <p className="text-rose-400 text-sm font-medium">Failed to load asset catalog</p>
          <p className="text-slate-400 text-xs mt-1">Please ensure the backend service is running.</p>
        </div>
      ) : data?.items?.length === 0 ? (
        <div className="glass-card rounded-2xl p-16 text-center max-w-md mx-auto space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto">
            <Sparkles className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">No approved assets yet</h3>
            <p className="text-sm text-slate-400 mt-1">
              Upload images to begin. Newly uploaded assets start in PENDING moderation queue.
            </p>
          </div>
          <Link
            to="/upload"
            className="inline-flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl transition"
          >
            Go to Upload
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {data?.items?.map((asset: Asset) => (
            <Link
              key={asset.id}
              to={`/assets/${asset.public_id}`}
              className="group glass-card rounded-2xl overflow-hidden hover:border-indigo-500/40 transition-all duration-300 hover:shadow-xl hover:shadow-indigo-500/10 flex flex-col"
            >
              {/* Asset Preview Thumbnail */}
              <div className="relative w-full h-56 bg-slate-900 overflow-hidden">
                <img
                  src={asset.presets?.thumbnail || asset.cloudinary_url || ""}
                  alt={asset.original_filename}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  loading="lazy"
                />
                {/* UGC Quality Score Pill */}
                {asset.intelligence && (
                  <div className="absolute top-2.5 left-2.5">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold font-mono border backdrop-blur-md ${
                        asset.intelligence.quality_score >= 80
                          ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                          : asset.intelligence.quality_score >= 60
                          ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/30"
                          : "bg-amber-500/20 text-amber-300 border-amber-500/30"
                      }`}
                    >
                      {asset.intelligence.quality_score}/100
                    </span>
                  </div>
                )}
                <div className="absolute top-2.5 right-2.5">
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 backdrop-blur-md">
                    Approved
                  </span>
                </div>
              </div>

              {/* Asset Metadata */}
              <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                <div>
                  <div className="flex items-start justify-between gap-1">
                    <h4 className="font-semibold text-sm text-slate-100 truncate group-hover:text-indigo-400 transition-colors">
                      {asset.original_filename}
                    </h4>
                  </div>
                  <div className="flex items-center space-x-2 text-[11px] text-slate-400 mt-0.5 font-mono">
                    <span>{(asset.file_size / 1024).toFixed(0)} KB</span>
                    {asset.width && asset.height && (
                      <>
                        <span>•</span>
                        <span>{asset.width}×{asset.height}</span>
                      </>
                    )}
                    {asset.intelligence?.best_use && (
                      <>
                        <span>•</span>
                        <span className="text-cyan-400 font-sans font-medium">{asset.intelligence.best_use}</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Tags */}
                {asset.tags && asset.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {asset.tags.slice(0, 3).map((t) => (
                      <span
                        key={t.id}
                        onClick={(e) => {
                          e.preventDefault();
                          setSelectedTag(t.tag);
                          setPage(1);
                        }}
                        className="inline-flex items-center text-[10px] px-2 py-0.5 rounded-md bg-slate-800/80 text-slate-300 border border-slate-700/60 hover:bg-indigo-600/20 hover:text-indigo-300 transition"
                      >
                        #{t.tag}
                      </span>
                    ))}
                    {asset.tags.length > 3 && (
                      <span className="text-[10px] text-slate-500 self-center">
                        +{asset.tags.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-center space-x-2 pt-6">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(p - 1, 1))}
            className="px-4 py-2 rounded-xl text-xs font-medium bg-slate-900 border border-slate-800 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800 transition"
          >
            Previous
          </button>
          <span className="text-xs text-slate-400 font-mono">
            Page {page} of {data.total_pages}
          </span>
          <button
            disabled={page >= data.total_pages}
            onClick={() => setPage((p) => Math.min(p + 1, data.total_pages))}
            className="px-4 py-2 rounded-xl text-xs font-medium bg-slate-900 border border-slate-800 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800 transition"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};
