// ═══════════════════════════════════════════════════════════
// LineChart — ECharts line chart, restyled for the glass/vivid theme
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

function LineChart({ title, timestamps, series, height = 280, yUnit = "" }: LineChartProps) {
  const labels = timestamps.map((t) => {
    try { return new Date(t).toLocaleTimeString(); } catch { return t; }
  });

  const option = {
    backgroundColor: "transparent",
    title: {
      text: title,
      textStyle: { color: "#F1F5F9", fontSize: 13, fontWeight: 600, fontFamily: "Space Grotesk" },
      left: 8,
      top: 8,
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#131728",
      borderColor: "rgba(255,255,255,0.1)",
      textStyle: { color: "#F1F5F9", fontSize: 12 },
      formatter: (params: any[]) => {
        let html = `<div style="margin-bottom:4px;color:#8A93A6;font-size:11px">${params[0]?.axisValue ?? ""}</div>`;
        params.forEach((p) => {
          html += `<div style="display:flex;align-items:center;gap:6px;margin:2px 0">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color}"></span>
            <span>${p.seriesName}:</span><strong>${p.value}${yUnit}</strong></div>`;
        });
        return html;
      },
    },
    legend: {
      top: 8, right: 8,
      textStyle: { color: "#8A93A6", fontSize: 11 },
      icon: "circle", itemWidth: 8, itemHeight: 8,
    },
    grid: { top: 48, left: 48, right: 16, bottom: 40 },
    xAxis: {
      type: "category",
      data: labels,
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.1)" } },
      axisLabel: { color: "#565F73", fontSize: 10, rotate: 30, interval: Math.floor(labels.length / 6) },
      splitLine: { show: false },
    },
    yAxis: {
      type: "value",
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.1)" } },
      axisLabel: { color: "#565F73", fontSize: 10, formatter: (val: number) => `${val}${yUnit}` },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)", type: "dashed" } },
    },
    series: series.map((s) => ({
      name: s.name,
      type: "line",
      data: s.data,
      smooth: true,
      symbol: "none",
      lineStyle: { color: s.color, width: 2.5 },
      areaStyle: {
        color: {
          type: "linear", x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: s.color + "35" }, { offset: 1, color: s.color + "00" }],
        },
      },
    })),
  };

  return (
    <div className="glass-card" style={{ padding: "8px" }}>
      <ReactECharts option={option} style={{ height: `${height}px`, width: "100%" }} opts={{ renderer: "canvas" }} />
    </div>
  );
}

export default LineChart;