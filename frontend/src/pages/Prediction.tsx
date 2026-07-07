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

// ── Form option lists ────────────────────────────────────────
const GENRES = [
  "fps_shooter", "battle_royale", "open_world_rpg",
  "racing", "moba", "rts", "indie_2d",
];
const RESOLUTIONS = [
  "1280x720", "1920x1080", "2560x1440", "3840x2160",
];
const PRESETS = ["low", "medium", "high", "ultra"];
const UPSCALING = [
  "none", "dlss_quality", "dlss_balanced",
  "dlss_performance", "fsr_quality", "fsr_balanced",
];

// ── Default form values (RTX 3050 Ti typical session) ────────
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

  // ── Phase 2: FPS heatmap state ─────────────────────────────
  const [heatmapData,    setHeatmapData]    = useState<number[][] | null>(null);
  const [heatmapLoading, setHeatmapLoading] = useState(false);
  const [heatmapError,   setHeatmapError]   = useState<string | null>(null);

  // ── Input handlers ────────────────────────────────────────
  const handleNumber = (key: keyof PredictionRequest, val: string) => {
    setForm((f) => ({ ...f, [key]: val === "" ? 0 : parseFloat(val) }));
  };

  const handleSelect = (key: keyof PredictionRequest, val: string) => {
    setForm((f) => ({ ...f, [key]: val }));
  };

  const handleBool = (key: keyof PredictionRequest, val: boolean) => {
    setForm((f) => ({ ...f, [key]: val }));
  };

  // ── Submit ────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // form field names match backend PredictRequest exactly
      const data = await postPredict(form);
      setResult(data); // postPredict returns PredictionResult directly
    } catch (err: any) {
      if (err?.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Prediction failed — is FastAPI running on port 8000?");
      }
    } finally {
      setLoading(false);
    }
  };

  // ── Phase 2: Generate heatmap ───────────────────────────────
  // Fires one prediction per (resolution, preset) combination, holding
  // genre / upscaling / ray tracing / hardware metrics fixed at current
  // form values. Renders predicted FPS as a color-graded ECharts heatmap.
  const generateHeatmap = async () => {
    setHeatmapLoading(true);
    setHeatmapError(null);
    setHeatmapData(null);

    try {
      const combos: { resolution: string; preset: string }[] = [];
      RESOLUTIONS.forEach((resolution) =>
        PRESETS.forEach((preset) => combos.push({ resolution, preset }))
      );

      const results = await Promise.all(
        combos.map(({ resolution, preset }) =>
          postPredict({ ...form, resolution, preset })
        )
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
      backgroundColor: "#22252e",
      borderColor: "#2a2d35",
      textStyle: { color: "#e0e0e0" },
      formatter: (params: any) => {
        const res    = RESOLUTIONS[params.data[0]];
        const preset = PRESETS[params.data[1]];
        return `${res} · ${preset.toUpperCase()}<br/>Predicted FPS: <b>${params.data[2]}</b>`;
      },
    },
    grid: { top: 10, left: 90, right: 20, bottom: 60 },
    xAxis: {
      type: "category",
      data: RESOLUTIONS,
      axisLabel: { color: "#888", fontSize: 11 },
      splitArea: { show: true },
    },
    yAxis: {
      type: "category",
      data: PRESETS.map((p) => p.toUpperCase()),
      axisLabel: { color: "#888", fontSize: 11 },
      splitArea: { show: true },
    },
    visualMap: {
      min: 0,
      max: 200,
      calculable: true,
      orient: "horizontal",
      left: "center",
      bottom: 0,
      textStyle: { color: "#888", fontSize: 10 },
      inRange: { color: ["#dc3545", "#ffc107", "#198754"] },
    },
    series: [
      {
        type: "heatmap",
        data,
        label: { show: true, color: "#fff", fontSize: 11, fontWeight: 700 },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: "rgba(0,0,0,0.5)" },
        },
      },
    ],
  });

  // ── Bottleneck badge color ────────────────────────────────
  const bottleneckColor = (cls: string | null) => {
    if (!cls) return "#888";
    const map: Record<string, string> = {
      GPU:      "#0dcaf0",
      CPU:      "#6f42c1",
      MEMORY:   "#fd7e14",
      THERMAL:  "#dc3545",
      BALANCED: "#198754",
    };
    return map[cls] ?? "#888";
  };

  // ── Tier color lookup (strips emoji from key) ─────────────
  const getTierColor = (tier: string): string => {
    const entry = Object.entries(TIER_COLORS).find(([k]) =>
      tier.toLowerCase().includes(k.toLowerCase())
    );
    return entry ? entry[1] : "#888";
  };

  // ── Input style helper ────────────────────────────────────
  const inputStyle: React.CSSProperties = {
    backgroundColor: "#22252e",
    border: "1px solid #2a2d35",
    color: "#e0e0e0",
    borderRadius: "6px",
    padding: "6px 10px",
    fontSize: "13px",
    width: "100%",
  };

  const labelStyle: React.CSSProperties = {
    fontSize: "11px",
    color: "#888",
    fontWeight: 600,
    letterSpacing: "0.5px",
    textTransform: "uppercase",
    marginBottom: "4px",
    display: "block",
  };

  return (
    <div>
      {/* ── Page header ───────────────────────────────────── */}
      <div className="mb-4">
        <h4 style={{ color: "#fff", margin: 0, fontWeight: 700 }}>
          🎯 FPS Prediction
        </h4>
        <div style={{ fontSize: "12px", color: "#666", marginTop: "4px" }}>
          Enter your hardware metrics + game settings to predict FPS
        </div>
      </div>

      <div className="row g-4">

        {/* ── Left — Form ───────────────────────────────── */}
        <div className="col-12 col-lg-5">
          <form onSubmit={handleSubmit}>
            <div
              className="card p-3"
              style={{
                backgroundColor: "#1a1d23",
                border: "1px solid #2a2d35",
                borderRadius: "10px",
              }}
            >

              {/* Hardware metrics section header */}
              <div style={{
                fontSize: "11px", color: "#555",
                fontWeight: 700, letterSpacing: "1px",
                textTransform: "uppercase", marginBottom: "12px",
              }}>
                Hardware Metrics
              </div>

              <div className="row g-2 mb-3">
                {(["cpu_usage", "gpu_usage", "ram_usage", "vram_usage",
                   "cpu_temp", "gpu_temp"] as const).map((key) => (
                  <div className="col-6" key={key}>
                    <label style={labelStyle}>
                      {key.replace(/_/g, " ")}
                    </label>
                    <input
                      type="number"
                      style={inputStyle}
                      value={form[key] ?? ""}
                      min={0}
                      max={key.includes("temp") ? 120 : 100}
                      onChange={(e) => handleNumber(key, e.target.value)}
                    />
                  </div>
                ))}
              </div>

              {/* Game settings section header */}
              <div style={{
                fontSize: "11px", color: "#555",
                fontWeight: 700, letterSpacing: "1px",
                textTransform: "uppercase",
                marginBottom: "12px",
                borderTop: "1px solid #2a2d35",
                paddingTop: "12px",
              }}>
                Game Settings
              </div>

              <div className="row g-2 mb-3">

                {/* Genre */}
                <div className="col-12">
                  <label style={labelStyle}>Game Genre</label>
                  <select
                    style={inputStyle}
                    value={form.game_genre}
                    onChange={(e) => handleSelect("game_genre", e.target.value)}
                  >
                    {GENRES.map((g) => (
                      <option key={g} value={g}>
                        {g.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Resolution */}
                <div className="col-6">
                  <label style={labelStyle}>Resolution</label>
                  <select
                    style={inputStyle}
                    value={form.resolution}
                    onChange={(e) => handleSelect("resolution", e.target.value)}
                  >
                    {RESOLUTIONS.map((r) => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                </div>

                {/* Preset */}
                <div className="col-6">
                  <label style={labelStyle}>Quality Preset</label>
                  <select
                    style={inputStyle}
                    value={form.preset}
                    onChange={(e) => handleSelect("preset", e.target.value)}
                  >
                    {PRESETS.map((p) => (
                      <option key={p} value={p}>
                        {p.charAt(0).toUpperCase() + p.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Upscaling */}
                <div className="col-12">
                  <label style={labelStyle}>Upscaling</label>
                  <select
                    style={inputStyle}
                    value={form.upscaling}
                    onChange={(e) => handleSelect("upscaling", e.target.value)}
                  >
                    {UPSCALING.map((u) => (
                      <option key={u} value={u}>
                        {u.replace(/_/g, " ").toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Ray Tracing toggle */}
                <div className="col-12">
                  <div className="d-flex align-items-center gap-3 mt-1">
                    <label style={{ ...labelStyle, marginBottom: 0 }}>
                      Ray Tracing
                    </label>
                    <div className="d-flex gap-2">
                      {[true, false].map((val) => (
                        <button
                          key={String(val)}
                          type="button"
                          onClick={() => handleBool("ray_tracing", val)}
                          style={{
                            padding: "4px 14px",
                            borderRadius: "6px",
                            fontSize: "12px",
                            fontWeight: 600,
                            border: "1px solid",
                            cursor: "pointer",
                            backgroundColor:
                              form.ray_tracing === val ? "#6f42c1" : "#22252e",
                            borderColor:
                              form.ray_tracing === val ? "#6f42c1" : "#2a2d35",
                            color:
                              form.ray_tracing === val ? "#fff" : "#888",
                          }}
                        >
                          {val ? "ON" : "OFF"}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Submit button */}
              <button
                type="submit"
                disabled={loading}
                className="w-100"
                style={{
                  backgroundColor: loading ? "#2a2d35" : "#6f42c1",
                  border: "none",
                  color: "#fff",
                  padding: "10px",
                  borderRadius: "8px",
                  fontWeight: 700,
                  fontSize: "14px",
                  cursor: loading ? "not-allowed" : "pointer",
                  marginTop: "4px",
                }}
              >
                {loading ? "⏳ Predicting..." : "🎯 Predict FPS"}
              </button>

              {/* Error message */}
              {error && (
                <div
                  className="mt-3 p-2"
                  style={{
                    backgroundColor: "#2a1215",
                    border: "1px solid #dc3545",
                    borderRadius: "6px",
                    color: "#dc3545",
                    fontSize: "12px",
                  }}
                >
                  ⚠️ {error}
                </div>
              )}
            </div>
          </form>

          {/* ── Phase 2: Heatmap trigger card ─────────────── */}
          <div
            className="card p-3 mt-3"
            style={{
              backgroundColor: "#1a1d23",
              border: "1px solid #2a2d35",
              borderRadius: "10px",
            }}
          >
            <div style={{
              fontSize: "11px", color: "#555",
              fontWeight: 700, letterSpacing: "1px",
              textTransform: "uppercase", marginBottom: "8px",
            }}>
              FPS Heatmap
            </div>
            <div style={{ fontSize: "11px", color: "#666", marginBottom: "10px" }}>
              Predicts FPS across all 16 resolution × preset combinations,
              using the current genre, upscaling, ray tracing, and hardware
              metrics above.
            </div>
            <button
              type="button"
              onClick={generateHeatmap}
              disabled={heatmapLoading}
              className="w-100"
              style={{
                backgroundColor: heatmapLoading ? "#2a2d35" : "#0dcaf0",
                border: "none",
                color: heatmapLoading ? "#888" : "#0a0a0a",
                padding: "8px",
                borderRadius: "8px",
                fontWeight: 700,
                fontSize: "13px",
                cursor: heatmapLoading ? "not-allowed" : "pointer",
              }}
            >
              {heatmapLoading ? "⏳ Generating heatmap (16 predictions)..." : "🗺️ Generate FPS Heatmap"}
            </button>
            {heatmapError && (
              <div
                className="mt-2 p-2"
                style={{
                  backgroundColor: "#2a1215",
                  border: "1px solid #dc3545",
                  borderRadius: "6px",
                  color: "#dc3545",
                  fontSize: "11px",
                }}
              >
                ⚠️ {heatmapError}
              </div>
            )}
          </div>
        </div>

        {/* ── Right — Results ───────────────────────────── */}
        <div className="col-12 col-lg-7">

          {/* Empty state */}
          {!result && !loading && !heatmapData && (
            <div
              className="d-flex align-items-center justify-content-center"
              style={{
                height: "100%",
                minHeight: "300px",
                color: "#444",
                fontSize: "14px",
                flexDirection: "column",
                gap: "12px",
              }}
            >
              <span style={{ fontSize: "48px" }}>🎯</span>
              <span>Fill in the form and click Predict FPS</span>
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div
              className="d-flex align-items-center justify-content-center"
              style={{
                height: "300px",
                color: "#888",
                flexDirection: "column",
                gap: "12px",
              }}
            >
              <div className="spinner-border text-secondary" role="status" />
              <span>Running LightGBM model...</span>
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="mb-3">

              {/* ── Main metric cards ─────────────────────── */}
              <div className="row g-3 mb-3">
                <div className="col-6 col-md-3">
                  <MetricCard
                    label="Predicted FPS"
                    value={Math.round(result.predicted_fps)}
                    icon="🎮"
                    color="#198754"
                    subtitle="Best estimate"
                  />
                </div>
                <div className="col-6 col-md-3">
                  <MetricCard
                    label="1% Low FPS"
                    value={result.low_1pct_fps
                      ? Math.round(result.low_1pct_fps)
                      : null}
                    icon="📉"
                    color="#ffc107"
                    subtitle="Worst-case"
                  />
                </div>
                <div className="col-6 col-md-3">
                  <MetricCard
                    label="Frame Time"
                    value={result.frame_time_ms}
                    unit="ms"
                    icon="⏱️"
                    color="#0dcaf0"
                    subtitle="Per frame"
                  />
                </div>
                <div className="col-6 col-md-3">
                  <MetricCard
                    label="Health Score"
                    value={result.health_score
                      ? Math.round(result.health_score)
                      : null}
                    unit="/100"
                    icon="💚"
                    color={
                      result.health_score
                        ? result.health_score >= 70
                          ? "#198754"
                          : result.health_score >= 50
                          ? "#ffc107"
                          : "#dc3545"
                        : "#888"
                    }
                    subtitle="System health"
                  />
                </div>
              </div>

              {/* ── Tier + Bottleneck + Model badges ─────── */}
              <div
                className="card p-3 mb-3"
                style={{
                  backgroundColor: "#1a1d23",
                  border: "1px solid #2a2d35",
                  borderRadius: "10px",
                }}
              >
                <div className="d-flex align-items-center justify-content-between flex-wrap gap-3">

                  {/* Performance tier */}
                  <div>
                    <div style={{
                      fontSize: "10px", color: "#666",
                      fontWeight: 700, letterSpacing: "1px",
                      textTransform: "uppercase", marginBottom: "6px",
                    }}>
                      Performance Tier
                    </div>
                    <span style={{
                      backgroundColor: getTierColor(result.performance_tier) + "22",
                      color:           getTierColor(result.performance_tier),
                      border:         `1px solid ${getTierColor(result.performance_tier)}`,
                      padding: "4px 16px",
                      borderRadius: "20px",
                      fontWeight: 700,
                      fontSize: "14px",
                    }}>
                      {result.performance_tier}
                    </span>
                  </div>

                  {/* Bottleneck class */}
                  {result.bottleneck_class && (
                    <div>
                      <div style={{
                        fontSize: "10px", color: "#666",
                        fontWeight: 700, letterSpacing: "1px",
                        textTransform: "uppercase", marginBottom: "6px",
                      }}>
                        Bottleneck
                      </div>
                      <span style={{
                        backgroundColor: bottleneckColor(result.bottleneck_class) + "22",
                        color:           bottleneckColor(result.bottleneck_class),
                        border:         `1px solid ${bottleneckColor(result.bottleneck_class)}`,
                        padding: "4px 16px",
                        borderRadius: "20px",
                        fontWeight: 700,
                        fontSize: "14px",
                      }}>
                        {result.bottleneck_class}
                      </span>
                    </div>
                  )}

                  {/* Model used */}
                  <div>
                    <div style={{
                      fontSize: "10px", color: "#666",
                      fontWeight: 700, letterSpacing: "1px",
                      textTransform: "uppercase", marginBottom: "6px",
                    }}>
                      Model
                    </div>
                    <span style={{
                      backgroundColor: "#6f42c122",
                      color: "#6f42c1",
                      border: "1px solid #6f42c1",
                      padding: "4px 16px",
                      borderRadius: "20px",
                      fontWeight: 700,
                      fontSize: "13px",
                    }}>
                      {result.model_name}
                    </span>
                  </div>

                </div>
              </div>

              {/* ── FPS quality reference guide ───────────── */}
              <div
                className="card p-3"
                style={{
                  backgroundColor: "#1a1d23",
                  border: "1px solid #2a2d35",
                  borderRadius: "10px",
                }}
              >
                <div style={{
                  fontSize: "11px", color: "#555",
                  fontWeight: 700, letterSpacing: "1px",
                  textTransform: "uppercase", marginBottom: "10px",
                }}>
                  FPS Quality Reference
                </div>
                <div className="d-flex gap-3 flex-wrap">
                  {[
                    { label: "144+ FPS", color: "#198754", note: "Excellent" },
                    { label: "60+ FPS",  color: "#6f42c1", note: "Smooth"    },
                    { label: "30-60 FPS",color: "#ffc107", note: "Playable"  },
                    { label: "<30 FPS",  color: "#dc3545", note: "Unplayable"},
                  ].map((t) => (
                    <div
                      key={t.label}
                      className="d-flex align-items-center gap-2"
                    >
                      <div style={{
                        width: "10px", height: "10px",
                        borderRadius: "50%",
                        backgroundColor: t.color,
                        flexShrink: 0,
                      }} />
                      <span style={{
                        color: t.color,
                        fontSize: "12px",
                        fontWeight: 600,
                      }}>
                        {t.label}
                      </span>
                      <span style={{ color: "#666", fontSize: "11px" }}>
                        — {t.note}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}

          {/* ── Phase 2: FPS Heatmap ───────────────────────── */}
          {heatmapLoading && (
            <div
              className="d-flex align-items-center justify-content-center"
              style={{
                height: "200px",
                color: "#888",
                flexDirection: "column",
                gap: "12px",
              }}
            >
              <div className="spinner-border text-secondary" role="status" />
              <span>Running 16 predictions across the grid...</span>
            </div>
          )}

          {heatmapData && !heatmapLoading && (
            <div
              className="card p-2"
              style={{
                backgroundColor: "#1a1d23",
                border: "1px solid #2a2d35",
                borderRadius: "10px",
              }}
            >
              <div style={{
                fontSize: "11px", color: "#555",
                fontWeight: 700, letterSpacing: "1px",
                textTransform: "uppercase", padding: "10px 10px 0",
              }}>
                Resolution × Preset FPS Heatmap
              </div>
              <ReactECharts
                option={buildHeatmapOption(heatmapData)}
                style={{ height: "320px", width: "100%" }}
                opts={{ renderer: "canvas" }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Prediction;