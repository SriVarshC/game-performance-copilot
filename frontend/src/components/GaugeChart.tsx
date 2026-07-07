// ═══════════════════════════════════════════════════════════
// GaugeChart — ECharts gauge for CPU%, GPU%, RAM%, VRAM%, and
// GPU Temperature (via mode="temperature")
// ═══════════════════════════════════════════════════════════

import ReactECharts from "echarts-for-react";

interface GaugeChartProps {
  title:  string;
  value:  number | null;
  color?: string;
  max?:   number;
  /**
   * "percent"     — default. Thresholds at 50/75/90 (of `max`).
   *                 Used for CPU/GPU/RAM/VRAM usage gauges.
   * "temperature" — Thresholds at 70/80/85°C, matching the
   *                 thermal-throttle logic in dataset_generator.py
   *                 (throttling begins at 85°C).
   */
  mode?: "percent" | "temperature";
}

function GaugeChart({
  title,
  value,
  color,
  max   = 100,
  mode  = "percent",
}: GaugeChartProps) {
  const safeValue = value ?? 0;

  // ── Healthy/idle band is now genuinely green, not brand purple —
  // gauges read green → yellow → orange → red at a glance. ──────────
  const HEALTHY_GREEN = "#28a745";

  const getColor = (val: number): string => {
    if (mode === "temperature") {
      if (val >= 85) return "#dc3545";   // red — thermal throttling zone
      if (val >= 80) return "#fd7e14";   // orange — approaching throttle
      if (val >= 70) return "#ffc107";   // yellow — warm
      return color ?? HEALTHY_GREEN;      // green — safe operating temp
    }
    // percent mode (CPU/GPU/RAM/VRAM usage)
    if (val >= 90) return "#dc3545";     // red — critical
    if (val >= 75) return "#fd7e14";     // orange — high
    if (val >= 50) return "#ffc107";     // yellow — medium
    return color ?? HEALTHY_GREEN;        // green — healthy/idle
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
            val === 0 && value === null ? "N/A" : `${val}${unitSuffix}`,
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