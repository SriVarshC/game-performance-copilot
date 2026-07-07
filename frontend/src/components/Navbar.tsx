// ═══════════════════════════════════════════════════════════
// Navbar — Top navigation bar
// ═══════════════════════════════════════════════════════════

import { useEffect, useState } from "react";
import { getHealth } from "../services/api";
import { useAuth } from "../contexts/AuthContext";

function Navbar() {
  const [apiStatus, setApiStatus] = useState<"online" | "offline" | "checking">("checking");
  const [modelName, setModelName] = useState<string>("");
  const { username, isAuthenticated, logout } = useAuth();

  useEffect(() => {

    const check = async () => {
      try {
        const data = await getHealth();
        if (data.status === "healthy") {
          setApiStatus("online");
          setModelName(data.model_name ?? "LightGBM");
        } else {
          setApiStatus("offline");
        }
      } catch {
        setApiStatus("offline");
      }
    };

    check();
    // Re-check every 30 seconds
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  const statusColor = {
    online:   "#198754",
    offline:  "#dc3545",
    checking: "#ffc107",
  }[apiStatus];

  const statusLabel = {
    online:   "API Online",
    offline:  "API Offline",
    checking: "Checking...",
  }[apiStatus];

  return (
    <nav
      className="d-flex align-items-center justify-content-between px-4 py-2"
      style={{
        backgroundColor: "#1a1d23",
        borderBottom: "1px solid #2a2d35",
        height: "56px",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}
    >
      {/* Left — Logo + Title */}
      <div className="d-flex align-items-center gap-2">
        <span style={{ fontSize: "22px" }}>🎮</span>
        <div>
          <span
            style={{
              fontWeight: 700,
              fontSize: "16px",
              color: "#ffffff",
              letterSpacing: "0.5px",
            }}
          >
            Game Performance Copilot
          </span>
          <span
            style={{
              fontSize: "11px",
              color: "#888",
              marginLeft: "10px",
            }}
          >
            RTX 3050 Ti · i7-12650H · 16GB RAM
          </span>
        </div>
      </div>

      {/* Right — API status + model badge + auth */}
      <div className="d-flex align-items-center gap-3">
        {/* Model badge */}
        {modelName && (
          <span
            style={{
              fontSize: "11px",
              backgroundColor: "#6f42c1",
              color: "#fff",
              padding: "3px 10px",
              borderRadius: "12px",
              fontWeight: 600,
            }}
          >
            {modelName}
          </span>
        )}

        {/* API status dot */}
        <div className="d-flex align-items-center gap-2">
          <div
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              backgroundColor: statusColor,
              boxShadow: `0 0 6px ${statusColor}`,
            }}
          />
          <span style={{ fontSize: "12px", color: "#aaa" }}>
            {statusLabel}
          </span>
        </div>

        {/* Phase 8: user + logout */}
        {isAuthenticated && (
          <div className="d-flex align-items-center gap-2">
            <span style={{ fontSize: "12px", color: "#888" }}>
              👤 {username}
            </span>
            <button
              onClick={logout}
              style={{
                backgroundColor: "#22252e",
                border: "1px solid #2a2d35",
                color: "#888",
                fontSize: "11px",
                padding: "4px 10px",
                borderRadius: "6px",
                cursor: "pointer",
              }}
            >
              Log Out
            </button>
          </div>
        )}
      </div>
    </nav>
  );
}

export default Navbar;