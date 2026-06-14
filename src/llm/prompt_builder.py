"""
Prompt Builder for Game Performance Copilot LLM Assistant.
Injects live telemetry + diagnostics into prompts so the LLM
gives hardware-specific answers instead of generic advice.
"""

from typing import Any, Dict, List, Optional


# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT_BASE = """You are an expert PC gaming performance assistant built into Game Performance Copilot.
You help gamers diagnose performance issues, understand hardware bottlenecks, and optimize game settings.

SYSTEM HARDWARE:
- GPU: NVIDIA GeForce RTX 3050 Ti Laptop (4GB VRAM dedicated, supports DLSS and Ray Tracing)
- CPU: Intel i7-12650H (10 cores / 16 threads, hybrid Performance + Efficiency core architecture)
- RAM: 16 GB total (this system idles at 82-85% RAM usage — that is NORMAL for this machine)
- OS: Windows 11, NVIDIA Optimus hybrid graphics

HARDWARE THRESHOLDS (tuned specifically for this machine — use THESE numbers, not generic ones):
- GPU thermal warning    : 85 C  (throttling begins here on this laptop)
- GPU thermal critical   : 91 C  (severe throttle, performance tanks)
- CPU thermal warning    : 90 C
- GPU bottleneck         : above 95% utilization
- CPU bottleneck         : above 85% utilization (while GPU is below 55%)
- VRAM warning           : above 75% (3.07 GB of 4 GB)
- VRAM critical          : above 90% (3.69 GB of 4 GB)
- RAM warning            : above 82% (this is normal idle for this machine)
- RAM critical           : above 92%
- DLSS performance boost : up to 1.90x FPS
- Ray Tracing FPS cost   : approximately 48% FPS reduction on this GPU

IMPORTANT — NVIDIA OPTIMUS NOTE:
This laptop uses NVIDIA Optimus hybrid graphics. When not actively gaming, the RTX 3050 Ti
powers down completely. GPU metrics showing 0 utilization/low clock/low power means the GPU
is in power-save mode — this is NORMAL, not a problem.

RESPONSE RULES:
1. Be concise and specific — give actionable advice, not vague generic tips
2. Always reference the actual hardware above when relevant (RTX 3050 Ti, i7-12650H, etc.)
3. If live telemetry is provided, base your answer on THOSE EXACT numbers
4. Use ONLY the thresholds listed above — never use generic thresholds from your training data
5. If GPU metrics show 0, tell the user the GPU is idle due to Optimus power-save mode
6. Keep answers under 200 words unless a detailed explanation is genuinely needed
7. Write in plain conversational English — no markdown headers, no bullet symbols
8. If asked about something unrelated to PC gaming performance, politely redirect
"""


# ── Public Function ───────────────────────────────────────────────────────────
def build_prompt(
    question: str,
    metrics:  Optional[Dict[str, Any]]       = None,
    issues:   Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, str]]:
    """
    Build the messages list for the Ollama chat API.
    Injects live telemetry + detected issues into the system prompt.

    Returns:
        [
            {"role": "system", "content": "...hardware context..."},
            {"role": "user",   "content": "...question..."}
        ]
    """
    system_content = SYSTEM_PROMPT_BASE

    if metrics:
        system_content += "\n\nCURRENT LIVE HARDWARE METRICS (collected right now):\n"
        system_content += _format_metrics(metrics)
    else:
        system_content += "\n\nCURRENT LIVE HARDWARE METRICS: Not available for this query.\n"

    if issues:
        system_content += "\n\nCURRENT AI-DETECTED ISSUES:\n"
        system_content += _format_issues(issues)
    else:
        system_content += "\n\nCURRENT AI-DETECTED ISSUES: None — system appears optimal.\n"

    return [
        {"role": "system", "content": system_content},
        {"role": "user",   "content": question},
    ]


# ── Private Helpers ───────────────────────────────────────────────────────────
def _val(value, unit: str = "", zero_means_idle: bool = False) -> str:
    """
    Format a single metric value cleanly.
    - None        -> "N/A"
    - 0 (idle)    -> "0 [GPU idle — Optimus power-save mode]" if zero_means_idle=True
    - normal      -> "value unit"
    """
    if value is None:
        return "N/A"
    if zero_means_idle and (value == 0 or value == 0.0):
        return f"0{unit} (GPU is idle — Optimus power-save mode, normal when not gaming)"
    return f"{value}{unit}"


def _format_metrics(metrics: Dict[str, Any]) -> str:
    """
    Format telemetry dict into clean readable text for the LLM.

    Actual keys from TelemetryCollector.collect_all():
      gpu    -> gpu_name, gpu_utilization, vram_used_mb, vram_total_mb,
                vram_utilization, gpu_temperature, gpu_clock_mhz, gpu_power_watts
      cpu    -> cpu_utilization, cpu_temperature, cpu_frequency_mhz
      memory -> ram_used_gb, ram_total_gb, ram_utilization, page_file_utilization
    """
    lines = []

    # ── GPU ──────────────────────────────────────────────────────────────────
    gpu = metrics.get("gpu", {})
    if gpu:
        gpu_name = gpu.get("gpu_name", "RTX 3050 Ti Laptop")
        gpu_util = gpu.get("gpu_utilization", None)
        gpu_temp = gpu.get("gpu_temperature", None)
        gpu_clk  = gpu.get("gpu_clock_mhz",  None)
        gpu_pwr  = gpu.get("gpu_power_watts", None)
        vram_u   = gpu.get("vram_used_mb",    None)
        vram_t   = gpu.get("vram_total_mb",   4096)
        vram_pct = gpu.get("vram_utilization", None)

        lines.append(f"GPU Name        : {gpu_name}")
        lines.append(f"GPU Utilization : {_val(gpu_util, '%',  zero_means_idle=True)}")
        lines.append(f"GPU Temperature : {_val(gpu_temp, ' C', zero_means_idle=True)}")
        lines.append(f"GPU Clock       : {_val(gpu_clk,  ' MHz', zero_means_idle=True)}")
        lines.append(f"GPU Power       : {_val(gpu_pwr,  ' W',  zero_means_idle=True)}")
        lines.append(
            f"VRAM Used       : {_val(vram_u, ' MB')} "
            f"/ {vram_t} MB "
            f"({_val(vram_pct, '%')})"
        )

    # ── CPU ──────────────────────────────────────────────────────────────────
    cpu = metrics.get("cpu", {})
    if cpu:
        lines.append(f"CPU Utilization : {_val(cpu.get('cpu_utilization'),  '%')}")
        lines.append(f"CPU Temperature : {_val(cpu.get('cpu_temperature'),  ' C')}")
        lines.append(f"CPU Frequency   : {_val(cpu.get('cpu_frequency_mhz'), ' MHz')}")

    # ── Memory ───────────────────────────────────────────────────────────────
    memory = metrics.get("memory", {})
    if memory:
        lines.append(
            f"RAM Used        : {_val(memory.get('ram_used_gb'), ' GB')}"
            f" / {_val(memory.get('ram_total_gb'), ' GB')}"
            f" ({_val(memory.get('ram_utilization'), '%')})"
        )
        lines.append(
            f"Page File       : {_val(memory.get('page_file_utilization'), '%')} used"
        )

    return "\n".join(lines) if lines else "Telemetry fields were empty."


def _format_issues(issues: List[Dict[str, Any]]) -> str:
    """Format diagnostics issues list into clean readable text for the LLM."""
    if not issues:
        return "No issues detected."

    lines = []
    for issue in issues:
        issue_type  = issue.get("issue_type",  "UNKNOWN")
        severity    = issue.get("severity",    "UNKNOWN")
        confidence  = issue.get("confidence",  0)
        description = issue.get("description", "")
        lines.append(
            f"[{severity}] {issue_type}"
            f" (confidence: {confidence:.0%})"
            f" — {description}"
        )

    return "\n".join(lines)