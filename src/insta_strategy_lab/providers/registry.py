"""Truthful provider availability reporting without exposing credentials."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from insta_strategy_lab.generation.config import load_generation_config
from .policy import GenerationPolicy


class ProviderRegistry:
    def __init__(self, root: Path):
        self.root = root
        self.config = load_generation_config(root)
        self.policy = GenerationPolicy(root)

    def public_status(self) -> dict[str, Any]:
        providers = self.config["providers"]
        veo = providers["veo"]
        hf = providers["huggingface"]
        local = providers["local"]
        veo_credential = self.policy.credentials.gemini_configured
        hf_credential = self.policy.credentials.huggingface_configured
        veo_state = "DISABLED" if not veo.get("enabled") or not veo.get("api_mode_enabled") else ("READY" if veo_credential else "MISSING_CREDENTIALS")
        hf_state = "READY" if hf.get("enabled") and hf.get("api_mode_enabled") and hf_credential else ("MISSING_CREDENTIALS" if hf.get("enabled") and hf.get("api_mode_enabled") else "DISABLED")
        return {
            "default_mode": self.config["generation"]["default_mode"],
            "require_paid_api_approval": bool(self.config["generation"]["require_paid_api_approval"]),
            "media_budget_inr": self.config["generation"]["media_budget_inr"],
            "providers": [
                {"id": "veo", "label": "Veo API", "api_state": veo_state, "manual_state": "READY" if veo.get("manual_mode_enabled") else "DISABLED", "model": veo.get("model"), "api_tested": False, "capabilities": veo.get("capabilities", [])},
                {"id": "huggingface", "label": "Hugging Face API", "api_state": hf_state, "manual_state": "READY" if hf.get("manual_mode_enabled") else "DISABLED", "model": hf.get("model"), "api_tested": False, "capabilities": hf.get("capabilities", [])},
                {"id": "local", "label": "Local fallback", "api_state": "READY" if local.get("enabled") else "DISABLED", "manual_state": "N/A", "model": "Pillow + FFmpeg", "api_tested": True, "capabilities": local.get("capabilities", [])},
            ],
            "claim": "Production architecture implemented. Manual provider workflow is available. API mode is configured but not reported as connected or tested unless a successful request is recorded.",
        }
