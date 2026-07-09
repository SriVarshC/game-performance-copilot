// ═══════════════════════════════════════════════════════════
// Navbar — Top navigation bar
// ═══════════════════════════════════════════════════════════

import { useEffect, useState } from "react";
import { getHealth } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import { IconGamepad, IconUser } from "../icons";

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
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  const statusColor = {
    online:   "var(--success)",
    offline:  "var(--danger)",
    checking: "var(--warn)",
  }[apiStatus];

  const statusLabel = {
    online:   "API Online",
    offline:  "API Offline",
    checking: "Checking...",
  }[apiStatus];

  return (
    <nav
      className="d-flex align-items-center justify-content-between px-4"
      style={{
        background: "rgba(11, 14, 26, 0.55)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        borderBottom: "1px solid var(--border)",
        height: "64px",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}
    >
      {/* Left — Logo + Title */}
      <div className="d-flex align-items-center gap-3">
        <div
          className="icon-chip"
          style={{
            background: "linear-gradient(135deg, var(--teal) 0%, var(--violet) 100%)",
            width: "38px",
            height: "38px",
            borderRadius: "12px",
          }}
        >
          <IconGamepad size={20} color="#fff" />
        </div>
        <div>
          <div
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: 700,
              fontSize: "16px",
              color: "#fff",
              letterSpacing: "-0.2px",
            }}
          >
            Game Performance Copilot
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
            RTX 3050 Ti · i7-12650H · 16GB RAM
          </div>
        </div>
      </div>

      {/* Right — API status + model badge + auth */}
      <div className="d-flex align-items-center gap-3">
        {modelName && (
          <span
            className="pill"
            style={{
              background: "linear-gradient(135deg, var(--violet) 0%, var(--violet-2) 100%)",
              color: "#fff",
            }}
          >
            {modelName}
          </span>
        )}

        <span
          className="pill"
          style={{
            background: `${statusColor}22`,
            color: statusColor,
          }}
        >
          <span
            className={apiStatus === "online" ? "hud-live-dot" : ""}
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              backgroundColor: statusColor,
            }}
          />
          {statusLabel}
        </span>

        {isAuthenticated && (
          <div className="d-flex align-items-center gap-2">
            <span
              className="pill"
              style={{ background: "rgba(255,255,255,0.06)", color: "var(--text-muted)" }}
            >
              <IconUser size={12} /> {username}
            </span>
            <button
              onClick={logout}
              style={{
                background: "rgba(255,255,255,0.06)",
                border: "1px solid var(--border)",
                color: "var(--text-muted)",
                fontSize: "11px",
                fontWeight: 600,
                padding: "6px 14px",
                borderRadius: "999px",
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