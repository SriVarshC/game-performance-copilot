"""
FPS Dataset Generator for Game Performance Copilot
Generates a realistic synthetic training dataset based on
real-world GPU benchmark patterns and hardware behavior.

Why synthetic data?
- Collecting 1000+ real gaming sessions takes months
- Synthetic data lets us start training immediately
- Based on real RTX 3050 Ti / i7-12650H benchmark numbers
- Later phases will replace/augment with real session data
"""

import numpy as np
import pandas as pd
import os
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# SEED FOR REPRODUCIBILITY
# ─────────────────────────────────────────────────────────────
np.random.seed(42)


# ─────────────────────────────────────────────────────────────
# GAME PROFILES
# ─────────────────────────────────────────────────────────────
GAME_PROFILES = {
    "fps_competitive": {
        "base_fps":        180,
        "gpu_sensitivity":  0.8,
        "cpu_sensitivity":  0.6,
        "vram_threshold":  2048,
        "description":    "Competitive FPS (Valorant, CS2, Apex)"
    },
    "fps_aaa": {
        "base_fps":        85,
        "gpu_sensitivity":  1.1,
        "cpu_sensitivity":  0.4,
        "vram_threshold":  3500,
        "description":    "AAA FPS (Cyberpunk, COD, Battlefield)"
    },
    "rpg_open_world": {
        "base_fps":        75,
        "gpu_sensitivity":  1.0,
        "cpu_sensitivity":  0.7,
        "vram_threshold":  3200,
        "description":    "Open World RPG (Elden Ring, Witcher, RDR2)"
    },
    "moba": {
        "base_fps":        200,
        "gpu_sensitivity":  0.5,
        "cpu_sensitivity":  0.8,
        "vram_threshold":  2048,
        "description":    "MOBA (Dota 2, League of Legends)"
    },
    "battle_royale": {
        "base_fps":        95,
        "gpu_sensitivity":  1.0,
        "cpu_sensitivity":  0.6,
        "vram_threshold":  3000,
        "description":    "Battle Royale (Fortnite, PUBG, Warzone)"
    },
    "racing": {
        "base_fps":        120,
        "gpu_sensitivity":  0.9,
        "cpu_sensitivity":  0.3,
        "vram_threshold":  3000,
        "description":    "Racing (Forza, F1)"
    },
    "strategy": {
        "base_fps":        60,
        "gpu_sensitivity":  0.5,
        "cpu_sensitivity":  1.2,
        "vram_threshold":  2500,
        "description":    "Strategy (Total War, Civilization)"
    }
}

# ─────────────────────────────────────────────────────────────
# RESOLUTION MULTIPLIERS
# ─────────────────────────────────────────────────────────────
RESOLUTION_CONFIG = {
    "1280x720":  {"multiplier": 1.45, "label": "720p"},
    "1920x1080": {"multiplier": 1.00, "label": "1080p"},
    "2560x1440": {"multiplier": 0.62, "label": "1440p"},
    "3840x2160": {"multiplier": 0.32, "label": "4K"},
}

# ─────────────────────────────────────────────────────────────
# GRAPHICS PRESET MULTIPLIERS
# ─────────────────────────────────────────────────────────────
PRESET_CONFIG = {
    "low":    {"multiplier": 1.55, "vram_usage_factor": 0.45},
    "medium": {"multiplier": 1.20, "vram_usage_factor": 0.60},
    "high":   {"multiplier": 1.00, "vram_usage_factor": 0.78},
    "ultra":  {"multiplier": 0.72, "vram_usage_factor": 0.92},
    "epic":   {"multiplier": 0.55, "vram_usage_factor": 0.97},
}

# ─────────────────────────────────────────────────────────────
# RAY TRACING PENALTY
# ─────────────────────────────────────────────────────────────
RAY_TRACING_PENALTY = 0.52

# ─────────────────────────────────────────────────────────────
# DLSS / FSR BOOST
# ─────────────────────────────────────────────────────────────
UPSCALING_BOOST = {
    "none":               1.00,
    "fsr_quality":        1.30,
    "fsr_balanced":       1.50,
    "dlss_quality":       1.45,
    "dlss_balanced":      1.65,
    "dlss_performance":   1.90,
}


# ─────────────────────────────────────────────────────────────
# NEW — BOTTLENECK LABEL (Model 3 target)
# ─────────────────────────────────────────────────────────────
def get_bottleneck_label(gpu_util: float, cpu_util: float,
                          vram_util: float, gpu_temp: float,
                          ram_util: float) -> str:
    """Classify the dominant bottleneck for a gaming session."""
    if gpu_temp > 85:     return "THERMAL"
    if vram_util > 80:    return "MEMORY"
    if gpu_util > 90:     return "GPU"
    if cpu_util > 85:     return "CPU"
    return "BALANCED"


# ─────────────────────────────────────────────────────────────
# NEW — HEALTH SCORE (Model 4 target)
# ─────────────────────────────────────────────────────────────
def calculate_health_score(fps: float, gpu_temp: float,
                            gpu_util: float, cpu_util: float,
                            ram_util: float) -> float:
    """
    0-100 performance health score.
    40 pts — FPS quality   (target: 60 FPS = full score)
    30 pts — GPU temp      (under 75C = full score)
    30 pts — System load   (penalize RAM/CPU pressure)
    """
    # FPS component
    fps_score = min(fps / 60.0, 1.0) * 40.0

    # Temperature component
    if gpu_temp <= 75.0:
        temp_score = 30.0
    elif gpu_temp <= 85.0:
        temp_score = 30.0 * (1.0 - (gpu_temp - 75.0) / 10.0)
    else:
        temp_score = 0.0

    # System balance component
    balance = 30.0
    if ram_util > 90.0:    balance -= 15.0
    elif ram_util > 82.0:  balance -= 5.0
    if cpu_util > 90.0:    balance -= 10.0
    balance_score = max(0.0, balance)

    return round(min(100.0, fps_score + temp_score + balance_score), 1)


# ─────────────────────────────────────────────────────────────
# BOTTLENECK PENALTIES
# ─────────────────────────────────────────────────────────────
def compute_bottleneck_penalty(gpu_util, cpu_util, vram_util,
                                ram_util, gpu_temp, vram_threshold_mb,
                                vram_used_mb):
    """
    Calculate combined performance penalty from all bottlenecks.
    Returns a multiplier between 0.1 and 1.0
    """
    penalty = 1.0

    # CPU bottleneck
    if cpu_util > 88 and gpu_util < 60:
        severity = (cpu_util - 88) / 12.0
        penalty *= (1.0 - 0.35 * severity)

    # GPU bottleneck
    if gpu_util > 95:
        penalty *= 0.92

    # VRAM overflow
    if vram_used_mb > vram_threshold_mb:
        overflow_ratio = (vram_used_mb - vram_threshold_mb) / vram_threshold_mb
        penalty *= max(0.4, 1.0 - overflow_ratio * 0.6)

    # Thermal throttling
    if gpu_temp > 85:
        throttle = min((gpu_temp - 85) / 10.0, 1.0)
        penalty *= (1.0 - 0.25 * throttle)

    # RAM pressure
    if ram_util > 90:
        penalty *= 0.88
    elif ram_util > 82:
        penalty *= 0.96

    return max(0.15, penalty)


def generate_one_session(game_key: str, resolution: str,
                          preset: str, ray_tracing: bool,
                          upscaling: str) -> dict:
    """
    Simulate one gaming session and return all metrics + target values.
    """
    game          = GAME_PROFILES[game_key]
    res           = RESOLUTION_CONFIG[resolution]
    pre           = PRESET_CONFIG[preset]
    upscale_boost = UPSCALING_BOOST[upscaling]

    # ── GPU utilization ───────────────────────────────────────
    gpu_base_util = min(95, 45 + (
        list(RESOLUTION_CONFIG.keys()).index(resolution) * 12 +
        list(PRESET_CONFIG.keys()).index(preset) * 8
    ))
    gpu_util = float(np.clip(
        np.random.normal(gpu_base_util, 8), 20, 99
    ))

    # ── CPU utilization ───────────────────────────────────────
    cpu_base_util = 35 + game["cpu_sensitivity"] * 30
    cpu_util = float(np.clip(
        np.random.normal(cpu_base_util, 10), 10, 99
    ))

    # ── VRAM usage ────────────────────────────────────────────
    vram_base = (
        pre["vram_usage_factor"] *
        (0.6 + list(RESOLUTION_CONFIG.keys()).index(resolution) * 0.1) *
        4096
    )
    if ray_tracing:
        vram_base *= 1.25
    vram_used = float(np.clip(
        np.random.normal(vram_base, 150), 200, 4200
    ))
    vram_util = round((vram_used / 4096) * 100, 2)

    # ── RAM utilization ───────────────────────────────────────
    ram_util = float(np.clip(
        np.random.normal(78, 6), 55, 98
    ))

    # ── GPU Temperature ───────────────────────────────────────
    temp_base = 42 + (gpu_util * 0.45) + (
        list(PRESET_CONFIG.keys()).index(preset) * 2
    )
    gpu_temp = float(np.clip(
        np.random.normal(temp_base, 4), 38, 98
    ))

    # ── GPU Clock ─────────────────────────────────────────────
    base_clock = 1695
    if gpu_temp > 85:
        base_clock -= (gpu_temp - 85) * 15
    gpu_clock = float(np.clip(
        np.random.normal(base_clock, 80), 400, 1695
    ))

    # ── GPU Power ─────────────────────────────────────────────
    gpu_power = float(np.clip(
        np.random.normal(45 + gpu_util * 0.35, 5), 12, 80
    ))

    # ── Compute FPS ───────────────────────────────────────────
    fps  = game["base_fps"]
    fps *= res["multiplier"]
    fps *= pre["multiplier"]

    if ray_tracing:
        fps *= RAY_TRACING_PENALTY

    fps *= upscale_boost

    penalty = compute_bottleneck_penalty(
        gpu_util, cpu_util, vram_util, ram_util,
        gpu_temp, game["vram_threshold"], vram_used
    )
    fps *= penalty

    fps = float(np.clip(
        np.random.normal(fps, fps * 0.07), 5, 400
    ))
    fps = round(fps, 1)

    frame_time = round(1000.0 / fps, 2) if fps > 0 else 999.0

    return {
        # ── Input Features ────────────────────────────────────
        "game_genre":       game_key,
        "resolution":       resolution,
        "preset":           preset,
        "ray_tracing":      int(ray_tracing),
        "upscaling":        upscaling,
        "gpu_utilization":  round(gpu_util, 2),
        "vram_used_mb":     round(vram_used, 2),
        "vram_utilization": vram_util,
        "cpu_utilization":  round(cpu_util, 2),
        "ram_utilization":  round(ram_util, 2),
        "gpu_temperature":  round(gpu_temp, 2),
        "gpu_clock_mhz":    round(gpu_clock, 2),
        "gpu_power_watts":  round(gpu_power, 2),

        # ── Derived Features ──────────────────────────────────
        "cpu_gpu_ratio":    round(cpu_util / max(gpu_util, 1), 4),
        "vram_pressure":    int(vram_used > game["vram_threshold"]),
        "thermal_throttle": int(gpu_temp > 85),

        # ── Resolution as numeric ─────────────────────────────
        "resolution_width":  int(resolution.split("x")[0]),
        "resolution_height": int(resolution.split("x")[1]),
        "total_pixels":      int(resolution.split("x")[0]) * int(resolution.split("x")[1]),

        # ── Preset as ordinal ─────────────────────────────────
        "preset_ordinal": list(PRESET_CONFIG.keys()).index(preset),

        # ── Target Variables ──────────────────────────────────
        "fps":        fps,
        "frame_time": frame_time,

        # NEW — additional targets for Models 2, 3, 4
        "low_1pct_fps":     round(fps * float(np.random.uniform(0.45, 0.65)), 1),
        "bottleneck_class": get_bottleneck_label(
                                gpu_util, cpu_util, vram_util,
                                gpu_temp, ram_util),
        "health_score":     calculate_health_score(
                                fps, gpu_temp, gpu_util,
                                cpu_util, ram_util),
    }


def generate_dataset(n_samples: int = 5000,
                     save_path: str = "data/fps_dataset.csv") -> pd.DataFrame:
    """
    Generate a full FPS training dataset.
    """
    print(f"[INFO] Generating {n_samples} gaming session records...")
    print(f"[INFO] Games: {len(GAME_PROFILES)} genres")
    print(f"[INFO] Resolutions: {list(RESOLUTION_CONFIG.keys())}")
    print(f"[INFO] Presets: {list(PRESET_CONFIG.keys())}")
    print()

    records     = []
    game_keys   = list(GAME_PROFILES.keys())
    resolutions = list(RESOLUTION_CONFIG.keys())
    presets     = list(PRESET_CONFIG.keys())
    upscaling   = list(UPSCALING_BOOST.keys())

    for i in range(n_samples):
        game       = np.random.choice(game_keys)
        resolution = np.random.choice(resolutions, p=[0.05, 0.55, 0.28, 0.12])
        preset     = np.random.choice(presets,     p=[0.10, 0.20, 0.35, 0.25, 0.10])
        rt         = np.random.choice([True, False], p=[0.20, 0.80])

        if preset in ["ultra", "epic"]:
            up = np.random.choice(upscaling, p=[0.25, 0.15, 0.15, 0.20, 0.15, 0.10])
        else:
            up = np.random.choice(upscaling, p=[0.55, 0.10, 0.10, 0.10, 0.10, 0.05])

        record = generate_one_session(game, resolution, preset, rt, up)
        records.append(record)

        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1}/{n_samples} records...")

    df = pd.DataFrame(records)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    df.to_csv(save_path, index=False)

    print(f"\n[INFO] Dataset saved to: {save_path}")
    print(f"[INFO] Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"\n[INFO] FPS Statistics:")
    print(f"  Min FPS    : {df['fps'].min():.1f}")
    print(f"  Max FPS    : {df['fps'].max():.1f}")
    print(f"  Mean FPS   : {df['fps'].mean():.1f}")
    print(f"  Median FPS : {df['fps'].median():.1f}")
    print(f"\n[INFO] Bottleneck Distribution:")
    print(df['bottleneck_class'].value_counts().to_string())
    print(f"\n[INFO] Health Score Statistics:")
    print(f"  Min    : {df['health_score'].min():.1f}")
    print(f"  Max    : {df['health_score'].max():.1f}")
    print(f"  Mean   : {df['health_score'].mean():.1f}")
    print(f"\n[INFO] Preset Distribution:")
    print(df['preset'].value_counts().to_string())
    print(f"\n[INFO] Resolution Distribution:")
    print(df['resolution'].value_counts().to_string())

    return df


if __name__ == "__main__":
    df = generate_dataset(n_samples=5000)
    print(f"\n[INFO] First 3 rows preview:")
    print(df.head(3).to_string())