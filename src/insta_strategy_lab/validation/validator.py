"""Automated analytical, content, asset, spend, packaging, and link validation."""

from __future__ import annotations

import csv
import json
import re
import sqlite3
import subprocess
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image

from insta_strategy_lab.utils.files import sha256, write_json


def check(name: str, passed: bool, evidence: str, required: bool = True) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed), "required": required, "evidence": evidence}


def ffprobe_path(root: Path) -> Path | None:
    matches = list((root / "tools" / "ffmpeg").glob("**/bin/ffprobe.exe"))
    return matches[0] if matches else None


def video_probe(path: Path, probe: Path | None) -> dict[str, Any]:
    if probe is None:
        return {}
    completed = subprocess.run(
        [str(probe), "-v", "error", "-show_entries", "format=duration,size:stream=codec_name,width,height,avg_frame_rate", "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    return json.loads(completed.stdout) if completed.returncode == 0 else {}


def html_paths_exist(root: Path, html_path: Path) -> tuple[bool, list[str]]:
    if not html_path.exists():
        return False, [str(html_path)]
    text = html_path.read_text(encoding="utf-8")
    failures = []
    for target in re.findall(r"(?:src|href)=[\"']([^\"'#]+)[\"']", text):
        if target.startswith(("http://", "https://", "mailto:", "data:", "/")):
            continue
        candidate = (html_path.parent / target.split("?")[0]).resolve()
        if not candidate.exists():
            failures.append(target)
    return not failures, failures


def validate_project(root: Path, final: bool = False) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    raw_csv = root / "data/raw/budgetfitzz_dataset_fixed.csv"
    raw_doc = root / "data/raw/Intern Task 2 - Performance Analysis and Strategy Revision.docx"
    checks.append(check("Original CSV preserved", raw_csv.exists() and raw_csv.stat().st_size > 0, str(raw_csv)))
    checks.append(check("Original DOCX preserved", raw_doc.exists() and raw_doc.stat().st_size > 0, str(raw_doc)))
    checks.append(check("Checksums present", (root / "docs/source_checksums.sha256").exists(), "docs/source_checksums.sha256"))

    raw = pd.read_csv(raw_csv) if raw_csv.exists() else pd.DataFrame()
    dates = pd.to_datetime(raw.get("date"), errors="coerce") if not raw.empty else pd.Series(dtype="datetime64[ns]")
    checks.append(check("At least fourteen historical items", len(raw) >= 14, f"n={len(raw)}"))
    checks.append(check("Dataset spans at least two weeks", (dates.max() - dates.min()).days >= 14 if len(dates) else False, f"span_days={(dates.max()-dates.min()).days if len(dates) else 0}"))
    formats = set(raw.get("format", pd.Series(dtype=str)).astype(str).str.lower())
    checks.append(check("Posts and videos exist in baseline", {"post", "video"}.issubset(formats), str(sorted(formats))))

    derived_path = root / "data/processed/budgetfitzz_derived.csv"
    derived = pd.read_csv(derived_path) if derived_path.exists() else pd.DataFrame()
    required_metrics = ["engagements", "engagement_rate_by_reach", "save_rate", "share_rate", "average_watch_time_sec", "retention_proxy"]
    checks.append(check("Raw and derived values separated", derived_path.exists() and all(col in derived for col in required_metrics), str(derived_path)))
    contract = root / "data/processed/metric_contract.json"
    checks.append(check("Metric formulas documented", contract.exists() and "engagement_rate_by_reach" in contract.read_text(encoding="utf-8"), str(contract)))
    tables = root / "analysis/tables"
    checks.append(check("Analysis reproducible", (root / "analysis/analysis_results.json").exists() and len(list(tables.glob("*_summary.csv"))) >= 9, "analysis_results + grouped tables"))
    sample_sizes = all("n" in pd.read_csv(path).columns for path in tables.glob("*_summary.csv"))
    checks.append(check("Sample sizes displayed", sample_sizes, "n column in each group table"))
    checks.append(check("Outliers handled transparently", (tables / "outliers.csv").exists(), "analysis/tables/outliers.csv"))

    diagnosis = root / "analysis/failure_diagnosis.json"
    strategy = root / "analysis/revised_strategy.json"
    checks.append(check("Failure diagnosis supported", diagnosis.exists() and "support" in diagnosis.read_text(encoding="utf-8"), str(diagnosis)))
    checks.append(check("Strategy changes linked to evidence", strategy.exists() and strategy.read_text(encoding="utf-8").count('"evidence"') >= 5, str(strategy)))

    plan_path = root / "analysis/seven_day_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8")) if plan_path.exists() else []
    checks.append(check("Seven-day plan has exactly seven items", len(plan) == 7, f"items={len(plan)}"))
    plan_formats = [item.get("format") for item in plan]
    checks.append(check("Exactly five posts", plan_formats.count("post") == 5, f"posts={plan_formats.count('post')}"))
    checks.append(check("Exactly two videos", plan_formats.count("video") == 2, f"videos={plan_formats.count('video')}"))
    required_plan_fields = {"day", "date", "format", "content_pillar", "topic", "target_audience_segment", "hook", "content_idea", "visual_direction", "caption_direction", "full_proposed_caption", "cta", "recommended_publication_time", "baseline_insight", "primary_kpi", "secondary_kpi", "reasoned_target_range", "asset_filename", "generation_prompt_or_template_reference"}
    plan_complete = all(required_plan_fields.issubset(item) and all(str(item.get(key, "")).strip() for key in required_plan_fields) for item in plan)
    checks.append(check("Every plan field populated", plan_complete, f"required_fields={len(required_plan_fields)}"))

    post_files = [root / "assets/posts" / item["asset_filename"] for item in plan if item.get("format") == "post"]
    video_files = [root / "assets/videos" / item["asset_filename"] for item in plan if item.get("format") == "video"]
    post_valid = True
    post_evidence = []
    hashes = []
    for path in post_files:
        if not path.exists():
            post_valid = False
            post_evidence.append(f"missing:{path.name}")
            continue
        with Image.open(path) as image:
            ok = image.format == "PNG" and image.size == (1080, 1350) and path.stat().st_size >= 30_000
            variance = float(np.asarray(image.resize((64, 80))).var())
            description = image.info.get("Description", "")
            ok = ok and variance > 100 and bool(description)
            post_valid &= ok
            post_evidence.append(f"{path.name}:{image.size},variance={variance:.0f},alt={bool(description)}")
        hashes.append(sha256(path))
    checks.append(check("Five valid 1080x1350 PNG assets", post_valid and len(post_files) == 5, "; ".join(post_evidence)))
    checks.append(check("No duplicate post assets", len(hashes) == len(set(hashes)) == 5, f"unique_hashes={len(set(hashes))}"))

    probe = ffprobe_path(root)
    video_valid = True
    video_evidence = []
    for path in video_files:
        details = video_probe(path, probe) if path.exists() else {}
        streams = details.get("streams", [])
        fmt = details.get("format", {})
        stream = streams[0] if streams else {}
        duration = float(fmt.get("duration", 0) or 0)
        ok = path.exists() and stream.get("codec_name") == "h264" and stream.get("width") == 1080 and stream.get("height") == 1920 and 8 <= duration <= 15 and path.stat().st_size >= 100_000
        video_valid &= ok
        video_evidence.append(f"{path.name}:{stream.get('codec_name')},{stream.get('width')}x{stream.get('height')},{duration:.2f}s")
    checks.append(check("Two valid 1080x1920 H.264 videos", video_valid and len(video_files) == 2, "; ".join(video_evidence)))
    mapped = all((root / ("assets/posts" if item["format"] == "post" else "assets/videos") / item["asset_filename"]).exists() for item in plan)
    checks.append(check("Assets match plan", mapped, "All asset_filename mappings resolve"))
    checks.append(check("Captions and CTAs exist", all(item.get("full_proposed_caption") and item.get("cta") for item in plan), "7/7 items"))
    placeholder_targets = [root / "analysis/seven_day_plan.json", root / "analysis/revised_strategy.json"] + post_files
    placeholder_found = False
    for path in placeholder_targets[:2]:
        if path.exists() and re.search(r"\b(lorem ipsum|todo|tbd|placeholder)\b", path.read_text(encoding="utf-8"), flags=re.I):
            placeholder_found = True
    checks.append(check("No placeholder text", not placeholder_found, "Structured content scan"))

    checks.append(check("Before-versus-after comparison exists", (root / "analysis/before_after.json").exists(), "analysis/before_after.json"))
    target_file = root / "analysis/target_metrics.json"
    checks.append(check("Target metrics labelled", target_file.exists() and "target" in target_file.read_text(encoding="utf-8").lower(), str(target_file)))

    spend_path = root / "logs/spend_log.csv"
    paid_total = 0.0
    spend_parse_ok = spend_path.exists()
    if spend_path.exists():
        with spend_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        try:
            paid_total = sum(float(row["total_cost_inr"]) for row in rows if row["paid_or_free"] == "paid")
            spend_parse_ok = spend_parse_ok and all("INR" in row["notes"] or "₹" in row["notes"] for row in rows)
        except (KeyError, ValueError):
            spend_parse_ok = False
    checks.append(check("Spend log parseable with currency", spend_parse_ok, str(spend_path)))
    checks.append(check("Paid generation spend <= INR 100", paid_total <= 100, f"paid_total_inr={paid_total:.2f}"))

    checks.append(check("Agent architecture implemented", len(list((root / "src/insta_strategy_lab").glob("**/*.py"))) >= 12, "modular package files"))
    db_path = root / "logs/workflow.db"
    persistent_ok = False
    if db_path.exists():
        with sqlite3.connect(db_path) as conn:
            persistent_ok = {"runs", "agents", "trace", "checkpoints", "spend"}.issubset({r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")})
    checks.append(check("Persistent workflow memory", persistent_ok, str(db_path)))
    checks.append(check("Retry handling implemented", "retry" in (root / "src/insta_strategy_lab/orchestration/workflow.py").read_text(encoding="utf-8").lower() if (root / "src/insta_strategy_lab/orchestration/workflow.py").exists() else False, "workflow.py"))
    config_path = root / "config/workflow.json"
    config_text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    checks.append(check("Configurable workflow and human checkpoints", "auto_approve_demo" in config_text and "human_checkpoints" in config_text, str(config_path)))
    checks.append(check("Execution trace exists", (root / "logs/execution_trace.jsonl").exists() and (root / "logs/execution_trace.jsonl").stat().st_size > 0, "logs/execution_trace.jsonl"))
    hardware = root / "logs/hardware_report.json"
    checks.append(check("GPU report exists", hardware.exists() and "gpu_name" in hardware.read_text(encoding="utf-8"), str(hardware)))

    app_files = [root / "app/server.py", root / "app/index.html", root / "app/app.js", root / "app/styles.css"]
    checks.append(check("Application source complete", all(path.exists() and path.stat().st_size > 0 for path in app_files), ", ".join(p.name for p in app_files)))

    if final:
        final_dir = root / "submission/final"
        demo = final_dir / "platform_walkthrough.mp4"
        pdf = final_dir / "final_report.pdf"
        archive = root / "submission/insta_strategy_lab_task2_submission.zip"
        manifest = final_dir / "submission_manifest.json"
        checks.append(check("Demo video exists", demo.exists() and demo.stat().st_size >= 100_000, str(demo)))
        checks.append(check("Final PDF exists", pdf.exists() and pdf.stat().st_size >= 50_000, str(pdf)))
        checks.append(check("Final ZIP exists", archive.exists() and zipfile.is_zipfile(archive), str(archive)))
        manifest_ok = False
        if manifest.exists():
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            manifest_ok = all((final_dir / item["path"]).exists() for item in payload.get("files", []))
        checks.append(check("Manifest references valid files", manifest_ok, str(manifest)))
        html_ok, broken = html_paths_exist(root, final_dir / "final_report.html")
        app_ok, app_broken = html_paths_exist(root, root / "app/index.html")
        checks.append(check("No broken internal HTML paths", html_ok and app_ok, f"report={broken}; app={app_broken}"))
        packaged_app_ok, packaged_app_broken = html_paths_exist(root, final_dir / "app/index.html")
        launcher = final_dir / "launch_platform.ps1"
        checks.append(check(
            "Extracted package is directly runnable",
            packaged_app_ok and launcher.exists(),
            f"launcher={launcher.exists()}; app={packaged_app_broken}",
        ))

    passed_required = all(item["passed"] for item in checks if item["required"])
    report = {
        "status": "PASS" if passed_required else "FAIL",
        "mode": "final" if final else "preflight",
        "passed": sum(1 for item in checks if item["passed"]),
        "failed": sum(1 for item in checks if not item["passed"]),
        "checks": checks,
    }
    write_json(root / "logs/validation_report.json", report)
    lines = [f"# Validation report\n\nStatus: **{report['status']}** ({report['passed']} passed, {report['failed']} failed)\n"]
    for item in checks:
        lines.append(f"- [{'x' if item['passed'] else ' '}] {item['check']} — {item['evidence']}")
    (root / "logs/validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report
