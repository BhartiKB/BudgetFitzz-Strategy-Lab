"""Bounded Hugging Face promotional-credit image generation for five static posts."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .policy import GenerationPolicy, GenerationPolicyError


class HuggingFaceImageClient:
    """Generate five FLUX photographs through HF routing without using FAL."""

    MODEL = "black-forest-labs/FLUX.1-schnell"
    ROUTING_PROVIDER = "replicate"
    LIST_COST_PER_OUTPUT_USD = 0.003
    OUTPUT_COUNT = 5

    def __init__(self, root: Path):
        self.root = root
        self.policy = GenerationPolicy(root)

    def generate_batch(self, prompts: dict[str, str], output_dir: Path) -> dict[str, Any]:
        ledger = self.root / "logs/hf_promotional_image_batch.json"
        if ledger.exists():
            try:
                existing = json.loads(ledger.read_text(encoding="utf-8"))
                detail = (
                    f"status={existing.get('status')}; "
                    f"completed={existing.get('completed_outputs', 0)}/"
                    f"{existing.get('planned_outputs', self.OUTPUT_COUNT)}"
                )
            except (OSError, json.JSONDecodeError):
                detail = "ledger unreadable"
            raise GenerationPolicyError(
                "the Hugging Face post-image batch is already reserved or completed; "
                f"inspect the existing ledger instead of retrying ({detail})"
            )
        self.policy.assert_promotional_image_batch_allowed(
            provider="huggingface",
            routing_provider=self.ROUTING_PROVIDER,
            output_count=len(prompts),
            list_cost_per_output_usd=self.LIST_COST_PER_OUTPUT_USD,
            estimated_cash_cost_inr=0,
        )
        if len(set(prompts)) != self.OUTPUT_COUNT:
            raise GenerationPolicyError("the post-image batch must contain five unique output filenames")

        resolved_root = self.root.resolve()
        resolved_output = output_dir.resolve()
        if not resolved_output.is_relative_to(resolved_root):
            raise GenerationPolicyError("the post-image outputs must stay inside the project")
        if resolved_output.exists() and any(resolved_output.iterdir()):
            raise GenerationPolicyError("the post-image source directory must be empty before the one-shot batch")

        token = self.policy.credential("HF_TOKEN")
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise RuntimeError("huggingface_hub is required for the HF image batch") from exc

        client = InferenceClient(provider=self.ROUTING_PROVIDER, api_key=token, timeout=300)
        output_dir.mkdir(parents=True, exist_ok=True)
        started_at = datetime.now(UTC)
        audit: dict[str, Any] = {
            "status": "reserved",
            "timestamp": started_at.isoformat(),
            "provider": "huggingface",
            "routing_provider": self.ROUTING_PROVIDER,
            "model": self.MODEL,
            "operation": "five-post promotional-credit text-to-image batch",
            "planned_outputs": len(prompts),
            "completed_outputs": 0,
            "list_cost_per_output_usd": self.LIST_COST_PER_OUTPUT_USD,
            "estimated_batch_list_cost_usd": round(
                len(prompts) * self.LIST_COST_PER_OUTPUT_USD, 6
            ),
            "cash_cost_inr": 0,
            "paid_or_free": "free promotional credit",
            "fal_key_used": False,
            "fal_routing_used": False,
            "outputs": [],
        }
        _write_ledger(ledger, audit)

        for filename, prompt in prompts.items():
            entry: dict[str, Any] = {
                "filename": filename,
                "status": "reserved",
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "started_at": datetime.now(UTC).isoformat(),
            }
            audit["outputs"].append(entry)
            _write_ledger(ledger, audit)
            try:
                generated = client.text_to_image(
                    prompt,
                    model=self.MODEL,
                    extra_body={
                        "aspect_ratio": "4:5",
                        "output_format": "jpg",
                        "output_quality": 95,
                        "num_outputs": 1,
                        "num_inference_steps": 4,
                        "go_fast": True,
                        "megapixels": "1",
                    },
                )
                path = output_dir / filename
                generated.convert("RGB").save(path, "JPEG", quality=95, optimize=True)
                payload = path.read_bytes()
                entry.update({
                    "status": "succeeded",
                    "finished_at": datetime.now(UTC).isoformat(),
                    "output": str(path.relative_to(self.root)).replace("\\", "/"),
                    "output_bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "dimensions": list(generated.size),
                })
                audit["completed_outputs"] += 1
                _write_ledger(ledger, audit)
            except Exception as exc:
                response = getattr(exc, "response", None)
                status_code = getattr(response, "status_code", None)
                rejected_no_credit = status_code == 402
                failure_status = "rejected_no_credit" if rejected_no_credit else "failed_or_ambiguous"
                entry.update({
                    "status": failure_status,
                    "finished_at": datetime.now(UTC).isoformat(),
                    "failure_type": type(exc).__name__,
                    "http_status": status_code,
                })
                audit["status"] = failure_status
                audit["finished_at"] = datetime.now(UTC).isoformat()
                audit["estimated_consumed_list_cost_usd"] = round(
                    audit["completed_outputs"] * self.LIST_COST_PER_OUTPUT_USD, 6
                )
                _write_ledger(ledger, audit)
                raise

        audit["status"] = "succeeded"
        audit["finished_at"] = datetime.now(UTC).isoformat()
        _write_ledger(ledger, audit)
        return audit

    def resume_after_credit_restored(
        self, prompts: dict[str, str], output_dir: Path
    ) -> dict[str, Any]:
        """Resume only the four user-confirmed missing/rejected post images."""
        ledger = self.root / "logs/hf_promotional_image_batch.json"
        if not ledger.exists():
            raise GenerationPolicyError("the original HF post-image ledger is missing")
        audit = json.loads(ledger.read_text(encoding="utf-8"))
        if audit.get("status") != "rejected_no_credit":
            raise GenerationPolicyError(
                f"the HF image batch is not eligible for a credit-restored resume: {audit.get('status')}"
            )
        image_policy = self.policy.settings.get("promotional_credit", {}).get("image_batch", {})
        if not image_policy.get("credit_restored_confirmed_by_user"):
            raise GenerationPolicyError("restored HF image credit has not been confirmed by the user")
        maximum_resume = int(image_policy.get("maximum_resume_outputs", 0))
        if len(prompts) != maximum_resume:
            raise GenerationPolicyError(
                f"the credit-restored resume must contain exactly {maximum_resume} outputs"
            )
        self.policy.assert_promotional_image_batch_allowed(
            provider="huggingface",
            routing_provider=self.ROUTING_PROVIDER,
            output_count=len(prompts),
            list_cost_per_output_usd=self.LIST_COST_PER_OUTPUT_USD,
            estimated_cash_cost_inr=0,
        )
        estimated_resume_cost = len(prompts) * self.LIST_COST_PER_OUTPUT_USD
        if estimated_resume_cost > float(image_policy.get("maximum_resume_list_cost_usd", 0)):
            raise GenerationPolicyError("the resume cost exceeds the restored-credit ceiling")

        resolved_root = self.root.resolve()
        if not output_dir.resolve().is_relative_to(resolved_root):
            raise GenerationPolicyError("the resumed post-image outputs must stay inside the project")
        token = self.policy.credential("HF_TOKEN")
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise RuntimeError("huggingface_hub is required for the HF image resume") from exc

        client = InferenceClient(provider=self.ROUTING_PROVIDER, api_key=token, timeout=300)
        output_dir.mkdir(parents=True, exist_ok=True)
        resume: dict[str, Any] = {
            "status": "reserved",
            "confirmed_by_user": True,
            "started_at": datetime.now(UTC).isoformat(),
            "planned_outputs": len(prompts),
            "completed_outputs": 0,
            "estimated_list_cost_usd": round(estimated_resume_cost, 6),
            "cash_cost_inr": 0,
            "fal_key_used": False,
            "fal_routing_used": False,
            "outputs": [],
        }
        audit["status"] = "resume_reserved"
        audit["credit_restored_resume"] = resume
        _write_ledger(ledger, audit)

        for filename, prompt in prompts.items():
            entry: dict[str, Any] = {
                "filename": filename,
                "status": "reserved",
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "started_at": datetime.now(UTC).isoformat(),
            }
            resume["outputs"].append(entry)
            _write_ledger(ledger, audit)
            try:
                generated = client.text_to_image(
                    prompt,
                    model=self.MODEL,
                    extra_body={
                        "aspect_ratio": "4:5",
                        "output_format": "jpg",
                        "output_quality": 95,
                        "num_outputs": 1,
                        "num_inference_steps": 4,
                        "go_fast": True,
                        "megapixels": "1",
                    },
                )
                path = output_dir / filename
                generated.convert("RGB").save(path, "JPEG", quality=95, optimize=True)
                payload = path.read_bytes()
                entry.update({
                    "status": "succeeded",
                    "finished_at": datetime.now(UTC).isoformat(),
                    "output": str(path.relative_to(self.root)).replace("\\", "/"),
                    "output_bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "dimensions": list(generated.size),
                })
                resume["completed_outputs"] += 1
                _write_ledger(ledger, audit)
            except Exception as exc:
                response = getattr(exc, "response", None)
                status_code = getattr(response, "status_code", None)
                failure_status = "rejected_no_credit" if status_code == 402 else "failed_or_ambiguous"
                entry.update({
                    "status": failure_status,
                    "finished_at": datetime.now(UTC).isoformat(),
                    "failure_type": type(exc).__name__,
                    "http_status": status_code,
                })
                resume["status"] = failure_status
                resume["finished_at"] = datetime.now(UTC).isoformat()
                resume["estimated_consumed_list_cost_usd"] = round(
                    resume["completed_outputs"] * self.LIST_COST_PER_OUTPUT_USD,
                    6,
                )
                audit["status"] = f"resume_{failure_status}"
                audit["estimated_consumed_list_cost_usd"] = round(
                    float(audit.get("estimated_consumed_list_cost_usd", 0))
                    + resume["estimated_consumed_list_cost_usd"],
                    6,
                )
                _write_ledger(ledger, audit)
                raise

        resume["status"] = "generated_pending_visual_qa"
        resume["finished_at"] = datetime.now(UTC).isoformat()
        audit["status"] = "generated_pending_visual_qa"
        audit["estimated_consumed_list_cost_usd"] = round(
            float(audit.get("estimated_consumed_list_cost_usd", 0)) + estimated_resume_cost,
            6,
        )
        _write_ledger(ledger, audit)
        return audit


def _write_ledger(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
