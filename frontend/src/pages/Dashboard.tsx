import React, { useState, useEffect, useRef } from "react";
import MetricCard from "../components/MetricCard";
import GaugeChart from "../components/GaugeChart";
import LineChart from "../components/LineChart";
import { getTelemetry, getTelemetryHistory } from "../services/api";
import type { TelemetryData, TelemetryHistory } from "../types";

const Dashboard: React.FC = () => {
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [history, setHistory]     = useState<TelemetryHistory | null>(null);
  const [error, setError]         = useState<string | null>(null);
  const [isLive, setIsLive]       = useState(false);

  // ── Guard: only one telemetry request in-flight at a time ─────────────────
  const isFetchingRef = useRef(false);

  const fetchTelemetry = async () => {
    if (isFetchingRef.current) return;          // skip if previous still pending
    isFetchingRef.current = true;
    try {
      const data = await getTelemetry();
      setTelemetry(data);
      setIsLive(true);
      setError(null);
    } catch {
      setError("Cannot reach FastAPI — is it running on port 8000?");
      setIsLive(false);
    } finally {
      isFetchingRef.current = false;
    }
  };

  const fetchHistory = async () => {
    try {
      const data = await getTelemetryHistory(1, 60);
      setHistory(data);
    } catch {
      // non-critical — charts just stay empty
    }
  };

  useEffect(() => {
    fetchTelemetry();
    fetchHistory();
    const t1 = setInterval(fetchTelemetry, 2000);
    const t2 = setInterval(fetchHistory, 10000);
    return () => { clearInterval(t1); clearInterval(t2); };
  }, []);

  // ── FPS colour helper ─────────────────────────────────────────────────────
  const fpsColor = (v: number | null) =>
    v === null ? "#888" : v >= 60 ? "#44bb44" : v >= 30 ? "#ffcc00" : "#ff4444";

  return (
    <div className="p-4">

      {/* Header */}
      <div className="d-flex align-items-center gap-3 mb-4">
        <h2 className="text-white mb-0">Live Dashboard</h2>
        <span
          className={`badge rounded-pill ${isLive ? "bg-success" : "bg-secondary"}`}
          style={{ fontSize: "0.75rem" }}
        >
          {isLive ? "● LIVE" : "○ OFFLINE"}
        </span>
      </div>

      {/* Error banner */}
      {error && (
        <div className="alert alert-danger mb-4">
          <strong>⚠️ Connection Error:</strong> {error}
        </div>
      )}

      {/* ── Metric cards ─────────────────────────────────────────────────── */}
      <div className="row g-3 mb-4">
        {[
          { label: "FPS",      value: telemetry?.fps,        unit: "fps", icon: "🎮", color: fpsColor(telemetry?.fps ?? null) },
          { label: "CPU Usage",value: telemetry?.cpu_usage,  unit: "%",   icon: "🖥️", color: "#4fc3f7" },
          { label: "GPU Usage",value: telemetry?.gpu_usage,  unit: "%",   icon: "🎴", color: "#ab47bc" },
          { label: "RAM Usage",value: telemetry?.ram_usage,  unit: "%",   icon: "💾", color: "#66bb6a" },
          { label: "VRAM",     value: telemetry?.vram_usage, unit: "%",   icon: "⚡", color: "#ffa726" },
          { label: "GPU Temp", value: telemetry?.gpu_temp,   unit: "°C",  icon: "🌡️", color: "#ef5350" },
        ].map(({ label, value, unit, icon, color }) => (
          <div key={label} className="col-6 col-md-4 col-xl-2">
            <MetricCard
              label={label}
              value={value ?? null}
              unit={unit}
              icon={icon}
              color={color}
            />
          </div>
        ))}
      </div>

      {/* ── Gauge row ────────────────────────────────────────────────────── */}
      {/* Now 5 gauges: CPU/GPU/RAM/VRAM use percent thresholds (green <50,
          yellow 50-75, orange 75-90, red 90+); GPU Temp uses temperature
          thresholds tied to the actual thermal-throttle point (85°C). */}
      <div className="row g-3 mb-4">
        {[
          { title: "CPU",  value: telemetry?.cpu_usage  ?? 0, mode: "percent" as const,     max: 100 },
          { title: "GPU",  value: telemetry?.gpu_usage  ?? 0, mode: "percent" as const,     max: 100 },
          { title: "RAM",  value: telemetry?.ram_usage  ?? 0, mode: "percent" as const,     max: 100 },
          { title: "VRAM", value: telemetry?.vram_usage ?? 0, mode: "percent" as const,     max: 100 },
          { title: "GPU Temp", value: telemetry?.gpu_temp ?? 0, mode: "temperature" as const, max: 100 },
        ].map(({ title, value, mode, max }) => (
          <div key={title} className="col-6 col-md-4 col-xl">
            <GaugeChart title={title} value={value} max={max} mode={mode} />
          </div>
        ))}
      </div>

      {/* ── Line charts ──────────────────────────────────────────────────── */}
      <div className="row g-3">
        <div className="col-12 col-lg-6">
          <LineChart
            title="FPS History"
            timestamps={history?.timestamps ?? []}
            series={[{ name: "FPS", data: history?.fps ?? [], color: "#66bb6a" }]}
            height={300}
            yUnit="fps"
          />
        </div>
        <div className="col-12 col-lg-6">
          <LineChart
            title="System Usage"
            timestamps={history?.timestamps ?? []}
            series={[
              { name: "CPU", data: history?.cpu_usage ?? [], color: "#4fc3f7" },
              { name: "GPU", data: history?.gpu_usage ?? [], color: "#ab47bc" },
              { name: "RAM", data: history?.ram_usage ?? [], color: "#66bb6a" },
            ]}
            height={300}
            yUnit="%"
          />
        </div>
      </div>

    </div>
  );
};

export default Dashboard;