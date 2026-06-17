"""
Game Performance Copilot — Full Dashboard
Phase 1 + Phase 2 + Phase 6: Telemetry + ML FPS Prediction + Recommendations + Feedback
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.telemetry.collector import TelemetryCollector
from src.database.db_manager import DatabaseManager
from src.diagnostics.engine import DiagnosticsEngine
from src.ml.predictor import FPSPredictor
from src.ml.recommendation_engine import RecommendationEngine
from src.ml.dataset_generator import (
    GAME_PROFILES, PRESET_CONFIG,
    RESOLUTION_CONFIG, UPSCALING_BOOST
)

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Game Performance Copilot",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    div[data-testid="metric-container"] {
        background-color: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 10px;
        padding: 12px;
    }
    .rec-card {
        background-color: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# INITIALIZE ALL COMPONENTS (cached — load once)
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def load_components():
    collector   = TelemetryCollector()
    db          = DatabaseManager()
    diagnostics = DiagnosticsEngine()
    predictor   = FPSPredictor()
    rec_engine  = RecommendationEngine(predictor)
    return collector, db, diagnostics, predictor, rec_engine

collector, db, diagnostics_engine, predictor, rec_engine = load_components()

# ─────────────────────────────────────────────────────────────
# SESSION STATE — Recommendations + Feedback
# Initialized ONCE before the while loop so they survive reruns
# ─────────────────────────────────────────────────────────────
if "recs"           not in st.session_state:
    st.session_state.recs           = None   # list of rec dicts with ids
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = {}     # { rec_id: True/False }

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎮 Game Performance Copilot")
    st.markdown("---")

    # ── System Info ──────────────────────────────────────────
    st.markdown("### 💻 Your System")
    st.markdown("""
    | Component | Spec |
    |---|---|
    | **GPU** | RTX 3050 Ti Laptop |
    | **VRAM** | 4 GB Dedicated |
    | **CPU** | i7-12650H |
    | **Cores** | 10C / 16T |
    | **RAM** | 16 GB |
    """)

    st.markdown("---")

    # ── Game Settings ─────────────────────────────────────────
    st.markdown("### 🎮 Game Settings")
    st.caption("Set these to match your current game configuration")

    game_genre = st.selectbox(
        "Game Genre",
        options=list(GAME_PROFILES.keys()),
        index=0,
        format_func=lambda x: GAME_PROFILES[x]["description"]
    )

    resolution = st.selectbox(
        "Resolution",
        options=list(RESOLUTION_CONFIG.keys()),
        index=1   # Default: 1080p
    )

    preset = st.selectbox(
        "Quality Preset",
        options=list(PRESET_CONFIG.keys()),
        index=2   # Default: high
    )

    ray_tracing = st.checkbox("🌟 Ray Tracing Enabled", value=False)

    upscaling = st.selectbox(
        "Upscaling / Anti-Aliasing",
        options=list(UPSCALING_BOOST.keys()),
        index=0   # Default: none
    )

    st.markdown("---")

    # ── Dashboard Controls ────────────────────────────────────
    refresh_rate = st.slider("⏱️ Refresh Rate (sec)", 1, 10, 2)
    save_to_db   = st.checkbox("💾 Save to Database", value=True)

    st.markdown("---")

    # ── Stats ─────────────────────────────────────────────────
    try:
        st.metric("📊 Records Collected", f"{db.get_total_records():,}")
    except Exception:
        pass

    # ── ML Model Status ───────────────────────────────────────
    st.markdown("---")
    if predictor.is_loaded:
        st.success(f"✅ ML Model Active\n\n**{predictor.model_name}**")
    else:
        st.error("❌ No model loaded\n\nRun: `python -m src.ml.trainer`")

    st.markdown("---")
    st.caption("Phase 1+2+6: Telemetry + ML + Feedback")
    st.caption("Built with Python · Streamlit · LightGBM")

# ─────────────────────────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────────────────────────
st.title("🎮 Game Performance Copilot")
st.markdown("**Real-Time AI Monitoring  ·  ML FPS Prediction  ·  Optimization Recommendations**")
st.markdown("---")

# ─────────────────────────────────────────────────────────────
# LIVE LOOP
# ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
# REFRESH BUTTON — must live OUTSIDE the while loop so Streamlit
# only registers the key="refresh_recs" widget once per script run.
# Placing it inside the loop (or inside placeholder.container())
# re-registers the same key on every iteration → DuplicateWidgetID.
# ─────────────────────────────────────────────────────────────
col_btn, col_hint = st.columns([2, 8])
with col_btn:
    if st.button("🔄 Refresh Recommendations", key="refresh_recs"):
        st.session_state.recs           = None
        st.session_state.feedback_given = {}
with col_hint:
    st.caption(
        "Recommendations are generated once per session. "
        "Click Refresh to regenerate with current live metrics."
    )

placeholder = st.empty()

while True:

    # ── Collect all metrics ───────────────────────────────────
    metrics = collector.collect_all()

    if save_to_db:
        try:
            db.insert_telemetry(metrics)
        except Exception:
            pass

    # ── Run diagnostics ───────────────────────────────────────
    issues = diagnostics_engine.analyze(metrics)

    # ── Run ML prediction ─────────────────────────────────────
    prediction = predictor.predict(
        metrics, game_genre, resolution, preset, ray_tracing, upscaling
    )

    # ── Generate recommendations ONCE per session ─────────────
    # Only regenerates when session_state.recs is None
    # (first load, or after user clicks "Refresh Recommendations")
    if st.session_state.recs is None:
        try:
            raw_recs = rec_engine.generate(
                metrics, game_genre, resolution, preset,
                ray_tracing, upscaling, issues
            )
            # Store every recommendation to DB, attach returned ID
            for rec in raw_recs:
                rid = db.insert_recommendation(
                    recommendation     = rec.get("action", ""),
                    estimated_fps_gain = float(rec.get("estimated_fps_gain", 0)),
                    category           = rec.get("category", "general")
                )
                rec["id"] = rid      # attach so feedback buttons can reference it
            st.session_state.recs = raw_recs
        except Exception:
            st.session_state.recs = []

    # Use the stored recommendations for this render pass
    recs = st.session_state.recs or []

    # ── Unpack metric values ──────────────────────────────────
    gpu  = metrics.get("gpu", {})
    cpu  = metrics.get("cpu", {})
    mem  = metrics.get("memory", {})
    sys_ = metrics.get("system", {})

    gpu_util  = gpu.get("gpu_utilization") or 0
    vram_util = gpu.get("vram_utilization") or 0
    vram_used = gpu.get("vram_used_mb") or 0
    gpu_temp  = gpu.get("gpu_temperature") or 0
    gpu_clock = gpu.get("gpu_clock_mhz") or 0
    gpu_power = gpu.get("gpu_power_watts")

    cpu_util  = cpu.get("cpu_utilization") or 0
    per_core  = cpu.get("per_core_utilization") or []

    ram_util  = mem.get("ram_utilization") or 0
    ram_used  = mem.get("ram_used_gb") or 0
    ram_avail = mem.get("ram_available_gb") or 0

    with placeholder.container():

        # ════════════════════════════════════════════════════════
        # SECTION 1 — LIVE HARDWARE METRICS
        # ════════════════════════════════════════════════════════
        st.subheader("📊 Live Hardware Metrics")

        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

        with c1:
            st.metric("🖥️ GPU Usage", f"{gpu_util}%",
                      delta="MAXED" if gpu_util > 95 else ("High" if gpu_util > 80 else "Normal"),
                      delta_color="inverse" if gpu_util > 95 else "normal")
        with c2:
            vram_gb = round(vram_used / 1024, 2)
            st.metric("💾 VRAM Used", f"{vram_gb} GB",
                      delta="⚠️ Low" if vram_util > 75 else "OK",
                      delta_color="inverse" if vram_util > 75 else "normal")
        with c3:
            st.metric("🌡️ GPU Temp", f"{gpu_temp}°C",
                      delta="🔥 HOT" if gpu_temp > 85 else "OK",
                      delta_color="inverse" if gpu_temp > 85 else "normal")
        with c4:
            st.metric("⚡ GPU Clock", f"{gpu_clock} MHz")
        with c5:
            st.metric("⚙️ CPU Usage", f"{cpu_util}%",
                      delta="High" if cpu_util > 85 else "Normal",
                      delta_color="inverse" if cpu_util > 85 else "normal")
        with c6:
            st.metric("🧠 RAM Used", f"{ram_used} GB",
                      delta=f"{ram_avail:.1f} GB free",
                      delta_color="inverse" if ram_util > 82 else "normal")
        with c7:
            if gpu_power:
                st.metric("🔋 GPU Power", f"{gpu_power}W")
            else:
                st.metric("📊 RAM %", f"{ram_util}%")

        st.markdown("---")

        # ════════════════════════════════════════════════════════
        # SECTION 2 — UTILIZATION GAUGES
        # ════════════════════════════════════════════════════════
        st.subheader("📈 Utilization Gauges")

        def make_gauge(title, value, warn=75, crit=90):
            color = (
                "#ef4444" if value >= crit else
                "#f59e0b" if value >= warn else
                "#22c55e"
            )
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=round(value, 1),
                number={"suffix": "%", "font": {"size": 22, "color": "white"}},
                title={"text": title, "font": {"size": 13, "color": "white"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "white"},
                    "bar": {"color": color},
                    "bgcolor": "#1e2130",
                    "steps": [
                        {"range": [0, warn],     "color": "#111827"},
                        {"range": [warn, crit],  "color": "#1c1917"},
                        {"range": [crit, 100],   "color": "#1f0a0a"},
                    ],
                    "threshold": {
                        "line": {"color": "#ef4444", "width": 3},
                        "thickness": 0.8,
                        "value": crit
                    }
                }
            ))
            fig.update_layout(
                height=210,
                margin=dict(l=15, r=15, t=35, b=10),
                paper_bgcolor="#0e1117",
                font={"color": "white"}
            )
            return fig

        g1, g2, g3, g4 = st.columns(4)
        with g1:
            st.plotly_chart(make_gauge("GPU %",  gpu_util,  80, 95), use_container_width=True)
        with g2:
            st.plotly_chart(make_gauge("VRAM %", vram_util, 75, 90), use_container_width=True)
        with g3:
            st.plotly_chart(make_gauge("CPU %",  cpu_util,  80, 90), use_container_width=True)
        with g4:
            st.plotly_chart(make_gauge("RAM %",  ram_util,  82, 92), use_container_width=True)

        st.markdown("---")

        # ════════════════════════════════════════════════════════
        # SECTION 3 — AI DIAGNOSTICS ENGINE
        # ════════════════════════════════════════════════════════
        st.subheader("🤖 AI Diagnostics Engine")

        crit_count = sum(1 for i in issues if i["severity"] == "CRITICAL")
        high_count = sum(1 for i in issues if i["severity"] == "HIGH")

        if crit_count > 0:
            st.error(f"🚨 {crit_count} CRITICAL issue(s) detected — immediate action required!")
        elif high_count > 0:
            st.warning(f"⚠️ {high_count} HIGH severity issue(s) detected.")
        else:
            st.success("✅ System running optimally — no bottlenecks detected.")

        for issue in issues:
            sev   = issue["severity"]
            itype = issue["issue_type"].replace("_", " ")
            conf  = f"{issue['confidence'] * 100:.0f}%"
            desc  = issue["description"]

            if sev == "NONE":
                with st.expander(f"✅ {itype}  |  Confidence: {conf}", expanded=True):
                    st.write(desc)
            elif sev == "CRITICAL":
                with st.expander(f"🚨 CRITICAL  |  {itype}  |  Confidence: {conf}", expanded=True):
                    st.error(desc)
            elif sev == "HIGH":
                with st.expander(f"⚠️ HIGH  |  {itype}  |  Confidence: {conf}", expanded=True):
                    st.warning(desc)
            elif sev == "MEDIUM":
                with st.expander(f"ℹ️ MEDIUM  |  {itype}  |  Confidence: {conf}", expanded=False):
                    st.info(desc)

        st.markdown("---")

        # ════════════════════════════════════════════════════════
        # SECTION 4 — ML FPS PREDICTION
        # ════════════════════════════════════════════════════════
        st.subheader("🎯 ML FPS Prediction")

        pred_fps   = prediction.get("predicted_fps")
        pred_ft    = prediction.get("frame_time_ms")
        pred_tier  = prediction.get("performance_tier", "")
        pred_model = prediction.get("model_name", "")
        pred_err   = prediction.get("error")

        if pred_err:
            st.warning(f"⚠️ Prediction unavailable: {pred_err}")
            st.info("Run `python -m src.ml.trainer` to train the model first.")

        elif pred_fps:
            pm1, pm2, pm3, pm4, pm5 = st.columns(5)

            with pm1:
                fps_delta_color = "normal" if pred_fps >= 60 else "inverse"
                st.metric(
                    "🎮 Predicted FPS",
                    f"{pred_fps:.0f} FPS",
                    delta=pred_tier,
                    delta_color=fps_delta_color
                )
            with pm2:
                st.metric("⏱️ Frame Time", f"{pred_ft} ms")
            with pm3:
                genre_short = GAME_PROFILES[game_genre]["description"].split("(")[0].strip()
                st.metric("🕹️ Genre", genre_short)
            with pm4:
                rt_str = "ON 🔴" if ray_tracing else "OFF ✅"
                st.metric("🌟 Ray Tracing", rt_str)
            with pm5:
                up_label = upscaling.replace("_", " ").title() if upscaling != "none" else "None"
                st.metric("🚀 Upscaling", up_label)

            if pred_fps >= 144:
                st.success(
                    f"🟢 **EXCELLENT**  —  {pred_fps:.0f} FPS  ·  {pred_ft}ms frame time  ·  "
                    f"Well above 144 Hz target. Your settings are great!"
                )
            elif pred_fps >= 60:
                st.success(
                    f"🟡 **SMOOTH**  —  {pred_fps:.0f} FPS  ·  {pred_ft}ms frame time  ·  "
                    f"Above 60 FPS target. Good gaming experience."
                )
            elif pred_fps >= 30:
                st.warning(
                    f"🟠 **ACCEPTABLE**  —  {pred_fps:.0f} FPS  ·  {pred_ft}ms frame time  ·  "
                    f"Playable but not ideal. Check recommendations below."
                )
            else:
                st.error(
                    f"🔴 **POOR**  —  {pred_fps:.0f} FPS  ·  {pred_ft}ms frame time  ·  "
                    f"Below 30 FPS — significant optimization needed."
                )

            st.caption(
                f"Model: **{pred_model}** (R²=97.5%, MAE=7.8 FPS)  ·  "
                f"Based on live telemetry + selected game settings"
            )

        st.markdown("---")

        # ════════════════════════════════════════════════════════
        # SECTION 5 — OPTIMIZATION RECOMMENDATIONS + FEEDBACK
        # ════════════════════════════════════════════════════════
        st.subheader("💡 Optimization Recommendations")

        if not predictor.is_loaded:
            st.info("ℹ️ Train the ML model to get AI-powered recommendations.")

        elif not recs:
            st.success(
                "✅ Your current settings are already well-optimized "
                "for your RTX 3050 Ti + i7-12650H!"
            )
        else:
            st.caption(
                f"Found **{len(recs)}** recommendation(s) — try them and use "
                f"👍 / 👎 to tell us if they helped!"
            )

            for rec in recs:
                rec_id = rec.get("id")
                gain   = rec.get("estimated_fps_gain", 0)
                gain_badge = (
                    "🟢 HIGH IMPACT"   if gain >= 20 else
                    "🟡 MEDIUM IMPACT" if gain >= 10 else
                    "🔵 LOW IMPACT"
                )

                with st.container(border=True):
                    left_col, right_col = st.columns([8, 2])

                    with left_col:
                        st.markdown(
                            f"**{rec.get('icon', '🎮')} {rec.get('action', 'Recommendation')}**"
                            f"  —  {gain_badge}  —  **+{gain:.0f} FPS** estimated"
                        )
                        st.caption(rec.get("description", ""))
                        st.markdown(
                            f"`{rec.get('category', '').upper()}` &nbsp;|&nbsp; "
                            f"Difficulty: `{rec.get('difficulty', '')}`"
                        )

                    with right_col:
                        # Show recorded state OR voting buttons
                        if rec_id in st.session_state.feedback_given:
                            if st.session_state.feedback_given[rec_id]:
                                st.success("👍 Helpful!")
                            else:
                                st.info("👎 Noted")
                        else:
                            st.caption("Was this helpful?")
                            fb1, fb2 = st.columns(2)
                            with fb1:
                                if st.button("👍", key=f"up_{rec_id}",
                                             help="This helped me!"):
                                    db.update_recommendation_feedback(rec_id, True)
                                    st.session_state.feedback_given[rec_id] = True
                            with fb2:
                                if st.button("👎", key=f"dn_{rec_id}",
                                             help="Did not help"):
                                    db.update_recommendation_feedback(rec_id, False)
                                    st.session_state.feedback_given[rec_id] = False

        st.markdown("---")

        # ════════════════════════════════════════════════════════
        # SECTION 6 — FPS PREDICTION MATRIX
        # ════════════════════════════════════════════════════════
        st.subheader("📊 FPS Prediction Matrix")
        st.caption(
            f"Predicted FPS across all Resolution × Quality Preset combinations  "
            f"(★ = your current setting  |  no RT  |  no upscaling  |  "
            f"genre: {GAME_PROFILES[game_genre]['description'].split('(')[0].strip()})"
        )

        if predictor.is_loaded:
            try:
                res_list    = list(RESOLUTION_CONFIG.keys())
                preset_list = list(PRESET_CONFIG.keys())
                matrix_rows = []

                for res in res_list:
                    row = {"Resolution": res}
                    for p in preset_list:
                        r      = predictor.predict(metrics, game_genre, res, p, False, "none")
                        fps    = r.get("predicted_fps")
                        marker = "★ " if (res == resolution and p == preset) else ""
                        row[p.title()] = f"{marker}{fps:.0f}" if fps else "N/A"
                    matrix_rows.append(row)

                df_matrix = pd.DataFrame(matrix_rows)
                st.dataframe(df_matrix, use_container_width=True, hide_index=True)
                st.caption("★ = Your current settings | Values in FPS")

            except Exception as e:
                st.caption(f"Matrix unavailable: {e}")
        else:
            st.info("Train the model to see the FPS matrix.")

        st.markdown("---")

        # ════════════════════════════════════════════════════════
        # SECTION 7 — PER-CORE CPU UTILIZATION
        # ════════════════════════════════════════════════════════
        if per_core:
            st.subheader(f"🔧 Per-Core CPU Utilization — i7-12650H ({len(per_core)} Threads)")
            st.caption("First 12 = Performance cores (6P × 2 threads)  |  Last 4 = Efficiency cores")

            core_labels = []
            for i in range(len(per_core)):
                core_labels.append(
                    f"P{i//2}·T{i%2}" if i < 12 else f"E{i - 12}"
                )

            bar_colors = [
                "#ef4444" if v > 90 else
                "#f59e0b" if v > 70 else
                "#3b82f6"
                for v in per_core
            ]

            fig = go.Figure(go.Bar(
                x=core_labels,
                y=per_core,
                marker_color=bar_colors,
                text=[f"{v:.0f}%" for v in per_core],
                textposition="outside",
                textfont={"size": 10, "color": "white"}
            ))
            fig.update_layout(
                height=260,
                paper_bgcolor="#0e1117",
                plot_bgcolor="#0e1117",
                font={"color": "white", "size": 11},
                xaxis={"tickangle": 0, "gridcolor": "#1e2130"},
                yaxis={"range": [0, 115], "gridcolor": "#1e2130"},
                margin=dict(l=10, r=10, t=30, b=30)
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("---")

        # ════════════════════════════════════════════════════════
        # SECTION 8 — TOP BACKGROUND PROCESSES
        # ════════════════════════════════════════════════════════
        st.subheader("🔍 Top Background Processes (CPU Impact)")
        top_procs = sys_.get("top_processes", [])

        if top_procs:
            df_procs = pd.DataFrame(top_procs)[
                ["pid", "name", "cpu_percent", "memory_percent"]
            ]
            df_procs.columns     = ["PID", "Process Name", "CPU %", "Memory %"]
            df_procs["CPU %"]    = df_procs["CPU %"].round(2)
            df_procs["Memory %"] = df_procs["Memory %"].round(2)
            st.dataframe(df_procs, use_container_width=True, hide_index=True)

        st.markdown("---")

        # ════════════════════════════════════════════════════════
        # SECTION 9 — FEEDBACK ANALYTICS
        # ════════════════════════════════════════════════════════
        st.subheader("📊 Recommendation Feedback Analytics")

        try:
            summary = db.get_feedback_summary()

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📋 Total Stored",   summary["total_recommendations"])
            m2.metric("💬 Feedback Given", summary["feedback_given"])
            m3.metric("👍 Helpful",        summary["helpful"])
            m4.metric("👎 Not Helpful",    summary["not_helpful"])

            if summary["feedback_given"] > 0:
                st.progress(
                    summary["helpful_percentage"] / 100,
                    text=(
                        f"**{summary['helpful_percentage']}% "
                        f"of rated recommendations were helpful**"
                    )
                )

                if summary["by_category"]:
                    st.subheader("By Category")
                    cat_df = pd.DataFrame(summary["by_category"])
                    st.bar_chart(
                        cat_df.set_index("category")[["helpful", "not_helpful"]]
                    )
            else:
                st.info(
                    "No feedback recorded yet — use 👍 / 👎 buttons above "
                    "after trying a recommendation!"
                )

            with st.expander("📋 Recent Recommendations History"):
                recent = db.get_recent_recommendations(limit=20)
                if recent:
                    df_recent = pd.DataFrame(recent)
                    # Map int/None to readable labels — use fillna for NaN safety
                    df_recent["was_helpful"] = (
                        df_recent["was_helpful"]
                        .map({1: "👍 Helpful", 0: "👎 Not Helpful"})
                        .fillna("⏳ Pending")
                    )
                    st.dataframe(df_recent, use_container_width=True, hide_index=True)
                else:
                    st.caption("No history yet.")

        except Exception as e:
            st.warning(f"Could not load feedback analytics: {e}")

        # ════════════════════════════════════════════════════════
        # FOOTER
        # ════════════════════════════════════════════════════════
        st.markdown("---")
        fa, fb, fc = st.columns(3)
        with fa:
            st.caption(f"🕐 Last updated: {metrics['timestamp']}")
        with fb:
            st.caption(f"⏱️ Refresh: every {refresh_rate}s")
        with fc:
            try:
                st.caption(f"💾 Records saved: {db.get_total_records():,}")
            except Exception:
                pass

    time.sleep(refresh_rate)