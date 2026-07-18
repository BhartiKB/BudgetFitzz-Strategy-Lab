"""Submission assembly, manifesting, checksums, and ZIP packaging."""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Iterable

from insta_strategy_lab.utils.files import sha256, write_json


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tree(source: Path, destination: Path) -> None:
    if source.exists():
        shutil.copytree(source, destination, dirs_exist_ok=True)


def assemble_submission(root: Path) -> Path:
    final_dir = root / "submission/final"
    final_dir.mkdir(parents=True, exist_ok=True)
    file_map = {
        "README.md": "README.md",
        "docs/business_context.md": "business_context.md",
        "docs/qualitative_observations.md": "qualitative_observations.md",
        "docs/data_provenance.md": "data_provenance.md",
        "docs/source_checksums.sha256": "source_checksums.sha256",
        "data/raw/budgetfitzz_dataset_fixed.csv": "references/budgetfitzz_dataset_fixed.csv",
        "data/raw/Intern Task 2 - Performance Analysis and Strategy Revision.docx": "references/Intern Task 2 - Performance Analysis and Strategy Revision.docx",
        "data/processed/budgetfitzz_clean.csv": "data/budgetfitzz_clean.csv",
        "data/processed/budgetfitzz_derived.csv": "data/budgetfitzz_derived.csv",
        "data/processed/metric_contract.json": "metric_definitions.json",
        "docs/metric_definitions.md": "metric_definitions.md",
        "analysis/analysis_results.json": "analysis/analysis_results.json",
        "analysis/failure_diagnosis.json": "failure_diagnosis.json",
        "analysis/revised_strategy.json": "revised_strategy.json",
        "analysis/seven_day_plan.csv": "seven_day_plan.csv",
        "analysis/seven_day_plan.json": "seven_day_plan.json",
        "analysis/before_after.json": "before_after.json",
        "analysis/target_metrics.json": "target_metrics.json",
        "assets/captions.md": "captions.md",
        "prompts/prompt_catalogue.md": "prompt_catalogue.md",
        "logs/spend_log.csv": "spend_log.csv",
        "logs/spend_summary.json": "spend_summary.json",
        "logs/hf_promotional_credit_test.json": "logs/hf_promotional_credit_test.json",
        "logs/execution_trace.jsonl": "logs/execution_trace.jsonl",
        "logs/agent_decisions.jsonl": "logs/agent_decisions.jsonl",
        "logs/hardware_report.json": "hardware_report.json",
        "logs/timing_report.json": "timing_report.json",
        "logs/retry_report.json": "retry_report.json",
        "logs/validation_report.json": "validation_report.json",
        "logs/validation_report.md": "validation_report.md",
        "logs/lint_report.json": "logs/lint_report.json",
        "logs/test_report.txt": "logs/test_report.txt",
        "logs/workflow.db": "logs/workflow.db",
    }
    for source, destination in file_map.items():
        src = root / source
        if src.exists():
            copy_file(src, final_dir / destination)
    copy_tree(root / "analysis/charts", final_dir / "charts")
    copy_tree(root / "analysis/charts", final_dir / "analysis/charts")
    copy_tree(root / "analysis/tables", final_dir / "analysis/tables")
    copy_tree(root / "assets/posts", final_dir / "posts")
    copy_tree(root / "assets/videos", final_dir / "videos")
    copy_tree(root / "assets/video_frames", final_dir / "video_frames")
    copy_tree(root / "assets/source_media", final_dir / "source_media")
    copy_tree(root / "app", final_dir / "app")
    for source_dir in ["src", "app", "config", "scripts", "tests", "docs", "prompts"]:
        copy_tree(root / source_dir, final_dir / "source" / source_dir)
    for filename in ["pyproject.toml", "requirements.lock.txt", "setup.ps1", "run_app.ps1", "generate_submission.ps1", "validate_submission.ps1", "record_demo.ps1", "CHANGELOG.md", "AGENTS.md"]:
        src = root / filename
        if src.exists():
            copy_file(src, final_dir / "source" / filename)
    package_launcher = root / "launch_package.ps1"
    if package_launcher.exists():
        copy_file(package_launcher, final_dir / "launch_platform.ps1")
    return final_dir


def write_manifest(final_dir: Path) -> dict:
    files = []
    excluded = {"submission_manifest.json", "file_checksums.sha256"}
    for path in sorted(p for p in final_dir.rglob("*") if p.is_file() and p.name not in excluded):
        files.append({
            "path": path.relative_to(final_dir).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    manifest = {"schema_version": "1.0.0", "file_count": len(files), "files": files}
    write_json(final_dir / "submission_manifest.json", manifest)
    (final_dir / "file_checksums.sha256").write_text(
        "\n".join(f"{item['sha256']}  {item['path']}" for item in files) + "\n", encoding="utf-8"
    )
    return manifest


def create_zip(root: Path, final_dir: Path) -> Path:
    output = root / "submission/insta_strategy_lab_task2_submission.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in final_dir.rglob("*") if p.is_file()):
            archive.write(path, Path("insta_strategy_lab_task2") / path.relative_to(final_dir))
    return output


def assemble_deploy_bundle(root: Path, final_dir: Path, archive: Path) -> Path:
    """Copy only public deliverables required by the hosted application."""
    deploy_dir = root / "deploy"
    deploy_dir.mkdir(parents=True, exist_ok=True)
    file_map = {
        final_dir / "final_report.pdf": deploy_dir / "final_report.pdf",
        final_dir / "platform_walkthrough.mp4": deploy_dir / "platform_walkthrough.mp4",
        final_dir / "submission_manifest.json": deploy_dir / "submission_manifest.json",
        root / "logs/validation_report.json": deploy_dir / "validation_report.json",
        archive: deploy_dir / "insta_strategy_lab_task2_submission.zip",
    }
    for source, destination in file_map.items():
        if not source.is_file():
            raise FileNotFoundError(f"Required deployment artifact is missing: {source}")
        copy_file(source, destination)
    copy_file(
        final_dir / "platform_walkthrough.mp4",
        deploy_dir / "budgetfitzz_platform_walkthrough_with_architecture.mp4",
    )
    return deploy_dir
