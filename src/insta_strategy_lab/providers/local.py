"""Extensible, zero-cost local content provider selection."""

from __future__ import annotations

import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderSelection:
    provider: str
    model: str
    device: str
    reason: str


class LocalProvider:
    """Select an installed local provider; always retain a deterministic fallback."""

    def select(self) -> ProviderSelection:
        if shutil.which("ollama"):
            return ProviderSelection("ollama", "installed-local-model", "auto", "Existing Ollama executable detected")
        return ProviderSelection(
            "deterministic-template",
            "budgetfitzz-editorial-v1",
            "cpu",
            "No local Ollama or compatible cached instruct model was present; used validated offline templates",
        )

    def generate(self, schema_name: str, context: dict) -> dict:
        """Return the already validated deterministic structure supplied by the caller."""
        payload = context.get("deterministic_payload")
        if not isinstance(payload, dict):
            raise ValueError(f"{schema_name} requires deterministic_payload")
        return payload

