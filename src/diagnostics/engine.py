class DiagnosticsEngine:
    """
    Rule-based bottleneck detection engine.
    Thresholds tuned specifically for:
      - NVIDIA RTX 3050 Ti Laptop (4 GB VRAM)
      - Intel i7-12650H (10 cores)
      - 16 GB RAM
    """

    # ── CPU Thresholds ───────────────────────────────────────
    CPU_BOTTLENECK_THRESHOLD = 85.0
    # i7-12650H: if overall CPU > 85% while GPU is low, CPU is the bottleneck

    GPU_LOW_THRESHOLD = 55.0
    # If GPU usage is below 55% while CPU is maxed, CPU is starving the GPU

    # ── GPU Thresholds ───────────────────────────────────────
    GPU_BOTTLENECK_THRESHOLD = 95.0
    # GPU is fully maxed — lower graphics settings

    # ── VRAM Thresholds (Critical for 4 GB RTX 3050 Ti) ─────
    VRAM_WARNING_THRESHOLD = 75.0
    # 75% of 4 GB = 3.0 GB used — start warning
    # At this point, shared GPU memory (system RAM) starts being used

    VRAM_CRITICAL_THRESHOLD = 90.0
    # 90% of 4 GB = 3.6 GB used — severe stuttering expected

    # ── RAM Thresholds (16 GB, already under pressure) ───────
    RAM_WARNING_THRESHOLD = 82.0
    # Your system idles near 82%, so flag at this level during gaming

    RAM_CRITICAL_THRESHOLD = 92.0
    # At 92% RAM, Windows aggressively pages to disk — major performance hit

    # ── Temperature Thresholds (Laptop runs hotter) ──────────
    GPU_THERMAL_WARNING = 85.0
    # RTX 3050 Ti Laptop thermal limit — throttling begins here

    GPU_THERMAL_CRITICAL = 91.0
    # Critical thermal state — severe clock reduction

    CPU_THERMAL_WARNING = 90.0
    # i7-12650H max is ~100°C, throttling starts around 90°C

    # ── Page File Threshold ──────────────────────────────────
    PAGE_FILE_THRESHOLD = 80.0
    # Heavy page file = reading game assets from slow disk = stutters

    def analyze(self, metrics: dict) -> list:
        """
        Analyze one telemetry snapshot.
        Returns a list of detected issues sorted by severity.
        """
        issues = []

        gpu = metrics.get("gpu", {})
        cpu = metrics.get("cpu", {})
        mem = metrics.get("memory", {})

        gpu_util  = gpu.get("gpu_utilization")
        vram_util = gpu.get("vram_utilization")
        vram_used = gpu.get("vram_used_mb")
        vram_free = gpu.get("vram_free_mb")
        gpu_temp  = gpu.get("gpu_temperature")

        cpu_util  = cpu.get("cpu_utilization")
        cpu_temp  = cpu.get("cpu_temperature")

        ram_util       = mem.get("ram_utilization")
        page_file_util = mem.get("page_file_utilization")

        # ── 1. CPU BOTTLENECK ────────────────────────────────
        if cpu_util is not None and gpu_util is not None:
            if cpu_util >= self.CPU_BOTTLENECK_THRESHOLD and gpu_util < self.GPU_LOW_THRESHOLD:
                confidence = round(min((cpu_util / 100) * 1.05, 1.0), 2)
                issues.append({
                    "issue_type": "CPU_BOTTLENECK",
                    "severity": "HIGH",
                    "confidence": confidence,
                    "description": (
                        f"Your i7-12650H is at {cpu_util}% utilization while "
                        f"your RTX 3050 Ti is only at {gpu_util}%. "
                        f"The CPU cannot send frames to the GPU fast enough. "
                        f"Try: Lower NPC density, simulation quality, or physics settings. "
                        f"Close background apps to free CPU cycles."
                    )
                })

        # ── 2. GPU BOTTLENECK ────────────────────────────────
        if gpu_util is not None and gpu_util >= self.GPU_BOTTLENECK_THRESHOLD:
            issues.append({
                "issue_type": "GPU_BOTTLENECK",
                "severity": "HIGH",
                "confidence": round(gpu_util / 100, 2),
                "description": (
                    f"RTX 3050 Ti is at {gpu_util}% — fully maxed out. "
                    f"The GPU cannot render frames any faster. "
                    f"Try: Lower resolution, disable ray tracing, enable DLSS, "
                    f"reduce shadow and texture quality."
                )
            })

        # ── 3. VRAM WARNING (4 GB is very limited) ───────────
        if vram_util is not None:
            if vram_util >= self.VRAM_CRITICAL_THRESHOLD:
                issues.append({
                    "issue_type": "VRAM_CRITICAL",
                    "severity": "CRITICAL",
                    "confidence": round(vram_util / 100, 2),
                    "description": (
                        f"VRAM is at {vram_util}% ({vram_used} MB used of 4096 MB). "
                        f"Only {vram_free} MB free. "
                        f"Your RTX 3050 Ti is OUT of video memory. "
                        f"Game assets are spilling into shared GPU memory (system RAM), "
                        f"causing severe stuttering. "
                        f"Immediately: Lower texture quality to Medium, reduce render resolution."
                    )
                })
            elif vram_util >= self.VRAM_WARNING_THRESHOLD:
                issues.append({
                    "issue_type": "VRAM_PRESSURE",
                    "severity": "HIGH",
                    "confidence": round(vram_util / 100, 2),
                    "description": (
                        f"VRAM is at {vram_util}% ({vram_used} MB of 4096 MB used). "
                        f"Getting close to your 4 GB limit. "
                        f"Stuttering may begin soon as assets overflow to system RAM. "
                        f"Consider lowering texture quality or disabling high-res texture packs."
                    )
                })

        # ── 4. GPU THERMAL THROTTLING ────────────────────────
        if gpu_temp is not None:
            if gpu_temp >= self.GPU_THERMAL_CRITICAL:
                issues.append({
                    "issue_type": "GPU_THERMAL_CRITICAL",
                    "severity": "CRITICAL",
                    "confidence": round(min(gpu_temp / 95.0, 1.0), 2),
                    "description": (
                        f"GPU temperature is {gpu_temp}°C — CRITICAL. "
                        f"Your RTX 3050 Ti Laptop is severely thermal throttling. "
                        f"Clock speeds are being reduced to prevent hardware damage. "
                        f"ACTION: Stop gaming immediately. Clean laptop vents, "
                        f"use a cooling pad, check thermal paste."
                    )
                })
            elif gpu_temp >= self.GPU_THERMAL_WARNING:
                issues.append({
                    "issue_type": "GPU_THERMAL_THROTTLING",
                    "severity": "HIGH",
                    "confidence": round(min(gpu_temp / 91.0, 1.0), 2),
                    "description": (
                        f"GPU temperature is {gpu_temp}°C. "
                        f"Laptop GPU throttling is beginning. Performance will drop. "
                        f"Use a cooling pad, ensure laptop vents are not blocked, "
                        f"reduce graphics settings to lower GPU load."
                    )
                })

        # ── 5. CPU THERMAL THROTTLING ────────────────────────
        if cpu_temp is not None and cpu_temp >= self.CPU_THERMAL_WARNING:
            issues.append({
                "issue_type": "CPU_THERMAL_THROTTLING",
                "severity": "HIGH",
                "confidence": round(min(cpu_temp / 100.0, 1.0), 2),
                "description": (
                    f"CPU temperature is {cpu_temp}°C. "
                    f"Your i7-12650H is thermal throttling. "
                    f"Performance core frequencies are being reduced. "
                    f"Use a cooling pad, close background applications."
                )
            })

        # ── 6. RAM PRESSURE ──────────────────────────────────
        if ram_util is not None:
            if ram_util >= self.RAM_CRITICAL_THRESHOLD:
                issues.append({
                    "issue_type": "RAM_CRITICAL",
                    "severity": "CRITICAL",
                    "confidence": round(ram_util / 100, 2),
                    "description": (
                        f"RAM usage is at {ram_util}% of 16 GB. "
                        f"Windows is heavily paging to disk. "
                        f"This causes severe stuttering as game assets load from disk instead of RAM. "
                        f"Close all background apps: browsers, Discord, Spotify, etc."
                    )
                })
            elif ram_util >= self.RAM_WARNING_THRESHOLD:
                issues.append({
                    "issue_type": "RAM_PRESSURE",
                    "severity": "MEDIUM",
                    "confidence": round(ram_util / 100, 2),
                    "description": (
                        f"RAM usage is at {ram_util}% of 16 GB. "
                        f"With only 16 GB RAM and shared GPU memory also using it, "
                        f"closing background apps (browser tabs, Discord, etc.) "
                        f"will free RAM and improve gaming performance."
                    )
                })

        # ── 7. PAGE FILE HEAVY USAGE ─────────────────────────
        if page_file_util is not None and page_file_util >= self.PAGE_FILE_THRESHOLD:
            issues.append({
                "issue_type": "PAGE_FILE_OVERUSE",
                "severity": "MEDIUM",
                "confidence": round(page_file_util / 100, 2),
                "description": (
                    f"Page file utilization is {page_file_util}%. "
                    f"Windows is using your SSD/HDD as virtual RAM. "
                    f"This is much slower than physical RAM and causes loading stutters. "
                    f"Close background applications to reduce RAM pressure."
                )
            })

        # ── 8. NO ISSUES ─────────────────────────────────────
        if not issues:
            issues.append({
                "issue_type": "SYSTEM_OPTIMAL",
                "severity": "NONE",
                "confidence": 1.0,
                "description": (
                    "No performance bottlenecks detected. "
                    "Your RTX 3050 Ti and i7-12650H are running optimally."
                )
            })

        # Sort by severity: CRITICAL > HIGH > MEDIUM > NONE
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "NONE": 3}
        issues.sort(key=lambda x: severity_order.get(x["severity"], 99))

        return issues