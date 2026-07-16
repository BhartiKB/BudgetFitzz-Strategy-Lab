"""SQLite workflow memory and append-only JSONL trace storage."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY, status TEXT NOT NULL, started_at TEXT NOT NULL,
  finished_at TEXT, config_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS agents (
  run_id TEXT NOT NULL, agent TEXT NOT NULL, status TEXT NOT NULL,
  retry_count INTEGER NOT NULL DEFAULT 0, input_ref TEXT, output_ref TEXT,
  error TEXT, updated_at TEXT NOT NULL, PRIMARY KEY (run_id, agent)
);
CREATE TABLE IF NOT EXISTS checkpoints (
  run_id TEXT NOT NULL, checkpoint TEXT NOT NULL, status TEXT NOT NULL,
  reason TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (run_id, checkpoint)
);
CREATE TABLE IF NOT EXISTS spend (
  run_id TEXT NOT NULL, timestamp TEXT NOT NULL, asset TEXT NOT NULL,
  provider TEXT NOT NULL, tool TEXT NOT NULL, operation TEXT NOT NULL,
  quantity INTEGER NOT NULL, unit_cost_inr REAL NOT NULL, total_cost_inr REAL NOT NULL,
  paid_or_free TEXT NOT NULL, evidence_ref TEXT NOT NULL, notes TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS trace (
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, timestamp TEXT NOT NULL,
  agent TEXT NOT NULL, action TEXT NOT NULL, status TEXT NOT NULL,
  decision_summary TEXT NOT NULL, evidence_ids TEXT NOT NULL, duration_sec REAL NOT NULL,
  retry_number INTEGER NOT NULL, input_ref TEXT, output_ref TEXT, error TEXT, provider TEXT NOT NULL
);
"""


class WorkflowMemory:
    def __init__(self, db_path: Path, trace_path: Path):
        self.db_path = db_path
        self.trace_path = trace_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def now() -> str:
        return datetime.now(UTC).isoformat()

    def start_run(self, run_id: str, config: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO runs(run_id,status,started_at,finished_at,config_json) VALUES(?,?,?,?,?)",
                (run_id, "running", self.now(), None, json.dumps(config, sort_keys=True)),
            )

    def finish_run(self, run_id: str, status: str) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE runs SET status=?, finished_at=? WHERE run_id=?", (status, self.now(), run_id))

    def agent_status(
        self, run_id: str, agent: str, status: str, retry_count: int,
        input_ref: str = "", output_ref: str = "", error: str | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO agents
                (run_id,agent,status,retry_count,input_ref,output_ref,error,updated_at)
                VALUES(?,?,?,?,?,?,?,?)""",
                (run_id, agent, status, retry_count, input_ref, output_ref, error, self.now()),
            )

    def checkpoint(self, run_id: str, name: str, status: str, reason: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO checkpoints VALUES(?,?,?,?,?)",
                (run_id, name, status, reason, self.now()),
            )

    def append_trace(self, entry: dict[str, Any]) -> None:
        normalized = {**entry}
        normalized.setdefault("timestamp", self.now())
        normalized.setdefault("evidence_ids", [])
        normalized.setdefault("error", None)
        with self.trace_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(normalized, ensure_ascii=False, default=str) + "\n")
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO trace(run_id,timestamp,agent,action,status,decision_summary,evidence_ids,
                duration_sec,retry_number,input_ref,output_ref,error,provider)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    normalized["run_id"], normalized["timestamp"], normalized["agent"],
                    normalized["action"], normalized["status"], normalized["decision_summary"],
                    json.dumps(normalized["evidence_ids"]), normalized["duration_sec"],
                    normalized["retry_number"], normalized.get("input_reference", ""),
                    normalized.get("output_reference", ""), normalized.get("error"),
                    normalized["provider_or_tool"],
                ),
            )

    def add_spend(self, entry: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO spend VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    entry["run_id"], str(entry["timestamp"]), entry["asset"], entry["provider"],
                    entry["model_or_tool"], entry["operation"], entry["quantity"],
                    entry["unit_cost_inr"], entry["total_cost_inr"], entry["paid_or_free"],
                    entry["evidence_or_receipt_reference"], entry["notes"],
                ),
            )

    def run_history(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM runs ORDER BY started_at DESC")]

