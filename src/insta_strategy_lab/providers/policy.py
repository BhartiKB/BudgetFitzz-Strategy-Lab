"""Credential discovery and hard guards for zero-cost media generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class GenerationPolicyError(RuntimeError):
    """Raised before an operation that violates the configured spend policy."""


def _dotenv_values(path: Path) -> dict[str, str]:
    """Read selected dotenv values without mutating the process environment."""
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if name == "FAL_KEY":
            # The fal credential is deliberately never retained or exposed.
            continue
        values[name] = value.strip().strip('"').strip("'")
    return values


@dataclass(frozen=True)
class CredentialStatus:
    gemini_configured: bool
    huggingface_configured: bool
    fal_ignored: bool = True


class GenerationPolicy:
    """Fail closed when a media call could consume paid credits."""

    def __init__(self, root: Path):
        self.root = root
        workflow = json.loads((root / "config/workflow.json").read_text(encoding="utf-8"))
        self.settings: dict[str, Any] = workflow.get("generation_policy", {})
        self.mode = str(self.settings.get("mode", "free_only"))
        self.allow_paid_generation = bool(self.settings.get("allow_paid_generation", False))
        self.maximum_paid_inr = float(self.settings.get("maximum_paid_generation_inr", 0))
        self.disabled_providers = {
            str(value).strip().lower() for value in self.settings.get("disabled_providers", ["fal"])
        }
        values = _dotenv_values(root / ".env")
        self._allowed_credentials = values
        gemini = values.get("GEMINI_API_KEY") or values.get("GOOGLE_API_KEY") or values.get("gemini_token")
        huggingface = values.get("HF_TOKEN")
        self.credentials = CredentialStatus(bool(gemini), bool(huggingface))

    def credential(self, name: str) -> str:
        """Return an allowed credential to a provider client without logging it."""
        if name == "HF_TOKEN":
            value = self._allowed_credentials.get("HF_TOKEN")
        elif name == "GEMINI_API_KEY":
            value = (
                self._allowed_credentials.get("GEMINI_API_KEY")
                or self._allowed_credentials.get("GOOGLE_API_KEY")
                or self._allowed_credentials.get("gemini_token")
            )
        else:
            raise GenerationPolicyError(f"credential {name!r} is not allowed by project policy")
        if not value:
            raise GenerationPolicyError(f"credential {name!r} is not configured")
        return value

    def assert_media_call_allowed(self, provider: str, estimated_cost_inr: float | None) -> None:
        normalized = provider.strip().lower()
        if normalized in self.disabled_providers or normalized.startswith("fal"):
            raise GenerationPolicyError("fal media generation is disabled by project policy")
        if estimated_cost_inr is None:
            raise GenerationPolicyError("media generation is blocked when the cost cannot be proven as INR 0")
        if estimated_cost_inr < 0:
            raise GenerationPolicyError("estimated media cost cannot be negative")
        if estimated_cost_inr > 0 and not self.allow_paid_generation:
            raise GenerationPolicyError("paid media generation is disabled; maximum permitted cost is INR 0")
        if estimated_cost_inr > self.maximum_paid_inr:
            raise GenerationPolicyError(
                f"estimated media cost INR {estimated_cost_inr:.2f} exceeds the configured maximum"
            )

    def assert_promotional_credit_call_allowed(
        self,
        provider: str,
        estimated_list_cost_usd: float,
        estimated_cash_cost_inr: float,
    ) -> None:
        """Allow one explicitly confirmed included-credit call while cash cost stays zero."""
        promotional = self.settings.get("promotional_credit", {})
        normalized = provider.strip().lower()
        if normalized in self.disabled_providers or normalized.startswith("fal"):
            raise GenerationPolicyError("fal media generation is disabled by project policy")
        if normalized != "huggingface":
            raise GenerationPolicyError("only Hugging Face included credit is confirmed")
        if not promotional.get("confirmed_by_user"):
            raise GenerationPolicyError("included credit has not been confirmed by the user")
        if estimated_cash_cost_inr != 0:
            raise GenerationPolicyError("promotional-credit calls must have an estimated cash cost of INR 0")
        maximum_usd = float(promotional.get("maximum_test_list_cost_usd", 0))
        if estimated_list_cost_usd <= 0 or estimated_list_cost_usd > maximum_usd:
            raise GenerationPolicyError(
                f"estimated list cost USD {estimated_list_cost_usd:.4f} exceeds the confirmed test ceiling"
            )

    def assert_promotional_image_batch_allowed(
        self,
        provider: str,
        routing_provider: str,
        output_count: int,
        list_cost_per_output_usd: float,
        estimated_cash_cost_inr: float,
    ) -> None:
        """Bound the user-confirmed five-post HF credit batch and exclude FAL routing."""
        batch = self.settings.get("promotional_credit", {}).get("image_batch", {})
        normalized = provider.strip().lower()
        route = routing_provider.strip().lower()
        if normalized != "huggingface":
            raise GenerationPolicyError("post-image credit is authorized only through Hugging Face")
        if route in self.disabled_providers or route.startswith("fal"):
            raise GenerationPolicyError("FAL routing is disabled by project policy")
        if route != str(batch.get("routing_provider", "")).lower():
            raise GenerationPolicyError("post images must use the confirmed Replicate route")
        if not batch.get("confirmed_by_user"):
            raise GenerationPolicyError("the Hugging Face post-image batch is not user-confirmed")
        if estimated_cash_cost_inr != 0:
            raise GenerationPolicyError("post-image generation must have an estimated cash cost of INR 0")
        maximum_outputs = int(batch.get("maximum_outputs", 0))
        if output_count <= 0 or output_count > maximum_outputs:
            raise GenerationPolicyError(
                f"post-image output count {output_count} exceeds the confirmed maximum {maximum_outputs}"
            )
        confirmed_unit_cost = float(batch.get("list_cost_per_output_usd", 0))
        if list_cost_per_output_usd != confirmed_unit_cost:
            raise GenerationPolicyError("post-image unit cost differs from the confirmed provider price")
        estimated_total = output_count * list_cost_per_output_usd
        maximum_total = float(batch.get("maximum_batch_list_cost_usd", 0))
        if estimated_total > maximum_total:
            raise GenerationPolicyError(
                f"post-image batch list cost USD {estimated_total:.4f} exceeds the confirmed ceiling"
            )

    def public_summary(self) -> dict[str, Any]:
        """Return audit-safe policy state; never return credential values."""
        video_ledger = self.root / "logs/hf_promotional_credit_test.json"
        image_ledger = self.root / "logs/hf_promotional_image_batch.json"

        def succeeded(path: Path) -> bool:
            if not path.exists():
                return False
            try:
                return json.loads(path.read_text(encoding="utf-8")).get("status") == "succeeded"
            except (OSError, json.JSONDecodeError):
                return False

        video_succeeded = succeeded(video_ledger)
        completed_image_files: set[str] = set()
        if image_ledger.exists():
            try:
                image_audit = json.loads(image_ledger.read_text(encoding="utf-8"))
                entries = list(image_audit.get("outputs", []))
                entries.extend(image_audit.get("credit_restored_resume", {}).get("outputs", []))
                completed_image_files = {
                    str(entry.get("filename"))
                    for entry in entries
                    if entry.get("status") == "succeeded" and entry.get("filename")
                }
            except (OSError, json.JSONDecodeError):
                completed_image_files = set()
        image_count = len(completed_image_files)
        images_succeeded = image_count == 5
        external_succeeded = video_succeeded or image_count > 0
        return {
            "mode": self.mode,
            "allow_paid_generation": self.allow_paid_generation,
            "maximum_paid_generation_inr": self.maximum_paid_inr,
            "disabled_providers": sorted(self.disabled_providers),
            "media_provider": "local + Hugging Face promotional sources" if external_succeeded else "local",
            "gemini_configured": self.credentials.gemini_configured,
            "huggingface_configured": self.credentials.huggingface_configured,
            "fal_ignored": self.credentials.fal_ignored,
            "external_media_calls_executed": external_succeeded,
            "external_media_cash_cost_inr": 0,
            "hf_promotional_video_succeeded": video_succeeded,
            "hf_promotional_post_images_succeeded": images_succeeded,
            "hf_promotional_post_images_completed": image_count,
            "hf_promotional_post_images_planned": 5,
            "hf_promotional_post_images_status": (
                "complete" if images_succeeded else "partial" if image_count else "not_started"
            ),
            "promotional_credit_test_enabled": bool(
                self.settings.get("promotional_credit", {}).get("confirmed_by_user")
            ),
        }
