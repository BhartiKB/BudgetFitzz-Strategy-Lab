"""Persistent, retrying, idempotent workflow for the full Task 2 submission."""

from __future__ import annotations

import csv
import json
import shutil
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from insta_strategy_lab.agents import (
    AssetGenerationAgent, ContentPlannerAgent, CreativeDirectorAgent, DataAuditAgent,
    FailureDiagnosisAgent, MetricsAgent, OrchestratorAgent, PackagingAgent,
    PerformanceAnalystAgent, QualityAssuranceAgent, StrategyAgent,
)
from insta_strategy_lab.agents.content_strategy import build_failure_diagnosis, build_plan, build_strategy
from insta_strategy_lab.analytics.charts import generate_charts
from insta_strategy_lab.analytics.core import METRIC_CONTRACT, analyze_dataset, apply_metric_contract, audit_dataset
from insta_strategy_lab.creative import generate_posts, generate_video_scenes
from insta_strategy_lab.providers import GenerationPolicy, LocalProvider
from insta_strategy_lab.reporting.builder import build_app_data, build_documentation, build_final_reports
from insta_strategy_lab.reporting.packaging import assemble_submission, create_zip, write_manifest
from insta_strategy_lab.schemas import PlanItem, SpendEntry
from insta_strategy_lab.storage import WorkflowMemory
from insta_strategy_lab.utils.files import write_json
from insta_strategy_lab.utils.hardware import hardware_report
from insta_strategy_lab.validation import validate_project
from insta_strategy_lab.video import generate_videos


class Workflow:
    def __init__(self, root: Path, resume: bool = False):
        self.root = root
        self.resume = resume
        self.config = json.loads((root / "config/workflow.json").read_text(encoding="utf-8"))
        self.run_id = datetime.now(UTC).strftime("budgetfitzz-%Y%m%dT%H%M%SZ")
        self.memory = WorkflowMemory(root / "logs/workflow.db", root / "logs/execution_trace.jsonl")
        self.context: dict[str, Any] = {}
        self.timings: dict[str, float] = {}
        self.retries: dict[str, int] = {}
        self._load_existing_context()

    def _load_existing_context(self) -> None:
        mapping = {
            "results": self.root / "analysis/analysis_results.json",
            "diagnosis": self.root / "analysis/failure_diagnosis.json",
            "strategy": self.root / "analysis/revised_strategy.json",
            "hardware": self.root / "logs/hardware_report.json",
            "before_after": self.root / "analysis/before_after.json",
            "targets": self.root / "analysis/target_metrics.json",
        }
        for key, path in mapping.items():
            if path.exists():
                self.context[key] = json.loads(path.read_text(encoding="utf-8"))
        plan_path = self.root / "analysis/seven_day_plan.json"
        if plan_path.exists():
            self.context["plan"] = [PlanItem.model_validate(item) for item in json.loads(plan_path.read_text(encoding="utf-8"))]

    def trace(self, agent: str, action: str, status: str, summary: str, duration: float = 0, retry: int = 0, error: str | None = None, input_ref: str = "", output_ref: str = "", evidence: list[str] | None = None, tool: str = "python-local") -> None:
        self.memory.append_trace({
            "run_id": self.run_id, "agent": agent, "action": action,
            "input_reference": input_ref, "output_reference": output_ref,
            "decision_summary": summary, "evidence_ids": evidence or [],
            "duration_sec": round(duration, 3), "status": status, "error": error,
            "retry_number": retry, "provider_or_tool": tool,
        })

    def stage(self, agent, input_ref: str, output_ref: str, evidence: list[str] | None = None) -> Any:
        name = agent.name
        max_retries = int(self.config["max_retries"])
        self.trace(name, "execute", "started", agent.responsibility, input_ref=input_ref, output_ref=output_ref, evidence=evidence)
        started = time.perf_counter()
        for attempt in range(max_retries + 1):
            try:
                self.memory.agent_status(self.run_id, name, "running", attempt, input_ref, output_ref)
                result = agent.run()
                duration = time.perf_counter() - started
                self.memory.agent_status(self.run_id, name, "completed", attempt, input_ref, output_ref)
                self.trace(name, "execute", "completed", agent.responsibility, duration, attempt, input_ref=input_ref, output_ref=output_ref, evidence=evidence)
                self.timings[name] = round(duration, 3)
                self.retries[name] = attempt
                return result
            except Exception as exc:
                duration = time.perf_counter() - started
                if attempt >= max_retries:
                    self.memory.agent_status(self.run_id, name, "failed", attempt, input_ref, output_ref, str(exc))
                    self.trace(name, "execute", "failed", f"Stage failed after bounded retries: {exc}", duration, attempt, str(exc), input_ref, output_ref, evidence)
                    raise
                self.trace(name, "execute", "retrying", f"Recoverable stage error; retrying with the same idempotent inputs: {exc}", duration, attempt, str(exc), input_ref, output_ref, evidence)
                time.sleep(float(self.config["retry_delay_seconds"]) * (2**attempt))
        raise RuntimeError("unreachable")

    def auto_checkpoint(self, name: str, evidence: list[str]) -> None:
        if not self.config.get("auto_approve_demo"):
            raise RuntimeError(f"Checkpoint {name} requires human approval")
        reason = "Auto-approved for the deterministic submission run after required evidence and validation artifacts were generated."
        self.memory.checkpoint(self.run_id, name, "approved", reason)
        self.trace("OrchestratorAgent", "checkpoint", "approved", reason, evidence=evidence, tool="workflow-state-machine")

    def write_plan(self, plan: list[PlanItem]) -> None:
        payload = [item.model_dump() for item in plan]
        write_json(self.root / "analysis/seven_day_plan.json", payload)
        with (self.root / "analysis/seven_day_plan.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(payload[0].keys()))
            writer.writeheader(); writer.writerows(payload)

    def write_spend(self, plan: list[PlanItem], provider: dict[str, Any]) -> None:
        path = self.root / "logs/spend_log.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = []
        for item in plan:
            hf_day_two = (
                item.asset_filename == "day02_one_shirt_three_ways.mp4"
                and (self.root / "assets/source_media/day02_hf_wan.mp4").exists()
                and (self.root / "logs/hf_promotional_credit_test.json").exists()
            )
            tool = "Pillow procedural renderer" if item.format == "post" else "Pillow scenes + FFmpeg NVENC"
            if hf_day_two:
                tool = "Wan 2.2 HF promotional source + Pillow cards + FFmpeg NVENC"
            entry = SpendEntry(
                timestamp=datetime.now(UTC), run_id=self.run_id, asset=item.asset_filename,
                provider="huggingface + local" if hf_day_two else provider["provider"],
                model_or_tool=tool,
                operation="promotional-credit source + local compositing" if hf_day_two else "local asset generation",
                quantity=1, unit_cost_inr=0, total_cost_inr=0, paid_or_free="free",
                evidence_or_receipt_reference=(
                    "logs/hf_promotional_credit_test.json; included credit confirmed by user"
                    if hf_day_two else "Local execution trace; no paid call or receipt"
                ),
                notes=(
                    "Currency INR; cash cost INR 0; promotional-credit list value USD 0.025; FAL not used."
                    if hf_day_two else
                    "Currency INR; direct revised-content generation cost INR 0. Development subscriptions, if any, are outside the direct-generation cap."
                ),
            )
            payload = entry.model_dump()
            rows.append(payload)
            self.memory.add_spend(payload)
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader(); writer.writerows(rows)
        write_json(self.root / "logs/spend_summary.json", {
            "currency": "INR", "paid_generation_total_inr": 0,
            "cap_inr": 100, "within_cap": True, "entries": len(rows),
            "promotional_credit_list_value_usd": 0.025 if any(
                row["provider"] == "huggingface + local" for row in rows
            ) else 0,
            "subscription_treatment": "Development subscriptions are separate from direct revised-content generation expenses.",
        })

    def before_after(self, results: dict[str, Any]) -> list[dict[str, str]]:
        facts = results["verified_facts"]
        return [
            {"dimension":"Content-pillar mix","before":f"Promotion {facts['promotion_share_pct']:.1f}%","after":"3 education / 2 value-first commercial / 2 community"},
            {"dimension":"Format mix","before":f"Posts {facts['post_share_pct']:.1f}% (137/150)","after":"5 posts / 2 videos in the pilot"},
            {"dimension":"Topic diversity","before":f"Top two topics {facts['top_two_topic_share_pct']:.1f}%","after":"Wardrobe systems, fit, votes, audit, sneakers, and two commercial anchors"},
            {"dimension":"Hook diversity","before":"Mostly emotional/aspirational repetitions","after":"Specific formulas, tension, bounded questions, and use-case decisions"},
            {"dimension":"CTA diversity","before":f"{facts['missing_cta_count']} missing plus repetitive link requests","after":"7/7 explicit CTAs across save, vote, screenshot, audit, and qualified link intent"},
            {"dimension":"Promotional concentration","before":f"{facts['promotion_share_pct']:.1f}% promotion","after":"Commercial content capped at 2/7 and must teach first"},
            {"dimension":"Educational value","before":"13/150 education items","after":"3/7 education items with on-frame takeaways"},
            {"dimension":"Community interaction","before":"2/150 items (anecdotal)","after":"2 bounded interaction items designed as tests"},
            {"dimension":"Save/share potential","before":f"Education median save {facts['education_median_save_rate_pct']:.3f}%","after":"Education post target save rate 0.50-0.75%"},
            {"dimension":"Video retention design","before":f"Median proxy {facts['video_median_retention_proxy_pct']:.1f}%","after":"First-second hooks, 3-second scenes, target 60-70%"},
            {"dimension":"Timing","before":"Uneven observational timing cells","after":"Two pre-registered test windows; compare within format/pillar"},
            {"dimension":"Visual quality","before":"Text-heavy, inconsistent source content","after":"Cohesive original editorial system with mobile-safe hierarchy"},
            {"dimension":"Expected performance","before":"Observed historical metrics","after":"Reasoned target ranges only; no claim of achieved lift"},
        ]

    def target_metrics(self, results: dict[str, Any]) -> dict[str, Any]:
        facts = results["verified_facts"]
        return {
            "status": "forward-looking targets / hypotheses, not observed results",
            "baseline": {"post_median_engagement_rate_pct": facts["post_median_er_pct"], "video_median_engagement_rate_pct": facts["video_median_er_pct"], "video_median_retention_proxy_pct": facts["video_median_retention_proxy_pct"]},
            "targets": [
                {"metric":"Education post save rate","target_range":"0.50-0.75%","rationale":"Near/above observed education median with creative optimized for saves"},
                {"metric":"Video retention proxy","target_range":"60-70%","rationale":"Modest improvement over observed median using shorter scenes and explicit progression"},
                {"metric":"Video engagement rate by reach","target_range":"6.5-8.0%","rationale":"Anchored near robust video/post medians, not the extreme mean"},
                {"metric":"Qualified community comments","target_range":"0.8-2.0% of reach","rationale":"Bounded questions; community baseline is anecdotal"},
                {"metric":"CTA coverage","target_range":"100%","rationale":"Direct quality-control requirement"},
                {"metric":"Content mix compliance","target_range":"3 education / 2 value-first / 2 community","rationale":"Pre-registered portfolio balance"},
            ],
        }

    def run(self) -> dict[str, Any]:
        self.memory.start_run(self.run_id, self.config)
        self.memory.agent_status(self.run_id, "OrchestratorAgent", "running", 0, "config/workflow.json", "submission/final")
        self.trace("OrchestratorAgent", "orchestrate", "started", "Started persistent state-machine workflow.", tool="workflow-state-machine")
        raw_csv = self.root / "data/raw/budgetfitzz_dataset_fixed.csv"

        def audit_action():
            audit = audit_dataset(pd.read_csv(raw_csv)); write_json(self.root / "analysis/dataset_audit.json", audit); self.context["audit"] = audit; return audit
        self.stage(DataAuditAgent("DataAuditAgent", "Validated schema, dates, missing values, duplicates, ranges, handles, and anomalies.", audit_action), "data/raw/budgetfitzz_dataset_fixed.csv", "analysis/dataset_audit.json")

        def metrics_action():
            raw = pd.read_csv(raw_csv); derived = apply_metric_contract(raw)
            raw.to_csv(self.root / "data/processed/budgetfitzz_clean.csv", index=False)
            derived.to_csv(self.root / "data/processed/budgetfitzz_derived.csv", index=False)
            write_json(self.root / "data/processed/metric_contract.json", METRIC_CONTRACT)
            return len(derived)
        self.stage(MetricsAgent("MetricsAgent", "Applied the machine-readable metric contract without modifying raw columns.", metrics_action), "data/raw/budgetfitzz_dataset_fixed.csv", "data/processed/budgetfitzz_derived.csv")

        def analysis_action():
            results = analyze_dataset(raw_csv, self.root / "data/processed", self.root / "analysis")
            frame = pd.read_csv(self.root / "data/processed/budgetfitzz_derived.csv")
            generate_charts(frame, self.root / "analysis/charts")
            self.context["results"] = results; return results
        results = self.stage(PerformanceAnalystAgent("PerformanceAnalystAgent", "Produced robust comparisons, charts, evidence objects, caveats, and uncertainty labels.", analysis_action), "data/processed/budgetfitzz_derived.csv", "analysis/analysis_results.json", ["E01","E02","E03","E04","E05","E06","E07","E08","E09"])

        def diagnosis_action():
            diagnosis = build_failure_diagnosis(results); write_json(self.root / "analysis/failure_diagnosis.json", diagnosis); self.context["diagnosis"] = diagnosis; return diagnosis
        diagnosis = self.stage(FailureDiagnosisAgent("FailureDiagnosisAgent", "Tested the proposed failure hypothesis, retained counterevidence, and selected the best-supported qualified diagnosis.", diagnosis_action), "analysis/evidence.json", "analysis/failure_diagnosis.json", ["E01","E02","E03","E05","E06","E07","E09"])
        self.auto_checkpoint("failure_diagnosis_approval", diagnosis["support"])

        def strategy_action():
            strategy = build_strategy(results); write_json(self.root / "analysis/revised_strategy.json", strategy); self.context["strategy"] = strategy; return strategy
        strategy = self.stage(StrategyAgent("StrategyAgent", "Converted each major finding into a behavioral strategy change, target, and limitation.", strategy_action), "analysis/failure_diagnosis.json", "analysis/revised_strategy.json", ["E01","E02","E03","E04","E05","E06","E07","E09"])
        self.auto_checkpoint("revised_strategy_approval", [x["evidence"] for x in strategy["evidence_linked_changes"]])

        def plan_action():
            plan = build_plan(); self.write_plan(plan); self.context["plan"] = plan; return plan
        plan = self.stage(ContentPlannerAgent("ContentPlannerAgent", "Created and programmatically validated seven consecutive items: exactly five posts and two videos.", plan_action), "analysis/revised_strategy.json", "analysis/seven_day_plan.json", ["E01","E02","E03","E05","E06","E07","E09"])

        media_policy = GenerationPolicy(self.root)
        provider = asdict(LocalProvider(self.root).select()); self.context["provider"] = provider
        def creative_action():
            if not (self.root / "config/brand_tokens.yaml").exists(): raise FileNotFoundError("brand tokens missing")
            write_json(self.root / "analysis/provider_selection.json", provider); return provider
        self.stage(CreativeDirectorAgent("CreativeDirectorAgent", "Locked the visual system, prompts, original-asset rules, and zero-cost local provider.", creative_action), "analysis/seven_day_plan.json", "config/brand_tokens.yaml", ["E03","E06","E07"])

        def asset_action():
            media_policy.assert_media_call_allowed("local", estimated_cost_inr=0)
            posts = generate_posts(plan, self.root / "assets/posts")
            scenes = generate_video_scenes(plan, self.root / "assets/video_frames")
            video_results = generate_videos(self.root, scenes, self.root / "assets/videos", self.root / "assets/video_frames")
            hardware = hardware_report(self.root, video_results); write_json(self.root / "logs/hardware_report.json", hardware)
            self.context.update({"video_results": video_results, "hardware": hardware}); return {"posts": [str(x) for x in posts], "videos": video_results}
        self.stage(AssetGenerationAgent("AssetGenerationAgent", "Composited four audited HF photographs into the agent-authored post system, retained the Day 7 deterministic fallback, and rendered two captioned H.264 videos with NVENC-first encoding.", asset_action), "analysis/seven_day_plan.json", "assets/posts + assets/videos", ["E03","E05","E09"])
        self.auto_checkpoint("asset_approval", ["E03","E05","E09"])

        hardware = self.context["hardware"]
        before_after = self.before_after(results); self.context["before_after"] = before_after; write_json(self.root / "analysis/before_after.json", before_after)
        targets = self.target_metrics(results); self.context["targets"] = targets; write_json(self.root / "analysis/target_metrics.json", targets)
        self.write_spend(plan, provider)
        build_documentation(self.root, results, diagnosis, strategy, plan, hardware, provider, self.run_id)

        def qa_action():
            report = validate_project(self.root, final=False)
            if report["status"] != "PASS":
                failed = [x["check"] for x in report["checks"] if not x["passed"]]
                raise RuntimeError(f"Preflight validation failures: {failed}")
            self.context["validation"] = report
            build_app_data(self.root, self.run_id, results, diagnosis, strategy, plan, provider, report, before_after)
            return report
        validation = self.stage(QualityAssuranceAgent("QualityAssuranceAgent", "Validated analysis, plan counts, assets, codecs, spend, architecture, memory, trace, and app source.", qa_action), "analysis + assets + logs", "logs/validation_report.json")

        def packaging_action():
            final_dir = assemble_submission(self.root)
            build_final_reports(final_dir, results, diagnosis, strategy, plan, hardware, validation, before_after)
            manifest = write_manifest(final_dir); archive = create_zip(self.root, final_dir)
            return {"final_dir": str(final_dir), "manifest_files": manifest["file_count"], "zip": str(archive)}
        packaged = self.stage(PackagingAgent("PackagingAgent", "Assembled reports, sources, assets, prompts, logs, manifest, checksums, and the submission ZIP.", packaging_action), "validated project", "submission/final + submission ZIP")

        self.auto_checkpoint("final_export_approval", ["validation:preflight-pass"])
        write_json(self.root / "logs/timing_report.json", {"run_id": self.run_id, "agent_timings_sec": self.timings})
        write_json(self.root / "logs/retry_report.json", {"run_id": self.run_id, "retry_counts": self.retries, "total_retries": sum(self.retries.values())})
        shutil.copy2(self.root / "logs/execution_trace.jsonl", self.root / "logs/agent_decisions.jsonl")
        self.memory.agent_status(self.run_id, "OrchestratorAgent", "completed", 0, "config/workflow.json", "submission/final")
        self.memory.finish_run(self.run_id, "complete")
        self.trace("OrchestratorAgent", "orchestrate", "completed", "All configured stages completed and the preflight package was generated.", tool="workflow-state-machine")
        return {"run_id": self.run_id, "validation": validation, "packaged": packaged, "hardware": hardware, "provider": provider}
