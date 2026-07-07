// ═══════════════════════════════════════════════════════════
// Login — Phase 8: login / register form
// ═══════════════════════════════════════════════════════════

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

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
    backgroundColor: "#22252e",
    border: "1px solid #2a2d35",
    color: "#e0e0e0",
    borderRadius: "6px",
    padding: "10px 12px",
    fontSize: "13px",
    width: "100%",
  };

  const labelStyle: React.CSSProperties = {
    fontSize: "11px",
    color: "#888",
    fontWeight: 600,
    letterSpacing: "0.5px",
    textTransform: "uppercase",
    marginBottom: "6px",
    display: "block",
  };

  return (
    <div
      className="d-flex align-items-center justify-content-center"
      style={{ minHeight: "100vh", backgroundColor: "#0f1117" }}
    >
      <div
        className="card p-4"
        style={{
          backgroundColor: "#1a1d23",
          border: "1px solid #2a2d35",
          borderRadius: "12px",
          width: "100%",
          maxWidth: "380px",
        }}
      >
        <div className="text-center mb-4">
          <span style={{ fontSize: "36px" }}>🎮</span>
          <h4 style={{ color: "#fff", fontWeight: 700, marginTop: "8px" }}>
            Game Performance Copilot
          </h4>
          <div style={{ fontSize: "12px", color: "#666" }}>
            RTX 3050 Ti · i7-12650H · 16GB RAM
          </div>
        </div>

        {/* Mode toggle */}
        <div className="d-flex gap-2 mb-4">
          {(["login", "register"] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => { setMode(m); setError(null); }}
              style={{
                flex: 1,
                padding: "8px",
                borderRadius: "6px",
                border: "1px solid",
                fontSize: "13px",
                fontWeight: 700,
                cursor: "pointer",
                backgroundColor: mode === m ? "#6f42c1" : "#22252e",
                borderColor:     mode === m ? "#6f42c1" : "#2a2d35",
                color:           mode === m ? "#fff" : "#888",
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
              className="mb-3 p-2"
              style={{
                backgroundColor: "#2a1215",
                border: "1px solid #dc3545",
                borderRadius: "6px",
                color: "#dc3545",
                fontSize: "12px",
              }}
            >
              ⚠️ {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-100"
            style={{
              backgroundColor: loading ? "#2a2d35" : "#6f42c1",
              border: "none",
              color: "#fff",
              padding: "10px",
              borderRadius: "8px",
              fontWeight: 700,
              fontSize: "14px",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading
              ? "⏳ Please wait..."
              : mode === "login" ? "Log In" : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Login;