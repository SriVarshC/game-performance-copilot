// ═══════════════════════════════════════════════════════════
// GaugeChart — ECharts gauge for CPU%, GPU%, RAM%, VRAM%
// ═══════════════════════════════════════════════════════════

import ReactECharts from "echarts-for-react";

interface GaugeChartProps {
  title:  string;
  value:  number | null;
  color?: string;
  max?:   number;
}

function GaugeChart({
  title,
  value,
  color = "#6f42c1",
  max   = 100,
}: GaugeChartProps) {
  const safeValue = value ?? 0;

  // Dynamic color based on usage level
  const getColor = (val: number) => {
    if (val >= 90) return "#dc3545";   // red — critical
    if (val >= 75) return "#fd7e14";   // orange — high
    if (val >= 50) return "#ffc107";   // yellow — medium
    return color;                       // default — healthy
  };

  const activeColor = getColor(safeValue);

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

        // Outer arc (filled)
        progress: {
          show: true,
          width: 12,
          itemStyle: {
            color: activeColor,
            shadowBlur: 8,
            shadowColor: activeColor,
          },
        },

        // Track (empty arc)
        axisLine: {
          lineStyle: {
            width: 12,
            color: [[1, "#2a2d35"]],
          },
        },

        // Tick marks
        axisTick: {
          show: false,
        },
        splitLine: {
          show: false,
        },
        axisLabel: {
          show: false,
        },

        // Needle pointer
        pointer: {
          show: true,
          length: "55%",
          width: 4,
          itemStyle: {
            color: activeColor,
          },
        },

        // Center value display
        detail: {
          valueAnimation: true,
          formatter: (val: number) =>
            val === 0 && value === null ? "N/A" : `${val}%`,
          color: "#ffffff",
          fontSize: 18,
          fontWeight: 700,
          offsetCenter: [0, "25%"],
        },

        // Title below gauge
        title: {
          show: true,
          offsetCenter: [0, "55%"],
          color: "#888",
          fontSize: 11,
          fontWeight: 600,
          text: title.toUpperCase(),
        },

        data: [{ value: safeValue, name: title }],
      },
    ],
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
        style={{ height: "180px", width: "100%" }}
        opts={{ renderer: "canvas" }}
      />
    </div>
  );
}

export default GaugeChart;