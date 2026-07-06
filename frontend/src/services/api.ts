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
} from "../types";

const api = axios.create({
  baseURL: "http://localhost:8000/api",
  timeout: 30000,
});

// ─── Health ──────────────────────────────────────────────────────────────────
export const getHealth = async (): Promise<HealthResponse> => {
  const res = await api.get("/health");
  return res.data;
};

// ─── Telemetry ───────────────────────────────────────────────────────────────
export const getTelemetry = async (): Promise<TelemetryData> => {
  const res = await api.get("/telemetry");
  // Handle both wrapped {status, data:{...}} and direct {...} responses
  return (res.data?.data as TelemetryData) ?? (res.data as TelemetryData);
};

export const getTelemetryHistory = async (
  hours = 1,
  limit = 60
): Promise<TelemetryHistory> => {
  const res = await api.get("/telemetry/history", {
    params: { hours, limit },
  });
  return (res.data?.data as TelemetryHistory) ?? (res.data as TelemetryHistory);
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
  const res = await api.post("/llm/ask", data);
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

// ─── Analytics ───────────────────────────────────────────────────────────────
export const getAnalytics = async (): Promise<AnalyticsData> => {
  const res = await api.get("/analytics");
  return res.data as AnalyticsData;
};