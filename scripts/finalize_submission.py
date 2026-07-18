"""Finalize reports, validation, manifest, and ZIP after the demo video exists."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from insta_strategy_lab.providers import LocalProvider  # noqa: E402
from insta_strategy_lab.reporting.builder import (  # noqa: E402
    build_app_data, build_documentation, build_final_reports, load_qualitative_observations,
)
from insta_strategy_lab.reporting.packaging import (  # noqa: E402
    assemble_deploy_bundle, assemble_submission, create_zip, write_manifest,
)
from insta_strategy_lab.schemas import PlanItem  # noqa: E402
from insta_strategy_lab.validation import validate_project  # noqa: E402


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> None:
    results = load("analysis/analysis_results.json")
    diagnosis = load("analysis/failure_diagnosis.json")
    strategy = load("analysis/revised_strategy.json")
    plan = [PlanItem.model_validate(x) for x in load("analysis/seven_day_plan.json")]
    hardware = load("logs/hardware_report.json")
    before_after = load("analysis/before_after.json")
    provider = load("analysis/provider_selection.json")
    qualitative = load_qualitative_observations(ROOT)
    history = []
    import sqlite3
    with sqlite3.connect(ROOT / "logs/workflow.db") as conn:
        row = conn.execute("SELECT run_id FROM runs ORDER BY started_at DESC LIMIT 1").fetchone()
        run_id = row[0] if row else "finalized-run"

    # Keep repository documentation aligned with the generated frontend manifest.
    build_documentation(ROOT, results, diagnosis, strategy, plan, hardware, provider, run_id)
    # Refresh the extracted-package layout before the first final-mode gate.
    final_dir = assemble_submission(ROOT)
    validation = validate_project(ROOT, final=True)
    if validation["status"] != "PASS":
        failed = [x["check"] for x in validation["checks"] if not x["passed"]]
        raise SystemExit(f"Final validation failed before rebuild: {failed}")
    build_app_data(ROOT, run_id, results, diagnosis, strategy, plan, provider, validation, before_after)
    final_dir = assemble_submission(ROOT)
    build_final_reports(final_dir, results, diagnosis, strategy, plan, hardware, validation, before_after, qualitative)
    write_manifest(final_dir); create_zip(ROOT, final_dir)

    validation = validate_project(ROOT, final=True)
    if validation["status"] != "PASS":
        failed = [x["check"] for x in validation["checks"] if not x["passed"]]
        raise SystemExit(f"Final validation failed after rebuild: {failed}")
    shutil.copy2(ROOT / "logs/validation_report.json", final_dir / "validation_report.json")
    shutil.copy2(ROOT / "logs/validation_report.md", final_dir / "validation_report.md")
    build_final_reports(final_dir, results, diagnosis, strategy, plan, hardware, validation, before_after, qualitative)
    write_manifest(final_dir); archive = create_zip(ROOT, final_dir)
    deploy_dir = assemble_deploy_bundle(ROOT, final_dir, archive)
    print(json.dumps({"status":"PASS","pdf":str(final_dir/'final_report.pdf'),"demo":str(final_dir/'platform_walkthrough.mp4'),"zip":str(archive),"deploy_dir":str(deploy_dir)}, indent=2))


if __name__ == "__main__":
    main()
