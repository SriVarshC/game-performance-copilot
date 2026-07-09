// ═══════════════════════════════════════════════════════════
// MetricCard — glass stat card with colored icon chip
// Supports a "filled" hero variant for emphasis
// ═══════════════════════════════════════════════════════════

import type { ReactNode } from "react";

interface MetricCardProps {
  label:     string;
  value:     number | string | null;
  unit?:     string;
  icon?:     ReactNode;
  color?:    string;
  subtitle?: string;
  live?:     boolean;
  filled?:   boolean;   // NEW — renders as a solid gradient hero card
}

function MetricCard({
  label,
  value,
  unit      = "",
  icon,
  color     = "var(--teal)",
  subtitle,
  live      = false,
  filled    = false,
}: MetricCardProps) {
  const displayValue = value === null || value === undefined ? "—" : value;

  const cardStyle = filled
    ? {
        padding: "18px",
        background: `linear-gradient(135deg, ${color} 0%, color-mix(in srgb, ${color} 60%, #6D28D9) 100%)`,
        border: "none",
      }
    : { padding: "18px" };

  const textColor = filled ? "#fff" : color;
  const labelColor = filled ? "rgba(255,255,255,0.85)" : "var(--text-muted)";

  return (
    <div className={filled ? "h-100" : "glass-card h-100"} style={{ ...cardStyle, borderRadius: "var(--radius)" }}>
      <div className="d-flex align-items-center justify-content-between mb-3">
        <div className="d-flex align-items-center gap-2">
          {icon && (
            <div
              className="icon-chip"
              style={{
                background: filled ? "rgba(255,255,255,0.2)" : `${color}22`,
                color: filled ? "#fff" : color,
              }}
            >
              {icon}
            </div>
          )}
          <span className="hud-label" style={{ color: labelColor }}>{label}</span>
        </div>
        {live && (
          <span
            className="hud-live-dot"
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              backgroundColor: filled ? "#fff" : "var(--success)",
              boxShadow: filled ? "0 0 8px #fff" : "0 0 8px var(--success)",
            }}
          />
        )}
      </div>

      <div className="stat-value" style={{ fontSize: "28px", color: textColor, lineHeight: 1.1 }}>
        {displayValue}
        {value !== null && value !== undefined && unit && (
          <span
            style={{
              fontSize: "13px",
              fontWeight: 500,
              color: filled ? "rgba(255,255,255,0.75)" : "var(--text-muted)",
              marginLeft: "4px",
              fontFamily: "var(--font-sans)",
            }}
          >
            {unit}
          </span>
        )}
      </div>

      {subtitle && (
        <div style={{ fontSize: "11px", color: filled ? "rgba(255,255,255,0.7)" : "var(--text-dim)", marginTop: "8px" }}>
          {subtitle}
        </div>
      )}
    </div>
  );
}

export default MetricCard;