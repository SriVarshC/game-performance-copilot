"""
Optimization Recommendation Engine
Generates actionable, ML-backed performance recommendations
using the FPS predictor and live diagnostic results.
"""

from src.ml.dataset_generator import PRESET_CONFIG, RESOLUTION_CONFIG, UPSCALING_BOOST


class RecommendationEngine:
    """
    Generates ranked optimization recommendations.
    Each recommendation uses the ML predictor to estimate real FPS gain.
    Tuned specifically for RTX 3050 Ti (4GB VRAM) + i7-12650H + 16GB RAM.
    """

    def __init__(self, predictor):
        self.predictor = predictor

    # ─────────────────────────────────────────────────────────
    # MAIN ENTRY POINT
    # ─────────────────────────────────────────────────────────
    def generate(self, live_metrics: dict, game_genre: str,
                 resolution: str, preset: str,
                 ray_tracing: bool, upscaling: str,
                 issues: list) -> list:
        """
        Generate top-6 optimization recommendations.
        Each recommendation includes ML-predicted FPS gain.

        Args:
            live_metrics : Current hardware telemetry snapshot
            game_genre   : Selected game genre key
            resolution   : Current resolution string e.g. "1920x1080"
            preset       : Current quality preset e.g. "high"
            ray_tracing  : Whether ray tracing is enabled
            upscaling    : Current upscaling mode
            issues       : List of detected diagnostic issues

        Returns:
            List of recommendation dicts sorted by estimated FPS gain
        """
        if not self.predictor.is_loaded:
            return []

        # Get baseline FPS for current settings
        baseline = self.predictor.predict(
            live_metrics, game_genre, resolution, preset, ray_tracing, upscaling
        )
        baseline_fps = baseline.get("predicted_fps")
        if not baseline_fps:
            return []

        presets      = list(PRESET_CONFIG.keys())
        resolutions  = list(RESOLUTION_CONFIG.keys())
        curr_p_idx   = presets.index(preset)         if preset      in presets      else 2
        curr_r_idx   = resolutions.index(resolution) if resolution  in resolutions  else 1

        recs = []

        # ── 1. Disable Ray Tracing ────────────────────────────
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

        # ── 2. Enable DLSS (RTX exclusive, AI-based) ─────────
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

        # ── 3. Enable FSR (works on all GPUs) ────────────────
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

        # ── 4. Lower Quality Preset ───────────────────────────
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

        # ── 5. Lower Resolution ───────────────────────────────
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

        # ── 6. Two-Step Combo: Lower Preset + Enable DLSS ────
        if curr_p_idx > 0 and upscaling == "none":
            lower_preset = presets[curr_p_idx - 1]
            result = self.predictor.predict(
                live_metrics, game_genre, resolution,
                lower_preset, ray_tracing, "dlss_quality"
            )
            gain = self._gain(result, baseline_fps)
            if gain > 15:
                recs.append(self._build(
                    action=f"Lower Preset + Enable DLSS Quality",
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

        # ── 7. Diagnostics-Based Recommendations ─────────────
        issue_types = {i["issue_type"] for i in issues}

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

        # ── Sort by gain, deduplicate, return top 6 ──────────
        recs.sort(key=lambda x: x["estimated_fps_gain"], reverse=True)

        seen_actions, unique_recs = set(), []
        for rec in recs:
            if rec["action"] not in seen_actions:
                seen_actions.add(rec["action"])
                unique_recs.append(rec)

        return unique_recs[:6]

    # ─────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────
    def _gain(self, result: dict, baseline_fps: float) -> float:
        """Safely compute FPS gain over baseline."""
        pred = result.get("predicted_fps")
        if pred is None:
            return 0.0
        return round(pred - baseline_fps, 1)

    def _build(self, action: str, category: str, icon: str,
               gain: float, desc: str, difficulty: str) -> dict:
        """Build a recommendation dict."""
        return {
            "action":             action,
            "category":           category,
            "icon":               icon,
            "estimated_fps_gain": gain,
            "description":        desc,
            "difficulty":         difficulty
        }