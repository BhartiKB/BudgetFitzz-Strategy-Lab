"""Provider selection that never silently authorizes a paid external request."""

from __future__ import annotations

from pathlib import Path

from .base import GenerationRequest, GenerationResult
from .registry import ProviderRegistry


class ProviderRouter:
    def __init__(self, root: Path):
        self.root = root
        self.registry = ProviderRegistry(root)

    def select_mode(self, explicit_mode: str | None = None) -> str:
        if explicit_mode:
            return explicit_mode
        status = {item["id"]: item for item in self.registry.public_status()["providers"]}
        if status["veo"]["api_state"] == "READY":
            return "VEO_API"
        if status["huggingface"]["api_state"] == "READY":
            return "HUGGINGFACE_API"
        if status["veo"]["manual_state"] == "READY":
            return "MANUAL_PROVIDER"
        return "LOCAL_FALLBACK"

    def prepare(self, request: GenerationRequest, user_approved: bool = False) -> GenerationResult:
        mode = request.provider_mode
        if mode in {"VEO_API", "HUGGINGFACE_API"} and request.estimated_cost_inr > 0 and not user_approved:
            return GenerationResult(**request.model_dump(), access_method="API", status="API_APPROVAL_REQUIRED")
        if mode == "MANUAL_PROVIDER":
            return GenerationResult(**request.model_dump(), access_method="Manual web interface", status="AWAITING_IMPORT")
        if mode == "LOCAL_FALLBACK":
            return GenerationResult(**request.model_dump(), access_method="Local", status="FALLBACK_REQUIRED")
        provider = "veo" if mode == "VEO_API" else "huggingface"
        state = next(item["api_state"] for item in self.registry.public_status()["providers"] if item["id"] == provider)
        return GenerationResult(**request.model_dump(), access_method="API", status=state)
