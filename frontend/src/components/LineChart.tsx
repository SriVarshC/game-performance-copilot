// ═══════════════════════════════════════════════════════════
// LineChart — ECharts line chart for FPS/CPU/GPU over time
// Used by Dashboard (live history from /api/telemetry/history)
// ═══════════════════════════════════════════════════════════

import ReactECharts from "echarts-for-react";

interface LineSeries {
  name:  string;
  data:  number[];
  color: string;
}

interface LineChartProps {
  title:      string;
  timestamps: string[];
  series:     LineSeries[];
  height?:    number;
  yUnit?:     string;
}

function LineChart({
  title,
  timestamps,
  series,
  height = 280,
  yUnit  = "",
}: LineChartProps) {

  // Format timestamps to HH:MM:SS for x-axis labels
  const labels = timestamps.map((t) => {
    try {
      return new Date(t).toLocaleTimeString();
    } catch {
      return t;
    }
  });

  const option = {
    backgroundColor: "transparent",

    title: {
      text: title,
      textStyle: {
        color: "#cccccc",
        fontSize: 13,
        fontWeight: 600,
      },
      left: 8,
      top: 8,
    },

    tooltip: {
      trigger: "axis",
      backgroundColor: "#22252e",
      borderColor: "#2a2d35",
      textStyle: { color: "#e0e0e0", fontSize: 12 },
      formatter: (params: any[]) => {
        let html = `<div style="margin-bottom:4px;color:#888;font-size:11px">
          ${params[0]?.axisValue ?? ""}
        </div>`;
        params.forEach((p) => {
          html += `
            <div style="display:flex;align-items:center;gap:6px;margin:2px 0">
              <span style="
                display:inline-block;width:10px;height:10px;
                border-radius:50%;background:${p.color}">
              </span>
              <span>${p.seriesName}:</span>
              <strong>${p.value}${yUnit}</strong>
            </div>`;
        });
        return html;
      },
    },

    legend: {
      top: 8,
      right: 8,
      textStyle: { color: "#888", fontSize: 11 },
      icon: "circle",
      itemWidth: 8,
      itemHeight: 8,
    },

    grid: {
      top: 48,
      left: 48,
      right: 16,
      bottom: 40,
    },

    xAxis: {
      type: "category",
      data: labels,
      axisLine:  { lineStyle: { color: "#2a2d35" } },
      axisLabel: {
        color: "#666",
        fontSize: 10,
        rotate: 30,
        interval: Math.floor(labels.length / 6),
      },
      splitLine: { show: false },
    },

    yAxis: {
      type: "value",
      axisLine:  { lineStyle: { color: "#2a2d35" } },
      axisLabel: {
        color: "#666",
        fontSize: 10,
        formatter: (val: number) => `${val}${yUnit}`,
      },
      splitLine: {
        lineStyle: { color: "#2a2d35", type: "dashed" },
      },
    },

    series: series.map((s) => ({
      name: s.name,
      type: "line",
      data: s.data,
      smooth: true,
      symbol: "none",
      lineStyle: {
        color: s.color,
        width: 2,
      },
      areaStyle: {
        color: {
          type: "linear",
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0,   color: s.color + "40" },  // 25% opacity top
            { offset: 1,   color: s.color + "00" },  // 0% opacity bottom
          ],
        },
      },
    })),
  };

  return (
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
        option={option}
        style={{ height: `${height}px`, width: "100%" }}
        opts={{ renderer: "canvas" }}
      />
    </div>
  );
}

export default LineChart;