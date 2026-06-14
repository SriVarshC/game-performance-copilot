import psutil
import pynvml
import platform
from datetime import datetime


class TelemetryCollector:
    """
    Collects real-time hardware metrics.
    Configured for: NVIDIA RTX 3050 Ti Laptop + Intel i7-12650H + 16GB RAM
    """

    # Your hardware specs — used for utilization calculations
    GPU_DEDICATED_VRAM_MB = 4096   # RTX 3050 Ti Laptop = 4 GB dedicated VRAM
    CPU_NAME = "Intel i7-12650H"
    CPU_CORES = 10                 # 6 Performance + 4 Efficiency cores
    CPU_THREADS = 16
    RAM_TOTAL_GB = 16.0

    def __init__(self):
        self.gpu_available = False
        self._init_gpu()

    def _init_gpu(self):
        """Initialize NVIDIA GPU monitoring via pynvml."""
        try:
            pynvml.nvmlInit()
            self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            gpu_name = pynvml.nvmlDeviceGetName(self.gpu_handle)
            print(f"[INFO] GPU detected: {gpu_name}")
            print(f"[INFO] GPU monitoring initialized successfully.")
            self.gpu_available = True
        except pynvml.NVMLError as e:
            print(f"[WARNING] NVML Error: {e}")
            print(f"[INFO] Running in CPU-only mode.")
        except Exception as e:
            print(f"[WARNING] GPU monitoring unavailable: {e}")

    # ─────────────────────────────────────────────────────────
    # GPU METRICS
    # ─────────────────────────────────────────────────────────
    def get_gpu_metrics(self) -> dict:
        """
        Returns GPU utilization, VRAM usage, temperature, clock speed, power.
        Note: RTX 3050 Ti Laptop has 4 GB dedicated VRAM.
        Shared GPU memory (7.8 GB) uses system RAM — not tracked here.
        """
        if not self.gpu_available:
            return {
                "gpu_utilization": None,
                "vram_used_mb": None,
                "vram_total_mb": None,
                "vram_utilization": None,
                "vram_free_mb": None,
                "gpu_temperature": None,
                "gpu_clock_mhz": None,
                "gpu_power_watts": None,
                "gpu_name": "GPU Not Available"
            }

        result = {}

        try:
            # GPU Name
            result["gpu_name"] = pynvml.nvmlDeviceGetName(self.gpu_handle)

            # GPU Utilization
            utilization = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
            result["gpu_utilization"] = utilization.gpu

            # VRAM — dedicated only (4 GB for RTX 3050 Ti Laptop)
            memory = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
            vram_used = round(memory.used / (1024 ** 2), 2)
            vram_total = round(memory.total / (1024 ** 2), 2)
            vram_free = round(memory.free / (1024 ** 2), 2)
            result["vram_used_mb"] = vram_used
            result["vram_total_mb"] = vram_total
            result["vram_free_mb"] = vram_free
            result["vram_utilization"] = round((memory.used / memory.total) * 100, 2) if memory.total > 0 else 0

            # Temperature
            result["gpu_temperature"] = pynvml.nvmlDeviceGetTemperature(
                self.gpu_handle, pynvml.NVML_TEMPERATURE_GPU
            )

            # Clock Speed
            result["gpu_clock_mhz"] = pynvml.nvmlDeviceGetClockInfo(
                self.gpu_handle, pynvml.NVML_CLOCK_GRAPHICS
            )

        except Exception as e:
            print(f"[ERROR] GPU metric collection failed: {e}")

        # Power Draw — laptop GPUs sometimes don't report this
        try:
            power_mw = pynvml.nvmlDeviceGetPowerUsage(self.gpu_handle)
            result["gpu_power_watts"] = round(power_mw / 1000.0, 2)
        except Exception:
            result["gpu_power_watts"] = None  # Not supported on all laptop GPUs

        return result

    # ─────────────────────────────────────────────────────────
    # CPU METRICS
    # ─────────────────────────────────────────────────────────
    def get_cpu_metrics(self) -> dict:
        """
        Returns CPU utilization, per-core usage, frequency, temperature.
        i7-12650H: 10 cores (6P + 4E), 16 logical threads.
        """
        try:
            # Overall CPU usage
            cpu_overall = psutil.cpu_percent(interval=0.5)

            # Per-core usage (shows all 16 logical threads)
            per_core = psutil.cpu_percent(interval=0.5, percpu=True)

            # Frequency
            freq = psutil.cpu_freq()

            # Temperature (may not be available on all Windows machines)
            cpu_temp = None
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for key in ["coretemp", "cpu_thermal", "k10temp", "acpitz"]:
                        if key in temps:
                            cpu_temp = round(temps[key][0].current, 1)
                            break
            except Exception:
                pass  # Temperature not available on this platform

            return {
                "cpu_utilization": cpu_overall,
                "per_core_utilization": per_core,
                "cpu_core_count": len(per_core),
                "cpu_frequency_mhz": round(freq.current, 2) if freq else None,
                "cpu_max_frequency_mhz": round(freq.max, 2) if freq else None,
                "cpu_temperature": cpu_temp,
                "cpu_name": self.CPU_NAME
            }

        except Exception as e:
            print(f"[ERROR] CPU metric collection failed: {e}")
            return {}

    # ─────────────────────────────────────────────────────────
    # MEMORY METRICS
    # ─────────────────────────────────────────────────────────
    def get_memory_metrics(self) -> dict:
        """
        Returns RAM and page file usage.
        Note: Your system has 16 GB RAM, currently running near capacity.
        """
        try:
            ram = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                "ram_used_gb": round(ram.used / (1024 ** 3), 2),
                "ram_total_gb": round(ram.total / (1024 ** 3), 2),
                "ram_utilization": ram.percent,
                "ram_available_gb": round(ram.available / (1024 ** 3), 2),
                "page_file_used_gb": round(swap.used / (1024 ** 3), 2),
                "page_file_total_gb": round(swap.total / (1024 ** 3), 2),
                "page_file_utilization": swap.percent
            }

        except Exception as e:
            print(f"[ERROR] Memory metric collection failed: {e}")
            return {}

    # ─────────────────────────────────────────────────────────
    # SYSTEM METRICS
    # ─────────────────────────────────────────────────────────
    def get_system_metrics(self) -> dict:
        """Returns top background processes and disk activity."""
        try:
            processes = []
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    info = proc.info
                    if info["cpu_percent"] is not None:
                        processes.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Top 5 CPU-heavy processes
            top_processes = sorted(
                processes,
                key=lambda x: x.get("cpu_percent", 0),
                reverse=True
            )[:5]

            # Disk usage of C: drive
            try:
                disk = psutil.disk_usage("C:\\")
                disk_used = round(disk.used / (1024 ** 3), 2)
                disk_total = round(disk.total / (1024 ** 3), 2)
                disk_pct = disk.percent
            except Exception:
                disk_used = disk_total = disk_pct = None

            return {
                "top_processes": top_processes,
                "disk_used_gb": disk_used,
                "disk_total_gb": disk_total,
                "disk_utilization": disk_pct
            }

        except Exception as e:
            print(f"[ERROR] System metric collection failed: {e}")
            return {}

    # ─────────────────────────────────────────────────────────
    # COLLECT ALL
    # ─────────────────────────────────────────────────────────
    def collect_all(self) -> dict:
        """Collects all hardware metrics into a single snapshot."""
        return {
            "timestamp": datetime.now().isoformat(),
            "gpu": self.get_gpu_metrics(),
            "cpu": self.get_cpu_metrics(),
            "memory": self.get_memory_metrics(),
            "system": self.get_system_metrics()
        }

    def cleanup(self):
        """Cleanly shut down GPU monitoring."""
        if self.gpu_available:
            try:
                pynvml.nvmlShutdown()
                print("[INFO] GPU monitoring shut down cleanly.")
            except Exception:
                pass