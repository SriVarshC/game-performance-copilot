// ═══════════════════════════════════════════════════════════
// Performance — System monitoring: request volume, response
// times per endpoint, error rate (Phase 11)
// Polls /api/performance/summary every 30 seconds
// ═══════════════════════════════════════════════════════════

import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { getPerformanceSummary } from "../services/api";
import type { PerformanceSummary } from "../types";
import MetricCard from "../components/MetricCard";

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

  // ── Avg response time per endpoint — bar chart ─────────────
  const buildEndpointOption = (rows: PerformanceSummary["by_endpoint"]) => {
    const sorted = [...rows].sort((a, b) => b.avg_ms - a.avg_ms).slice(0, 12);
    const endpoints = sorted.map((r) => r.endpoint);
    const avgMs     = sorted.map((r) => r.avg_ms);

    return {
      backgroundColor: "transparent",
      title: {
        text: "Average Response Time by Endpoint",
        textStyle: { color: "#ccc", fontSize: 13, fontWeight: 600 },
        left: 8,
        top: 8,
      },
      tooltip: {
        trigger: "axis",
        backgroundColor: "#22252e",
        borderColor: "#2a2d35",
        textStyle: { color: "#e0e0e0" },
        formatter: (params: any) => {
          const p = params[0];
          const row = sorted[p.dataIndex];
          return `${p.name}<br/>Avg: <b>${p.value}ms</b><br/>Max: ${row.max_ms}ms<br/>Requests: ${row.count}`;
        },
      },
      grid: { top: 48, left: 16, right: 32, bottom: 16, containLabel: true },
      xAxis: {
        type: "value",
        axisLabel: { color: "#666", fontSize: 10, formatter: "{value}ms" },
        splitLine: { lineStyle: { color: "#2a2d35", type: "dashed" } },
      },
      yAxis: {
        type: "category",
        data: endpoints,
        axisLabel: { color: "#888", fontSize: 10 },
        axisLine:  { lineStyle: { color: "#2a2d35" } },
      },
      series: [
        {
          type: "bar",
          data: avgMs,
          barMaxWidth: 18,
          itemStyle: {
            borderRadius: [0, 4, 4, 0],
            color: (params: any) => {
              const v = params.value as number;
              if (v < 100) return "#198754";
              if (v < 1000) return "#ffc107";
              return "#dc3545";
            },
          },
        },
      ],
    };
  };

  // ── Request volume per endpoint — pie ──────────────────────
  const buildVolumeOption = (rows: PerformanceSummary["by_endpoint"]) => {
    const pieData = rows.map((r) => ({ name: r.endpoint, value: r.count }));

    return {
      backgroundColor: "transparent",
      title: {
        text: "Request Volume by Endpoint",
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
        right: 8,
        top: "center",
        textStyle: { color: "#888", fontSize: 10 },
        icon: "circle",
        itemWidth: 8,
        itemHeight: 8,
      },
      series: [
        {
          type: "pie",
          radius: ["40%", "70%"],
          center: ["38%", "55%"],
          data: pieData.length > 0 ? pieData : [{ name: "No data yet", value: 1 }],
          label: { show: false },
        },
      ],
    };
  };

  if (loading) {
    return (
      <div
        className="d-flex align-items-center justify-content-center"
        style={{ height: "60vh", color: "#888" }}
      >
        <div className="text-center">
          <div className="spinner-border text-secondary mb-3" role="status" />
          <div>Loading performance data...</div>
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
            ⚡ Performance
          </h4>
          <div style={{ fontSize: "12px", color: "#666", marginTop: "4px" }}>
            Request timing &amp; system health · Last update: {lastUpdate}
          </div>
        </div>

        <div className="d-flex align-items-center gap-2">
          {/* Time window toggle */}
          <div className="d-flex gap-1">
            {WINDOW_OPTIONS.map((opt) => (
              <button
                key={opt.hours}
                onClick={() => setHours(opt.hours)}
                style={{
                  backgroundColor: hours === opt.hours ? "#6f42c1" : "#22252e",
                  border: "1px solid",
                  borderColor: hours === opt.hours ? "#6f42c1" : "#2a2d35",
                  color: hours === opt.hours ? "#fff" : "#888",
                  fontSize: "11px",
                  padding: "4px 10px",
                  borderRadius: "6px",
                  cursor: "pointer",
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>

          <button
            className="btn btn-sm"
            onClick={() => fetchSummary(hours)}
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
            <div className="col-6 col-md-3">
              <MetricCard
                label="Total Requests"
                value={data.total_requests}
                icon="📈"
                color="#6f42c1"
                subtitle={`Last ${hours}h`}
              />
            </div>
            <div className="col-6 col-md-3">
              <MetricCard
                label="Avg Response"
                value={Math.round(data.avg_duration_ms)}
                unit="ms"
                icon="⏱️"
                color="#0dcaf0"
                subtitle="All endpoints"
              />
            </div>
            <div className="col-6 col-md-3">
              <MetricCard
                label="Errors"
                value={data.error_count}
                icon="⚠️"
                color={data.error_count > 0 ? "#dc3545" : "#198754"}
                subtitle={`${data.error_rate_pct}% error rate`}
              />
            </div>
            <div className="col-6 col-md-3">
              <MetricCard
                label="Endpoints"
                value={data.by_endpoint.length}
                icon="🔗"
                color="#ffc107"
                subtitle="Being monitored"
              />
            </div>
          </div>

          {/* ── Charts Row ────────────────────────────────── */}
          {data.by_endpoint.length > 0 ? (
            <div className="row g-3 mb-4">
              <div className="col-12 col-lg-7">
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
                    option={buildEndpointOption(data.by_endpoint)}
                    style={{ height: "340px", width: "100%" }}
                    opts={{ renderer: "canvas" }}
                  />
                </div>
              </div>
              <div className="col-12 col-lg-5">
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
                    option={buildVolumeOption(data.by_endpoint)}
                    style={{ height: "340px", width: "100%" }}
                    opts={{ renderer: "canvas" }}
                  />
                </div>
              </div>
            </div>
          ) : (
            <div
              className="card d-flex align-items-center justify-content-center"
              style={{
                backgroundColor: "#1a1d23",
                border: "1px solid #2a2d35",
                borderRadius: "10px",
                height: "200px",
                color: "#444",
                fontSize: "13px",
              }}
            >
              No request data yet for this time window
            </div>
          )}

          {/* ── Detail Table ──────────────────────────────── */}
          {data.by_endpoint.length > 0 && (
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
                    Endpoint Breakdown
                  </div>
                  <table className="table table-sm" style={{ marginBottom: 0 }}>
                    <thead>
                      <tr style={{ color: "#666", fontSize: "11px" }}>
                        <th style={{ borderColor: "#2a2d35" }}>Endpoint</th>
                        <th style={{ borderColor: "#2a2d35" }}>Requests</th>
                        <th style={{ borderColor: "#2a2d35" }}>Avg (ms)</th>
                        <th style={{ borderColor: "#2a2d35" }}>Max (ms)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...data.by_endpoint]
                        .sort((a, b) => b.count - a.count)
                        .map((row) => (
                          <tr key={row.endpoint} style={{ color: "#ccc", fontSize: "12px" }}>
                            <td style={{ borderColor: "#2a2d35" }}>{row.endpoint}</td>
                            <td style={{ borderColor: "#2a2d35" }}>{row.count}</td>
                            <td style={{ borderColor: "#2a2d35" }}>{row.avg_ms}</td>
                            <td style={{ borderColor: "#2a2d35" }}>{row.max_ms}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
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