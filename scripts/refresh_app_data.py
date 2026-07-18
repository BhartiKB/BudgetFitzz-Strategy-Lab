"""Refresh documentation and the frontend manifest from existing authoritative outputs.

This intentionally avoids rerunning the analytical workflow or packaging a ZIP. It is used
to preview a frontend-only change before the final walkthrough has been reviewed.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from insta_strategy_lab.reporting.builder import build_app_data, build_documentation  # noqa: E402
from insta_strategy_lab.schemas import PlanItem  # noqa: E402


def load(relative_path: str):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def main() -> None:
    results = load("analysis/analysis_results.json")
    diagnosis = load("analysis/failure_diagnosis.json")
    strategy = load("analysis/revised_strategy.json")
    plan = [PlanItem.model_validate(item) for item in load("analysis/seven_day_plan.json")]
    hardware = load("logs/hardware_report.json")
    provider = load("analysis/provider_selection.json")
    validation = load("logs/validation_report.json")
    before_after = load("analysis/before_after.json")
    with sqlite3.connect(ROOT / "logs/workflow.db") as connection:
        row = connection.execute("SELECT run_id FROM runs ORDER BY started_at DESC LIMIT 1").fetchone()
    run_id = row[0] if row else "manifest-refresh"
    build_documentation(ROOT, results, diagnosis, strategy, plan, hardware, provider, run_id)
    build_app_data(ROOT, run_id, results, diagnosis, strategy, plan, provider, validation, before_after)
    print(json.dumps({"status": "PASS", "manifest": "app/data/platform_manifest.json"}))


if __name__ == "__main__":
    main()
