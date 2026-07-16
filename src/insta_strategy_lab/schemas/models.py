"""Validated data contracts shared across agent boundaries."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Evidence(BaseModel):
    evidence_id: str
    finding: str
    metric: str
    value: float | int | str
    comparison: str
    sample_size: int
    confidence: Literal["anecdotal", "directional", "cautious", "robust"]
    source: str


class PlanItem(BaseModel):
    day: int = Field(ge=1, le=7)
    date: str
    format: Literal["post", "video"]
    content_pillar: str
    topic: str
    target_audience_segment: str
    hook: str
    content_idea: str
    visual_direction: str
    caption_direction: str
    full_proposed_caption: str
    cta: str
    recommended_publication_time: str
    baseline_insight: str
    primary_kpi: str
    secondary_kpi: str
    reasoned_target_range: str
    asset_filename: str
    generation_prompt_or_template_reference: str

    @field_validator("full_proposed_caption", "hook", "cta")
    @classmethod
    def no_placeholders(cls, value: str) -> str:
        lowered = value.lower()
        if any(token in lowered for token in ("lorem ipsum", "todo", "tbd", "placeholder")):
            raise ValueError("placeholder text is forbidden")
        return value


class SpendEntry(BaseModel):
    timestamp: datetime
    run_id: str
    asset: str
    provider: str
    model_or_tool: str
    operation: str
    quantity: int = 1
    unit_cost_inr: float = Field(ge=0)
    total_cost_inr: float = Field(ge=0)
    paid_or_free: Literal["paid", "free"]
    evidence_or_receipt_reference: str
    notes: str


class TraceEntry(BaseModel):
    timestamp: datetime
    run_id: str
    agent: str
    action: str
    input_reference: str
    output_reference: str
    decision_summary: str
    evidence_ids: list[str] = Field(default_factory=list)
    duration_sec: float = Field(ge=0)
    status: Literal["started", "completed", "failed", "retrying", "approved"]
    error: str | None = None
    retry_number: int = Field(ge=0)
    provider_or_tool: str

