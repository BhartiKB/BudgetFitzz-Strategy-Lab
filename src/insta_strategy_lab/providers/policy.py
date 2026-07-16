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

    def public_summary(self) -> dict[str, Any]:
        """Return audit-safe policy state; never return credential values."""
        credit_ledger = self.root / "logs/hf_promotional_credit_test.json"
        credit_succeeded = False
        if credit_ledger.exists():
            try:
                credit_succeeded = json.loads(credit_ledger.read_text(encoding="utf-8")).get(
                    "status"
                ) == "succeeded"
            except (OSError, json.JSONDecodeError):
                credit_succeeded = False
        return {
            "mode": self.mode,
            "allow_paid_generation": self.allow_paid_generation,
            "maximum_paid_generation_inr": self.maximum_paid_inr,
            "disabled_providers": sorted(self.disabled_providers),
            "media_provider": "local + Hugging Face promotional source" if credit_succeeded else "local",
            "gemini_configured": self.credentials.gemini_configured,
            "huggingface_configured": self.credentials.huggingface_configured,
            "fal_ignored": self.credentials.fal_ignored,
            "external_media_calls_executed": credit_succeeded,
            "external_media_cash_cost_inr": 0,
            "promotional_credit_test_enabled": bool(
                self.settings.get("promotional_credit", {}).get("confirmed_by_user")
            ),
        }
