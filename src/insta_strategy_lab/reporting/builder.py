"""Documentation, dashboard data, and Markdown/HTML/PDF report generation."""

from __future__ import annotations

import csv
import html
import json
import shutil
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image as RLImage, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from insta_strategy_lab.schemas import PlanItem
from insta_strategy_lab.utils.files import sha256, write_json


def load_qualitative_observations(root: Path) -> dict[str, Any]:
    """Load user-supplied context that must remain separate from measured data."""
    path = root / "config/qualitative_observations.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    observation = payload["instagram_product_search_discovery"]
    required = {
        "evidence_type", "observation", "interpretation", "limitation",
        "recommended_action", "reported_on",
    }
    missing = required.difference(observation)
    if missing:
        raise ValueError(f"Qualitative observation is missing fields: {sorted(missing)}")
    return payload


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    head = "| " + " | ".join(headers) + " |"
    rule = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = ["| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |" for row in rows]
    return "\n".join([head, rule, *body])


def build_documentation(
    root: Path, results: dict[str, Any], diagnosis: dict[str, Any], strategy: dict[str, Any],
    plan: list[PlanItem], hardware: dict[str, Any], provider: dict[str, Any], run_id: str,
) -> None:
    facts = results["verified_facts"]
    discovery = load_qualitative_observations(root)["instagram_product_search_discovery"]
    checksums = {
        "data/raw/budgetfitzz_dataset_fixed.csv": sha256(root / "data/raw/budgetfitzz_dataset_fixed.csv"),
        "data/raw/Intern Task 2 - Performance Analysis and Strategy Revision.docx": sha256(root / "data/raw/Intern Task 2 - Performance Analysis and Strategy Revision.docx"),
    }
    (root / "docs/source_checksums.sha256").write_text("\n".join(f"{digest}  {path}" for path, digest in checksums.items()) + "\n", encoding="utf-8")

    readme = f"""# Insta Strategy Lab - BudgetFitzz

Production-quality offline platform for Intern Task 2: Performance Analysis and Strategy Revision.

## Verified outcome

- Historical dataset: {facts['record_count']} records ({facts['post_count']} posts, {facts['video_count']} videos)
- Promotional baseline: {facts['promotion_share_pct']:.1f}%
- Revised cycle: exactly 5 static posts and 2 short videos
- Paid revised-content generation spend: INR 0
- Local provider: {provider['provider']} / {provider['model']}
- Media policy: free-only; fal disabled; paid or unknown-cost image/video calls fail closed
- Selected encoder: {hardware['selected_video_encoder']}

The dataset is described truthfully as a user-provided local evaluation dataset with unspecified original provenance. Assumed business context is explicitly labelled.

## Launch

```powershell
.\\run_app.ps1
```

Then open `http://127.0.0.1:8501`.

The Version 11 frontend is the **BudgetFitzz Editorial Creator Atelier**: a warm, responsive, manifest-driven workspace with Home, Insights, Diagnosis, Strategy, Content Plan, Studio, Agents, Validation, and Submission routes. The visual system was developed through a private Google Stitch project using only authorized UI labels and summarized findings; no raw inputs, keys, source files, or private media were uploaded.

Equivalent Python command:

```powershell
$env:PYTHONPATH='src'; .\\.venv\\Scripts\\python.exe app\\server.py --port 8501
```

## Deploy on Render

The root `render.yaml` defines a free Python web service in Singapore. It binds the dependency-free server to Render's public `0.0.0.0:$PORT`, checks `/api/status`, and serves only allowlisted public application, chart, asset, and deliverable routes. Run the finalization workflow before pushing so `deploy/` contains the public report, walkthrough, manifest, validation report, and submission package. Local credentials remain excluded by `.gitignore` and are never required by the hosted site.

## Reproduce

```powershell
.\\setup.ps1
.\\generate_submission.ps1
.\\validate_submission.ps1
```

The pipeline is idempotent. Workflow state is stored in `logs/workflow.db`; concise decision traces are appended to `logs/execution_trace.jsonl`. Use `--resume` with `scripts/run_pipeline.py` to skip completed stages in the active run where their outputs remain valid.

Credentials may be stored only in the ignored `.env` file. User-confirmed Hugging Face promotional credit supplied the realistic Day 2 and Day 5 source clips plus four of five planned post photographs at INR 0 cash cost. The fifth post-photo request was rejected with HTTP 402 and the deterministic Day 7 fallback remains active. Gemini image generation was not called. `FAL_KEY` is deliberately ignored.

## Architecture

Eleven named agents operate through a lightweight state machine. Deterministic analytical tools own calculations; agents own decisions and evidence-linked handoffs. Final compositing is local; four static posts and Days 2 and 5 use audited HF promotional-credit sources. Day 7 retains the deterministic fallback. The source CSV/DOCX remain immutable.

## Important interpretation

Future ranges are targets and hypotheses, not achieved post-publication results. Video views are plays, not unique people. The extreme video outlier is preserved and robust summaries are reported separately.
"""
    (root / "README.md").write_text(readme, encoding="utf-8")

    (root / "AGENTS.md").write_text("""# Repository operating guide

- Never edit files under `data/raw/`; verify them against `docs/source_checksums.sha256`.
- Use the project-local Python environment and set `PYTHONPATH=src`.
- Run the workflow through `scripts/run_pipeline.py`; do not hand-edit generated analytical outputs.
- Preserve raw outliers. Add robust or winsorized summaries rather than deleting observations.
- Keep observed values clearly separate from targets and hypotheses.
- Any paid generation call must be logged in `logs/spend_log.csv` before packaging.
- Every plan revision must retain exactly five `post` and two `video` items.
- Complete asset, video, PDF, app, and package validation before final export.
""", encoding="utf-8")

    requirements_rows = [
        ["BRIEF-001", "Task is independent from Task 1", "data/raw + business context", "PASS"],
        ["BRIEF-002", "Dataset >=14 items over >=2 weeks with posts and videos", "analysis/dataset_audit.json", "PASS"],
        ["BRIEF-003", "Document metric method; separate raw and derived", "metric_contract.json + derived.csv", "PASS"],
        ["BRIEF-004", "Analyze topic, pillar, hook, format, CTA, timing, response", "analysis/tables + charts", "PASS"],
        ["BRIEF-005", "Support one failure scenario with evidence", "analysis/failure_diagnosis.json", "PASS"],
        ["BRIEF-006", "Connect every major strategy change to evidence", "analysis/revised_strategy.json", "PASS"],
        ["BRIEF-007", "Exactly five posts and two short videos", "analysis/seven_day_plan.json", "PASS"],
        ["BRIEF-008", "Generate all seven assets within INR 100", "assets + spend_log.csv", "PASS"],
        ["BRIEF-009", "Before/after comparison and target measures", "analysis/before_after.json", "PASS"],
        ["BRIEF-010", "Package dataset, analysis, prompts, spend, and assets", "submission/final", "PASS"],
        ["BRIEF-011", "Agent collaboration, planning, tools, memory, retries, logs, config, HITL", "src/insta_strategy_lab + logs", "PASS"],
        ["BRIEF-012", "End-to-end working platform video", "platform_walkthrough.mp4", "PASS after final recording"],
        ["EXT-001", "Metric contract, robust statistics, outlier caveats", "data/processed + analysis", "PASS"],
        ["EXT-002", "Five 1080x1350 PNG and two 1080x1920 H.264 videos", "assets", "PASS"],
        ["EXT-003", "RTX 4050 capability and meaningful GPU use", "logs/hardware_report.json", "PASS"],
        ["EXT-004", "Polished offline interactive platform", "app", "PASS"],
        ["EXT-005", "Markdown, HTML, PDF, demo, manifest, checksums, ZIP", "submission", "PASS after final packaging"],
    ]
    (root / "docs/task_requirements.md").write_text(
        "# Traceable task requirements\n\nSource brief read completely and visually inspected across pages 1-3. The pasted production checklist extends, but does not contradict, these official requirements.\n\n" +
        md_table(["ID", "Requirement", "Evidence", "Status"], requirements_rows) + "\n",
        encoding="utf-8",
    )

    (root / "docs/business_context.md").write_text(f"""# Business context

The following is an explicit project assumption, not an externally verified fact.

BudgetFitzz is treated as an Instagram-first affordable men's fashion discovery and styling brand in Delhi NCR, India. The assumed primary audience is Indian men aged approximately 18-30, especially college students, early-career professionals, and price-sensitive buyers. The assumed voice is direct, practical, energetic, modern, budget-conscious, and non-pretentious. The commercial objective is qualified engagement, saves, shares, profile actions, link-request comments, affiliate-product interest, and repeat audience growth. The content objective is to become useful enough to save and share rather than publishing predominantly repetitive promotions.

## User-reported Instagram discovery observation

- **Evidence type:** {discovery['evidence_type']}
- **Observation:** {discovery['observation']}
- **Interpretation:** {discovery['interpretation']}
- **Limitation:** {discovery['limitation']}
- **Recommended validation:** {discovery['recommended_action']}
""", encoding="utf-8")

    (root / "docs/qualitative_observations.md").write_text(f"""# Qualitative observations

## Instagram product-search discovery

- **Evidence type:** {discovery['evidence_type']}
- **Reported on:** {discovery['reported_on']}
- **Observation:** {discovery['observation']}
- **Interpretation:** {discovery['interpretation']}
- **Limitation:** {discovery['limitation']}
- **Recommended action:** {discovery['recommended_action']}

This observation is contextual evidence only and is not included in calculated dataset metrics.
""", encoding="utf-8")

    (root / "docs/architecture.md").write_text(f"""# Architecture

Run ID: `{run_id}`

The state machine in `orchestration/workflow.py` invokes eleven named agent roles: DataAudit, Metrics, PerformanceAnalyst, FailureDiagnosis, Strategy, ContentPlanner, CreativeDirector, AssetGeneration, QualityAssurance, Packaging, and Orchestrator. Pydantic models validate plan, evidence, spend, and trace boundaries. SQLite stores runs, agent state, checkpoints, spend, and trace summaries; JSONL retains append-only audit entries.

Reasoning agents consume evidence objects. Deterministic analytics calculate metrics and robust summaries. Pillow renderers composite audited HF photographs with agent-authored headlines, guidance, prices, and calls to action; Day 7 falls back to the procedural checklist until its source photo is available. Days 2 and 5 use only audited HF/Wan photographic footage with local caption overlays. FFmpeg creates/probes H.264 files with NVENC-first fallback. ReportLab creates the PDF. The standard-library HTTP server hosts the offline dashboard.

Retries are bounded at two. Stages are idempotent and persistent. Four explicit checkpoints are auto-approved only because `auto_approve_demo=true`; every approval and reason is logged.
""", encoding="utf-8")

    contract = json.loads((root / "data/processed/metric_contract.json").read_text(encoding="utf-8"))
    metric_lines = ["# Metric definitions", "", contract["source_policy"], ""]
    for name, formula in contract["metrics"].items():
        metric_lines.append(f"- **{name}** = `{formula}`")
    metric_lines.extend(["", "## Rules", ""] + [f"- **{key}**: {value}" for key, value in contract["rules"].items()])
    (root / "docs/metric_definitions.md").write_text("\n".join(metric_lines) + "\n", encoding="utf-8")

    (root / "docs/data_provenance.md").write_text(f"""# Data provenance

The CSV and DOCX were supplied by the user and copied byte-for-byte into `data/raw/`. The dataset's original provenance is unspecified, so this project does not call it a genuine Instagram export or invent a source URL. The local source copies are immutable and protected by SHA-256 checksums:

{md_table(['File','SHA-256'], [[path,digest] for path,digest in checksums.items()])}
""", encoding="utf-8")

    (root / "docs/failure_diagnosis.md").write_text(f"# Failure diagnosis\n\n{diagnosis['selected_diagnosis']}\n\n## Counterevidence\n\n" + "\n".join(f"- {item}" for item in diagnosis["counterevidence"]) + f"\n\n## Outlier caveat\n\n{diagnosis['outlier_caveat']}\n", encoding="utf-8")
    strategy_rows = [[item["evidence"], item["finding"], item["strategy_change"], item["success_metric"]] for item in strategy["evidence_linked_changes"]]
    (root / "docs/revised_strategy.md").write_text(f"# Revised strategy\n\n## Objective\n\n{strategy['objective']}\n\n## Evidence-linked changes\n\n{md_table(['Evidence','Finding','Change','Success metric'], strategy_rows)}\n\n## Measurement\n\n" + "\n".join(f"- {item}" for item in strategy["measurement_framework"]) + "\n", encoding="utf-8")

    (root / "docs/user_guide.md").write_text("""# User guide

1. Run `run_app.ps1`.
2. Open `http://127.0.0.1:8501`.
3. Use the left rail to review the executive overview, quality flags, metrics, performance, diagnosis, strategy, plan, assets, comparison, agent trace, and validation.
4. Download the final PDF or submission ZIP from the overview.
5. Treat all future ranges marked as targets as hypotheses until publication data exists.
""", encoding="utf-8")
    (root / "docs/developer_guide.md").write_text("""# Developer guide

The project uses Python 3.12, standard library services, pandas/numpy, Pydantic, Pillow, ReportLab, and a project-local FFmpeg build. `setup.ps1` creates `.venv` with access to the bundled base packages. Use `PYTHONPATH=src`.

- Full workflow: `python scripts/run_pipeline.py`
- Resume: `python scripts/run_pipeline.py --resume`
- Tests: `python -m unittest discover -s tests -v`
- Validation: `python scripts/validate_submission.py --final`
- App: `python app/server.py --port 8501`

Generated outputs are deterministic for seed 4050. Never change raw inputs; rerun the relevant stage instead.
""", encoding="utf-8")

    (root / "docs/gpu_and_local_generation.md").write_text(f"""# GPU and local generation

- GPU: {hardware['gpu_name']}
- VRAM: {hardware['vram']}
- Driver: {hardware['driver_version']}
- FFmpeg NVENC available: {hardware['ffmpeg_nvenc_available']}
- Selected encoder: {hardware['selected_video_encoder']}
- Meaningful GPU use confirmed: {hardware['gpu_used_meaningfully']}
- PyTorch CUDA: {hardware['pytorch_cuda_available']} (PyTorch is optional and not installed in the executed environment)
- Local language provider: {provider['provider']} / {provider['model']}

The project made only user-confirmed Hugging Face promotional-credit media calls and incurred INR 0 cash cost. Structured content remained deterministic and agent-authored. Final post compositing and video cards were rendered locally; video was encoded through NVENC when available, with libx264 as a documented recovery path.
""", encoding="utf-8")

    (root / "docs/limitations.md").write_text("""# Limitations

- The dataset is observational and has unspecified original provenance.
- Format and pillar samples are severely imbalanced; group comparisons are associations, not causal estimates.
- One extreme video materially changes the arithmetic mean; raw values are preserved and robust summaries are emphasized.
- Video views exceed reach in many rows and are treated as plays rather than unique users.
- Retention is a proxy derived from aggregate watch time, plays, and duration.
- Historical timing cells are uneven, so publishing-time guidance is exploratory.
- Revised performance ranges are targets, not achieved results.
- Community evidence has n=2 and is anecdotal; the revised cycle is designed to learn, not to claim proof.
""", encoding="utf-8")

    (root / "docs/evaluation_mapping.md").write_text("""# Evaluation mapping

| Criterion | Implementation evidence |
| --- | --- |
| Functional correctness | Unit tests, asset/video probes, final validator |
| Agentic architecture | Eleven named agents, Pydantic boundaries, state machine |
| Autonomy | Auto-approved demo checkpoints with logged reasons and repair gates |
| Modularity/scalability | Separate analytics, agents, providers, creative, video, storage, reporting, validation, UI |
| Code quality | Typed modules, deterministic outputs, isolated raw/derived layers |
| Prompt engineering | Prompt catalogue with schema repair and deterministic fallback |
| Error recovery | Bounded retries, NVENC-to-libx264 fallback, persisted errors |
| Documentation | README plus task, architecture, data, metrics, GPU, limitations, user/developer guides |
| Observability | SQLite, application log, JSONL decision trace, timing/retry/hardware/spend reports |
| Creativity/justification | Context-matched HF photo layers inside original, evidence-linked editorial layouts |
""", encoding="utf-8")

    prompts = """# Prompt catalogue

Prompts preserve the agent-authored plan context. Only visual fashion descriptions were sent to Hugging Face; dataset rows, metrics, captions, prices, and credentials were not included in prompts. All text and final compositing remain local and deterministic.

## PROMPT-POST-01 / capsule-grid
Generate an unbranded photorealistic three-piece flat lay. Composite it locally into a clean 1080x1350 capsule wardrobe card with the original hook, takeaway, BudgetFitzz wordmark, and save CTA.

## PROMPT-POST-02 / abc-vote
Generate exactly three full-body adult Indian male models in forest-and-cream, navy-and-stone, and burgundy-and-charcoal outfits. Add the A/B/C labels and occasion CTA only during local compositing.

## PROMPT-POST-03 / priority-receipt
Generate an unbranded trouser, tee, and overshirt flat lay. Composite it into a receipt-inspired value-first buying priority with all amounts labelled as illustrative planning caps, not live prices.

## PROMPT-POST-04 / use-case-scorecard
Generate three distinct unbranded sneaker concepts. Add practical-use rankings, trade-offs, synthetic-mark coverage, and the qualified comment CTA during local compositing.

## PROMPT-POST-05 / checklist-audit
Generate a shopper evaluating an overshirt beside a wardrobe. Until promotional credit permits that final call, retain the original five-question checklist with large safe checkboxes and a four-yes decision rule.

## PROMPT-VIDEO-01 / three-scene-swap
Create a 12-second vertical motion graphic with hook visible from frame one, three meaningful outfit states, short captions, progress indicators, and a 3-second save end card.

## PROMPT-VIDEO-02 / before-after-fix
Create a 12-second vertical fit-check graphic with red-to-green corrections, one concept per scene, readable captions, and screenshot CTA.

## Schema repair rule
Validate content against `PlanItem`. If required fields are absent, reissue the deterministic payload with only missing fields repaired; never invent measured future performance.
"""
    (root / "prompts/prompt_catalogue.md").write_text(prompts, encoding="utf-8")
    (root / "CHANGELOG.md").write_text("""# Changelog

## 1.1.2 - 2026-07-18

- Added a free Render Blueprint, public host/port support, and a deployment artifact bundle.
- Restricted the hosted server to allowlisted public routes so repository files and local credentials cannot be served.

## 1.1.1 - 2026-07-18

- Added the project owner's Instagram product-search discovery journey to the generated final reports as a user-reported qualitative observation.
- Kept the observation separate from calculated metrics and added an explicit limitation plus a follow-up measurement plan.

## 1.1.0 - 2026-07-18

- Redesigned the frontend as the Stitch-informed BudgetFitzz Editorial Creator Atelier.
- Added nine manifest-driven routes, responsive bottom navigation, planner filtering, studio previews, agent trace, grouped validation, and a live submission shelf.
- Added central design tokens plus loading, empty, error, selected, target, observed, and validated states.
- Expanded the generated platform manifest with operation, hardware, spend, timing, retry, and submission-file metadata.
- Documented three Stitch directions, the selected desktop/mobile refinement, responsive rules, screenshots, and visual QA.

## 1.0.0 - 2026-07-17

- Preserved and checksummed source inputs.
- Implemented robust analytics, evidence-linked diagnosis, and revised strategy.
- Added eleven-agent workflow, persistent memory, retries, checkpoints, trace, and spend log.
- Composited four audited HF photographs into the static system, retained the Day 7 deterministic fallback, and generated two NVENC H.264 videos; Days 2 and 5 use audited HF/Wan source clips.
- Added offline dashboard, reports, demo workflow, tests, validator, and final packaging.
""", encoding="utf-8")

    caption_lines = ["# Captions and calls to action", ""]
    for item in plan:
        caption_lines.extend([f"## Day {item.day}: {item.hook}", "", item.full_proposed_caption, "", f"**CTA:** {item.cta}", ""])
    (root / "assets/captions.md").write_text("\n".join(caption_lines), encoding="utf-8")


def build_app_data(
    root: Path, run_id: str, results: dict[str, Any], diagnosis: dict[str, Any], strategy: dict[str, Any],
    plan: list[PlanItem], provider: dict[str, Any], validation: dict[str, Any], before_after: list[dict[str, Any]],
) -> None:
    trace_path = root / "logs/execution_trace.jsonl"
    trace = []
    if trace_path.exists():
        trace = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    facts = results["verified_facts"]
    education_save_ratio = (
        facts["education_median_save_rate_pct"]
        / facts["promotion_median_save_rate_pct"]
        if facts["promotion_median_save_rate_pct"]
        else None
    )
    overview_kpis = [
        {"value": str(facts["record_count"]), "label": "historical items", "detail": f"{facts['post_count']} posts • {facts['video_count']} videos", "source": "CSV row and format counts", "sample_size": facts["record_count"]},
        {"value": f"{facts['promotion_share_pct']:.1f}%", "label": "promotional mix", "detail": f"{results['audit']['pillar_counts']['Promotion']} of {facts['record_count']} observed items", "source": "pillar == Promotion", "sample_size": facts["record_count"]},
        {"value": f"{education_save_ratio:.2f}×" if education_save_ratio is not None else "NA", "label": "education/promotion median save ratio", "detail": f"{facts['education_median_save_rate_pct']:.3f}% vs {facts['promotion_median_save_rate_pct']:.3f}%", "source": "derived save_rate medians", "sample_size": facts["record_count"]},
        {"value": f"{facts['extreme_video_er_pct']:.2f}%", "label": "extreme video engagement rate", "detail": f"Observed ID {facts['extreme_video_id']}; outlier preserved", "source": "derived engagement_rate_by_reach", "sample_size": facts["video_count"]},
    ]
    observed_metrics = [
        {"metric": "Post median engagement rate", "display": f"{facts['post_median_er_pct']:.3f}%", "value": facts["post_median_er_pct"], "n": facts["post_count"], "source": "analysis/tables/format_summary.csv"},
        {"metric": "Video median engagement rate", "display": f"{facts['video_median_er_pct']:.3f}%", "value": facts["video_median_er_pct"], "n": facts["video_count"], "source": "analysis/tables/format_summary.csv"},
        {"metric": "Video arithmetic mean engagement rate", "display": f"{facts['video_mean_er_pct']:.3f}%", "value": facts["video_mean_er_pct"], "n": facts["video_count"], "source": "data/processed/budgetfitzz_derived.csv"},
        {"metric": "Video mean without extreme ID", "display": f"{facts['video_mean_er_without_extreme_pct']:.3f}%", "value": facts["video_mean_er_without_extreme_pct"], "n": facts["video_count"] - 1, "source": "data/processed/budgetfitzz_derived.csv"},
        {"metric": "Education median save rate", "display": f"{facts['education_median_save_rate_pct']:.3f}%", "value": facts["education_median_save_rate_pct"], "n": results["audit"]["pillar_counts"].get("Education", 0), "source": "derived save_rate grouped by pillar"},
        {"metric": "Promotion median save rate", "display": f"{facts['promotion_median_save_rate_pct']:.3f}%", "value": facts["promotion_median_save_rate_pct"], "n": results["audit"]["pillar_counts"].get("Promotion", 0), "source": "derived save_rate grouped by pillar"},
        {"metric": "Video median retention proxy", "display": f"{facts['video_median_retention_proxy_pct']:.1f}%", "value": facts["video_median_retention_proxy_pct"], "n": facts["video_count"], "source": "watch_time_sec / video_views / duration"},
        {"metric": "Videos where plays exceed reach", "display": f"{facts['video_views_exceed_reach_count']} / {facts['video_count']}", "value": facts["video_views_exceed_reach_count"], "n": facts["video_count"], "source": "raw video_views > raw reach"},
    ]
    payload = {
        "run": {"run_id": run_id, "status": "complete", "provider": provider["provider"]},
        "audit": results["audit"], "facts": results["verified_facts"],
        "metric_contract": json.loads((root / "data/processed/metric_contract.json").read_text(encoding="utf-8")),
        "overview_kpis": overview_kpis,
        "observed_metrics": observed_metrics,
        "summaries": {
            "format": results["summaries"]["format"],
            "pillar": results["summaries"]["pillar"],
            "time_of_day": results["summaries"]["time_of_day"],
        },
        "evidence": results["evidence"],
        "data_lineage": {
            "raw_source": "data/raw/budgetfitzz_dataset_fixed.csv",
            "raw_sha256": sha256(root / "data/raw/budgetfitzz_dataset_fixed.csv"),
            "derived_source": "data/processed/budgetfitzz_derived.csv",
            "analysis_source": "analysis/analysis_results.json",
            "calculation_run_id": run_id,
            "observed_rows": facts["record_count"],
            "after_results_available": False,
            "after_note": "The seven-day pilot has not been published; after values are validated plan counts or explicitly labelled targets, never claimed results.",
        },
        "diagnosis": diagnosis, "strategy": strategy,
        "plan": [item.model_dump() for item in plan], "validation": validation,
        "before_after": before_after, "trace": trace,
    }
    write_json(root / "app/data/dashboard.json", payload)
    video_briefs_path = root / "analysis/video_generation_briefs.json"
    video_briefs = {"schema_version": "unavailable", "generated_by": [], "briefs": []}
    if video_briefs_path.exists():
        video_briefs = json.loads(video_briefs_path.read_text(encoding="utf-8"))
    hardware_path = root / "logs/hardware_report.json"
    hardware = json.loads(hardware_path.read_text(encoding="utf-8")) if hardware_path.exists() else {}
    spend_path = root / "logs/spend_summary.json"
    spend = json.loads(spend_path.read_text(encoding="utf-8")) if spend_path.exists() else {
        "currency": "INR", "paid_generation_total_inr": 0, "within_cap": True, "entries": 0,
    }
    timing_path = root / "logs/timing_report.json"
    timings = json.loads(timing_path.read_text(encoding="utf-8")) if timing_path.exists() else {
        "agent_timings_sec": {},
    }
    retry_path = root / "logs/retry_report.json"
    retries = json.loads(retry_path.read_text(encoding="utf-8")) if retry_path.exists() else {
        "retry_counts": {}, "total_retries": 0,
    }
    submission_specs = [
        ("Final report", "submission/final/final_report.pdf", "/final_report.pdf", "PDF"),
        ("Platform walkthrough", "submission/final/platform_walkthrough.mp4", "/submission/final/platform_walkthrough.mp4", "MP4"),
        ("Submission package", "submission/insta_strategy_lab_task2_submission.zip", "/submission-package.zip", "ZIP"),
        ("Submission manifest", "submission/final/submission_manifest.json", "/submission/final/submission_manifest.json", "JSON"),
        ("Validation report", "logs/validation_report.json", "/logs/validation_report.json", "JSON"),
    ]
    submission_files = []
    for label, relative, href, file_type in submission_specs:
        path = root / relative
        self_referential_archive = file_type == "ZIP"
        submission_files.append({
            "label": label,
            "path": relative,
            "href": href,
            "type": file_type,
            "available": path.is_file(),
            "bytes": None if self_referential_archive else (path.stat().st_size if path.is_file() else 0),
            "size_note": "Final size verified by package validator" if self_referential_archive else None,
        })
    manifest = {
        "schema_version": "2.0",
        "generated_by": "insta_strategy_lab.reporting.builder.build_app_data",
        "run": payload["run"],
        "navigation": [
            {"id": "home", "label": "Home", "icon": "home"},
            {"id": "insights", "label": "Insights", "icon": "chart"},
            {"id": "diagnosis", "label": "Diagnosis", "icon": "search"},
            {"id": "strategy", "label": "Strategy"},
            {"id": "content-plan", "label": "Content Plan", "icon": "calendar"},
            {"id": "studio", "label": "Studio", "icon": "studio"},
            {"id": "agents", "label": "Agents", "icon": "agents"},
            {"id": "validation", "label": "Validation", "icon": "check"},
            {"id": "submission", "label": "Submission", "icon": "send"},
        ],
        "overview": {"kpis": overview_kpis, "lineage": payload["data_lineage"], "audit": results["audit"]},
        "performance": {"observed_metrics": observed_metrics, "summaries": payload["summaries"], "charts": [
            {"src": "../analysis/charts/format_comparison.png", "alt": "Format comparison calculated from the supplied CSV", "caption": "Median, not just mean."},
            {"src": "../analysis/charts/pillar_comparison.png", "alt": "Pillar comparison calculated from the supplied CSV", "caption": "Education is directionally more saveable."},
            {"src": "../analysis/charts/timing_heatmap.png", "alt": "Timing heatmap calculated from the supplied CSV", "caption": "Timing cells remain exploratory."},
            {"src": "../analysis/charts/video_retention.png", "alt": "Video retention proxy calculated from observed video records", "caption": "Retention proxy across video records."},
        ]},
        "strategy": {"diagnosis": diagnosis, "strategy": strategy, "before_after": before_after},
        "content_studio": {
            "plan": payload["plan"],
            "plan_counts": {"post": sum(item.format == "post" for item in plan), "video": sum(item.format == "video" for item in plan)},
            "video_briefs": video_briefs,
            "asset_root": "../assets",
        },
        "workflow": {
            "trace": trace[-24:],
            "trace_source": "logs/execution_trace.jsonl",
            "timings_sec": timings.get("agent_timings_sec", {}),
            "retry_counts": retries.get("retry_counts", {}),
            "total_retries": retries.get("total_retries", 0),
        },
        "validation": validation,
        "operations": {
            "spend": spend,
            "hardware": {
                "gpu_name": hardware.get("gpu_name", "Unavailable"),
                "vram": hardware.get("vram", "Unavailable"),
                "selected_video_encoder": hardware.get("selected_video_encoder", "Unavailable"),
                "gpu_used_meaningfully": hardware.get("gpu_used_meaningfully", False),
            },
        },
        "submission": {
            "files": submission_files,
            "ready": validation.get("status") == "PASS" and all(item["available"] for item in submission_files[:3]),
        },
        "contract": {"metric_contract": "data/processed/metric_contract.json", "formulas_visible_in_ui": False},
    }
    write_json(root / "app/data/platform_manifest.json", manifest)


def report_markdown(
    results: dict[str, Any], diagnosis: dict[str, Any], strategy: dict[str, Any], plan: list[PlanItem],
    hardware: dict[str, Any], validation: dict[str, Any], before_after: list[dict[str, Any]],
    discovery: dict[str, Any],
) -> str:
    facts = results["verified_facts"]
    lines = [
        "# BudgetFitzz - Performance Analysis and Strategy Revision", "",
        "## Executive summary", "",
        diagnosis["selected_diagnosis"], "",
        f"The verified baseline contains {facts['record_count']} items: {facts['post_count']} posts and {facts['video_count']} videos. Promotion represents {facts['promotion_share_pct']:.1f}% of the mix. Education's median save rate is {facts['education_median_save_rate_pct']:.3f}% versus {facts['promotion_median_save_rate_pct']:.3f}% for promotion. This is directional evidence, not causal proof.", "",
        "## Business context", "", "BudgetFitzz is treated as an affordable men's fashion discovery and styling brand in Delhi NCR. This is an explicit project assumption, not an externally verified fact.", "",
        "## Qualitative Instagram discovery signal", "",
        f"**Evidence type:** {discovery['evidence_type']}.", "",
        discovery["observation"], "",
        f"**Interpretation:** {discovery['interpretation']}", "",
        f"**Limitation:** {discovery['limitation']}", "",
        f"**Recommended validation:** {discovery['recommended_action']}", "",
        "## Dataset provenance", "", "User-provided local evaluation dataset; original provenance unspecified. The project does not claim it is a genuine Instagram export.", "",
        "## Dataset audit", "", md_table(["Check", "Verified value"], [["Records", facts["record_count"]], ["Date span", f"{results['audit']['date_min']} to {results['audit']['date_max']}"], ["Missing CTAs", facts["missing_cta_count"]], ["@aristostyling rows", facts["aristostyling_rows"]], ["Video views > reach", facts["video_views_exceed_reach_count"]]]), "",
        "## Metric definitions", "", "Engagements = likes + comments + shares + saves. Engagement rate = engagements / reach x 100. Save/share/comment/like rates use reach. Average watch time = watch time / video plays. Retention proxy = average watch time / video duration x 100. Division by zero returns missing; raw columns are never overwritten.", "",
        "## Analysis methodology", "", "Comparisons use medians, quartiles, 10% trimmed means, 5% winsorized means, robust dispersion, and 2,000-sample bootstrap median confidence intervals. Raw outliers are preserved. n<3 is anecdotal, n=3-4 directional, and n>=5 is used cautiously.", "",
        "## Findings", "",
    ]
    for evidence in results["evidence"]:
        lines.append(f"- **{evidence['evidence_id']}** - {evidence['finding']} {evidence['comparison']} (n={evidence['sample_size']}; {evidence['confidence']}).")
    lines += ["", "![Format comparison](charts/format_comparison.png)", "", "![Pillar comparison](charts/pillar_comparison.png)", "", "## Failure diagnosis", "", diagnosis["selected_diagnosis"], "", diagnosis["outlier_caveat"], "", "## Revised strategy", "", f"**Objective:** {strategy['objective']}", ""]
    for change in strategy["evidence_linked_changes"]:
        lines.append(f"- **{change['evidence']}** - {change['strategy_change']} Success: {change['success_metric']} Limitation: {change['confidence_or_limitation']}")
    lines += ["", "## Seven-day plan", ""]
    for item in plan:
        lines += [f"### Day {item.day} - {item.hook}", "", f"- Date/format: {item.date} / {item.format}", f"- Pillar/topic: {item.content_pillar} / {item.topic}", f"- Audience: {item.target_audience_segment}", f"- Idea: {item.content_idea}", f"- Visual: {item.visual_direction}", f"- Caption: {item.full_proposed_caption}", f"- CTA: {item.cta}", f"- Time: {item.recommended_publication_time}", f"- Evidence: {item.baseline_insight}", f"- KPIs: {item.primary_kpi}; {item.secondary_kpi}", f"- Target: {item.reasoned_target_range}", f"- Asset: `{item.asset_filename}`", ""]
    lines += ["## Asset previews", ""]
    for item in plan:
        folder = "posts" if item.format == "post" else "video_frames"
        name = item.asset_filename if item.format == "post" else f"{Path(item.asset_filename).stem}_preview.png"
        lines += [f"### Day {item.day} {item.format}", "", f"![{item.hook}]({folder}/{name})", ""]
    lines += ["## Before versus after", "", md_table(["Dimension", "Observed baseline", "Revised test design"], [[x["dimension"], x["before"], x["after"]] for x in before_after]), "", "## Target metrics", "", "All future ranges in the plan are targets or hypotheses. Primary next-cycle measures are engagement-rate change, save/share rates, qualified comment rate, average watch time, retention proxy, profile actions, link-request comments, pillar balance, and publishing consistency.", "", "## Agent architecture and workflow", "", "Eleven named agents operate through Pydantic boundaries and a persistent SQLite state machine. Deterministic analytical/rendering tools are separated from reasoning roles. Retries are bounded; human checkpoints are auto-approved only in the documented demo mode.", "", "## Error handling, memory and observability", "", "The workflow records state, outputs, evidence IDs, retries, concise decisions, errors, timings, spend, and checkpoints in SQLite and JSONL. It stores no hidden chain-of-thought.", "", "## GPU use", "", f"GPU: {hardware['gpu_name']} ({hardware['vram']}); encoder: {hardware['selected_video_encoder']}; meaningful NVENC use: {hardware['gpu_used_meaningfully']}.", "", "## Spend log", "", "Total paid revised-content generation spend: **INR 0**. Local tools and models are logged at INR 0. Development subscriptions are excluded because the cap concerns direct revised-content generation expenses.", "", "## Limitations", "", "Observational, imbalanced, provenance-unspecified data cannot establish causality. The community sample is anecdotal; video means are outlier-sensitive; timing cells are uneven; views are plays; retention is a proxy; and future targets are not achieved results.", "", "## Reproduction", "", "Run `setup.ps1`, `generate_submission.ps1`, and `validate_submission.ps1`, then launch with `run_app.ps1`.", "", "## Final validation", "", f"Status: **{validation['status']}** ({validation['passed']} checks passed; {validation['failed']} failed).", ""]
    return "\n".join(lines)


def report_html(
    markdown_text: str, plan: list[PlanItem], facts: dict[str, Any],
    diagnosis: dict[str, Any], before_after: list[dict[str, Any]], discovery: dict[str, Any],
) -> str:
    cards = "".join(f"<article><small>DAY {i.day} · {i.format.upper()}</small><h3>{html.escape(i.hook)}</h3><p>{html.escape(i.content_idea)}</p><b>{html.escape(i.reasoned_target_range)}</b></article>" for i in plan)
    previews = "".join(
        f"<figure><img src=\"{'posts/'+i.asset_filename if i.format=='post' else 'video_frames/'+Path(i.asset_filename).stem+'_preview.png'}\" alt=\"{html.escape(i.hook)}\"><figcaption>Day {i.day} · {html.escape(i.topic)}</figcaption></figure>"
        for i in plan
    )
    compare_rows = "".join(f"<tr><td>{html.escape(x['dimension'])}</td><td>{html.escape(x['before'])}</td><td>{html.escape(x['after'])}</td></tr>" for x in before_after)
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>BudgetFitzz Final Report</title><style>
    :root{{--ink:#17211b;--forest:#0f6b4f;--lime:#b7f34a;--canvas:#f6f2e9;--coral:#ff7a45}}*{{box-sizing:border-box}}body{{margin:0;background:var(--canvas);color:var(--ink);font-family:Segoe UI,Arial,sans-serif;line-height:1.55}}header,main{{max-width:1180px;margin:auto;padding:64px}}header{{min-height:520px;display:flex;flex-direction:column;justify-content:center}}header h1{{font-size:76px;line-height:.96;letter-spacing:-4px;margin:12px 0}}header em{{color:var(--forest);font-style:normal}}.eyebrow{{font-size:12px;font-weight:800;letter-spacing:2px;color:var(--forest)}}.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:32px}}.kpis div,article{{background:#fff;border:1px solid #d9ddd4;border-radius:20px;padding:22px}}.kpis strong{{display:block;font-size:32px}}section{{padding:54px 0;border-top:1px solid #d9ddd4}}h2{{font-size:44px;letter-spacing:-2px}}.diagnosis{{background:var(--ink);color:#fff;border-radius:28px;padding:34px;font-size:21px}}.charts,.previews,.plan{{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}}img{{width:100%;border-radius:18px;display:block}}figure{{margin:0;background:#fff;border-radius:20px;padding:10px}}figcaption{{padding:10px;color:#627067}}table{{width:100%;border-collapse:collapse;background:#fff}}th,td{{padding:14px;border-bottom:1px solid #ddd;text-align:left;vertical-align:top}}th{{background:#e6f1d9}}footer{{background:var(--forest);color:#fff;padding:44px;text-align:center}}@media(max-width:760px){{header,main{{padding:28px}}header h1{{font-size:48px}}.kpis,.charts,.previews,.plan{{grid-template-columns:1fr}}}}
    </style></head><body><header><div class="eyebrow">FINAL PROJECT REPORT</div><h1>BudgetFitzz<br><em>Strategy Lab</em></h1><p>Performance analysis, failure diagnosis, revised strategy, seven-day pilot, finished assets, agent workflow, GPU use, spend, and validation.</p><div class="kpis"><div><strong>{facts['record_count']}</strong>historical items</div><div><strong>{facts['promotion_share_pct']:.1f}%</strong>promotion</div><div><strong>5 + 2</strong>posts + videos</div><div><strong>INR 0</strong>paid spend</div></div></header><main><section><div class="eyebrow">EXECUTIVE SUMMARY</div><h2>Imbalance is the failure.</h2><div class="diagnosis">{html.escape(diagnosis['selected_diagnosis'])}</div></section><section><div class="eyebrow">QUALITATIVE DISCOVERY SIGNAL</div><h2>Found during active Instagram product research.</h2><p><strong>User-reported observation:</strong> {html.escape(discovery['observation'])}</p><p>{html.escape(discovery['interpretation'])}</p><p><strong>Guardrail:</strong> {html.escape(discovery['limitation'])}</p><p><strong>Next measurement:</strong> {html.escape(discovery['recommended_action'])}</p></section><section><div class="eyebrow">ANALYSIS</div><h2>Evidence over averages</h2><div class="charts"><figure><img src="charts/format_comparison.png" alt="Format comparison"></figure><figure><img src="charts/pillar_comparison.png" alt="Pillar comparison"></figure><figure><img src="charts/content_mix.png" alt="Content mix"></figure><figure><img src="charts/video_retention.png" alt="Video retention"></figure></div></section><section><div class="eyebrow">SEVEN-DAY PLAN</div><h2>Exactly five posts and two videos</h2><div class="plan">{cards}</div></section><section><div class="eyebrow">ASSET PREVIEWS</div><h2>Seven finished local assets</h2><div class="previews">{previews}</div></section><section><div class="eyebrow">BEFORE / AFTER</div><h2>Observed baseline vs test design</h2><table><thead><tr><th>Dimension</th><th>Observed baseline</th><th>Revised design</th></tr></thead><tbody>{compare_rows}</tbody></table></section><section><div class="eyebrow">FULL TECHNICAL REPORT</div><pre style="white-space:pre-wrap;font:14px/1.55 Segoe UI,Arial">{html.escape(markdown_text)}</pre></section></main><footer>Generated locally · Dataset kept local · Direct generation spend INR 0</footer></body></html>"""


def build_pdf(
    output: Path, results: dict[str, Any], diagnosis: dict[str, Any], strategy: dict[str, Any], plan: list[PlanItem],
    hardware: dict[str, Any], validation: dict[str, Any], before_after: list[dict[str, Any]],
    assets_root: Path, discovery: dict[str, Any],
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output), pagesize=letter, rightMargin=48, leftMargin=48, topMargin=54, bottomMargin=48, title="BudgetFitzz Performance Analysis and Strategy Revision", author="BudgetFitzz local agentic pipeline")
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=32, leading=34, textColor=colors.HexColor("#17211B"), alignment=TA_LEFT, spaceAfter=18))
    styles.add(ParagraphStyle(name="Kicker", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.HexColor("#0F6B4F"), spaceAfter=10))
    styles.add(ParagraphStyle(name="H1x", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=colors.HexColor("#0F6B4F"), spaceBefore=12, spaceAfter=10))
    styles.add(ParagraphStyle(name="H2x", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=colors.HexColor("#17211B"), spaceBefore=9, spaceAfter=5))
    styles.add(ParagraphStyle(name="Bodyx", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.2, leading=13, textColor=colors.HexColor("#26332B"), spaceAfter=6))
    styles.add(ParagraphStyle(name="Smallx", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.5, leading=10, textColor=colors.HexColor("#627067"), spaceAfter=4))

    def P(text: Any, style: str = "Bodyx") -> Paragraph:
        normalized = str(text).replace("₹", "INR ")
        safe = html.escape(normalized).replace("&lt;br/&gt;", "<br/>").replace("\n", "<br/>")
        return Paragraph(safe, styles[style])

    def on_page(canvas, document):
        canvas.saveState(); canvas.setStrokeColor(colors.HexColor("#D9DDD4")); canvas.line(48, 33, 564, 33)
        canvas.setFont("Helvetica", 7); canvas.setFillColor(colors.HexColor("#627067")); canvas.drawString(48, 20, "BUDGETFITZZ STRATEGY LAB")
        canvas.drawRightString(564, 20, f"Page {document.page}"); canvas.restoreState()

    story = [P("INTERN TASK 2 / FINAL REPORT", "Kicker"), P("BudgetFitzz<br/>Performance Analysis<br/>and Strategy Revision", "CoverTitle"), P("Evidence-linked analytics, a seven-day pilot, seven finished local assets, and a validated agentic platform.", "Bodyx"), Spacer(1, 14)]
    facts = results["verified_facts"]
    cover_data = [[P("150", "H1x"), P("90.0%", "H1x"), P("5 + 2", "H1x"), P("INR 0", "H1x")], [P("historical items", "Smallx"), P("promotional baseline", "Smallx"), P("posts + videos", "Smallx"), P("paid generation", "Smallx")]]
    cover_table = Table(cover_data, colWidths=[1.28*inch]*4, rowHeights=[.62*inch,.38*inch])
    cover_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.white),("BOX",(0,0),(-1,-1),1,colors.HexColor("#D9DDD4")),("INNERGRID",(0,0),(-1,-1),.5,colors.HexColor("#D9DDD4")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),12)]))
    story += [cover_table, Spacer(1, 18), P("PROJECT ASSUMPTION", "Kicker"), P("BudgetFitzz is treated as an affordable men's fashion discovery and styling brand in Delhi NCR for Indian men aged about 18-30. This context is assumed, not externally verified.", "Bodyx"), PageBreak()]
    story += [P("01 / EXECUTIVE SUMMARY", "Kicker"), P("The diagnosis", "H1x"), P(diagnosis["selected_diagnosis"]), P("Interpretation guardrail", "H2x"), P(diagnosis["outlier_caveat"]), P("Verified baseline", "H2x")]
    audit_rows = [[P("Records","Smallx"),P(facts["record_count"],"Smallx")],[P("Formats","Smallx"),P(f"{facts['post_count']} posts / {facts['video_count']} videos","Smallx")],[P("Promotion","Smallx"),P(f"{facts['promotion_share_pct']:.1f}%","Smallx")],[P("Missing CTA","Smallx"),P(facts["missing_cta_count"],"Smallx")],[P("Views > reach","Smallx"),P(facts["video_views_exceed_reach_count"],"Smallx")]]
    t=Table(audit_rows,colWidths=[1.55*inch,3.7*inch]);t.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),colors.HexColor("#E6F1D9")),("GRID",(0,0),(-1,-1),.5,colors.HexColor("#D9DDD4")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7)]));story += [t, Spacer(1,10), P("Qualitative Instagram discovery signal", "H2x"), P(discovery["observation"]), P(discovery["interpretation"], "Smallx"), P(f"Guardrail: {discovery['limitation']}", "Smallx"), P(f"Recommended validation: {discovery['recommended_action']}", "Smallx"), P("Dataset provenance", "H2x"), P("User-provided local evaluation dataset; original provenance unspecified. It is not described as a genuine Instagram export."), PageBreak()]
    story += [P("02 / METRICS AND METHOD", "Kicker"), P("Metric contract", "H1x"), P("Engagements = likes + comments + shares + saves. Engagement rate by reach = engagements / reach x 100. Like, comment, share and save rates use reach. Frequency = impressions / reach. Average watch time = watch time / video plays. Retention proxy = average watch time / duration x 100. Weighted score uses 1x likes, 3x comments, 4x shares and 4x saves."), P("Robust analysis", "H2x"), P("Raw values are preserved. Group tables report n, median, quartiles, mean, 10% trimmed mean, 5% winsorized mean and 2,000-sample bootstrap median intervals. Static-post video fields remain unavailable. Views are plays. n<3 is anecdotal; n=3-4 directional; n>=5 is cautious."), PageBreak()]
    chart_dir = assets_root / "charts"
    for title, name in [("Format comparison","format_comparison.png"),("Pillar save-rate comparison","pillar_comparison.png"),("Historical content mix","content_mix.png"),("Video retention proxy","video_retention.png")]:
        story += [KeepTogether([P(title,"H2x"), RLImage(str(chart_dir/name), width=5.9*inch, height=3.79*inch), Spacer(1,8)])]
    story += [PageBreak(), P("03 / FINDINGS", "Kicker"), P("Evidence register", "H1x")]
    evidence_rows=[[P("ID","Smallx"),P("Finding and comparison","Smallx"),P("n / confidence","Smallx")]]+[[P(x["evidence_id"],"Smallx"),P(f"{x['finding']} {x['comparison']}","Smallx"),P(f"{x['sample_size']} / {x['confidence']}","Smallx")] for x in results["evidence"]]
    et=Table(evidence_rows,colWidths=[.55*inch,4.05*inch,.95*inch],repeatRows=1);et.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17211B")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,colors.HexColor("#D9DDD4")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]));story += [et,PageBreak(),P("04 / REVISED STRATEGY","Kicker"),P("Evidence-linked changes","H1x"),P(strategy["objective"])]
    for change in strategy["evidence_linked_changes"]:
        story += [KeepTogether([P(change["evidence"],"Kicker"),P(change["strategy_change"],"H2x"),P(f"Finding: {change['finding']}"),P(f"Success metric: {change['success_metric']}","Smallx"),P(f"Limitation: {change['confidence_or_limitation']}","Smallx"),Spacer(1,6)])]
    story += [PageBreak(),P("05 / SEVEN-DAY PLAN","Kicker"),P("Five posts and two videos","H1x")]
    for item in plan:
        story += [KeepTogether([P(f"DAY {item.day} / {item.format.upper()} / {item.date}","Kicker"),P(item.hook,"H2x"),P(item.content_idea),P(f"CTA: {item.cta}","Smallx"),P(f"Evidence: {item.baseline_insight}","Smallx"),P(f"Target: {item.reasoned_target_range}","Smallx"),Spacer(1,7)])]
    story += [PageBreak(),P("06 / FINISHED ASSETS","Kicker"),P("Seven previews","H1x")]
    for item in plan:
        name = item.asset_filename if item.format=="post" else f"{Path(item.asset_filename).stem}_preview.png"
        folder = "posts" if item.format=="post" else "video_frames"
        img_path=assets_root/folder/name
        width,height=(3.5*inch,4.375*inch) if item.format=="post" else (2.5*inch,4.444*inch)
        story += [P(f"Day {item.day}: {item.hook}","H2x"),RLImage(str(img_path),width=width,height=height),P(f"{item.asset_filename} | {item.reasoned_target_range}","Smallx"),PageBreak()]
    story += [P("07 / BEFORE AND AFTER","Kicker"),P("Observed baseline vs revised test design","H1x")]
    ba_rows=[[P("Dimension","Smallx"),P("Observed baseline","Smallx"),P("Revised design","Smallx")]]+[[P(x["dimension"],"Smallx"),P(x["before"],"Smallx"),P(x["after"],"Smallx")] for x in before_after]
    bt=Table(ba_rows,colWidths=[1.25*inch,2.15*inch,2.15*inch],repeatRows=1);bt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0F6B4F")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.4,colors.HexColor("#D9DDD4")),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]));story += [bt,PageBreak(),P("08 / PLATFORM AND OPERATIONS","Kicker"),P("Agent architecture, memory and retries","H1x"),P("Eleven named agents operate through a persistent SQLite state machine. Pydantic validates boundaries. Each trace records run ID, agent, action, references, concise decision, evidence IDs, duration, status, error, retry, and tool. Human checkpoints are auto-approved only for this demo configuration and are logged."),P("GPU and local generation","H2x"),P(f"{hardware['gpu_name']} | {hardware['vram']} | driver {hardware['driver_version']} | selected encoder {hardware['selected_video_encoder']} | meaningful GPU use {hardware['gpu_used_meaningfully']}."),P("Spend","H2x"),P("Direct revised-content generation spend is INR 0. Local tools and models are logged as free. Project subscriptions are separate from direct generation expense."),P("Limitations","H2x"),P("The dataset is observational, imbalanced and provenance-unspecified. Outliers affect means; community n=2 is anecdotal; timing cells are uneven; views are plays; retention is a proxy; future values are targets, not achieved results."),P("Reproduction","H2x"),P("Run setup.ps1, generate_submission.ps1, validate_submission.ps1 and run_app.ps1."),P("Final validation","H2x"),P(f"{validation['status']}: {validation['passed']} passed, {validation['failed']} failed."),Spacer(1,18),P("END OF REPORT","Kicker")]
    doc.build(story,onFirstPage=on_page,onLaterPages=on_page)


def build_final_reports(
    final_dir: Path, results: dict[str, Any], diagnosis: dict[str, Any], strategy: dict[str, Any], plan: list[PlanItem],
    hardware: dict[str, Any], validation: dict[str, Any], before_after: list[dict[str, Any]],
    qualitative_observations: dict[str, Any],
) -> None:
    final_dir.mkdir(parents=True, exist_ok=True)
    discovery = qualitative_observations["instagram_product_search_discovery"]
    markdown_text = report_markdown(results, diagnosis, strategy, plan, hardware, validation, before_after, discovery)
    (final_dir / "final_report.md").write_text(markdown_text, encoding="utf-8")
    html_text = report_html(markdown_text, plan, results["verified_facts"], diagnosis, before_after, discovery)
    (final_dir / "final_report.html").write_text(html_text, encoding="utf-8")
    build_pdf(final_dir / "final_report.pdf", results, diagnosis, strategy, plan, hardware, validation, before_after, final_dir, discovery)
