"""Veo API execution gate.

No request is issued from this adapter unless configuration, credential, budget and a
per-request human approval are all present. The repository has no recorded successful
Veo request, so this module intentionally reports readiness rather than claiming use.
"""

from __future__ import annotations

from pathlib import Path

from .base import GenerationRequest, GenerationResult
from .registry import ProviderRegistry


class VeoProvider:
    def __init__(self, root: Path):
        self.root = root
        self.registry = ProviderRegistry(root)

    def prepare(self, request: GenerationRequest, approved: bool) -> GenerationResult:
        state = next(item["api_state"] for item in self.registry.public_status()["providers"] if item["id"] == "veo")
        if state != "READY":
            return GenerationResult(job_id=request.job_id, asset_id=request.asset_id, provider_mode="VEO_API", provider_name="Veo", model_name=request.model_name, access_method="API", status=state, estimated_cost_inr=request.estimated_cost_inr, error="No Veo API request was made")
        if request.estimated_cost_inr > request.maximum_cost_inr:
            return GenerationResult(job_id=request.job_id, asset_id=request.asset_id, provider_mode="VEO_API", provider_name="Veo", model_name=request.model_name, access_method="API", status="INSUFFICIENT_BUDGET", estimated_cost_inr=request.estimated_cost_inr)
        if not approved:
            return GenerationResult(job_id=request.job_id, asset_id=request.asset_id, provider_mode="VEO_API", provider_name="Veo", model_name=request.model_name, access_method="API", status="API_APPROVAL_REQUIRED", estimated_cost_inr=request.estimated_cost_inr)
        return GenerationResult(job_id=request.job_id, asset_id=request.asset_id, provider_mode="VEO_API", provider_name="Veo", model_name=request.model_name, access_method="API", status="FAILED", estimated_cost_inr=request.estimated_cost_inr, error="Veo API execution is configured as a gated contract but has not been implemented or tested in this offline demonstration")
