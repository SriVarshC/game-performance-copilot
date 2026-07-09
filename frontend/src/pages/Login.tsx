// ═══════════════════════════════════════════════════════════
// Login — login / register form
// ═══════════════════════════════════════════════════════════

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { IconGamepad, IconAlert } from "../icons";

function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "login") {
        await login({ username, password });
      } else {
        await register({ username, email, password });
      }
      navigate("/");
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ??
        "Something went wrong — check your details and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const inputStyle: React.CSSProperties = {
    backgroundColor: "rgba(255,255,255,0.04)",
    border: "1px solid var(--border)",
    color: "var(--text)",
    borderRadius: "10px",
    padding: "11px 14px",
    fontSize: "13px",
    width: "100%",
    outline: "none",
  };

  const labelStyle: React.CSSProperties = {
    fontSize: "11px",
    color: "var(--text-muted)",
    fontWeight: 600,
    letterSpacing: "0.5px",
    textTransform: "uppercase",
    marginBottom: "6px",
    display: "block",
  };

  return (
    <div
      className="d-flex align-items-center justify-content-center"
      style={{ minHeight: "100vh" }}
    >
      <div
        className="glass-card p-4"
        style={{ width: "100%", maxWidth: "400px" }}
      >
        <div className="text-center mb-4">
          <div
            className="icon-chip mx-auto mb-3"
            style={{
              width: "52px",
              height: "52px",
              borderRadius: "16px",
              background: "linear-gradient(135deg, var(--teal) 0%, var(--violet) 100%)",
            }}
          >
            <IconGamepad size={26} color="#fff" />
          </div>
          <h4 style={{ color: "#fff", fontFamily: "var(--font-display)", fontWeight: 700, marginTop: "4px" }}>
            Game Performance Copilot
          </h4>
          <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
            RTX 3050 Ti · i7-12650H · 16GB RAM
          </div>
        </div>

        {/* Mode toggle */}
        <div
          className="d-flex gap-1 mb-4"
          style={{ background: "rgba(255,255,255,0.04)", borderRadius: "999px", padding: "4px" }}
        >
          {(["login", "register"] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => { setMode(m); setError(null); }}
              style={{
                flex: 1,
                padding: "9px",
                borderRadius: "999px",
                border: "none",
                fontSize: "13px",
                fontWeight: 700,
                cursor: "pointer",
                background: mode === m
                  ? "linear-gradient(135deg, var(--violet) 0%, var(--violet-2) 100%)"
                  : "transparent",
                color: mode === m ? "#fff" : "var(--text-muted)",
                transition: "all 0.15s ease",
              }}
            >
              {m === "login" ? "Log In" : "Register"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label style={labelStyle}>Username</label>
            <input
              type="text"
              style={inputStyle}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              minLength={3}
            />
          </div>

          {mode === "register" && (
            <div className="mb-3">
              <label style={labelStyle}>Email</label>
              <input
                type="email"
                style={inputStyle}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          )}

          <div className="mb-3">
            <label style={labelStyle}>Password</label>
            <input
              type="password"
              style={inputStyle}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </div>

          {error && (
            <div
              className="d-flex align-items-center gap-2 mb-3 p-2"
              style={{
                background: "rgba(239,68,68,0.1)",
                border: "1px solid rgba(239,68,68,0.3)",
                borderRadius: "10px",
                color: "var(--danger)",
                fontSize: "12px",
              }}
            >
              <IconAlert size={14} /> {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-100"
            style={{
              background: loading
                ? "rgba(255,255,255,0.06)"
                : "linear-gradient(135deg, var(--teal) 0%, var(--violet) 100%)",
              border: "none",
              color: "#fff",
              padding: "12px",
              borderRadius: "999px",
              fontWeight: 700,
              fontSize: "14px",
              cursor: loading ? "not-allowed" : "pointer",
              boxShadow: loading ? "none" : "0 4px 20px rgba(139, 92, 246, 0.35)",
            }}
          >
            {loading
              ? "Please wait..."
              : mode === "login" ? "Log In" : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Login;