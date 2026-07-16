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
        gemini = values.get("GEMINI_API_KEY") or values.get("GOOGLE_API_KEY") or values.get("gemini_token")
        huggingface = values.get("HF_TOKEN")
        self.credentials = CredentialStatus(bool(gemini), bool(huggingface))

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

    def public_summary(self) -> dict[str, Any]:
        """Return audit-safe policy state; never return credential values."""
        return {
            "mode": self.mode,
            "allow_paid_generation": self.allow_paid_generation,
            "maximum_paid_generation_inr": self.maximum_paid_inr,
            "disabled_providers": sorted(self.disabled_providers),
            "media_provider": "local",
            "gemini_configured": self.credentials.gemini_configured,
            "huggingface_configured": self.credentials.huggingface_configured,
            "fal_ignored": self.credentials.fal_ignored,
            "external_media_calls_executed": False,
        }
