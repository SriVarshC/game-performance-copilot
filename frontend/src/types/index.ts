// ─── Telemetry ──────────────────────────────────────────────────────────────
export interface TelemetryData {
  fps: number;
  cpu_usage: number;
  gpu_usage: number;
  ram_usage: number;
  vram_usage: number;
  cpu_temp: number | null;
  gpu_temp: number;
  timestamp: string;
}

export interface TelemetryHistory {
  timestamps: string[];
  fps: number[];
  cpu_usage: number[];
  gpu_usage: number[];
  ram_usage: number[];
}

// ─── Prediction ─────────────────────────────────────────────────────────────
export interface PredictionRequest {
  cpu_usage:   number;
  gpu_usage:   number;
  ram_usage:   number;
  vram_usage:  number;
  cpu_temp:    number;
  gpu_temp:    number;
  resolution:  string;
  game_genre:  string;
  preset:      string;    // matches form: low/medium/high/ultra
  upscaling:   string;    // matches form: none/dlss_quality/fsr_quality/…
  ray_tracing: boolean;
}

export interface PredictionResult {
  predicted_fps:    number;
  frame_time_ms:    number;
  performance_tier: string;
  model_name:       string;
  low_1pct_fps:     number | null;
  bottleneck_class: string | null;
  health_score:     number | null;
  error:            string | null;
}

// ─── Recommendations ────────────────────────────────────────────────────────
export interface Recommendation {
  title: string;
  description: string;
  category: string;
  icon: string;
  estimated_gain: number;
  difficulty: string;
  severity?: string;
}

export interface RecommendRequest {
  cpu_usage: number;
  gpu_usage: number;
  ram_usage: number;
  vram_usage: number;
  fps: number;
  resolution: string;
  game_genre: string;
  graphics_preset: string;
  upscaling_enabled: boolean;
  ray_tracing_enabled: boolean;
  issues?: Array<{ issue_type: string; value?: number }>;
}

export interface RecommendResponse {
  recommendations: Recommendation[];
  total: number;
}

// ─── LLM / Copilot ──────────────────────────────────────────────────────────
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  interactionId?: number;
  feedbackGiven?: boolean;
}

export interface LLMRequest {
  question: string;
  include_telemetry?: boolean;
}

export interface LLMResponse {
  answer: string;
  model: string;
  question?: string;
  telemetry_included?: boolean;
  issues_detected?: number;
  knowledge_sources?: string[];
  response_time_seconds?: number;
  interaction_id?: number;
}

// ─── Analytics ──────────────────────────────────────────────────────────────
export interface AnalyticsTelemetry {
  total_readings: number;
  avg_fps: number;
  avg_cpu_usage: number;
  avg_gpu_usage: number;
  avg_ram_usage: number;
}

export interface AnalyticsPredictions {
  total_predictions: number;
  avg_predicted_fps: number;
  bottleneck_distribution: Record<string, number>;
}

export interface AnalyticsFeedback {
  total_feedback: number;
  helpful_count: number;
  not_helpful_count: number;
  helpful_percentage: number;
}

export interface AnalyticsData {
  status: string;
  telemetry: AnalyticsTelemetry;
  predictions: AnalyticsPredictions;
  feedback: AnalyticsFeedback;
}

// ─── Health ─────────────────────────────────────────────────────────────────
export interface HealthResponse {
  status: string;
  version: string;
  model_loaded: boolean;
  database: string;
  model_name?: string;
}

export interface FeedbackSummary {
  total: number;
  helpful: number;
  not_helpful: number;
  helpful_percentage: number;
}

// ─── Auth (Phase 8) ──────────────────────────────────────────────────────────
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  username: string;
  user_id: number;
}

// ─── Performance (Phase 11) ──────────────────────────────────────────────────
export interface PerformanceEndpoint {
  endpoint: string;
  count:    number;
  avg_ms:   number;
  max_ms:   number;
}

export interface PerformanceSummary {
  status:          string;
  window_hours:    number;
  total_requests:  number;
  avg_duration_ms: number;
  error_count:     number;
  error_rate_pct:  number;
  by_endpoint:     PerformanceEndpoint[];
}

// ─── UI helpers ─────────────────────────────────────────────────────────────
export const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: "#ff4444",
  HIGH:     "#ff8800",
  MEDIUM:   "#ffcc00",
  LOW:      "#44bb44",
};

export const TIER_COLORS: Record<string, string> = {
  Excellent:  "#44bb44",
  Good:       "#88cc44",
  Playable:   "#ffcc00",
  Poor:       "#ff8800",
  Unplayable: "#ff4444",
};