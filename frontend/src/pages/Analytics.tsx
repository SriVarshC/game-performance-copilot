// ═══════════════════════════════════════════════════════════
// Analytics — Bottleneck analysis + performance stats
// Polls /api/analytics every 30 seconds
// ═══════════════════════════════════════════════════════════

import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { getAnalytics } from "../services/api";
import type { AnalyticsData } from "../types";
import MetricCard from "../components/MetricCard";

// ── Bottleneck colors ────────────────────────────────────────
const BOTTLENECK_COLORS: Record<string, string> = {
  GPU:      "#0dcaf0",
  CPU:      "#6f42c1",
  MEMORY:   "#fd7e14",
  THERMAL:  "#dc3545",
  BALANCED: "#198754",
};

function Analytics() {
  const [data,       setData]       = useState<AnalyticsData | null>(null);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>("--");

  const fetchAnalytics = async () => {
    try {
      const res = await getAnalytics(); // res IS AnalyticsData — no .data needed
      setData(res);
      setLastUpdate(new Date().toLocaleTimeString());
      setError(null);
    } catch {
      setError("Cannot reach FastAPI — is the server running on port 8000?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000);
    return () => clearInterval(interval);
  }, []);

  // ── Bottleneck Pie Chart ───────────────────────────────────
  const buildPieOption = (dist: Record<string, number>) => {
    const pieData = Object.entries(dist).map(([name, value]) => ({
      name,
      value,
      itemStyle: { color: BOTTLENECK_COLORS[name] ?? "#888" },
    }));

    return {
      backgroundColor: "transparent",
      title: {
        text: "Bottleneck Distribution",
        textStyle: { color: "#ccc", fontSize: 13, fontWeight: 600 },
        left: 8,
        top: 8,
      },
      tooltip: {
        trigger: "item",
        backgroundColor: "#22252e",
        borderColor: "#2a2d35",
        textStyle: { color: "#e0e0e0" },
        formatter: "{b}: {c} ({d}%)",
      },
      legend: {
        orient: "vertical",
        right: 16,
        top: "center",
        textStyle: { color: "#888", fontSize: 11 },
        icon: "circle",
        itemWidth: 8,
        itemHeight: 8,
      },
      series: [
        {
          type: "pie",
          radius: ["40%", "70%"],
          center: ["40%", "55%"],
          data: pieData.length > 0 ? pieData : [{ name: "No data yet", value: 1, itemStyle: { color: "#333" } }],
          label: { show: false },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: "rgba(0,0,0,0.5)",
            },
          },
        },
      ],
    };
  };

  // ── Feedback Bar Chart ─────────────────────────────────────
  const buildFeedbackOption = (helpful: number, notHelpful: number) => ({
    backgroundColor: "transparent",
    title: {
      text: "Recommendation Feedback",
      textStyle: { color: "#ccc", fontSize: 13, fontWeight: 600 },
      left: 8,
      top: 8,
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#22252e",
      borderColor: "#2a2d35",
      textStyle: { color: "#e0e0e0" },
    },
    grid: { top: 48, left: 48, right: 16, bottom: 32 },
    xAxis: {
      type: "category",
      data: ["Helpful 👍", "Not Helpful 👎"],
      axisLabel: { color: "#888", fontSize: 12 },
      axisLine:  { lineStyle: { color: "#2a2d35" } },
    },
    yAxis: {
      type: "value",
      axisLabel:  { color: "#666", fontSize: 10 },
      splitLine:  { lineStyle: { color: "#2a2d35", type: "dashed" } },
    },
    series: [
      {
        type: "bar",
        data: [
          { value: helpful,    itemStyle: { color: "#198754", borderRadius: [4,4,0,0] } },
          { value: notHelpful, itemStyle: { color: "#dc3545", borderRadius: [4,4,0,0] } },
        ],
        barMaxWidth: 60,
      },
    ],
  });

  // ── Loading state ──────────────────────────────────────────
  if (loading) {
    return (
      <div
        className="d-flex align-items-center justify-content-center"
        style={{ height: "60vh", color: "#888" }}
      >
        <div className="text-center">
          <div className="spinner-border text-secondary mb-3" role="status" />
          <div>Loading analytics...</div>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* ── Page header ───────────────────────────────────── */}
      <div className="d-flex align-items-center justify-content-between mb-4">
        <div>
          <h4 style={{ color: "#fff", margin: 0, fontWeight: 700 }}>
            🔍 Analytics
          </h4>
          <div style={{ fontSize: "12px", color: "#666", marginTop: "4px" }}>
            Aggregated performance data · Last update: {lastUpdate}
          </div>
        </div>
        <button
          className="btn btn-sm"
          onClick={fetchAnalytics}
          style={{
            backgroundColor: "#22252e",
            color: "#888",
            border: "1px solid #2a2d35",
            fontSize: "12px",
          }}
        >
          🔄 Refresh
        </button>
      </div>

      {/* ── Error banner ──────────────────────────────────── */}
      {error && (
        <div
          className="mb-4 p-3"
          style={{
            backgroundColor: "#2a1215",
            border: "1px solid #dc3545",
            borderRadius: "8px",
            color: "#dc3545",
            fontSize: "13px",
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {data && (
        <>
          {/* ── Stats Row ─────────────────────────────────── */}
          <div className="row g-3 mb-4">
            <div className="col-6 col-md-4 col-lg-2">
              <MetricCard
                label="Readings"
                value={data.telemetry.total_readings}
                icon="📡"
                color="#6f42c1"
                subtitle="Total telemetry"
              />
            </div>
            <div className="col-6 col-md-4 col-lg-2">
              <MetricCard
                label="Avg FPS"
                value={Math.round(data.telemetry.avg_fps)}
                icon="🎮"
                color="#198754"
                subtitle="All sessions"
              />
            </div>
            <div className="col-6 col-md-4 col-lg-2">
              <MetricCard
                label="Avg CPU"
                value={Math.round(data.telemetry.avg_cpu_usage)}
                unit="%"
                icon="🖥️"
                color="#6f42c1"
                subtitle="i7-12650H"
              />
            </div>
            <div className="col-6 col-md-4 col-lg-2">
              <MetricCard
                label="Avg GPU"
                value={Math.round(data.telemetry.avg_gpu_usage)}
                unit="%"
                icon="🎴"
                color="#0dcaf0"
                subtitle="RTX 3050 Ti"
              />
            </div>
            <div className="col-6 col-md-4 col-lg-2">
              <MetricCard
                label="Predictions"
                value={data.predictions.total_predictions}
                icon="🎯"
                color="#ffc107"
                subtitle="Total runs"
              />
            </div>
            <div className="col-6 col-md-4 col-lg-2">
              <MetricCard
                label="Helpful %"
                value={Math.round(data.feedback.helpful_percentage)}
                unit="%"
                icon="👍"
                color="#198754"
                subtitle="Feedback rate"
              />
            </div>
          </div>

          {/* ── Charts Row ────────────────────────────────── */}
          <div className="row g-3 mb-4">
            {/* Bottleneck Pie */}
            <div className="col-12 col-lg-6">
              <div
                className="card"
                style={{
                  backgroundColor: "#1a1d23",
                  border: "1px solid #2a2d35",
                  borderRadius: "10px",
                  padding: "8px",
                }}
              >
                <ReactECharts
                  option={buildPieOption(
                    data.predictions.bottleneck_distribution
                  )}
                  style={{ height: "280px", width: "100%" }}
                  opts={{ renderer: "canvas" }}
                />
              </div>
            </div>

            {/* Feedback Bar */}
            <div className="col-12 col-lg-6">
              <div
                className="card"
                style={{
                  backgroundColor: "#1a1d23",
                  border: "1px solid #2a2d35",
                  borderRadius: "10px",
                  padding: "8px",
                }}
              >
                <ReactECharts
                  option={buildFeedbackOption(
                    data.feedback.helpful_count,
                    data.feedback.not_helpful_count
                  )}
                  style={{ height: "280px", width: "100%" }}
                  opts={{ renderer: "canvas" }}
                />
              </div>
            </div>
          </div>

          {/* ── Bottleneck Legend ─────────────────────────── */}
          <div className="row g-3">
            <div className="col-12">
              <div
                className="card p-3"
                style={{
                  backgroundColor: "#1a1d23",
                  border: "1px solid #2a2d35",
                  borderRadius: "10px",
                }}
              >
                <div style={{
                  fontSize: "11px", color: "#666",
                  fontWeight: 700, letterSpacing: "1px",
                  textTransform: "uppercase", marginBottom: "12px",
                }}>
                  Bottleneck Class Reference
                </div>
                <div className="d-flex flex-wrap gap-3">
                  {Object.entries({
                    GPU:      "Pixel fill rate limited — lower resolution or reduce shadows",
                    CPU:      "Simulation/AI limited — close background apps",
                    MEMORY:   "VRAM/RAM pressure — lower textures or enable upscaling",
                    THERMAL:  "Throttling detected — improve cooling",
                    BALANCED: "No single bottleneck — system is well balanced",
                  }).map(([key, desc]) => (
                    <div key={key} style={{ minWidth: "200px", flex: 1 }}>
                      <div className="d-flex align-items-center gap-2 mb-1">
                        <div style={{
                          width: "10px", height: "10px",
                          borderRadius: "50%",
                          backgroundColor: BOTTLENECK_COLORS[key],
                          flexShrink: 0,
                        }} />
                        <span style={{
                          color: BOTTLENECK_COLORS[key],
                          fontWeight: 700,
                          fontSize: "12px",
                        }}>
                          {key}
                        </span>
                      </div>
                      <div style={{
                        fontSize: "11px", color: "#666",
                        paddingLeft: "18px",
                      }}>
                        {desc}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default Analytics;