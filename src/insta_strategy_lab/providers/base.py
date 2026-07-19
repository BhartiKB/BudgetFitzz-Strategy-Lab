"""Provider-neutral contracts for hybrid revised-media generation."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field


ProviderMode = Literal["VEO_API", "HUGGINGFACE_API", "MANUAL_PROVIDER", "LOCAL_FALLBACK"]


class GenerationRequest(BaseModel):
    job_id: str
    asset_id: str
    plan_day: int
    asset_type: Literal["image", "video"]
    provider_mode: ProviderMode
    provider_name: str
    model_name: str | None = None
    prompt: str
    negative_prompt: str | None = None
    reference_files: list[str] = Field(default_factory=list)
    width: int
    height: int
    duration_seconds: float | None = None
    aspect_ratio: str
    seed: int | None = None
    estimated_cost_inr: Decimal = Decimal("0")
    maximum_cost_inr: Decimal = Decimal("100")
    metadata: dict[str, Any] = Field(default_factory=dict)


class GenerationResult(BaseModel):
    job_id: str
    asset_id: str
    provider_mode: ProviderMode
    provider_name: str
    model_name: str | None = None
    access_method: str
    status: str
    external_request_id: str | None = None
    raw_output_files: list[str] = Field(default_factory=list)
    final_output_files: list[str] = Field(default_factory=list)
    estimated_cost_inr: Decimal = Decimal("0")
    actual_cost_inr: Decimal = Decimal("0")
    promotional_credit_used: bool = False
    retries: int = 0
    latency_seconds: float | None = None
    error: str | None = None
    provenance_file: str | None = None
