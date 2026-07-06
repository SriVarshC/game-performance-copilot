// ═══════════════════════════════════════════════════════════
// MetricCard — Reusable stat card for live metrics
// Used by Dashboard for FPS, CPU%, GPU%, RAM%, VRAM%
// ═══════════════════════════════════════════════════════════

interface MetricCardProps {
  label:     string;
  value:     number | string | null;
  unit?:     string;
  icon?:     string;
  color?:    string;    // accent color for value text
  subtitle?: string;   // optional line below value
}

function MetricCard({
  label,
  value,
  unit      = "",
  icon      = "📊",
  color     = "#ffffff",
  subtitle,
}: MetricCardProps) {
  const displayValue = value === null || value === undefined ? "N/A" : value;

  return (
    <div
      className="card h-100"
      style={{
        backgroundColor: "#1a1d23",
        border: "1px solid #2a2d35",
        borderRadius: "10px",
        padding: "16px 20px",
        minWidth: "140px",
      }}
    >
      {/* Header row — icon + label */}
      <div
        className="d-flex align-items-center gap-2 mb-2"
        style={{ color: "#888", fontSize: "12px", fontWeight: 600 }}
      >
        <span style={{ fontSize: "16px" }}>{icon}</span>
        <span style={{ textTransform: "uppercase", letterSpacing: "0.8px" }}>
          {label}
        </span>
      </div>

      {/* Main value */}
      <div
        style={{
          fontSize: "32px",
          fontWeight: 700,
          color: color,
          lineHeight: 1.1,
          letterSpacing: "-0.5px",
        }}
      >
        {displayValue}
        {value !== null && value !== undefined && unit && (
          <span
            style={{
              fontSize: "14px",
              fontWeight: 400,
              color: "#888",
              marginLeft: "4px",
            }}
          >
            {unit}
          </span>
        )}
      </div>

      {/* Subtitle */}
      {subtitle && (
        <div
          style={{
            fontSize: "11px",
            color: "#666",
            marginTop: "6px",
          }}
        >
          {subtitle}
        </div>
      )}
    </div>
  );
}

export default MetricCard;