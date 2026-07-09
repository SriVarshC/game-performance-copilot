// ═══════════════════════════════════════════════════════════
// Performance — System monitoring: request volume, response
// times per endpoint, error rate
// ═══════════════════════════════════════════════════════════

import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { getPerformanceSummary } from "../services/api";
import type { PerformanceSummary } from "../types";
import MetricCard from "../components/MetricCard";
import { IconBolt, IconTrend, IconAlert, IconLink, IconRefresh } from "../icons";

const WINDOW_OPTIONS = [
  { label: "1h",  hours: 1   },
  { label: "24h", hours: 24  },
  { label: "7d",  hours: 168 },
];

function Performance() {
  const [data,       setData]       = useState<PerformanceSummary | null>(null);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>("--");
  const [hours,      setHours]      = useState(24);

  const fetchSummary = async (h: number) => {
    try {
      const res = await getPerformanceSummary(h);
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
    setLoading(true);
    fetchSummary(hours);
    const interval = setInterval(() => fetchSummary(hours), 30000);
    return () => clearInterval(interval);
  }, [hours]);

  const buildEndpointOption = (rows: PerformanceSummary["by_endpoint"]) => {
    const sorted = [...rows].sort((a, b) => b.avg_ms - a.avg_ms).slice(0, 12);
    const endpoints = sorted.map((r) => r.endpoint);
    const avgMs     = sorted.map((r) => r.avg_ms);

    return {
      backgroundColor: "transparent",
      title: { text: "Average Response Time by Endpoint", textStyle: { color: "#F1F5F9", fontSize: 13, fontWeight: 600, fontFamily: "Space Grotesk" }, left: 8, top: 8 },
      tooltip: {
        trigger: "axis",
        backgroundColor: "#131728",
        borderColor: "rgba(255,255,255,0.1)",
        textStyle: { color: "#F1F5F9" },
        formatter: (params: any) => {
          const p = params[0];
          const row = sorted[p.dataIndex];
          return `${p.name}<br/>Avg: <b>${p.value}ms</b><br/>Max: ${row.max_ms}ms<br/>Requests: ${row.count}`;
        },
      },
      grid: { top: 48, left: 16, right: 32, bottom: 16, containLabel: true },
      xAxis: { type: "value", axisLabel: { color: "#565F73", fontSize: 10, formatter: "{value}ms" }, splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)", type: "dashed" } } },
      yAxis: { type: "category", data: endpoints, axisLabel: { color: "#8A93A6", fontSize: 10 }, axisLine: { lineStyle: { color: "rgba(255,255,255,0.1)" } } },
      series: [{
        type: "bar", data: avgMs, barMaxWidth: 18,
        itemStyle: {
          borderRadius: [0, 6, 6, 0],
          color: (params: any) => {
            const v = params.value as number;
            if (v < 100) return "#22C55E";
            if (v < 1000) return "#F59E0B";
            return "#EF4444";
          },
        },
      }],
    };
  };

  const buildVolumeOption = (rows: PerformanceSummary["by_endpoint"]) => {
    const palette = ["#2DD4BF", "#8B5CF6", "#3B82F6", "#22C55E", "#F59E0B", "#EF4444", "#EC4899"];
    const pieData = rows.map((r, i) => ({ name: r.endpoint, value: r.count, itemStyle: { color: palette[i % palette.length] } }));

    return {
      backgroundColor: "transparent",
      title: { text: "Request Volume by Endpoint", textStyle: { color: "#F1F5F9", fontSize: 13, fontWeight: 600, fontFamily: "Space Grotesk" }, left: 8, top: 8 },
      tooltip: { trigger: "item", backgroundColor: "#131728", borderColor: "rgba(255,255,255,0.1)", textStyle: { color: "#F1F5F9" }, formatter: "{b}: {c} ({d}%)" },
      legend: { orient: "vertical", right: 8, top: "center", textStyle: { color: "#8A93A6", fontSize: 10 }, icon: "circle", itemWidth: 8, itemHeight: 8 },
      series: [{
        type: "pie", radius: ["40%", "70%"], center: ["38%", "55%"],
        data: pieData.length > 0 ? pieData : [{ name: "No data yet", value: 1 }],
        label: { show: false },
      }],
    };
  };

  if (loading) {
    return (
      <div className="d-flex align-items-center justify-content-center" style={{ height: "60vh", color: "var(--text-muted)" }}>
        <div className="text-center">
          <div className="spinner-border mb-3" style={{ color: "var(--teal)" }} role="status" />
          <div>Loading performance data...</div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="d-flex align-items-center justify-content-between mb-4">
        <div className="d-flex align-items-center gap-2">
          <IconBolt size={22} color="var(--teal)" />
          <div>
            <h4 style={{ color: "#fff", fontFamily: "var(--font-display)", margin: 0, fontWeight: 700 }}>Performance</h4>
            <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
              Request timing &amp; system health · Last update: {lastUpdate}
            </div>
          </div>
        </div>

        <div className="d-flex align-items-center gap-2">
          <div className="d-flex gap-1" style={{ background: "rgba(255,255,255,0.04)", borderRadius: "999px", padding: "3px" }}>
            {WINDOW_OPTIONS.map((opt) => (
              <button
                key={opt.hours}
                onClick={() => setHours(opt.hours)}
                style={{
                  background: hours === opt.hours ? "linear-gradient(135deg, var(--teal) 0%, var(--violet) 100%)" : "transparent",
                  border: "none",
                  color: hours === opt.hours ? "#fff" : "var(--text-muted)",
                  fontSize: "11px", fontWeight: 600, padding: "5px 12px", borderRadius: "999px", cursor: "pointer",
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <button
            onClick={() => fetchSummary(hours)}
            className="d-flex align-items-center gap-1"
            style={{ background: "rgba(255,255,255,0.04)", color: "var(--text-muted)", border: "1px solid var(--border)", fontSize: "12px", padding: "6px 14px", borderRadius: "999px" }}
          >
            <IconRefresh size={12} /> Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="d-flex align-items-center gap-2 mb-4 p-3" style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", borderRadius: "14px", color: "var(--danger)", fontSize: "13px" }}>
          <IconAlert size={16} /> {error}
        </div>
      )}

      {data && (
        <>
          <div className="row g-3 mb-4">
            <div className="col-6 col-md-3">
              <MetricCard label="Total Requests" value={data.total_requests} icon={<IconTrend size={18} />} color="var(--violet)" subtitle={`Last ${hours}h`} filled />
            </div>
            <div className="col-6 col-md-3">
              <MetricCard label="Avg Response" value={Math.round(data.avg_duration_ms)} unit="ms" icon={<IconBolt size={18} />} color="var(--teal)" subtitle="All endpoints" />
            </div>
            <div className="col-6 col-md-3">
              <MetricCard label="Errors" value={data.error_count} icon={<IconAlert size={18} />} color={data.error_count > 0 ? "var(--danger)" : "var(--success)"} subtitle={`${data.error_rate_pct}% error rate`} />
            </div>
            <div className="col-6 col-md-3">
              <MetricCard label="Endpoints" value={data.by_endpoint.length} icon={<IconLink size={18} />} color="var(--data-vram)" subtitle="Being monitored" />
            </div>
          </div>

          {data.by_endpoint.length > 0 ? (
            <div className="row g-3 mb-4">
              <div className="col-12 col-lg-7">
                <div className="glass-card" style={{ padding: "8px" }}>
                  <ReactECharts option={buildEndpointOption(data.by_endpoint)} style={{ height: "340px", width: "100%" }} opts={{ renderer: "canvas" }} />
                </div>
              </div>
              <div className="col-12 col-lg-5">
                <div className="glass-card" style={{ padding: "8px" }}>
                  <ReactECharts option={buildVolumeOption(data.by_endpoint)} style={{ height: "340px", width: "100%" }} opts={{ renderer: "canvas" }} />
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-card d-flex align-items-center justify-content-center" style={{ height: "200px", color: "var(--text-dim)", fontSize: "13px" }}>
              No request data yet for this time window
            </div>
          )}

          {data.by_endpoint.length > 0 && (
            <div className="row g-3">
              <div className="col-12">
                <div className="glass-card p-3">
                  <div className="hud-label mb-3">Endpoint Breakdown</div>

                  {/* Header row */}
                  <div
                    className="d-flex"
                    style={{
                      padding: "8px 12px",
                      fontSize: "11px",
                      fontWeight: 600,
                      color: "var(--text-muted)",
                      borderBottom: "1px solid var(--border)",
                    }}
                  >
                    <div style={{ flex: 3 }}>Endpoint</div>
                    <div style={{ flex: 1, textAlign: "right" }}>Requests</div>
                    <div style={{ flex: 1, textAlign: "right" }}>Avg (ms)</div>
                    <div style={{ flex: 1, textAlign: "right" }}>Max (ms)</div>
                  </div>

                  {/* Rows */}
                  {[...data.by_endpoint].sort((a, b) => b.count - a.count).map((row, i, arr) => (
                    <div
                      key={row.endpoint}
                      className="d-flex align-items-center"
                      style={{
                        padding: "10px 12px",
                        fontSize: "12px",
                        color: "var(--text)",
                        borderBottom: i < arr.length - 1 ? "1px solid var(--border)" : "none",
                      }}
                    >
                      <div style={{ flex: 3, fontFamily: "var(--font-mono)" }}>{row.endpoint}</div>
                      <div style={{ flex: 1, textAlign: "right", fontFamily: "var(--font-mono)" }}>{row.count}</div>
                      <div style={{ flex: 1, textAlign: "right", fontFamily: "var(--font-mono)" }}>{row.avg_ms}</div>
                      <div style={{ flex: 1, textAlign: "right", fontFamily: "var(--font-mono)" }}>{row.max_ms}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Performance;