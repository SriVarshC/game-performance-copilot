// ═══════════════════════════════════════════════════════════
// Prediction — FPS prediction form + results
// Calls POST /api/predict with game settings
// ═══════════════════════════════════════════════════════════

import { useState } from "react";
import ReactECharts from "echarts-for-react";
import { postPredict } from "../services/api";
import type { PredictionRequest, PredictionResult } from "../types";
import { TIER_COLORS } from "../types";
import MetricCard from "../components/MetricCard";
import { IconTarget, IconGamepad, IconTrend } from "../icons";

const GENRES = [
  "fps_shooter", "battle_royale", "open_world_rpg",
  "racing", "moba", "rts", "indie_2d",
];
const RESOLUTIONS = ["1280x720", "1920x1080", "2560x1440", "3840x2160"];
const PRESETS = ["low", "medium", "high", "ultra"];
const UPSCALING = [
  "none", "dlss_quality", "dlss_balanced",
  "dlss_performance", "fsr_quality", "fsr_balanced",
];

const DEFAULT_FORM: PredictionRequest = {
  cpu_usage:   45,
  gpu_usage:   78,
  ram_usage:   72,
  vram_usage:  68,
  cpu_temp:    65,
  gpu_temp:    72,
  game_genre:  "fps_shooter",
  resolution:  "1920x1080",
  preset:      "high",
  upscaling:   "none",
  ray_tracing: false,
};

function Prediction() {
  const [form,    setForm]    = useState<PredictionRequest>(DEFAULT_FORM);
  const [result,  setResult]  = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const [heatmapData,    setHeatmapData]    = useState<number[][] | null>(null);
  const [heatmapLoading, setHeatmapLoading] = useState(false);
  const [heatmapError,   setHeatmapError]   = useState<string | null>(null);

  const handleNumber = (key: keyof PredictionRequest, val: string) => {
    setForm((f) => ({ ...f, [key]: val === "" ? 0 : parseFloat(val) }));
  };
  const handleSelect = (key: keyof PredictionRequest, val: string) => {
    setForm((f) => ({ ...f, [key]: val }));
  };
  const handleBool = (key: keyof PredictionRequest, val: boolean) => {
    setForm((f) => ({ ...f, [key]: val }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await postPredict(form);
      setResult(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Prediction failed — is FastAPI running on port 8000?");
    } finally {
      setLoading(false);
    }
  };

  const generateHeatmap = async () => {
    setHeatmapLoading(true);
    setHeatmapError(null);
    setHeatmapData(null);

    try {
      const combos: { resolution: string; preset: string }[] = [];
      RESOLUTIONS.forEach((resolution) => PRESETS.forEach((preset) => combos.push({ resolution, preset })));

      const results = await Promise.all(
        combos.map(({ resolution, preset }) => postPredict({ ...form, resolution, preset }))
      );

      const data: number[][] = results.map((r: PredictionResult, idx: number) => {
        const resIdx    = RESOLUTIONS.indexOf(combos[idx].resolution);
        const presetIdx = PRESETS.indexOf(combos[idx].preset);
        return [resIdx, presetIdx, Math.round(r.predicted_fps)];
      });

      setHeatmapData(data);
    } catch {
      setHeatmapError("Heatmap generation failed — is FastAPI running on port 8000?");
    } finally {
      setHeatmapLoading(false);
    }
  };

  const buildHeatmapOption = (data: number[][]) => ({
    backgroundColor: "transparent",
    tooltip: {
      position: "top",
      backgroundColor: "#131728",
      borderColor: "rgba(255,255,255,0.1)",
      textStyle: { color: "#F1F5F9" },
      formatter: (params: any) => {
        const res    = RESOLUTIONS[params.data[0]];
        const preset = PRESETS[params.data[1]];
        return `${res} · ${preset.toUpperCase()}<br/>Predicted FPS: <b>${params.data[2]}</b>`;
      },
    },
    grid: { top: 10, left: 90, right: 20, bottom: 60 },
    xAxis: {
      type: "category", data: RESOLUTIONS,
      axisLabel: { color: "#8A93A6", fontSize: 11 },
      splitArea: { show: true },
    },
    yAxis: {
      type: "category", data: PRESETS.map((p) => p.toUpperCase()),
      axisLabel: { color: "#8A93A6", fontSize: 11 },
      splitArea: { show: true },
    },
    visualMap: {
      min: 0, max: 200, calculable: true, orient: "horizontal",
      left: "center", bottom: 0,
      textStyle: { color: "#8A93A6", fontSize: 10 },
      inRange: { color: ["#EF4444", "#F59E0B", "#22C55E"] },
    },
    series: [{
      type: "heatmap", data,
      label: { show: true, color: "#fff", fontSize: 11, fontWeight: 700 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.5)" } },
    }],
  });

  const bottleneckColor = (cls: string | null) => {
    if (!cls) return "#8A93A6";
    const map: Record<string, string> = {
      GPU: "#8B5CF6", CPU: "#3B82F6", MEMORY: "#F59E0B", THERMAL: "#EF4444", BALANCED: "#22C55E",
    };
    return map[cls] ?? "#8A93A6";
  };

  const getTierColor = (tier: string): string => {
    const entry = Object.entries(TIER_COLORS).find(([k]) => tier.toLowerCase().includes(k.toLowerCase()));
    return entry ? entry[1] : "#8A93A6";
  };

  const inputStyle: React.CSSProperties = {
    backgroundColor: "rgba(255,255,255,0.04)",
    border: "1px solid var(--border)",
    color: "var(--text)",
    borderRadius: "8px",
    padding: "7px 10px",
    fontSize: "13px",
    width: "100%",
  };

  const labelStyle: React.CSSProperties = {
    fontSize: "11px", color: "var(--text-muted)", fontWeight: 600,
    letterSpacing: "0.5px", textTransform: "uppercase", marginBottom: "4px", display: "block",
  };

  return (
    <div>
      <div className="mb-4 d-flex align-items-center gap-2">
        <IconTarget size={22} color="var(--teal)" />
        <div>
          <h4 style={{ color: "#fff", fontFamily: "var(--font-display)", margin: 0, fontWeight: 700 }}>
            FPS Prediction
          </h4>
          <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
            Enter your hardware metrics + game settings to predict FPS
          </div>
        </div>
      </div>

      <div className="row g-4">
        {/* ── Left — Form ─────────────────────────────── */}
        <div className="col-12 col-lg-5">
          <form onSubmit={handleSubmit}>
            <div className="glass-card p-3">
              <div className="hud-label mb-3">Hardware Metrics</div>

              <div className="row g-2 mb-3">
                {(["cpu_usage", "gpu_usage", "ram_usage", "vram_usage", "cpu_temp", "gpu_temp"] as const).map((key) => (
                  <div className="col-6" key={key}>
                    <label style={labelStyle}>{key.replace(/_/g, " ")}</label>
                    <input
                      type="number" style={inputStyle} value={form[key] ?? ""}
                      min={0} max={key.includes("temp") ? 120 : 100}
                      onChange={(e) => handleNumber(key, e.target.value)}
                    />
                  </div>
                ))}
              </div>

              <div className="hud-label mb-3" style={{ borderTop: "1px solid var(--border)", paddingTop: "12px" }}>
                Game Settings
              </div>

              <div className="row g-2 mb-3">
                <div className="col-12">
                  <label style={labelStyle}>Game Genre</label>
                  <select style={inputStyle} value={form.game_genre} onChange={(e) => handleSelect("game_genre", e.target.value)}>
                    {GENRES.map((g) => (
                      <option key={g} value={g}>{g.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</option>
                    ))}
                  </select>
                </div>
                <div className="col-6">
                  <label style={labelStyle}>Resolution</label>
                  <select style={inputStyle} value={form.resolution} onChange={(e) => handleSelect("resolution", e.target.value)}>
                    {RESOLUTIONS.map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
                <div className="col-6">
                  <label style={labelStyle}>Quality Preset</label>
                  <select style={inputStyle} value={form.preset} onChange={(e) => handleSelect("preset", e.target.value)}>
                    {PRESETS.map((p) => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
                  </select>
                </div>
                <div className="col-12">
                  <label style={labelStyle}>Upscaling</label>
                  <select style={inputStyle} value={form.upscaling} onChange={(e) => handleSelect("upscaling", e.target.value)}>
                    {UPSCALING.map((u) => <option key={u} value={u}>{u.replace(/_/g, " ").toUpperCase()}</option>)}
                  </select>
                </div>
                <div className="col-12">
                  <div className="d-flex align-items-center gap-3 mt-1">
                    <label style={{ ...labelStyle, marginBottom: 0 }}>Ray Tracing</label>
                    <div className="d-flex gap-2">
                      {[true, false].map((val) => (
                        <button
                          key={String(val)} type="button" onClick={() => handleBool("ray_tracing", val)}
                          style={{
                            padding: "5px 16px", borderRadius: "999px", fontSize: "12px", fontWeight: 700,
                            border: "none", cursor: "pointer",
                            background: form.ray_tracing === val
                              ? "linear-gradient(135deg, var(--violet) 0%, var(--violet-2) 100%)"
                              : "rgba(255,255,255,0.05)",
                            color: form.ray_tracing === val ? "#fff" : "var(--text-muted)",
                          }}
                        >
                          {val ? "ON" : "OFF"}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <button
                type="submit" disabled={loading} className="w-100 d-flex align-items-center justify-content-center gap-2"
                style={{
                  background: loading ? "rgba(255,255,255,0.06)" : "linear-gradient(135deg, var(--teal) 0%, var(--violet) 100%)",
                  border: "none", color: "#fff", padding: "11px", borderRadius: "999px",
                  fontWeight: 700, fontSize: "14px", cursor: loading ? "not-allowed" : "pointer",
                  boxShadow: loading ? "none" : "0 4px 20px rgba(139, 92, 246, 0.3)",
                }}
              >
                <IconTarget size={16} color="#fff" />
                {loading ? "Predicting..." : "Predict FPS"}
              </button>

              {error && (
                <div className="mt-3 p-2" style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: "10px", color: "var(--danger)", fontSize: "12px" }}>
                  {error}
                </div>
              )}
            </div>
          </form>

          <div className="glass-card p-3 mt-3">
            <div className="hud-label mb-2">FPS Heatmap</div>
            <div style={{ fontSize: "11px", color: "var(--text-dim)", marginBottom: "10px" }}>
              Predicts FPS across all 16 resolution × preset combinations, using the current genre, upscaling, ray tracing, and hardware metrics above.
            </div>
            <button
              type="button" onClick={generateHeatmap} disabled={heatmapLoading} className="w-100"
              style={{
                background: heatmapLoading ? "rgba(255,255,255,0.06)" : "linear-gradient(135deg, var(--teal) 0%, var(--teal-2) 100%)",
                border: "none", color: "#fff", padding: "9px", borderRadius: "999px",
                fontWeight: 700, fontSize: "13px", cursor: heatmapLoading ? "not-allowed" : "pointer",
              }}
            >
              {heatmapLoading ? "Generating heatmap (16 predictions)..." : "Generate FPS Heatmap"}
            </button>
            {heatmapError && (
              <div className="mt-2 p-2" style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: "10px", color: "var(--danger)", fontSize: "11px" }}>
                {heatmapError}
              </div>
            )}
          </div>
        </div>

        {/* ── Right — Results ─────────────────────────── */}
        <div className="col-12 col-lg-7">
          {!result && !loading && !heatmapData && (
            <div className="d-flex align-items-center justify-content-center" style={{ height: "100%", minHeight: "300px", color: "var(--text-dim)", fontSize: "14px", flexDirection: "column", gap: "12px" }}>
              <IconTarget size={48} color="var(--text-dim)" />
              <span>Fill in the form and click Predict FPS</span>
            </div>
          )}

          {loading && (
            <div className="d-flex align-items-center justify-content-center" style={{ height: "300px", color: "var(--text-muted)", flexDirection: "column", gap: "12px" }}>
              <div className="spinner-border" style={{ color: "var(--teal)" }} role="status" />
              <span>Running LightGBM model...</span>
            </div>
          )}

          {result && (
            <div className="mb-3">
              <div className="row g-3 mb-3">
                <div className="col-6 col-md-3">
                  <MetricCard label="Predicted FPS" value={Math.round(result.predicted_fps)} icon={<IconGamepad size={18} />} color="var(--data-fps)" subtitle="Best estimate" filled />
                </div>
                <div className="col-6 col-md-3">
                  <MetricCard label="1% Low FPS" value={result.low_1pct_fps ? Math.round(result.low_1pct_fps) : null} icon={<IconTrend size={18} />} color="var(--data-vram)" subtitle="Worst-case" />
                </div>
                <div className="col-6 col-md-3">
                  <MetricCard label="Frame Time" value={result.frame_time_ms} unit="ms" icon={<IconTrend size={18} />} color="var(--data-cpu)" subtitle="Per frame" />
                </div>
                <div className="col-6 col-md-3">
                  <MetricCard
                    label="Health Score"
                    value={result.health_score ? Math.round(result.health_score) : null}
                    unit="/100"
                    icon={<IconTrend size={18} />}
                    color={result.health_score ? (result.health_score >= 70 ? "var(--success)" : result.health_score >= 50 ? "var(--warn)" : "var(--danger)") : "var(--text-muted)"}
                    subtitle="System health"
                  />
                </div>
              </div>

              <div className="glass-card p-3 mb-3">
                <div className="d-flex align-items-center justify-content-between flex-wrap gap-3">
                  <div>
                    <div className="hud-label mb-2">Performance Tier</div>
                    <span className="pill" style={{ background: getTierColor(result.performance_tier) + "22", color: getTierColor(result.performance_tier), fontSize: "13px" }}>
                      {result.performance_tier}
                    </span>
                  </div>

                  {result.bottleneck_class && (
                    <div>
                      <div className="hud-label mb-2">Bottleneck</div>
                      <span className="pill" style={{ background: bottleneckColor(result.bottleneck_class) + "22", color: bottleneckColor(result.bottleneck_class), fontSize: "13px" }}>
                        {result.bottleneck_class}
                      </span>
                    </div>
                  )}

                  <div>
                    <div className="hud-label mb-2">Model</div>
                    <span className="pill" style={{ background: "rgba(139,92,246,0.15)", color: "var(--violet)", fontSize: "13px" }}>
                      {result.model_name}
                    </span>
                  </div>
                </div>
              </div>

              <div className="glass-card p-3">
                <div className="hud-label mb-3">FPS Quality Reference</div>
                <div className="d-flex gap-3 flex-wrap">
                  {[
                    { label: "144+ FPS", color: "var(--success)", note: "Excellent" },
                    { label: "60+ FPS", color: "var(--violet)", note: "Smooth" },
                    { label: "30-60 FPS", color: "var(--warn)", note: "Playable" },
                    { label: "<30 FPS", color: "var(--danger)", note: "Unplayable" },
                  ].map((t) => (
                    <div key={t.label} className="d-flex align-items-center gap-2">
                      <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: t.color, flexShrink: 0 }} />
                      <span style={{ color: t.color, fontSize: "12px", fontWeight: 600 }}>{t.label}</span>
                      <span style={{ color: "var(--text-dim)", fontSize: "11px" }}>— {t.note}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {heatmapLoading && (
            <div className="d-flex align-items-center justify-content-center" style={{ height: "200px", color: "var(--text-muted)", flexDirection: "column", gap: "12px" }}>
              <div className="spinner-border" style={{ color: "var(--teal)" }} role="status" />
              <span>Running 16 predictions across the grid...</span>
            </div>
          )}

          {heatmapData && !heatmapLoading && (
            <div className="glass-card p-2">
              <div className="hud-label" style={{ padding: "10px 10px 0" }}>Resolution × Preset FPS Heatmap</div>
              <ReactECharts option={buildHeatmapOption(heatmapData)} style={{ height: "320px", width: "100%" }} opts={{ renderer: "canvas" }} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Prediction;