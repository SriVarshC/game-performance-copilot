import axios from "axios";
import type {
  TelemetryData,
  TelemetryHistory,
  PredictionRequest,
  PredictionResult,
  RecommendRequest,
  RecommendResponse,
  LLMRequest,
  LLMResponse,
  AnalyticsData,
  FeedbackSummary,
  HealthResponse,
  RegisterRequest,
  LoginRequest,
  TokenResponse,
  PerformanceSummary,
} from "../types";

const api = axios.create({
  baseURL: "http://localhost:8000/api",
  timeout: 30000,
});

// Copilot requests can run much slower when Ollama is running inside
// Docker without confirmed GPU-accelerated inference (CPU-tier token
// speeds on a RAG-enriched ~1200 token prompt can take 60-90s). A
// separate, longer-timeout instance is used only for /llm/ask so the
// rest of the app keeps a snappy 30s timeout.
const llmApi = axios.create({
  baseURL: "http://localhost:8000/api",
  timeout: 120000,
});

const attachAuth = (config: any) => {
  const token = localStorage.getItem("gc_token");
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
};

const handle401 = (error: any) => {
  if (error?.response?.status === 401) {
    localStorage.removeItem("gc_token");
    localStorage.removeItem("gc_username");
    if (window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  }
  return Promise.reject(error);
};

// ─── Phase 8: attach JWT to every outgoing request ──────────────────────────
api.interceptors.request.use(attachAuth);
llmApi.interceptors.request.use(attachAuth);

// ─── Phase 8: on 401, clear stale token and bounce to login ─────────────────
api.interceptors.response.use((response) => response, handle401);
llmApi.interceptors.response.use((response) => response, handle401);

// ─── Auth ────────────────────────────────────────────────────────────────────
export const postRegister = async (data: RegisterRequest): Promise<TokenResponse> => {
  const res = await api.post("/auth/register", data);
  return res.data as TokenResponse;
};

export const postLogin = async (data: LoginRequest): Promise<TokenResponse> => {
  const res = await api.post("/auth/login", data);
  return res.data as TokenResponse;
};

// ─── Health ──────────────────────────────────────────────────────────────────
export const getHealth = async (): Promise<HealthResponse> => {
  const res = await api.get("/health");
  return res.data;
};

// ─── Telemetry ───────────────────────────────────────────────────────────────
export const getTelemetry = async (): Promise<TelemetryData> => {
  const res = await api.get("/telemetry");
  return (res.data?.data as TelemetryData) ?? (res.data as TelemetryData);
};

// Backend returns { history: [{fps, timestamp, cpu_usage, ...}, ...], count }
// — an array of per-reading objects. The frontend's TelemetryHistory type
// expects parallel arrays instead ({timestamps: [], fps: [], ...}), so we
// transform the shape here rather than changing every chart consumer.
export const getTelemetryHistory = async (
  hours = 1,
  limit = 60
): Promise<TelemetryHistory> => {
  const res = await api.get("/telemetry/history", {
    params: { hours, limit },
  });

  const raw = res.data?.data ?? res.data;
  const rows: any[] = raw?.history ?? [];

  return {
    timestamps: rows.map((r) => r.timestamp),
    fps:        rows.map((r) => r.fps ?? 0),
    cpu_usage:  rows.map((r) => r.cpu_usage ?? 0),
    gpu_usage:  rows.map((r) => r.gpu_usage ?? 0),
    ram_usage:  rows.map((r) => r.ram_usage ?? 0),
  };
};

export const getTelemetryDiagnostics = async () => {
  const res = await api.get("/telemetry/diagnostics");
  return res.data;
};

// ─── Prediction ──────────────────────────────────────────────────────────────
export const postPredict = async (
  data: PredictionRequest
): Promise<PredictionResult> => {
  const res = await api.post("/predict", data);
  return res.data as PredictionResult;
};

// ─── Recommendations ─────────────────────────────────────────────────────────
export const postRecommend = async (
  data: RecommendRequest
): Promise<RecommendResponse> => {
  const res = await api.post("/recommend", data);
  return res.data as RecommendResponse;
};

// ─── LLM ─────────────────────────────────────────────────────────────────────
export const postLLMQuestion = async (
  data: LLMRequest
): Promise<LLMResponse> => {
  const res = await llmApi.post("/llm/ask", data);
  return res.data as LLMResponse;
};

// ─── Feedback ────────────────────────────────────────────────────────────────
export const postFeedback = async (
  id: number,
  helpful: boolean
): Promise<void> => {
  await api.post(`/feedback/${id}`, { helpful });
};

export const getFeedbackSummary = async (): Promise<FeedbackSummary> => {
  const res = await api.get("/feedback/summary");
  return res.data as FeedbackSummary;
};

// ─── Copilot Feedback ────────────────────────────────────────────────────────
export const postCopilotFeedback = async (
  interactionId: number,
  wasHelpful: boolean
): Promise<void> => {
  await api.post(`/llm/feedback/${interactionId}`, { was_helpful: wasHelpful });
};

// ─── Analytics ───────────────────────────────────────────────────────────────
export const getAnalytics = async (): Promise<AnalyticsData> => {
  const res = await api.get("/analytics");
  return res.data as AnalyticsData;
};

// ─── Prediction History (Phase 2 — health score over time) ─────────────────
export interface PredictionHistoryItem {
  created_at:       string;
  health_score:     number | null;
  predicted_fps:    number | null;
  bottleneck_class: string | null;
}

export interface PredictionHistoryResponse {
  status:      string;
  predictions: PredictionHistoryItem[];
}

export const getPredictionsHistory = async (
  limit = 50
): Promise<PredictionHistoryResponse> => {
  const res = await api.get("/predictions/history", { params: { limit } });
  return res.data as PredictionHistoryResponse;
};

// ─── Performance (Phase 11) ───────────────────────────────────────────────────
export const getPerformanceSummary = async (
  hours = 24
): Promise<PerformanceSummary> => {
  const res = await api.get("/performance/summary", { params: { hours } });
  return res.data as PerformanceSummary;
};