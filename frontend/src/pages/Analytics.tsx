// ═══════════════════════════════════════════════════════════
// Analytics — Bottleneck analysis + performance stats
// ═══════════════════════════════════════════════════════════

import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { getAnalytics, getPredictionsHistory } from "../services/api";
import type { AnalyticsData } from "../types";
import type { PredictionHistoryItem } from "../services/api";
import MetricCard from "../components/MetricCard";
import { IconAnalytics, IconRadio, IconGamepad, IconCpu, IconGpu, IconTarget, IconThumbsUp, IconRefresh } from "../icons";

const BOTTLENECK_COLORS: Record<string, string> = {
  GPU: "#8B5CF6", CPU: "#3B82F6", MEMORY: "#F59E0B", THERMAL: "#EF4444", BALANCED: "#22C55E",
};

function Analytics() {
  const [data,       setData]       = useState<AnalyticsData | null>(null);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>("--");
  const [healthHistory, setHealthHistory] = useState<PredictionHistoryItem[]>([]);

  const fetchAnalytics = async () => {
    try {
      const res = await getAnalytics();
      setData(res);
      setLastUpdate(new Date().toLocaleTimeString());
      setError(null);
    } catch {
      setError("Cannot reach FastAPI — is the server running on port 8000?");
    } finally {
      setLoading(false);
    }
  };

  const fetchHealthHistory = async () => {
    try {
      const res = await getPredictionsHistory(50);
      setHealthHistory(res.predictions.filter((p) => p.health_score !== null && p.health_score !== undefined));
    } catch {
      // non-fatal
    }
  };

  useEffect(() => {
    fetchAnalytics();
    fetchHealthHistory();
    const interval = setInterval(() => { fetchAnalytics(); fetchHealthHistory(); }, 30000);
    return () => clearInterval(interval);
  }, []);

  const buildPieOption = (dist: Record<string, number>) => {
    const pieData = Object.entries(dist).map(([name, value]) => ({ name, value, itemStyle: { color: BOTTLENECK_COLORS[name] ?? "#8A93A6" } }));
    return {
      backgroundColor: "transparent",
      title: { text: "Bottleneck Distribution", textStyle: { color: "#F1F5F9", fontSize: 13, fontWeight: 600, fontFamily: "Space Grotesk" }, left: 8, top: 8 },
      tooltip: { trigger: "item", backgroundColor: "#131728", borderColor: "rgba(255,255,255,0.1)", textStyle: { color: "#F1F5F9" }, formatter: "{b}: {c} ({d}%)" },
      legend: { orient: "vertical", right: 16, top: "center", textStyle: { color: "#8A93A6", fontSize: 11 }, icon: "circle", itemWidth: 8, itemHeight: 8 },
      series: [{
        type: "pie", radius: ["40%", "70%"], center: ["40%", "55%"],
        data: pieData.length > 0 ? pieData : [{ name: "No data yet", value: 1, itemStyle: { color: "#2A3240" } }],
        label: { show: false },
        emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.5)" } },
      }],
    };
  };

  const buildFeedbackOption = (helpful: number, notHelpful: number) => ({
    backgroundColor: "transparent",
    title: { text: "Recommendation Feedback", textStyle: { color: "#F1F5F9", fontSize: 13, fontWeight: 600, fontFamily: "Space Grotesk" }, left: 8, top: 8 },
    tooltip: { trigger: "axis", backgroundColor: "#131728", borderColor: "rgba(255,255,255,0.1)", textStyle: { color: "#F1F5F9" } },
    grid: { top: 48, left: 48, right: 16, bottom: 32 },
    xAxis: { type: "category", data: ["Helpful", "Not Helpful"], axisLabel: { color: "#8A93A6", fontSize: 12 }, axisLine: { lineStyle: { color: "rgba(255,255,255,0.1)" } } },
    yAxis: { type: "value", axisLabel: { color: "#565F73", fontSize: 10 }, splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)", type: "dashed" } } },
    series: [{
      type: "bar",
      data: [
        { value: helpful, itemStyle: { color: "#22C55E", borderRadius: [6, 6, 0, 0] } },
        { value: notHelpful, itemStyle: { color: "#EF4444", borderRadius: [6, 6, 0, 0] } },
      ],
      barMaxWidth: 60,
    }],
  });

  const buildHealthHistoryOption = (history: PredictionHistoryItem[]) => {
    const times  = history.map((h) => (h.created_at ? new Date(h.created_at).toLocaleTimeString() : ""));
    const scores = history.map((h) => h.health_score ?? 0);
    return {
      backgroundColor: "transparent",
      title: { text: "Health Score Over Time", textStyle: { color: "#F1F5F9", fontSize: 13, fontWeight: 600, fontFamily: "Space Grotesk" }, left: 8, top: 8 },
      tooltip: {
        trigger: "axis", backgroundColor: "#131728", borderColor: "rgba(255,255,255,0.1)", textStyle: { color: "#F1F5F9" },
        formatter: (params: any) => { const p = params[0]; return `${p.axisValue}<br/>Health Score: <b>${p.value}</b>/100`; },
      },
      grid: { top: 48, left: 40, right: 16, bottom: 56 },
      xAxis: { type: "category", data: times, axisLabel: { color: "#565F73", fontSize: 9, rotate: 45 }, axisLine: { lineStyle: { color: "rgba(255,255,255,0.1)" } } },
      yAxis: { type: "value", min: 0, max: 100, axisLabel: { color: "#565F73", fontSize: 10 }, splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)", type: "dashed" } } },
      series: [{
        type: "bar", data: scores, barMaxWidth: 18,
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: (params: any) => {
            const v = params.value as number;
            if (v >= 70) return "#22C55E";
            if (v >= 50) return "#F59E0B";
            return "#EF4444";
          },
        },
      }],
    };
  };

  if (loading) {
    return (
      <div className="d-flex align-items-center justify-content-center" style={{ height: "60vh", color: "var(--text-muted)" }}>
        <div className="text-center">
          <div className="spinner-border mb-3" style={{ color: "var(--teal)" }} role="status" />
          <div>Loading analytics...</div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="d-flex align-items-center justify-content-between mb-4">
        <div className="d-flex align-items-center gap-2">
          <IconAnalytics size={22} color="var(--teal)" />
          <div>
            <h4 style={{ color: "#fff", fontFamily: "var(--font-display)", margin: 0, fontWeight: 700 }}>Analytics</h4>
            <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
              Aggregated performance data · Last update: {lastUpdate}
            </div>
          </div>
        </div>
        <button
          onClick={() => { fetchAnalytics(); fetchHealthHistory(); }}
          className="d-flex align-items-center gap-1"
          style={{ background: "rgba(255,255,255,0.04)", color: "var(--text-muted)", border: "1px solid var(--border)", fontSize: "12px", padding: "6px 14px", borderRadius: "999px" }}
        >
          <IconRefresh size={12} /> Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3" style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: "14px", color: "var(--danger)", fontSize: "13px" }}>
          {error}
        </div>
      )}

      {data && (
        <>
          <div className="row g-3 mb-4">
            <div className="col-6 col-md-4 col-lg-2">
              <MetricCard label="Readings" value={data.telemetry.total_readings} icon={<IconRadio size={16} />} color="var(--violet)" subtitle="Total telemetry" filled />
            </div>
            <div className="col-6 col-md-4 col-lg-2">
              <MetricCard label="Avg FPS" value={Math.round(data.telemetry.avg_fps)} icon={<IconGamepad size={16} />} color="var(--data-fps)" subtitle="All sessions" />
            </div>
            <div className="col-6 col-md-4 col-lg-2">
              <MetricCard label="Avg CPU" value={Math.round(data.telemetry.avg_cpu_usage)} unit="%" icon={<IconCpu size={16} />} color="var(--data-cpu)" subtitle="i7-12650H" />
            </div>
            <div className="col-6 col-md-4 col-lg-2">
              <MetricCard label="Avg GPU" value={Math.round(data.telemetry.avg_gpu_usage)} unit="%" icon={<IconGpu size={16} />} color="var(--data-gpu)" subtitle="RTX 3050 Ti" />
            </div>
            <div className="col-6 col-md-4 col-lg-2">
              <MetricCard label="Predictions" value={data.predictions.total_predictions} icon={<IconTarget size={16} />} color="var(--data-vram)" subtitle="Total runs" />
            </div>
            <div className="col-6 col-md-4 col-lg-2">
              <MetricCard label="Helpful %" value={Math.round(data.feedback.helpful_percentage)} unit="%" icon={<IconThumbsUp size={16} />} color="var(--success)" subtitle="Feedback rate" />
            </div>
          </div>

          <div className="row g-3 mb-4">
            <div className="col-12 col-lg-6">
              <div className="glass-card" style={{ padding: "8px" }}>
                <ReactECharts option={buildPieOption(data.predictions.bottleneck_distribution)} style={{ height: "280px", width: "100%" }} opts={{ renderer: "canvas" }} />
              </div>
            </div>
            <div className="col-12 col-lg-6">
              <div className="glass-card" style={{ padding: "8px" }}>
                <ReactECharts option={buildFeedbackOption(data.feedback.helpful_count, data.feedback.not_helpful_count)} style={{ height: "280px", width: "100%" }} opts={{ renderer: "canvas" }} />
              </div>
            </div>
          </div>

          <div className="row g-3 mb-4">
            <div className="col-12">
              <div className="glass-card" style={{ padding: "8px" }}>
                {healthHistory.length > 0 ? (
                  <ReactECharts option={buildHealthHistoryOption(healthHistory)} style={{ height: "260px", width: "100%" }} opts={{ renderer: "canvas" }} />
                ) : (
                  <div className="d-flex align-items-center justify-content-center" style={{ height: "260px", color: "var(--text-dim)", fontSize: "13px" }}>
                    No prediction history yet — run some predictions on the Prediction page
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="row g-3">
            <div className="col-12">
              <div className="glass-card p-3">
                <div className="hud-label mb-3">Bottleneck Class Reference</div>
                <div className="d-flex flex-wrap gap-3">
                  {Object.entries({
                    GPU: "Pixel fill rate limited — lower resolution or reduce shadows",
                    CPU: "Simulation/AI limited — close background apps",
                    MEMORY: "VRAM/RAM pressure — lower textures or enable upscaling",
                    THERMAL: "Throttling detected — improve cooling",
                    BALANCED: "No single bottleneck — system is well balanced",
                  }).map(([key, desc]) => (
                    <div key={key} style={{ minWidth: "200px", flex: 1 }}>
                      <div className="d-flex align-items-center gap-2 mb-1">
                        <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: BOTTLENECK_COLORS[key], flexShrink: 0 }} />
                        <span style={{ color: BOTTLENECK_COLORS[key], fontWeight: 700, fontSize: "12px" }}>{key}</span>
                      </div>
                      <div style={{ fontSize: "11px", color: "var(--text-dim)", paddingLeft: "16px" }}>{desc}</div>
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