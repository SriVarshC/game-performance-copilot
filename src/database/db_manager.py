import sqlite3
import json
import os
from datetime import datetime


class DatabaseManager:
    """
    Handles all SQLite database operations.
    Stores telemetry snapshots, diagnostics, and recommendations.
    DB Location: data/telemetry.db
    """

    def __init__(self, db_path: str = "data/telemetry.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_tables()
        print(f"[INFO] Database ready at: {db_path}")

    def _get_connection(self):
        """Create and return a new SQLite connection."""
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        """Create all tables on first run."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # ── Telemetry Table ──────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp               TEXT    NOT NULL,
                gpu_utilization         REAL,
                vram_used_mb            REAL,
                vram_total_mb           REAL,
                vram_utilization        REAL,
                vram_free_mb            REAL,
                gpu_temperature         REAL,
                gpu_clock_mhz           REAL,
                gpu_power_watts         REAL,
                gpu_name                TEXT,
                cpu_utilization         REAL,
                cpu_temperature         REAL,
                cpu_frequency_mhz       REAL,
                cpu_core_count          INTEGER,
                ram_used_gb             REAL,
                ram_total_gb            REAL,
                ram_utilization         REAL,
                ram_available_gb        REAL,
                page_file_used_gb       REAL,
                page_file_utilization   REAL,
                raw_data                TEXT
            )
        """)

        # ── Diagnostics Table ────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnostics (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT    NOT NULL,
                issue_type      TEXT    NOT NULL,
                severity        TEXT    NOT NULL,
                confidence      REAL    NOT NULL,
                description     TEXT,
                raw_metrics     TEXT
            )
        """)

        # ── Recommendations Table ────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp           TEXT    NOT NULL,
                recommendation      TEXT    NOT NULL,
                estimated_fps_gain  REAL,
                category            TEXT,
                was_helpful         INTEGER DEFAULT NULL
            )
        """)

        conn.commit()
        conn.close()

    # ─────────────────────────────────────────────────────────
    # INSERT OPERATIONS
    # ─────────────────────────────────────────────────────────
    def insert_telemetry(self, metrics: dict):
        """Save one telemetry snapshot to the database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        gpu = metrics.get("gpu", {})
        cpu = metrics.get("cpu", {})
        mem = metrics.get("memory", {})

        cursor.execute("""
            INSERT INTO telemetry (
                timestamp, gpu_utilization, vram_used_mb, vram_total_mb,
                vram_utilization, vram_free_mb, gpu_temperature, gpu_clock_mhz,
                gpu_power_watts, gpu_name, cpu_utilization, cpu_temperature,
                cpu_frequency_mhz, cpu_core_count, ram_used_gb, ram_total_gb,
                ram_utilization, ram_available_gb, page_file_used_gb,
                page_file_utilization, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metrics.get("timestamp"),
            gpu.get("gpu_utilization"),
            gpu.get("vram_used_mb"),
            gpu.get("vram_total_mb"),
            gpu.get("vram_utilization"),
            gpu.get("vram_free_mb"),
            gpu.get("gpu_temperature"),
            gpu.get("gpu_clock_mhz"),
            gpu.get("gpu_power_watts"),
            gpu.get("gpu_name"),
            cpu.get("cpu_utilization"),
            cpu.get("cpu_temperature"),
            cpu.get("cpu_frequency_mhz"),
            cpu.get("cpu_core_count"),
            mem.get("ram_used_gb"),
            mem.get("ram_total_gb"),
            mem.get("ram_utilization"),
            mem.get("ram_available_gb"),
            mem.get("page_file_used_gb"),
            mem.get("page_file_utilization"),
            json.dumps(metrics)
        ))

        conn.commit()
        conn.close()

    def insert_diagnostic(self, issue_type: str, severity: str,
                           confidence: float, description: str, raw_metrics: dict):
        """Save a detected bottleneck/issue."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO diagnostics (timestamp, issue_type, severity, confidence, description, raw_metrics)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            issue_type, severity, confidence, description,
            json.dumps(raw_metrics)
        ))
        conn.commit()
        conn.close()

    def insert_recommendation(self, recommendation: str,
                               estimated_fps_gain: float, category: str) -> int:
        """
        Save a performance recommendation.
        Returns the new row ID so callers can attach feedback later.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recommendations (timestamp, recommendation, estimated_fps_gain, category)
            VALUES (?, ?, ?, ?)
        """, (datetime.now().isoformat(), recommendation, estimated_fps_gain, category))
        conn.commit()
        new_id = cursor.lastrowid   # ← capture BEFORE close
        conn.close()
        return new_id               # ← return so route can attach to recommendation dict

    def update_recommendation_feedback(self, recommendation_id: int, was_helpful: bool):
        """Record whether a recommendation was useful (for future ML training)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE recommendations SET was_helpful = ? WHERE id = ?",
            (1 if was_helpful else 0, recommendation_id)
        )
        conn.commit()
        conn.close()

    # ─────────────────────────────────────────────────────────
    # READ OPERATIONS
    # ─────────────────────────────────────────────────────────
    def get_recent_telemetry(self, limit: int = 100) -> list:
        """Fetch the N most recent telemetry records."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM telemetry ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def get_diagnostic_history(self, limit: int = 50) -> list:
        """Fetch recent diagnostic issues."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM diagnostics ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def get_total_records(self) -> int:
        """Get total number of telemetry records stored."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM telemetry")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_feedback_summary(self) -> dict:
        """Return aggregated feedback statistics from the recommendations table."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Total recommendations ever stored
        cursor.execute("SELECT COUNT(*) FROM recommendations")
        total = cursor.fetchone()[0] or 0

        # How many have feedback recorded
        cursor.execute(
            "SELECT COUNT(*) FROM recommendations WHERE was_helpful IS NOT NULL"
        )
        feedback_given = cursor.fetchone()[0] or 0

        # Helpful count
        cursor.execute(
            "SELECT COUNT(*) FROM recommendations WHERE was_helpful = 1"
        )
        helpful = cursor.fetchone()[0] or 0

        # Not-helpful count
        cursor.execute(
            "SELECT COUNT(*) FROM recommendations WHERE was_helpful = 0"
        )
        not_helpful = cursor.fetchone()[0] or 0

        # Helpful percentage
        helpful_pct = round((helpful / feedback_given * 100), 1) if feedback_given > 0 else 0.0

        # Per-category breakdown
        cursor.execute("""
            SELECT   category,
                     COUNT(*)                                          AS total,
                     SUM(CASE WHEN was_helpful = 1 THEN 1 ELSE 0 END) AS helpful,
                     SUM(CASE WHEN was_helpful = 0 THEN 1 ELSE 0 END) AS not_helpful
            FROM     recommendations
            WHERE    was_helpful IS NOT NULL
            GROUP BY category
            ORDER BY helpful DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        return {
            "total_recommendations": total,
            "feedback_given":        feedback_given,
            "helpful":               helpful,
            "not_helpful":           not_helpful,
            "helpful_percentage":    helpful_pct,
            "by_category": [
                {
                    "category":    row[0],
                    "total":       row[1],
                    "helpful":     row[2],
                    "not_helpful": row[3]
                }
                for row in rows
            ]
        }

    def get_recent_recommendations(self, limit: int = 20) -> list:
        """Return recent recommendations with their feedback status."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT   id, recommendation, estimated_fps_gain,
                     category, was_helpful, timestamp
            FROM     recommendations
            ORDER BY id DESC
            LIMIT    ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id":             row[0],
                "recommendation": row[1],
                "fps_gain":       row[2],
                "category":       row[3],
                "was_helpful":    row[4],
                "timestamp":      row[5]
            }
            for row in rows
        ]