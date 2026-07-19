"""Adapter that exposes the existing Hugging Face clients through the neutral contract."""

from __future__ import annotations

from pathlib import Path

from .base import GenerationRequest, GenerationResult
from .registry import ProviderRegistry


class HuggingFaceProvider:
    def __init__(self, root: Path):
        self.root = root
        self.registry = ProviderRegistry(root)

    def prepare(self, request: GenerationRequest, approved: bool = False) -> GenerationResult:
        state = next(item["api_state"] for item in self.registry.public_status()["providers"] if item["id"] == "huggingface")
        if state != "READY":
            return GenerationResult(job_id=request.job_id, asset_id=request.asset_id, provider_mode="HUGGINGFACE_API", provider_name="Hugging Face", model_name=request.model_name, access_method="API", status=state, estimated_cost_inr=request.estimated_cost_inr, error="No Hugging Face request was made")
        if request.estimated_cost_inr > 0 and not approved:
            return GenerationResult(job_id=request.job_id, asset_id=request.asset_id, provider_mode="HUGGINGFACE_API", provider_name="Hugging Face", model_name=request.model_name, access_method="API", status="API_APPROVAL_REQUIRED", estimated_cost_inr=request.estimated_cost_inr)
        return GenerationResult(job_id=request.job_id, asset_id=request.asset_id, provider_mode="HUGGINGFACE_API", provider_name="Hugging Face", model_name=request.model_name, access_method="API", status="AWAITING_PROVIDER_SELECTION", estimated_cost_inr=request.estimated_cost_inr, error="Use the existing bounded HuggingFaceImageClient or HuggingFaceVideoClient only after their credit policy passes")
