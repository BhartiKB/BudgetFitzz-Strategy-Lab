"""Secure import, validation, versioning and approval for manually generated media."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from insta_strategy_lab.generation.config import load_generation_config
from insta_strategy_lab.generation.prompts import generation_public_data
from insta_strategy_lab.providers.registry import ProviderRegistry
from insta_strategy_lab.utils.files import sha256, write_json
from insta_strategy_lab.video.generator import ffmpeg_paths, probe_video


class ImportValidationError(ValueError):
    pass


SAFE_PROVIDERS = {"Google Flow / Veo", "Hugging Face", "FAL", "Runway", "Higgsfield", "Kling", "Stock media", "Local generation", "Other"}
SAFE_ACCESS = {"API", "Manual web interface", "Free website credits", "Promotional credits", "Paid website generation", "Licensed stock media", "Local"}
IMAGE_SIGNATURES = {b"\x89PNG\r\n\x1a\n": "image/png", b"\xff\xd8\xff": "image/jpeg", b"RIFF": "image/webp"}
VIDEO_SIGNATURES = (b"ftyp",)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _safe_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).name).strip("._")
    if not cleaned:
        raise ImportValidationError("A safe filename could not be derived")
    return cleaned[:120]


class ImportService:
    def __init__(self, root: Path):
        self.root = root
        self.config = load_generation_config(root)
        self.ffmpeg, self.ffprobe = ffmpeg_paths(root)

    def _load(self, relative: str, default: dict[str, Any]) -> dict[str, Any]:
        path = self.root / relative
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

    def _write(self, relative: str, payload: dict[str, Any]) -> None:
        write_json(self.root / relative, payload)

    def _sync_manifest_generation(self) -> None:
        """Keep only the generated job/version slice current after an import or approval."""
        manifest_path = self.root / "app/data/platform_manifest.json"
        if not manifest_path.exists():
            return
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        studio = manifest.get("content_studio")
        if not isinstance(studio, dict):
            return
        generation = generation_public_data(self.root)
        generation["provider_status"] = ProviderRegistry(self.root).public_status()
        studio["generation"] = generation
        write_json(manifest_path, manifest)

    def _prompt_for(self, asset_id: str) -> dict[str, Any]:
        prompts = self._load("analysis/content_generation_prompts.json", {"assets": []})["assets"]
        match = next((item for item in prompts if item["asset_id"] == asset_id), None)
        if not match:
            raise ImportValidationError("Unknown asset; select an asset from the approved seven-day plan")
        return match

    def _next_version(self, asset_id: str) -> str:
        versions = self._load("analysis/media_versions.json", {"assets": {}})["assets"].get(asset_id, {})
        return f"v{len(versions.get('versions', [])) + 1:03}"

    def _validate_image(self, path: Path) -> dict[str, Any]:
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                image = image.convert("RGB")
                if image.width < 480 or image.height < 480:
                    raise ImportValidationError("Image resolution is too small for an editorial final")
                extrema = image.getextrema()
                if all(low == high for low, high in extrema):
                    raise ImportValidationError("Image appears blank or flat")
                return {"mime_type": Image.MIME.get(image.format, "image/unknown"), "width": image.width, "height": image.height, "format": image.format}
        except (OSError, ValueError) as exc:
            raise ImportValidationError(f"Unreadable image: {exc}") from exc

    def _validate_video(self, path: Path) -> dict[str, Any]:
        try:
            payload = probe_video(self.ffprobe, path)
        except Exception as exc:
            raise ImportValidationError(f"ffprobe rejected video: {exc}") from exc
        video = next((stream for stream in payload.get("streams", []) if stream.get("codec_name")), None)
        if not video or not video.get("width") or not video.get("height"):
            raise ImportValidationError("Video has no readable visual stream")
        duration = float(payload["format"].get("duration", 0))
        if duration <= 0 or duration > 120:
            raise ImportValidationError("Video duration must be greater than zero and no longer than 120 seconds")
        if video.get("pix_fmt") not in {"yuv420p", "yuvj420p", "yuv420p10le"}:
            raise ImportValidationError("Video uses an unsupported pixel format")
        return {"mime_type": "video/mp4", "width": video["width"], "height": video["height"], "duration_seconds": duration, "codec": video["codec_name"], "pix_fmt": video.get("pix_fmt"), "frame_rate": video.get("avg_frame_rate")}

    def _postprocess_image(self, source: Path, destination: Path) -> None:
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
        image = ImageOps.fit(image, (1080, 1350), Image.Resampling.LANCZOS, centering=(0.5, 0.42))
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination, "PNG", optimize=True)

    def _postprocess_video(self, source: Path, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        command = [str(self.ffmpeg), "-y", "-hide_banner", "-loglevel", "error", "-i", str(source), "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x17211B,format=yuv420p", "-an", "-r", "30", "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20", "-movflags", "+faststart", str(destination)]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode:
            fallback = command.copy(); fallback[fallback.index("h264_nvenc")] = "libx264"; fallback[fallback.index("p4")] = "medium"; fallback[fallback.index("-cq")] = "-crf"
            completed = subprocess.run(fallback, capture_output=True, text=True)
        if completed.returncode:
            raise ImportValidationError(f"Video post-processing failed: {completed.stderr[-800:]}")

    def import_media(self, fields: dict[str, str], filename: str, content: bytes) -> dict[str, Any]:
        if len(content) == 0:
            raise ImportValidationError("The selected media file is empty")
        limit = int(self.config["generation"].get("maximum_upload_mb", 80)) * 1024 * 1024
        if len(content) > limit:
            raise ImportValidationError("The selected media file exceeds the configured upload limit")
        asset_id = fields.get("asset_id", "")
        prompt = self._prompt_for(asset_id)
        if fields.get("provider") not in SAFE_PROVIDERS or fields.get("access_method") not in SAFE_ACCESS:
            raise ImportValidationError("Provider or access method is not allowlisted")
        if fields.get("permission_confirmed") != "true":
            raise ImportValidationError("Permission to use the media must be confirmed")
        if fields.get("prompt_version") != str(prompt["prompt_version"]):
            raise ImportValidationError("Prompt version does not match the selected asset")
        name = _safe_name(filename)
        job_id = fields.get("job_id") or f"{asset_id}-{uuid.uuid4().hex[:10]}"
        quarantine = self.root / "artifacts/quarantine" / f"{job_id}-{name}"
        quarantine.parent.mkdir(parents=True, exist_ok=True)
        quarantine.write_bytes(content)
        digest = sha256(quarantine)
        expected_type = prompt["asset_type"]
        is_image = content.startswith(tuple(IMAGE_SIGNATURES))
        is_video = any(signature in content[:64] for signature in VIDEO_SIGNATURES)
        try:
            if expected_type == "image" and not is_image:
                raise ImportValidationError("Selected asset requires an image with an allowlisted file signature")
            if expected_type == "video" and not is_video:
                raise ImportValidationError("Selected asset requires an MP4-style video signature")
            validation = self._validate_image(quarantine) if expected_type == "image" else self._validate_video(quarantine)
            versions_payload = self._load("analysis/media_versions.json", {"assets": {}})
            existing = versions_payload["assets"].get(asset_id, {}).get("versions", [])
            if any(version.get("source_file_hash") == digest for version in existing):
                raise ImportValidationError("Duplicate media is already recorded for this asset")
            version = self._next_version(asset_id)
            extension = ".png" if expected_type == "image" else ".mp4"
            raw = self.root / "artifacts/raw_imports" / asset_id / version / name
            raw.parent.mkdir(parents=True, exist_ok=True)
            os.replace(quarantine, raw)
            candidate = self.root / "artifacts/processed_candidates" / asset_id / f"{version}{extension}"
            if expected_type == "image": self._postprocess_image(raw, candidate)
            else: self._postprocess_video(raw, candidate)
            final_validation = self._validate_image(candidate) if expected_type == "image" else self._validate_video(candidate)
            provenance = {
                "asset_id": asset_id, "provider": fields["provider"], "model": fields.get("model") or None, "access_method": fields["access_method"], "api_used": fields["access_method"] == "API", "prompt_version": prompt["prompt_version"], "prompt_hash": prompt["prompt_hash"], "source_file_hash": digest, "generation_date": fields.get("generation_date") or _now(), "attempts": int(fields.get("attempts") or 1), "actual_cost_inr": float(fields.get("actual_cost_inr") or 0), "credit_type": fields.get("credit_type") or "not specified", "raw_import": raw.relative_to(self.root).as_posix(), "final_output": candidate.relative_to(self.root).as_posix(), "postprocessing": ["image_resize_1080x1350"] if expected_type == "image" else ["crop_or_pad_9x16", "resize_1080x1920", "h264_nvenc_or_libx264"], "approval_status": "awaiting_review", "validation": {"source": validation, "final": final_validation}, "caption_to_beat_mapping": fields.get("beat_mappings", "")[:2000], "notes": fields.get("notes", "")[:1000], "provider_request_id": fields.get("provider_request_id", "")[:200],
            }
            provenance_path = self.root / "analysis/media_provenance" / f"{asset_id}-{version}.json"
            write_json(provenance_path, provenance)
            record = {"version": version, "status": "AWAITING_REVIEW", "source_file_hash": digest, "raw_import": provenance["raw_import"], "candidate_output": provenance["final_output"], "provenance_file": provenance_path.relative_to(self.root).as_posix(), "created_at": _now(), "approval_history": []}
            versions_payload["assets"].setdefault(asset_id, {"active_version": "v001", "versions": []})["versions"].append(record)
            self._write("analysis/media_versions.json", versions_payload)
            jobs = self._load("analysis/generation_jobs.json", {"jobs": []})
            jobs["jobs"].append({"job_id": job_id, "asset_id": asset_id, "plan_day": prompt["plan_day"], "mode": "MANUAL_PROVIDER", "provider": fields["provider"], "model": fields.get("model") or None, "status": "AWAITING_REVIEW", "retry_count": 0, "prompt_version": prompt["prompt_version"], "imported_file": provenance["raw_import"], "final_output": provenance["final_output"], "provenance_file": provenance_path.relative_to(self.root).as_posix(), "spend_inr": provenance["actual_cost_inr"], "created_at": _now()})
            self._write("analysis/generation_jobs.json", jobs)
            self._sync_manifest_generation()
            return {"job_id": job_id, "asset_id": asset_id, "version": version, "status": "AWAITING_REVIEW", "provenance_file": provenance_path.relative_to(self.root).as_posix()}
        except Exception:
            quarantine.unlink(missing_ok=True)
            raise

    def approve(self, job_id: str) -> dict[str, Any]:
        jobs = self._load("analysis/generation_jobs.json", {"jobs": []})
        job = next((item for item in jobs["jobs"] if item["job_id"] == job_id), None)
        if not job or job["status"] != "AWAITING_REVIEW":
            raise ImportValidationError("Only an awaiting-review imported job can be approved")
        prompt = self._prompt_for(job["asset_id"])
        source = self.root / job["final_output"]
        destination = self.root / "assets" / ("videos" if prompt["asset_type"] == "video" else "posts") / f"{job['asset_id']}{'.mp4' if prompt['asset_type'] == 'video' else '.png'}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        job["status"] = "APPROVED"; job["approved_at"] = _now(); job["active_output"] = destination.relative_to(self.root).as_posix()
        versions = self._load("analysis/media_versions.json", {"assets": {}})
        item = versions["assets"][job["asset_id"]]; item["active_version"] = next(version["version"] for version in item["versions"] if version["candidate_output"] == job["final_output"])
        for version in item["versions"]:
            if version["candidate_output"] == job["final_output"]:
                version["status"] = "APPROVED"; version["approval_history"].append({"status": "approved", "at": _now()})
        self._write("analysis/media_versions.json", versions); self._write("analysis/generation_jobs.json", jobs); self._sync_manifest_generation()
        return {"job_id": job_id, "status": "APPROVED", "active_output": job["active_output"]}
