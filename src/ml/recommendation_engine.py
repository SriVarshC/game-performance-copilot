"""
Optimization Recommendation Engine v2 — Phase 6 Upgrade
Generates actionable, severity-ranked, bottleneck-aware recommendations
using the FPS predictor and live diagnostic results.

Phase 6 changes:
  1. _assign_severity()      — CRITICAL / HIGH / MEDIUM / LOW per recommendation
  2. BOTTLENECK_ACTIONS      — Targeted actions per bottleneck class from predictor
  3. health_score context    — Health score appended to bottleneck descriptions
"""

from src.ml.dataset_generator import PRESET_CONFIG, RESOLUTION_CONFIG, UPSCALING_BOOST


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6 — BOTTLENECK ACTION TABLES (module-level, used by RecommendationEngine)
# ═══════════════════════════════════════════════════════════════════════════════

# Action names per bottleneck class — matches predictor's bottleneck_class output
BOTTLENECK_ACTIONS = {
    "CPU":     ["Lower crowd density", "Reduce simulation settings", "Disable background apps"],
    "GPU":     ["Lower resolution",    "Reduce shadow quality",      "Disable ray tracing"],
    "MEMORY":  ["Lower texture quality","Enable upscaling",          "Close other apps"],
    "THERMAL": ["Clean laptop vents",  "Reduce power limit",         "Enable power saver mode"],
}

# Full metadata for each bottleneck action: (category, icon, est_gain, description, difficulty)
_BOTTLENECK_ACTION_META = {

    # ── CPU actions ──────────────────────────────────────────────────────────
    "Lower crowd density": (
        "System", "🖥️", 7.0,
        "CPU bottleneck detected. Lowering crowd/NPC density directly reduces CPU simulation "
        "load on your i7-12650H — one of the most CPU-intensive in-game settings.",
        "Easy"
    ),
    "Reduce simulation settings": (
        "System", "🖥️", 6.0,
        "CPU bottleneck detected. Physics, AI, and simulation settings run on CPU threads. "
        "Reducing these frees headroom on your i7-12650H's performance cores.",
        "Easy"
    ),
    "Disable background apps": (
        "System", "🖥️", 8.0,
        "CPU bottleneck detected. Background processes compete directly for CPU cycles. "
        "Close Chrome, Discord, Spotify, and OneDrive to recover CPU headroom.",
        "Easy"
    ),

    # ── GPU actions ──────────────────────────────────────────────────────────
    "Lower resolution": (
        "Resolution", "📐", 10.0,
        "GPU bottleneck detected. Resolution has the largest per-frame GPU cost. "
        "Dropping one resolution tier directly reduces pixel fill rate on your RTX 3050 Ti.",
        "Medium"
    ),
    "Reduce shadow quality": (
        "Graphics", "🌟", 7.0,
        "GPU bottleneck detected. Shadow rendering is one of the most GPU-intensive settings. "
        "Medium shadows on RTX 3050 Ti gives strong FPS gains with minimal visual impact.",
        "Easy"
    ),
    "Disable ray tracing": (
        "Graphics", "🌟", 12.0,
        "GPU bottleneck detected. Ray tracing is extremely expensive on 4GB VRAM. "
        "Disabling it recovers both GPU compute and VRAM headroom immediately.",
        "Easy"
    ),

    # ── MEMORY actions ───────────────────────────────────────────────────────
    "Lower texture quality": (
        "VRAM", "💾", 10.0,
        "Memory bottleneck detected. Textures are the largest VRAM consumer. "
        "Setting textures to Medium prevents overflow into shared system RAM on RTX 3050 Ti.",
        "Easy"
    ),
    "Enable upscaling": (
        "Upscaling", "🚀", 8.0,
        "Memory bottleneck detected. Upscaling (DLSS/FSR) reduces render resolution, "
        "lowering both GPU memory bandwidth and VRAM usage significantly.",
        "Easy"
    ),
    "Close other apps": (
        "System", "🧠", 5.0,
        "Memory bottleneck detected. With 16GB RAM at 82-85% idle usage, "
        "closing background apps frees shared memory used by both CPU and GPU.",
        "Easy"
    ),

    # ── THERMAL actions ──────────────────────────────────────────────────────
    "Clean laptop vents": (
        "Thermal", "❄️", 8.0,
        "Thermal throttling detected on RTX 3050 Ti Laptop. Dust-blocked vents are a common "
        "cause. Cleaning them typically reduces temps by 5-10°C and recovers clock speed.",
        "Medium"
    ),
    "Reduce power limit": (
        "Thermal", "❄️", 6.0,
        "Thermal throttling detected. Capping GPU power limit (e.g. 80W → 60W via "
        "MSI Afterburner) reduces heat output and prevents thermal throttling cycles.",
        "Easy"
    ),
    "Enable power saver mode": (
        "Thermal", "❄️", 5.0,
        "Thermal throttling detected. Switching to Balanced/Power Saver in Windows power "
        "settings reduces sustained CPU+GPU TDP and stabilises frame times under heat.",
        "Easy"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class RecommendationEngine:
    """
    Generates ranked, severity-labelled, bottleneck-aware optimization recommendations.
    Each recommendation uses the ML predictor to estimate real FPS gain.
    Tuned specifically for RTX 3050 Ti (4GB VRAM) + i7-12650H + 16GB RAM.

    Phase 6 upgrades:
      - severity field on every recommendation (CRITICAL/HIGH/MEDIUM/LOW)
      - bottleneck_class from predictor drives a dedicated targeted rec section
      - health_score from predictor appended as context to bottleneck descriptions
    """

    def __init__(self, predictor):
        self.predictor = predictor

    # ─────────────────────────────────────────────────────────────────────────
    # MAIN ENTRY POINT
    # ─────────────────────────────────────────────────────────────────────────
    def generate(self, live_metrics: dict, game_genre: str,
                 resolution: str, preset: str,
                 ray_tracing: bool, upscaling: str,
                 issues: list) -> list:
        """
        Generate top-6 optimization recommendations.
        Each recommendation includes ML-predicted FPS gain and severity label.

        Args:
            live_metrics : Current hardware telemetry snapshot
            game_genre   : Selected game genre key
            resolution   : Current resolution string e.g. "1920x1080"
            preset       : Current quality preset e.g. "high"
            ray_tracing  : Whether ray tracing is enabled
            upscaling    : Current upscaling mode
            issues       : List of detected diagnostic issues

        Returns:
            List of recommendation dicts sorted by estimated FPS gain.
            Each dict now includes a 'severity' key (Phase 6).
        """
        if not self.predictor.is_loaded:
            return []

        # ── Baseline prediction ───────────────────────────────────────────────
        # Phase 6: also captures bottleneck_class and health_score from predictor
        baseline     = self.predictor.predict(
            live_metrics, game_genre, resolution, preset, ray_tracing, upscaling
        )
        baseline_fps = baseline.get("predicted_fps")
        if not baseline_fps:
            return []

        # Phase 6 — extract new ML outputs (both Optional, safe if model not loaded)
        bottleneck_class = baseline.get("bottleneck_class")   # "CPU"|"GPU"|"MEMORY"|"THERMAL"|None
        health_score     = baseline.get("health_score")        # float 0-100 | None

        # ── Phase 6: Build health context string ──────────────────────────────
        # Appended to bottleneck recommendation descriptions for user awareness
        health_ctx = ""
        if health_score is not None:
            if health_score < 30:
                health_ctx = (
                    f" System health is critically low ({health_score:.0f}/100)"
                    f" — immediate action strongly recommended."
                )
            elif health_score < 50:
                health_ctx = (
                    f" System health is poor ({health_score:.0f}/100)"
                    f" — multiple improvements needed."
                )
            elif health_score < 70:
                health_ctx = f" System health is fair ({health_score:.0f}/100)."
            # health >= 70: no context appended (system is healthy)

        presets     = list(PRESET_CONFIG.keys())
        resolutions = list(RESOLUTION_CONFIG.keys())
        curr_p_idx  = presets.index(preset)         if preset     in presets     else 2
        curr_r_idx  = resolutions.index(resolution) if resolution in resolutions else 1

        recs = []

        # ── 1. Disable Ray Tracing ────────────────────────────────────────────
        if ray_tracing:
            result = self.predictor.predict(
                live_metrics, game_genre, resolution, preset, False, upscaling
            )
            gain = self._gain(result, baseline_fps)
            if gain > 2:
                recs.append(self._build(
                    action="Disable Ray Tracing",
                    category="Graphics",
                    icon="🌟",
                    gain=gain,
                    desc=(
                        "Ray tracing is extremely GPU-intensive on RTX 3050 Ti (4GB VRAM). "
                        "Disabling it recovers both GPU compute and VRAM headroom at once."
                    ),
                    difficulty="Easy"
                ))

        # ── 2. Enable DLSS (RTX exclusive, AI-based) ─────────────────────────
        if upscaling == "none":
            best_gain, best_mode = 0, None
            for mode in ["dlss_quality", "dlss_balanced", "dlss_performance"]:
                result = self.predictor.predict(
                    live_metrics, game_genre, resolution, preset, ray_tracing, mode
                )
                gain = self._gain(result, baseline_fps)
                if gain > best_gain:
                    best_gain, best_mode = gain, mode

            if best_gain > 5 and best_mode:
                label = best_mode.replace("_", " ").title()
                recs.append(self._build(
                    action=f"Enable DLSS ({label})",
                    category="Upscaling",
                    icon="🚀",
                    gain=best_gain,
                    desc=(
                        f"Your RTX 3050 Ti supports NVIDIA DLSS AI upscaling. "
                        f"DLSS {label} boosts FPS significantly with minimal visual quality loss. "
                        f"Best option for your GPU."
                    ),
                    difficulty="Easy"
                ))

        # ── 3. Enable FSR (works on all GPUs) ────────────────────────────────
        if upscaling == "none":
            best_gain, best_mode = 0, None
            for mode in ["fsr_quality", "fsr_balanced"]:
                result = self.predictor.predict(
                    live_metrics, game_genre, resolution, preset, ray_tracing, mode
                )
                gain = self._gain(result, baseline_fps)
                if gain > best_gain:
                    best_gain, best_mode = gain, mode

            if best_gain > 3 and best_mode:
                label = best_mode.replace("_", " ").title()
                recs.append(self._build(
                    action=f"Enable FSR ({label})",
                    category="Upscaling",
                    icon="⚡",
                    gain=best_gain,
                    desc=(
                        f"AMD FSR works on ALL GPUs including RTX 3050 Ti. "
                        f"FSR {label} uses spatial upscaling for a solid FPS gain. "
                        f"Good fallback if game doesn't support DLSS."
                    ),
                    difficulty="Easy"
                ))

        # ── 4. Lower Quality Preset ───────────────────────────────────────────
        if curr_p_idx > 0:
            lower_preset = presets[curr_p_idx - 1]
            result = self.predictor.predict(
                live_metrics, game_genre, resolution, lower_preset, ray_tracing, upscaling
            )
            gain = self._gain(result, baseline_fps)
            if gain > 2:
                recs.append(self._build(
                    action=f"Lower Preset: {preset.title()} → {lower_preset.title()}",
                    category="Preset",
                    icon="🔧",
                    gain=gain,
                    desc=(
                        f"Dropping one quality tier reduces overall GPU workload. "
                        f"On RTX 3050 Ti, the difference between {preset} and {lower_preset} "
                        f"is often visually subtle but FPS-significant."
                    ),
                    difficulty="Easy"
                ))

        # ── 5. Lower Resolution ───────────────────────────────────────────────
        if curr_r_idx > 0:
            lower_res = resolutions[curr_r_idx - 1]
            result = self.predictor.predict(
                live_metrics, game_genre, lower_res, preset, ray_tracing, upscaling
            )
            gain = self._gain(result, baseline_fps)
            if gain > 2:
                recs.append(self._build(
                    action=f"Lower Resolution → {lower_res}",
                    category="Resolution",
                    icon="📐",
                    gain=gain,
                    desc=(
                        f"Resolution has the single largest impact on GPU workload. "
                        f"Dropping to {lower_res} dramatically reduces pixel fill rate "
                        f"on your RTX 3050 Ti."
                    ),
                    difficulty="Medium"
                ))

        # ── 6. Two-Step Combo: Lower Preset + Enable DLSS ────────────────────
        if curr_p_idx > 0 and upscaling == "none":
            lower_preset = presets[curr_p_idx - 1]
            result = self.predictor.predict(
                live_metrics, game_genre, resolution,
                lower_preset, ray_tracing, "dlss_quality"
            )
            gain = self._gain(result, baseline_fps)
            if gain > 15:
                recs.append(self._build(
                    action="Lower Preset + Enable DLSS Quality",
                    category="Combo",
                    icon="🎯",
                    gain=gain,
                    desc=(
                        f"Best-of-both-worlds combo: drop to {lower_preset} preset for lower "
                        f"GPU load, then use DLSS Quality to restore visual fidelity. "
                        f"Highly recommended for RTX 3050 Ti."
                    ),
                    difficulty="Easy"
                ))

        # ── 7. Diagnostics-Based Recommendations ─────────────────────────────
       
        
        issue_types = {
            i.get("issue_type")
            for i in issues
            if isinstance(i, dict) and i.get("issue_type")
            }
        

        if "CPU_BOTTLENECK" in issue_types:
            recs.append(self._build(
                action="Close Background Applications",
                category="System",
                icon="🖥️",
                gain=8.0,
                desc=(
                    "CPU bottleneck detected (i7-12650H at high utilization). "
                    "Close Chrome tabs, Discord, Spotify, OneDrive to free CPU cycles "
                    "and also reduce shared RAM pressure."
                ),
                difficulty="Easy"
            ))

        if {"VRAM_CRITICAL", "VRAM_PRESSURE"} & issue_types:
            recs.append(self._build(
                action="Lower Texture Quality to Medium",
                category="VRAM",
                icon="💾",
                gain=12.0,
                desc=(
                    "VRAM pressure detected on 4GB RTX 3050 Ti. "
                    "Textures are the single largest VRAM consumer. "
                    "Setting textures to Medium prevents overflow into shared system RAM."
                ),
                difficulty="Easy"
            ))

        if {"RAM_PRESSURE", "RAM_CRITICAL", "PAGE_FILE_OVERUSE"} & issue_types:
            recs.append(self._build(
                action="Free System RAM (Close Browser Tabs)",
                category="System",
                icon="🧠",
                gain=5.0,
                desc=(
                    "RAM under pressure (16GB system already ~82%+ used). "
                    "Your GPU uses shared system RAM for VRAM overflow. "
                    "Freeing RAM improves both system and GPU performance."
                ),
                difficulty="Easy"
            ))

        if {"GPU_THERMAL_THROTTLING", "GPU_THERMAL_CRITICAL"} & issue_types:
            recs.append(self._build(
                action="Use a Laptop Cooling Pad",
                category="Thermal",
                icon="❄️",
                gain=10.0,
                desc=(
                    "GPU thermal throttling detected on RTX 3050 Ti Laptop. "
                    "A cooling pad typically reduces temps by 5-15°C "
                    "and recovers throttled GPU clock speed."
                ),
                difficulty="Medium"
            ))

        # ── 8. Phase 6: Bottleneck-Aware Recommendations ─────────────────────
        # Uses bottleneck_class from the Phase 5 ML predictor to inject
        # targeted actions. health_score appended as context to descriptions.
        if bottleneck_class and bottleneck_class in BOTTLENECK_ACTIONS:
            for action_name in BOTTLENECK_ACTIONS[bottleneck_class]:
                meta = _BOTTLENECK_ACTION_META.get(action_name)
                if not meta:
                    continue
                category, icon, gain, desc, difficulty = meta
                recs.append(self._build(
                    action=action_name,
                    category=category,
                    icon=icon,
                    gain=gain,
                    desc=desc + health_ctx,   # Phase 6: health context appended
                    difficulty=difficulty
                ))

        # ── Sort by gain, deduplicate by action name, return top 6 ────────────
        recs.sort(key=lambda x: x["estimated_fps_gain"], reverse=True)

        seen_actions, unique_recs = set(), []
        for rec in recs:
            if rec["action"] not in seen_actions:
                seen_actions.add(rec["action"])
                unique_recs.append(rec)

        return unique_recs[:6]

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _assign_severity(self, fps_gain: float) -> str:
        """
        Phase 6 — Classify recommendation urgency by estimated FPS gain.

        CRITICAL : >= 20 FPS — major bottleneck, act now
        HIGH     : >= 10 FPS — significant improvement available
        MEDIUM   : >=  5 FPS — noticeable improvement
        LOW      :  <  5 FPS — minor tweak
        """
        if fps_gain >= 20: return "CRITICAL"
        if fps_gain >= 10: return "HIGH"
        if fps_gain >= 5:  return "MEDIUM"
        return "LOW"

    def _gain(self, result: dict, baseline_fps: float) -> float:
        """Safely compute FPS gain over baseline."""
        pred = result.get("predicted_fps")
        if pred is None:
            return 0.0
        return round(pred - baseline_fps, 1)

    def _build(self, action: str, category: str, icon: str,
               gain: float, desc: str, difficulty: str) -> dict:
        """
        Build a recommendation dict.
        Phase 6: 'severity' field auto-assigned via _assign_severity().
        """
        return {
            "action":             action,
            "category":          category,
            "icon":              icon,
            "estimated_fps_gain": gain,
            "severity":          self._assign_severity(gain),  # Phase 6: NEW
            "description":       desc,
            "difficulty":        difficulty
        }