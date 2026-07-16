"""Extensible, zero-cost local content provider selection."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .policy import GenerationPolicy


@dataclass(frozen=True)
class ProviderSelection:
    provider: str
    model: str
    device: str
    reason: str
    generation_policy: dict | None = None


class LocalProvider:
    """Select an installed local provider; always retain a deterministic fallback."""

    def __init__(self, root: Path | None = None):
        self.policy = GenerationPolicy(root) if root is not None else None

    def select(self) -> ProviderSelection:
        policy_summary = self.policy.public_summary() if self.policy else None
        if shutil.which("ollama"):
            return ProviderSelection(
                "ollama", "installed-local-model", "auto",
                "Existing Ollama executable detected; media generation remains local and zero-cost",
                policy_summary,
            )
        return ProviderSelection(
            "deterministic-template",
            "budgetfitzz-editorial-v1",
            "cpu",
            "Free-only policy selected validated local templates; no paid external media endpoint was called",
            policy_summary,
        )

    def generate(self, schema_name: str, context: dict) -> dict:
        """Return the already validated deterministic structure supplied by the caller."""
        payload = context.get("deterministic_payload")
        if not isinstance(payload, dict):
            raise ValueError(f"{schema_name} requires deterministic_payload")
        return payload
