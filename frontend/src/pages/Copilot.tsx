// ═══════════════════════════════════════════════════════════
// Copilot — AI chat interface with Ollama LLM
// Calls POST /api/llm/ask
// ═══════════════════════════════════════════════════════════

import { useState, useRef, useEffect } from "react";
import { postLLMQuestion, getTelemetry, postCopilotFeedback } from "../services/api";
import type { ChatMessage, TelemetryData } from "../types";

// ── Suggested starter questions ──────────────────────────────
const SUGGESTIONS = [
  "Why is my FPS dropping below 30?",
  "Should I enable DLSS on RTX 3050 Ti?",
  "What settings hurt FPS the most?",
  "How do I fix GPU thermal throttling?",
  "Is 4GB VRAM enough for 1080p gaming?",
];

function Copilot() {
  const [messages,  setMessages]  = useState<ChatMessage[]>([
    {
      role:      "assistant",
      content:   "Hi! I'm your Game Performance Copilot 🎮\n\nI can help you optimize your RTX 3050 Ti + i7-12650H setup. Ask me anything about FPS, settings, bottlenecks, or thermal issues.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input,     setInput]     = useState("");
  const [loading,   setLoading]   = useState(false);
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [sendTelemetry, setSendTelemetry] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  // ── Auto-scroll to bottom on new message ─────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ── Fetch live telemetry (display only — backend fetches its own
  //     live telemetry server-side for the actual LLM context) ─────
  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await getTelemetry();
        setTelemetry(res);
      } catch {
        // silently fail
      }
    };
    fetch();
    const interval = setInterval(fetch, 5000);
    return () => clearInterval(interval);
  }, []);

  // ── Send message ──────────────────────────────────────────
  const handleSend = async (question?: string) => {
    const text = (question ?? input).trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = {
      role:      "user",
      content:   text,
      timestamp: new Date().toISOString(),
    };

    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await postLLMQuestion({
        question: text,
        include_telemetry: sendTelemetry,
      });

      const assistantMsg: ChatMessage = {
        role:          "assistant",
        content:       res.answer,
        timestamp:     new Date().toISOString(),
        interactionId: res.interaction_id,
      };
      setMessages((m) => [...m, assistantMsg]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          role:      "assistant",
          content:   "⚠️ Could not reach the LLM. Make sure Ollama is running:\n\nollama serve\nollama run llama3.2",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // ── Handle feedback click ─────────────────────────────────
  const handleFeedback = async (idx: number, wasHelpful: boolean) => {
    const msg = messages[idx];
    if (!msg.interactionId || msg.feedbackGiven) return;

    try {
      await postCopilotFeedback(msg.interactionId, wasHelpful);
      setMessages((m) =>
        m.map((item, i) =>
          i === idx ? { ...item, feedbackGiven: true } : item
        )
      );
    } catch {
      // silently fail — non-critical
    }
  };

  // ── Handle Enter key ──────────────────────────────────────
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ── Format timestamp ──────────────────────────────────────
  const formatTime = (iso: string) => {
    try { return new Date(iso).toLocaleTimeString(); }
    catch { return ""; }
  };

  return (
    <div style={{ height: "calc(100vh - 120px)", display: "flex", flexDirection: "column" }}>

      {/* ── Page header ───────────────────────────────────── */}
      <div className="d-flex align-items-center justify-content-between mb-3">
        <div>
          <h4 style={{ color: "#fff", margin: 0, fontWeight: 700 }}>
            🤖 AI Copilot
          </h4>
          <div style={{ fontSize: "12px", color: "#666", marginTop: "4px" }}>
            Powered by Ollama · llama3.2 · Runs locally
          </div>
        </div>

        {/* Telemetry toggle */}
        <div className="d-flex align-items-center gap-2">
          <span style={{ fontSize: "11px", color: "#666" }}>
            Attach live telemetry
          </span>
          <div
            onClick={() => setSendTelemetry((v) => !v)}
            style={{
              width: "36px",
              height: "20px",
              borderRadius: "10px",
              backgroundColor: sendTelemetry ? "#6f42c1" : "#2a2d35",
              cursor: "pointer",
              position: "relative",
              transition: "background-color 0.2s",
            }}
          >
            <div style={{
              position: "absolute",
              top: "2px",
              left: sendTelemetry ? "18px" : "2px",
              width: "16px",
              height: "16px",
              borderRadius: "50%",
              backgroundColor: "#fff",
              transition: "left 0.2s",
            }} />
          </div>
          {telemetry && sendTelemetry && (
            <span style={{
              fontSize: "10px",
              color: "#198754",
              backgroundColor: "#19875422",
              padding: "2px 8px",
              borderRadius: "8px",
              border: "1px solid #198754",
            }}>
              📡 Live
            </span>
          )}
        </div>
      </div>

      {/* ── Suggestions ───────────────────────────────────── */}
      <div className="d-flex gap-2 flex-wrap mb-3">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => handleSend(s)}
            disabled={loading}
            style={{
              backgroundColor: "#22252e",
              border: "1px solid #2a2d35",
              color: "#888",
              borderRadius: "16px",
              padding: "4px 12px",
              fontSize: "11px",
              cursor: loading ? "not-allowed" : "pointer",
              whiteSpace: "nowrap",
              transition: "all 0.15s",
            }}
          >
            {s}
          </button>
        ))}
      </div>

      {/* ── Message list ──────────────────────────────────── */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          backgroundColor: "#1a1d23",
          border: "1px solid #2a2d35",
          borderRadius: "10px",
          padding: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
          marginBottom: "12px",
        }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: msg.role === "user" ? "flex-end" : "flex-start",
              gap: "4px",
            }}
          >
            {/* Role label */}
            <div style={{
              fontSize: "10px",
              color: "#555",
              fontWeight: 700,
              letterSpacing: "0.5px",
              textTransform: "uppercase",
              paddingLeft: msg.role !== "user" ? "4px" : "0",
              paddingRight: msg.role === "user" ? "4px" : "0",
            }}>
              {msg.role === "user" ? "You" : "🤖 Copilot"} · {formatTime(msg.timestamp)}
            </div>

            {/* Bubble */}
            <div style={{
              maxWidth: "80%",
              backgroundColor: msg.role === "user" ? "#6f42c1" : "#22252e",
              border: `1px solid ${msg.role === "user" ? "#6f42c1" : "#2a2d35"}`,
              borderRadius: msg.role === "user"
                ? "16px 16px 4px 16px"
                : "16px 16px 16px 4px",
              padding: "10px 14px",
              fontSize: "13px",
              lineHeight: 1.6,
              color: "#e0e0e0",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}>
              {msg.content}
            </div>

            {/* Feedback buttons — only on assistant messages that have an interactionId */}
            {msg.role === "assistant" && msg.interactionId && (
              <div style={{ display: "flex", gap: "6px", paddingLeft: "4px" }}>
                <button
                  onClick={() => handleFeedback(idx, true)}
                  disabled={msg.feedbackGiven}
                  title="Helpful"
                  style={{
                    background: "none",
                    border: "1px solid #2a2d35",
                    borderRadius: "6px",
                    padding: "2px 8px",
                    fontSize: "12px",
                    cursor: msg.feedbackGiven ? "default" : "pointer",
                    opacity: msg.feedbackGiven ? 0.4 : 1,
                    color: "#888",
                  }}
                >
                  👍
                </button>
                <button
                  onClick={() => handleFeedback(idx, false)}
                  disabled={msg.feedbackGiven}
                  title="Not helpful"
                  style={{
                    background: "none",
                    border: "1px solid #2a2d35",
                    borderRadius: "6px",
                    padding: "2px 8px",
                    fontSize: "12px",
                    cursor: msg.feedbackGiven ? "default" : "pointer",
                    opacity: msg.feedbackGiven ? 0.4 : 1,
                    color: "#888",
                  }}
                >
                  👎
                </button>
                {msg.feedbackGiven && (
                  <span style={{ fontSize: "10px", color: "#555", alignSelf: "center" }}>
                    Thanks for the feedback!
                  </span>
                )}
              </div>
            )}
          </div>
        ))}

        {/* Loading bubble */}
        {loading && (
          <div style={{ display: "flex", flexDirection: "column",
            alignItems: "flex-start", gap: "4px" }}>
            <div style={{ fontSize: "10px", color: "#555",
              fontWeight: 700, textTransform: "uppercase",
              paddingLeft: "4px" }}>
              🤖 Copilot · thinking...
            </div>
            <div style={{
              backgroundColor: "#22252e",
              border: "1px solid #2a2d35",
              borderRadius: "16px 16px 16px 4px",
              padding: "12px 16px",
            }}>
              <div className="d-flex gap-1 align-items-center">
                {[0, 1, 2].map((i) => (
                  <div key={i} style={{
                    width: "6px", height: "6px",
                    borderRadius: "50%",
                    backgroundColor: "#6f42c1",
                    animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
                  }} />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* ── Input row ─────────────────────────────────────── */}
      <div className="d-flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about FPS, settings, bottlenecks... (Enter to send)"
          rows={2}
          style={{
            flex: 1,
            backgroundColor: "#22252e",
            border: "1px solid #2a2d35",
            color: "#e0e0e0",
            borderRadius: "8px",
            padding: "10px 14px",
            fontSize: "13px",
            resize: "none",
            outline: "none",
          }}
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          style={{
            backgroundColor:
              loading || !input.trim() ? "#22252e" : "#6f42c1",
            border: "1px solid",
            borderColor:
              loading || !input.trim() ? "#2a2d35" : "#6f42c1",
            color: loading || !input.trim() ? "#555" : "#fff",
            borderRadius: "8px",
            padding: "0 20px",
            fontWeight: 700,
            fontSize: "18px",
            cursor: loading || !input.trim() ? "not-allowed" : "pointer",
            transition: "all 0.15s",
          }}
        >
          ➤
        </button>
      </div>

      {/* Bounce animation */}
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40%            { transform: scale(1.0); opacity: 1;   }
        }
      `}</style>
    </div>
  );
}

export default Copilot;