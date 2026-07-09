import React, { useState, useEffect, useRef } from "react";
import MetricCard from "../components/MetricCard";
import GaugeChart from "../components/GaugeChart";
import LineChart from "../components/LineChart";
import { getTelemetry, getTelemetryHistory } from "../services/api";
import type { TelemetryData, TelemetryHistory } from "../types";
import { IconGamepad, IconCpu, IconGpu, IconRam, IconBolt, IconThermometer, IconAlert } from "../icons";

const Dashboard: React.FC = () => {
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [history, setHistory]     = useState<TelemetryHistory | null>(null);
  const [error, setError]         = useState<string | null>(null);
  const [isLive, setIsLive]       = useState(false);

  const isFetchingRef = useRef(false);

  const fetchTelemetry = async () => {
    if (isFetchingRef.current) return;
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
      // non-critical
    }
  };

  useEffect(() => {
    fetchTelemetry();
    fetchHistory();
    const t1 = setInterval(fetchTelemetry, 2000);
    const t2 = setInterval(fetchHistory, 10000);
    return () => { clearInterval(t1); clearInterval(t2); };
  }, []);

  const fpsColor = (v: number | null) =>
    v === null ? "var(--text-muted)" : v >= 60 ? "var(--data-fps)" : v >= 30 ? "var(--data-vram)" : "var(--danger)";

  return (
    <div className="p-4">

      {/* Header */}
      <div className="d-flex align-items-center gap-3 mb-4">
        <h2 style={{ color: "#fff", fontFamily: "var(--font-display)", fontWeight: 700, margin: 0 }}>
          Live Dashboard
        </h2>
        <span
          className="pill"
          style={{
            background: isLive ? "rgba(34,197,94,0.15)" : "rgba(148,163,184,0.15)",
            color: isLive ? "var(--success)" : "var(--text-muted)",
          }}
        >
          <span
            className={isLive ? "hud-live-dot" : ""}
            style={{ width: 6, height: 6, borderRadius: "50%", background: "currentColor" }}
          />
          {isLive ? "LIVE" : "OFFLINE"}
        </span>
      </div>

      {/* Error banner */}
      {error && (
        <div
          className="glass-card d-flex align-items-center gap-2 mb-4 p-3"
          style={{ borderColor: "rgba(239,68,68,0.4)", color: "var(--danger)", fontSize: "13px" }}
        >
          <IconAlert size={16} /> <strong>Connection Error:</strong> {error}
        </div>
      )}

      {/* ── Metric cards ─────────────────────────────────── */}
      <div className="row g-3 mb-4">
        {[
          { label: "FPS",       value: telemetry?.fps,        unit: "fps", icon: <IconGamepad size={18} />,      color: fpsColor(telemetry?.fps ?? null) },
          { label: "CPU Usage", value: telemetry?.cpu_usage,  unit: "%",   icon: <IconCpu size={18} />,          color: "var(--data-cpu)" },
          { label: "GPU Usage", value: telemetry?.gpu_usage,  unit: "%",   icon: <IconGpu size={18} />,          color: "var(--data-gpu)" },
          { label: "RAM Usage", value: telemetry?.ram_usage,  unit: "%",   icon: <IconRam size={18} />,          color: "var(--data-ram)" },
          { label: "VRAM",      value: telemetry?.vram_usage, unit: "%",   icon: <IconBolt size={18} />,         color: "var(--data-vram)" },
          { label: "GPU Temp",  value: telemetry?.gpu_temp,   unit: "°C",  icon: <IconThermometer size={18} />,  color: "var(--data-temp)" },
        ].map(({ label, value, unit, icon, color }) => (
          <div key={label} className="col-6 col-md-4 col-xl-2">
            <MetricCard label={label} value={value ?? null} unit={unit} icon={icon} color={color} live={isLive} />
          </div>
        ))}
      </div>

      {/* ── Gauge row ────────────────────────────────────── */}
      <div className="row g-3 mb-4">
        {[
          { title: "CPU",  value: telemetry?.cpu_usage  ?? 0, mode: "percent" as const,     color: "#3B82F6" },
          { title: "GPU",  value: telemetry?.gpu_usage  ?? 0, mode: "percent" as const,     color: "#8B5CF6" },
          { title: "RAM",  value: telemetry?.ram_usage  ?? 0, mode: "percent" as const,     color: "#22C55E" },
          { title: "VRAM", value: telemetry?.vram_usage ?? 0, mode: "percent" as const,     color: "#F59E0B" },
          { title: "GPU Temp", value: telemetry?.gpu_temp ?? 0, mode: "temperature" as const, color: "#2DD4BF" },
        ].map(({ title, value, mode, color }) => (
          <div key={title} className="col-6 col-md-4 col-xl">
            <GaugeChart title={title} value={value} max={100} mode={mode} color={color} />
          </div>
        ))}
      </div>

      {/* ── Line charts ──────────────────────────────────── */}
      <div className="row g-3">
        <div className="col-12 col-lg-6">
          <LineChart
            title="FPS History"
            timestamps={history?.timestamps ?? []}
            series={[{ name: "FPS", data: history?.fps ?? [], color: "#2DD4BF" }]}
            height={300}
            yUnit="fps"
          />
        </div>
        <div className="col-12 col-lg-6">
          <LineChart
            title="System Usage"
            timestamps={history?.timestamps ?? []}
            series={[
              { name: "CPU", data: history?.cpu_usage ?? [], color: "#3B82F6" },
              { name: "GPU", data: history?.gpu_usage ?? [], color: "#8B5CF6" },
              { name: "RAM", data: history?.ram_usage ?? [], color: "#22C55E" },
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