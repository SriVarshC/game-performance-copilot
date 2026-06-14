import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.telemetry.collector import TelemetryCollector
from src.database.db_manager import DatabaseManager
from src.diagnostics.engine import DiagnosticsEngine

# ─────────────────────────────────────────────────────────────
# PAGE CONFIGURATION
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
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# INITIALIZE (cached so they only load once)
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def load_components():
    collector   = TelemetryCollector()
    db          = DatabaseManager()
    diagnostics = DiagnosticsEngine()
    return collector, db, diagnostics

collector, db, diagnostics_engine = load_components()

# ─────────────────────────────────────────────────────────────
# SIDEBAR — YOUR SYSTEM INFO
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎮 Game Performance Copilot")
    st.markdown("---")

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
    refresh_rate = st.slider("⏱️ Refresh Rate (sec)", 1, 10, 2)
    save_to_db   = st.checkbox("💾 Save to Database", value=True)
    st.markdown("---")

    # Database record count
    try:
        total_records = db.get_total_records()
        st.metric("📊 Records Collected", f"{total_records:,}")
    except Exception:
        pass

    st.markdown("---")
    st.caption("Phase 1: Telemetry + Diagnostics")
    st.caption("Built with Python + Streamlit")

# ─────────────────────────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────────────────────────
st.title("🎮 Game Performance Copilot")
st.markdown("**Real-Time AI Hardware Monitoring & Bottleneck Diagnostics**")
st.markdown("---")

# ─────────────────────────────────────────────────────────────
# LIVE MONITORING LOOP
# ─────────────────────────────────────────────────────────────
placeholder = st.empty()

while True:
    # Collect metrics
    metrics = collector.collect_all()

    # Save to database
    if save_to_db:
        try:
            db.insert_telemetry(metrics)
        except Exception as e:
            pass

    # Run diagnostics
    issues = diagnostics_engine.analyze(metrics)

    # Extract values
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
    cpu_freq  = cpu.get("cpu_frequency_mhz") or 0
    cpu_temp  = cpu.get("cpu_temperature")
    per_core  = cpu.get("per_core_utilization") or []

    ram_util  = mem.get("ram_utilization") or 0
    ram_used  = mem.get("ram_used_gb") or 0
    ram_avail = mem.get("ram_available_gb") or 0
    pf_util   = mem.get("page_file_utilization") or 0

    with placeholder.container():

        # ── SECTION 1: KEY METRICS ROW ──────────────────────
        st.subheader("📊 Live Hardware Metrics")

        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

        with c1:
            color = "inverse" if gpu_util > 95 else "normal"
            st.metric("🖥️ GPU Usage",
                      f"{gpu_util}%",
                      delta="MAXED" if gpu_util > 95 else ("High" if gpu_util > 80 else "Normal"),
                      delta_color=color)
        with c2:
            vram_gb = round(vram_used / 1024, 1)
            st.metric("💾 VRAM",
                      f"{vram_gb} GB",
                      delta="⚠️ Low" if vram_util > 75 else "OK",
                      delta_color="inverse" if vram_util > 75 else "normal")
        with c3:
            st.metric("🌡️ GPU Temp",
                      f"{gpu_temp}°C",
                      delta="🔥 HOT" if gpu_temp > 85 else "OK",
                      delta_color="inverse" if gpu_temp > 85 else "normal")
        with c4:
            st.metric("⚡ GPU Clock",
                      f"{gpu_clock} MHz")
        with c5:
            st.metric("⚙️ CPU Usage",
                      f"{cpu_util}%",
                      delta="High" if cpu_util > 85 else "Normal",
                      delta_color="inverse" if cpu_util > 85 else "normal")
        with c6:
            st.metric("🧠 RAM Usage",
                      f"{ram_used} GB",
                      delta=f"{ram_avail:.1f} GB free",
                      delta_color="inverse" if ram_util > 82 else "normal")
        with c7:
            if gpu_power is not None:
                st.metric("🔋 GPU Power", f"{gpu_power}W")
            else:
                st.metric("🌡️ CPU Temp",
                          f"{cpu_temp}°C" if cpu_temp else "N/A")

        st.markdown("---")

        # ── SECTION 2: UTILIZATION GAUGES ───────────────────
        st.subheader("📈 Utilization Gauges")

        g1, g2, g3, g4 = st.columns(4)

        def make_gauge(title, value, max_val=100, warn=75, crit=90, unit="%"):
            bar_color = "#ef4444" if value >= crit else ("#f59e0b" if value >= warn else "#22c55e")
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=round(value, 1),
                number={"suffix": unit, "font": {"size": 22, "color": "white"}},
                title={"text": title, "font": {"size": 13, "color": "white"}},
                gauge={
                    "axis": {"range": [0, max_val], "tickcolor": "white"},
                    "bar": {"color": bar_color},
                    "bgcolor": "#1e2130",
                    "bordercolor": "#2d3250",
                    "steps": [
                        {"range": [0, warn], "color": "#111827"},
                        {"range": [warn, crit], "color": "#1c1917"},
                        {"range": [crit, max_val], "color": "#1f0a0a"},
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

        with g1:
            st.plotly_chart(
                make_gauge("GPU %", gpu_util, warn=80, crit=95),
                use_container_width=True
            )
        with g2:
            st.plotly_chart(
                make_gauge("VRAM %", vram_util, warn=75, crit=90),
                use_container_width=True
            )
        with g3:
            st.plotly_chart(
                make_gauge("CPU %", cpu_util, warn=80, crit=90),
                use_container_width=True
            )
        with g4:
            st.plotly_chart(
                make_gauge("RAM %", ram_util, warn=82, crit=92),
                use_container_width=True
            )

        st.markdown("---")

        # ── SECTION 3: AI DIAGNOSTICS ────────────────────────
        st.subheader("🤖 AI Diagnostics Engine")

        critical_count = sum(1 for i in issues if i["severity"] == "CRITICAL")
        high_count     = sum(1 for i in issues if i["severity"] == "HIGH")

        if critical_count > 0:
            st.error(f"🚨 {critical_count} CRITICAL issue(s) detected! Immediate action required.")
        elif high_count > 0:
            st.warning(f"⚠️ {high_count} HIGH severity issue(s) detected.")
        else:
            st.success("✅ System running optimally. No bottlenecks detected.")

        for issue in issues:
            sev  = issue["severity"]
            itype = issue["issue_type"].replace("_", " ")
            conf  = issue["confidence"]
            desc  = issue["description"]
            conf_pct = f"{conf * 100:.0f}%"

            if sev == "NONE":
                with st.expander(f"✅ {itype} | Confidence: {conf_pct}", expanded=True):
                    st.write(desc)
            elif sev == "CRITICAL":
                with st.expander(f"🚨 CRITICAL | {itype} | Confidence: {conf_pct}", expanded=True):
                    st.error(desc)
            elif sev == "HIGH":
                with st.expander(f"⚠️ HIGH | {itype} | Confidence: {conf_pct}", expanded=True):
                    st.warning(desc)
            elif sev == "MEDIUM":
                with st.expander(f"ℹ️ MEDIUM | {itype} | Confidence: {conf_pct}", expanded=False):
                    st.info(desc)

        st.markdown("---")

        # ── SECTION 4: PER-CORE CPU BAR CHART ───────────────
        if per_core:
            st.subheader(f"🔧 Per-Core CPU Utilization — i7-12650H ({len(per_core)} Threads)")

            # First 6 are Performance cores (P-cores), next 4 are Efficiency cores (E-cores)
            core_labels = []
            for i in range(len(per_core)):
                if i < 12:  # P-cores have 2 threads each = 12 logical (6 cores x 2)
                    core_labels.append(f"P-Core {i//2} T{i%2}")
                else:
                    core_labels.append(f"E-Core {(i-12)//1}")

            bar_colors = [
                "#ef4444" if v > 90 else "#f59e0b" if v > 70 else "#3b82f6"
                for v in per_core
            ]

            fig = go.Figure(go.Bar(
                x=core_labels,
                y=per_core,
                marker_color=bar_colors,
                text=[f"{v}%" for v in per_core],
                textposition="outside"
            ))
            fig.update_layout(
                height=280,
                paper_bgcolor="#0e1117",
                plot_bgcolor="#0e1117",
                font={"color": "white", "size": 11},
                xaxis={"tickangle": -45},
                yaxis={"range": [0, 110], "gridcolor": "#1e2130"},
                margin=dict(l=10, r=10, t=20, b=60),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("---")

        # ── SECTION 5: TOP BACKGROUND PROCESSES ─────────────
        st.subheader("🔍 Top Background Processes (CPU Impact)")

        top_procs = sys_.get("top_processes", [])
        if top_procs:
            df_procs = pd.DataFrame(top_procs)[["pid", "name", "cpu_percent", "memory_percent"]]
            df_procs.columns = ["PID", "Process Name", "CPU %", "Memory %"]
            df_procs["CPU %"]    = df_procs["CPU %"].round(2)
            df_procs["Memory %"] = df_procs["Memory %"].round(2)
            st.dataframe(df_procs, use_container_width=True, hide_index=True)

        # ── FOOTER ───────────────────────────────────────────
        st.markdown("---")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.caption(f"🕐 Last updated: {metrics['timestamp']}")
        with col_b:
            st.caption(f"⏱️ Refresh: every {refresh_rate}s")
        with col_c:
            try:
                st.caption(f"💾 Records saved: {db.get_total_records():,}")
            except Exception:
                pass

    time.sleep(refresh_rate)