"""Create visible final media prompts and download-ready generation packages."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from insta_strategy_lab.schemas import PlanItem
from insta_strategy_lab.utils.files import sha256, write_json


def _asset_id(item: PlanItem) -> str:
    return Path(item.asset_filename).stem


def _references(root: Path, item: PlanItem) -> list[str]:
    if item.format == "video":
        candidate = root / "assets/source_media" / ("day02_hf_wan.mp4" if item.day == 2 else "day05_hf_wan.mp4")
        return [candidate.relative_to(root).as_posix()] if candidate.exists() else []
    photo = root / "assets/source_media/posts" / f"{_asset_id(item)}_hf.jpg"
    return [photo.relative_to(root).as_posix()] if photo.exists() else []


def _brief_by_day(video_briefs: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(brief["day"]): brief for brief in video_briefs.get("briefs", [])}


def _prompt(item: PlanItem, brief: dict[str, Any] | None) -> tuple[str, str, list[str], list[dict[str, Any]]]:
    aspect = "9:16" if item.format == "video" else "4:5"
    medium = "a 10-second vertical smartphone fashion video" if item.format == "video" else "a vertical editorial fashion photograph"
    # Preserve the approved direction while translating any legacy illustration wording
    # into the realistic photographic treatment required for manual generation.
    visual = item.visual_direction.rstrip(".").replace("illustrations", "photographed garment layouts").replace("illustration", "photographed garment layout")
    prompt = (
        f"Create {medium} for BudgetFitzz. Subject: practical Indian menswear, realistic adult male model, "
        f"{item.topic.lower()}. Scene: {item.content_idea}. Visual direction: {visual}. "
        f"Use natural garment texture, believable hands and anatomy, clean contemporary Indian home or city setting, "
        f"soft daylight, restrained editorial composition, no brand logos, and leave safe negative space for the exact caption and CTA. "
        f"The creative must support this approved hook: {item.hook}. Aspect ratio {aspect}."
    )
    negative = "cartoon, sketch, illustration, CGI look, distorted anatomy, extra fingers, unreadable text, brand logos, watermark, price claims, before-and-after transformation, sexualized styling"
    beats: list[dict[str, Any]] = []
    phrases: list[str] = []
    if brief:
        beats = brief["beats"]
        phrases = [beat["caption_evidence"] for beat in beats]
        beat_copy = "; ".join(f"{beat['step']}: {beat['takeaway']}" for beat in beats)
        prompt += f" Storyboard beats, in order: {beat_copy}."
    return prompt, negative, phrases, beats


def create_prompt_artifacts(root: Path, plan: list[PlanItem], video_briefs: dict[str, Any]) -> dict[str, Any]:
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    by_day = _brief_by_day(video_briefs)
    entries: list[dict[str, Any]] = []
    package_dir = root / "analysis/generation_packages"
    package_dir.mkdir(parents=True, exist_ok=True)
    for item in plan:
        asset_type = "video" if item.format == "video" else "image"
        width, height = (1080, 1920) if asset_type == "video" else (1080, 1350)
        brief = by_day.get(item.day)
        prompt, negative, phrases, beats = _prompt(item, brief)
        asset_id = _asset_id(item)
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        package = {
            "job_id": f"day{item.day:02}-{asset_type}-v001",
            "asset_id": asset_id,
            "asset_filename": item.asset_filename,
            "plan_day": item.day,
            "asset_type": asset_type,
            "recommended_provider": "Google Flow / Veo",
            "recommended_model": "Veo" if asset_type == "video" else "Google Flow image model",
            "execution_mode": "MANUAL_PROVIDER",
            "prompt": prompt,
            "negative_prompt": negative,
            "aspect_ratio": "9:16" if asset_type == "video" else "4:5",
            "width": width,
            "height": height,
            "duration_seconds": 10 if asset_type == "video" else None,
            "frame_rate_intention": 30 if asset_type == "video" else None,
            "reference_files": _references(root, item),
            "visual_style": item.visual_direction,
            "caption_phrases": phrases,
            "storyboard_beats": beats,
            "caption_to_visual_mapping": [{"caption_phrase": beat["caption_evidence"], "visual_beat": beat["step"], "source_time_range": beat["source_window_sec"]} for beat in beats],
            "cta": item.cta,
            "prohibited_elements": negative.split(", "),
            "safety_instructions": "Use an adult model; no logos, no false price claims, no personal data, and no deceptive before-and-after framing.",
            "provider_specific_notes": "Manual web workflow is the current demonstration. No provider login, CAPTCHA, web submission, or website download is automated.",
            "maximum_media_cost_inr": 100,
            "prompt_version": 1,
            "prompt_hash": digest,
            "generated_by": ["ContentPlannerAgent", "CreativeDirectorAgent"],
            "generation_timestamp": generated_at,
            "decision_summary": "Final generation brief derived from the approved plan, caption and validated video beats; it contains no hidden chain-of-thought.",
        }
        write_json(package_dir / f"{asset_id}.json", package)
        markdown = "\n".join([
            f"# Generation package — {asset_id}", "", "**Prompt generated by the BudgetFitzz content workflow**", "",
            "## Prompt", "", prompt, "", "## Negative prompt", "", negative, "",
            "## Parameters", "", f"- Provider recommendation: {package['recommended_provider']}", f"- Model recommendation: {package['recommended_model']}", f"- Aspect ratio: {package['aspect_ratio']}", f"- Resolution: {width}×{height}", f"- Duration: {package['duration_seconds'] or 'Not applicable'}", f"- Prompt hash: `{digest}`", "",
            "## Caption-to-visual mapping", "", *[f"- {item['caption_phrase']} → {item['visual_beat']}" for item in package["caption_to_visual_mapping"]], "",
            "## CTA", "", item.cta, "",
        ])
        (package_dir / f"{asset_id}.md").write_text(markdown, encoding="utf-8")
        entries.append(package)
    payload = {"schema_version": "1.0", "generated_by": ["ContentPlannerAgent", "CreativeDirectorAgent"], "generated_at": generated_at, "assets": entries}
    write_json(root / "analysis/content_generation_prompts.json", payload)
    versions_path = root / "analysis/media_versions.json"
    if not versions_path.exists():
        versions: dict[str, Any] = {"schema_version": "1.0", "assets": {}}
        for entry in entries:
            active = root / "assets" / ("videos" if entry["asset_type"] == "video" else "posts") / entry["asset_filename"]
            versions["assets"][entry["asset_id"]] = {
                "active_version": "v001",
                "versions": [{
                    "version": "v001", "status": "APPROVED", "source_file_hash": sha256(active) if active.exists() else None,
                    "raw_import": None, "candidate_output": active.relative_to(root).as_posix() if active.exists() else None,
                    "provenance_file": None, "created_at": generated_at,
                    "approval_history": [{"status": "approved_existing_asset", "at": generated_at}],
                }],
            }
        write_json(versions_path, versions)
    readable = ["# Content generation prompts", "", "The visible and exportable prompts below are the exact same prompt strings. They are final briefs, evidence links and generation parameters—not hidden reasoning.", ""]
    for entry in entries:
        readable.extend([f"## Day {entry['plan_day']} — {entry['asset_id']}", "", "### Prompt", "", entry["prompt"], "", "### Negative prompt", "", entry["negative_prompt"], "", f"Provider: {entry['recommended_provider']} · Model: {entry['recommended_model']} · {entry['width']}×{entry['height']} · {entry['aspect_ratio']}", ""])
    readable_text = "\n".join(readable)
    (root / "analysis/content_generation_prompts.md").write_text(readable_text, encoding="utf-8")
    (root / "docs/content_generation_prompts.md").write_text(readable_text, encoding="utf-8")
    return payload


def generation_public_data(root: Path) -> dict[str, Any]:
    prompt_path = root / "analysis/content_generation_prompts.json"
    jobs_path = root / "analysis/generation_jobs.json"
    versions_path = root / "analysis/media_versions.json"
    prompt_payload = json.loads(prompt_path.read_text(encoding="utf-8")) if prompt_path.exists() else {"assets": []}
    return {
        "prompts": prompt_payload.get("assets", []),
        "jobs": json.loads(jobs_path.read_text(encoding="utf-8")).get("jobs", []) if jobs_path.exists() else [],
        "versions": json.loads(versions_path.read_text(encoding="utf-8")).get("assets", {}) if versions_path.exists() else {},
    }
