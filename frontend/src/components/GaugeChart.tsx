// ═══════════════════════════════════════════════════════════
// GaugeChart — ECharts gauge, restyled for the glass/vivid theme
// ═══════════════════════════════════════════════════════════

import ReactECharts from "echarts-for-react";

interface GaugeChartProps {
  title:  string;
  value:  number | null;
  color?: string;
  max?:   number;
  mode?:  "percent" | "temperature";
}

function GaugeChart({
  title,
  value,
  color,
  max   = 100,
  mode  = "percent",
}: GaugeChartProps) {
  const safeValue = value ?? 0;
  const HEALTHY = color ?? "#2DD4BF";

  const getColor = (val: number): string => {
    if (mode === "temperature") {
      if (val >= 85) return "#EF4444";
      if (val >= 80) return "#F97316";
      if (val >= 70) return "#F59E0B";
      return HEALTHY;
    }
    if (val >= 90) return "#EF4444";
    if (val >= 75) return "#F97316";
    if (val >= 50) return "#F59E0B";
    return HEALTHY;
  };

  const activeColor = getColor(safeValue);
  const unitSuffix = mode === "temperature" ? "°C" : "%";

  const option = {
    backgroundColor: "transparent",
    series: [
      {
        type: "gauge",
        startAngle: 210,
        endAngle: -30,
        min: 0,
        max: max,
        splitNumber: 5,
        radius: "85%",
        center: ["50%", "60%"],
        progress: {
          show: true,
          width: 12,
          itemStyle: { color: activeColor, shadowBlur: 10, shadowColor: activeColor },
        },
        axisLine: { lineStyle: { width: 12, color: [[1, "rgba(255,255,255,0.08)"]] } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        pointer: { show: true, length: "55%", width: 4, itemStyle: { color: activeColor } },
        detail: {
          valueAnimation: true,
          formatter: (val: number) => (val === 0 && value === null ? "N/A" : `${val}${unitSuffix}`),
          color: "#F1F5F9",
          fontSize: 18,
          fontWeight: 700,
          fontFamily: "Space Grotesk",
          offsetCenter: [0, "25%"],
        },
        title: {
          show: true,
          offsetCenter: [0, "55%"],
          color: "#8A93A6",
          fontSize: 11,
          fontWeight: 600,
          text: title.toUpperCase(),
        },
        data: [{ value: safeValue, name: title }],
      },
    ],
  };

  return (
    <div className="glass-card" style={{ padding: "8px" }}>
      <ReactECharts option={option} style={{ height: "180px", width: "100%" }} opts={{ renderer: "canvas" }} />
    </div>
  );
}

export default GaugeChart;