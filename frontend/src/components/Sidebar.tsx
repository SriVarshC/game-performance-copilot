// ═══════════════════════════════════════════════════════════
// Sidebar — Left navigation links
// ═══════════════════════════════════════════════════════════

import { NavLink } from "react-router-dom";

interface NavItem {
  path:  string;
  icon:  string;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { path: "/",            icon: "📊", label: "Dashboard"    },
  { path: "/analytics",   icon: "🔍", label: "Analytics"    },
  { path: "/prediction",  icon: "🎯", label: "Prediction"   },
  { path: "/copilot",     icon: "🤖", label: "Copilot"      },
  { path: "/performance", icon: "⚡", label: "Performance"  },
];

function Sidebar() {
  return (
    <aside
      style={{
        width: "200px",
        minWidth: "200px",
        backgroundColor: "#1a1d23",
        borderRight: "1px solid #2a2d35",
        paddingTop: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "4px",
      }}
    >
      {/* Section label */}
      <div
        style={{
          fontSize: "10px",
          color: "#555",
          fontWeight: 700,
          letterSpacing: "1.5px",
          textTransform: "uppercase",
          padding: "0 16px 8px",
        }}
      >
        Navigation
      </div>

      {/* Nav links */}
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          end={item.path === "/"}
          style={({ isActive }) => ({
            display: "flex",
            alignItems: "center",
            gap: "10px",
            padding: "10px 16px",
            textDecoration: "none",
            fontSize: "14px",
            fontWeight: isActive ? 600 : 400,
            color: isActive ? "#ffffff" : "#888",
            backgroundColor: isActive ? "#22252e" : "transparent",
            borderLeft: isActive
              ? "3px solid #6f42c1"
              : "3px solid transparent",
            borderRadius: "0 6px 6px 0",
            transition: "all 0.15s ease",
          })}
        >
          <span style={{ fontSize: "18px" }}>{item.icon}</span>
          <span>{item.label}</span>
        </NavLink>
      ))}

      {/* Bottom — version */}
      <div
        style={{
          marginTop: "auto",
          padding: "16px",
          fontSize: "11px",
          color: "#444",
          borderTop: "1px solid #2a2d35",
        }}
      >
        <div>v3.0.0 · Phase 11</div>
        <div style={{ marginTop: "4px" }}>Sri Varsh C</div>
        <div>UMass Amherst DACSS</div>
      </div>
    </aside>
  );
}

export default Sidebar;