"""
Game Performance Copilot — CLI Entry Point
Run this to test telemetry collection in terminal (no UI).
For the full dashboard, run: streamlit run src/dashboard/app.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.telemetry.collector import TelemetryCollector
from src.database.db_manager import DatabaseManager
from src.diagnostics.engine import DiagnosticsEngine


def main():
    print("=" * 65)
    print("   🎮  Game Performance Copilot — Starting Telemetry...")
    print("   GPU : NVIDIA RTX 3050 Ti Laptop (4 GB VRAM)")
    print("   CPU : Intel i7-12650H (10 Cores / 16 Threads)")
    print("   RAM : 16 GB")
    print("=" * 65)

    collector = TelemetryCollector()
    db        = DatabaseManager()
    engine    = DiagnosticsEngine()

    print("\n[INFO] Collecting every 2 seconds. Press Ctrl+C to stop.\n")

    try:
        while True:
            metrics = collector.collect_all()
            db.insert_telemetry(metrics)
            issues = engine.analyze(metrics)

            gpu = metrics.get("gpu", {})
            cpu = metrics.get("cpu", {})
            mem = metrics.get("memory", {})

            print(f"\n[{metrics['timestamp']}]")
            print(f"  GPU  : {gpu.get('gpu_utilization')}% | "
                  f"Temp: {gpu.get('gpu_temperature')}°C | "
                  f"VRAM: {gpu.get('vram_used_mb')} MB / 4096 MB "
                  f"({gpu.get('vram_utilization')}%)")
            print(f"  CPU  : {cpu.get('cpu_utilization')}% | "
                  f"Freq: {cpu.get('cpu_frequency_mhz')} MHz")
            print(f"  RAM  : {mem.get('ram_utilization')}% | "
                  f"Used: {mem.get('ram_used_gb')} GB / 16 GB | "
                  f"Free: {mem.get('ram_available_gb')} GB")

            if issues:
                for issue in issues:
                    if issue["severity"] in ("CRITICAL", "HIGH"):
                        print(f"  ⚠️  [{issue['severity']}] {issue['issue_type']}: "
                              f"{issue['description'][:90]}...")
                    elif issue["issue_type"] == "SYSTEM_OPTIMAL":
                        print(f"  ✅  System running optimally.")

            print(f"  DB   : {db.get_total_records()} records saved")
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n[INFO] Stopping... Cleaning up.")
        collector.cleanup()
        print(f"[INFO] Total records collected: {db.get_total_records()}")
        print("[INFO] Done. Goodbye! 🎮")


if __name__ == "__main__":
    main()