export type AssetStatus = "PROCESSING" | "PENDING" | "APPROVED" | "REJECTED" | "FAILED";
export type ModerationStatus = "PENDING" | "APPROVED" | "REJECTED";
export type TaskProcessingStatus = "NOT_REQUESTED" | "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface AssetTag {
  id: number;
  tag: string;
  confidence?: number | null;
  created_at: string;
}

export interface ProcessingState {
  id: number;
  tagging_status: TaskProcessingStatus;
  moderation_status: TaskProcessingStatus;
  background_removal_status: TaskProcessingStatus;
  processing_started_at?: string;
  processing_completed_at?: string;
  error_message?: string;
  updated_at: string;
}

export interface AssetPresets {
  delivery: string;
  thumbnail: string;
  square: string;
  landscape: string;
  portrait: string;
}

export interface QualityFactor {
  factor: string;
  passed: boolean;
  impact: "positive" | "neutral" | "negative";
  description: string;
  signal_used: string;
}

export interface UsageRecommendation {
  channel: string;
  decision: "READY" | "REVIEW" | "NOT_RECOMMENDED";
  reason: string;
  signals: string[];
  rules_triggered?: string[];
  supporting_metadata?: Record<string, any>;
}

export interface ExplanationBlock {
  summary: string;
  points: string[];
}

export interface DecisionExplanations {
  moderation: ExplanationBlock;
  tags: ExplanationBlock;
  crop: ExplanationBlock;
  recommendations: ExplanationBlock;
  quality: ExplanationBlock;
}

export interface TimelineStage {
  stage: string;
  status: "COMPLETED" | "PENDING" | "PROCESSING" | "FAILED";
  duration_ms?: number;
  details: string;
}

export interface AssetIntelligence {
  quality_score: number;
  quality_rating: string;
  quality_factors: QualityFactor[];
  unavailable_signals: string[];
  usage_recommendations: UsageRecommendation[];
  best_use?: string;
  recommended_format?: string;
  review_decision: "AUTO_APPROVED" | "AUTO_REJECTED" | "HUMAN_REVIEW";
  review_risk: "LOW" | "MEDIUM" | "HIGH";
  review_reason?: string;
  review_confidence?: number | null;
  explanations: DecisionExplanations;
  pipeline_timeline: TimelineStage[];
  version: string;
  status: string;
  error_message?: string;
}

export interface Asset {
  id: number;
  public_id: string;
  cloudinary_public_id: string;
  cloudinary_url?: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  width?: number;
  height?: number;
  status: AssetStatus;
  moderation_status: ModerationStatus;
  moderation_reason?: string;
  created_at: string;
  updated_at: string;
  approved_at?: string;
  rejected_at?: string;
  decision_at?: string;
  tags: AssetTag[];
  processing_state?: ProcessingState;
  presets?: AssetPresets;
  intelligence?: AssetIntelligence;
}

export interface SearchResult {
  items: Asset[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  query?: string;
  applied_filters?: Record<string, any>;
}

export interface AdminStats {
  total_assets: number;
  pending_count: number;
  approved_count: number;
  rejected_count: number;
  tag_coverage_percentage: number;
  automation_rate: number;
  average_decision_time_seconds?: number;
  processing_status_counts: Record<string, number>;
  average_quality_score?: number;
  auto_approved_percentage?: number;
  human_review_percentage?: number;
  production_ready_percentage?: number;
  most_common_review_reason?: string;
  total_intelligence_analyzed: number;
}
