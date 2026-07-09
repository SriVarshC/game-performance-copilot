// ═══════════════════════════════════════════════════════════
// Copilot — AI chat interface with Ollama LLM
// Calls POST /api/llm/ask
// ═══════════════════════════════════════════════════════════

import { useState, useRef, useEffect } from "react";
import { postLLMQuestion, getTelemetry, postCopilotFeedback } from "../services/api";
import type { ChatMessage, TelemetryData } from "../types";
import { IconCopilot, IconThumbsUp, IconThumbsDown, IconRadio } from "../icons";

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
      content:   "Hi! I'm your Game Performance Copilot.\n\nI can help you optimize your RTX 3050 Ti + i7-12650H setup. Ask me anything about FPS, settings, bottlenecks, or thermal issues.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input,     setInput]     = useState("");
  const [loading,   setLoading]   = useState(false);
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null);
  const [sendTelemetry, setSendTelemetry] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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

  const handleSend = async (question?: string) => {
    const text = (question ?? input).trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = { role: "user", content: text, timestamp: new Date().toISOString() };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await postLLMQuestion({ question: text, include_telemetry: sendTelemetry });
      const assistantMsg: ChatMessage = {
        role: "assistant", content: res.answer, timestamp: new Date().toISOString(), interactionId: res.interaction_id,
      };
      setMessages((m) => [...m, assistantMsg]);
    } catch {
      setMessages((m) => [...m, {
        role: "assistant",
        content: "Could not reach the LLM. Make sure Ollama is running:\n\nollama serve\nollama run llama3.2",
        timestamp: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (idx: number, wasHelpful: boolean) => {
    const msg = messages[idx];
    if (!msg.interactionId || msg.feedbackGiven) return;
    try {
      await postCopilotFeedback(msg.interactionId, wasHelpful);
      setMessages((m) => m.map((item, i) => (i === idx ? { ...item, feedbackGiven: true } : item)));
    } catch {
      // silently fail
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (iso: string) => {
    try { return new Date(iso).toLocaleTimeString(); } catch { return ""; }
  };

  return (
    <div style={{ height: "calc(100vh - 120px)", display: "flex", flexDirection: "column" }}>

      <div className="d-flex align-items-center justify-content-between mb-3">
        <div className="d-flex align-items-center gap-2">
          <IconCopilot size={22} color="var(--violet)" />
          <div>
            <h4 style={{ color: "#fff", fontFamily: "var(--font-display)", margin: 0, fontWeight: 700 }}>
              AI Copilot
            </h4>
            <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
              Powered by Ollama · llama3.2 · Runs locally
            </div>
          </div>
        </div>

        <div className="d-flex align-items-center gap-2">
          <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Attach live telemetry</span>
          <div
            onClick={() => setSendTelemetry((v) => !v)}
            style={{
              width: "38px", height: "22px", borderRadius: "999px",
              background: sendTelemetry ? "linear-gradient(135deg, var(--teal) 0%, var(--violet) 100%)" : "rgba(255,255,255,0.08)",
              cursor: "pointer", position: "relative", transition: "background 0.2s",
            }}
          >
            <div style={{
              position: "absolute", top: "3px", left: sendTelemetry ? "19px" : "3px",
              width: "16px", height: "16px", borderRadius: "50%", backgroundColor: "#fff", transition: "left 0.2s",
            }} />
          </div>
          {telemetry && sendTelemetry && (
            <span className="pill" style={{ background: "rgba(34,197,94,0.15)", color: "var(--success)" }}>
              <IconRadio size={11} /> Live
            </span>
          )}
        </div>
      </div>

      <div className="d-flex gap-2 flex-wrap mb-3">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => handleSend(s)}
            disabled={loading}
            style={{
              background: "rgba(255,255,255,0.04)",
              border: "1px solid var(--border)",
              color: "var(--text-muted)",
              borderRadius: "999px",
              padding: "5px 14px",
              fontSize: "11px",
              cursor: loading ? "not-allowed" : "pointer",
              whiteSpace: "nowrap",
            }}
          >
            {s}
          </button>
        ))}
      </div>

      <div
        className="glass-card"
        style={{
          flex: 1, overflowY: "auto", padding: "18px",
          display: "flex", flexDirection: "column", gap: "18px", marginBottom: "12px",
        }}
      >
        {messages.map((msg, idx) => (
          <div key={idx} style={{ display: "flex", flexDirection: "column", alignItems: msg.role === "user" ? "flex-end" : "flex-start", gap: "6px" }}>
            <div className="hud-label" style={{ paddingLeft: msg.role !== "user" ? "4px" : "0", paddingRight: msg.role === "user" ? "4px" : "0" }}>
              {msg.role === "user" ? "You" : "Copilot"} · {formatTime(msg.timestamp)}
            </div>

            <div style={{
              maxWidth: "80%",
              background: msg.role === "user"
                ? "linear-gradient(135deg, var(--teal) 0%, var(--violet) 100%)"
                : "rgba(255,255,255,0.04)",
              border: msg.role === "user" ? "none" : "1px solid var(--border)",
              borderRadius: msg.role === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
              padding: "12px 16px",
              fontSize: "13px",
              lineHeight: 1.6,
              color: msg.role === "user" ? "#fff" : "var(--text)",
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}>
              {msg.content}
            </div>

            {msg.role === "assistant" && msg.interactionId && (
              <div className="d-flex align-items-center gap-2" style={{ paddingLeft: "4px" }}>
                <button
                  onClick={() => handleFeedback(idx, true)}
                  disabled={msg.feedbackGiven}
                  title="Helpful"
                  style={{
                    background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)", borderRadius: "999px",
                    padding: "4px 10px", cursor: msg.feedbackGiven ? "default" : "pointer",
                    opacity: msg.feedbackGiven ? 0.4 : 1, color: "var(--success)", display: "flex", alignItems: "center",
                  }}
                >
                  <IconThumbsUp size={13} />
                </button>
                <button
                  onClick={() => handleFeedback(idx, false)}
                  disabled={msg.feedbackGiven}
                  title="Not helpful"
                  style={{
                    background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)", borderRadius: "999px",
                    padding: "4px 10px", cursor: msg.feedbackGiven ? "default" : "pointer",
                    opacity: msg.feedbackGiven ? 0.4 : 1, color: "var(--danger)", display: "flex", alignItems: "center",
                  }}
                >
                  <IconThumbsDown size={13} />
                </button>
                {msg.feedbackGiven && (
                  <span style={{ fontSize: "10px", color: "var(--text-dim)" }}>Thanks for the feedback!</span>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: "6px" }}>
            <div className="hud-label" style={{ paddingLeft: "4px" }}>Copilot · thinking...</div>
            <div style={{ background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)", borderRadius: "18px 18px 18px 4px", padding: "14px 18px" }}>
              <div className="d-flex gap-1 align-items-center">
                {[0, 1, 2].map((i) => (
                  <div key={i} style={{
                    width: "6px", height: "6px", borderRadius: "50%",
                    background: "var(--violet)",
                    animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
                  }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="d-flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about FPS, settings, bottlenecks... (Enter to send)"
          rows={2}
          style={{
            flex: 1, background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)",
            color: "var(--text)", borderRadius: "14px", padding: "12px 16px", fontSize: "13px",
            resize: "none", outline: "none",
          }}
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          style={{
            background: loading || !input.trim() ? "rgba(255,255,255,0.06)" : "linear-gradient(135deg, var(--teal) 0%, var(--violet) 100%)",
            border: "none",
            color: loading || !input.trim() ? "var(--text-dim)" : "#fff",
            borderRadius: "14px", padding: "0 24px", fontWeight: 700, fontSize: "16px",
            cursor: loading || !input.trim() ? "not-allowed" : "pointer",
          }}
        >
          →
        </button>
      </div>

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