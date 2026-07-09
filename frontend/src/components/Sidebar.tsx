// ═══════════════════════════════════════════════════════════
// Sidebar — Left navigation links
// ═══════════════════════════════════════════════════════════

import { NavLink } from "react-router-dom";
import { IconDashboard, IconAnalytics, IconTarget, IconCopilot, IconBolt } from "../icons";

interface NavItem {
  path:  string;
  icon:  React.ReactNode;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { path: "/",            icon: <IconDashboard size={18} />, label: "Dashboard"   },
  { path: "/analytics",   icon: <IconAnalytics size={18} />, label: "Analytics"   },
  { path: "/prediction",  icon: <IconTarget size={18} />,    label: "Prediction"  },
  { path: "/copilot",     icon: <IconCopilot size={18} />,   label: "Copilot"     },
  { path: "/performance", icon: <IconBolt size={18} />,      label: "Performance" },
];

function Sidebar() {
  return (
    <aside
      style={{
        width: "220px",
        minWidth: "220px",
        background: "rgba(11, 14, 26, 0.4)",
        borderRight: "1px solid var(--border)",
        paddingTop: "20px",
        display: "flex",
        flexDirection: "column",
        gap: "6px",
      }}
    >
      <div className="hud-label" style={{ padding: "0 18px 10px" }}>
        Navigation
      </div>

      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          end={item.path === "/"}
          style={({ isActive }) => ({
            display: "flex",
            alignItems: "center",
            gap: "10px",
            margin: "0 12px",
            padding: "10px 14px",
            textDecoration: "none",
            fontSize: "14px",
            fontWeight: isActive ? 600 : 500,
            color: isActive ? "#fff" : "var(--text-muted)",
            background: isActive
              ? "linear-gradient(135deg, var(--violet) 0%, var(--violet-2) 100%)"
              : "transparent",
            boxShadow: isActive ? "0 4px 16px rgba(139, 92, 246, 0.35)" : "none",
            borderRadius: "12px",
            transition: "all 0.15s ease",
          })}
        >
          {item.icon}
          <span>{item.label}</span>
        </NavLink>
      ))}

      <div
        style={{
          marginTop: "auto",
          padding: "16px 18px",
          fontSize: "11px",
          color: "var(--text-dim)",
          borderTop: "1px solid var(--border)",
        }}
      >
        <div>v3.0.0 · Phase 11</div>
        <div style={{ marginTop: "4px" }}>Srivarsh Cirigiri</div>
        <div>UMass Amherst</div>
      </div>
    </aside>
  );
}

export default Sidebar;