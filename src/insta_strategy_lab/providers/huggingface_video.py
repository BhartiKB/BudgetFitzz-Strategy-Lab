"""One-shot Hugging Face included-credit video generation."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .policy import GenerationPolicy, GenerationPolicyError


class HuggingFaceVideoClient:
    """Generate one bounded Wan video through HF routing without using FAL_KEY."""

    MODEL = "Wan-AI/Wan2.2-TI2V-5B"
    ROUTING_PROVIDER = "replicate"
    LIST_COST_USD = 0.025

    def __init__(self, root: Path):
        self.root = root
        self.policy = GenerationPolicy(root)

    def generate_test(self, prompt: str, output: Path) -> dict[str, Any]:
        return self._generate(
            prompt,
            output,
            self.root / "logs/hf_promotional_credit_test.json",
            "promotional-credit text-to-video test",
        )

    def generate_day_five(self, prompt: str, output: Path) -> dict[str, Any]:
        return self._generate(
            prompt,
            output,
            self.root / "logs/hf_promotional_credit_day05.json",
            "promotional-credit text-to-video source for Day 5",
        )

    def _generate(self, prompt: str, output: Path, ledger: Path, operation: str) -> dict[str, Any]:
        if ledger.exists():
            raise GenerationPolicyError(
                "the Hugging Face promotional-credit request is already reserved or completed; "
                "delete nothing and inspect the existing ledger"
            )
        existing_ledgers = [
            self.root / "logs/hf_promotional_credit_test.json",
            self.root / "logs/hf_promotional_credit_day05.json",
        ]
        maximum_calls = int(self.policy.settings.get("promotional_credit", {}).get("maximum_successful_calls", 1))
        if sum(path.exists() for path in existing_ledgers) >= maximum_calls:
            raise GenerationPolicyError("the confirmed Hugging Face promotional-credit video limit is already reserved")
        self.policy.assert_promotional_credit_call_allowed(
            "huggingface",
            estimated_list_cost_usd=self.LIST_COST_USD,
            estimated_cash_cost_inr=0,
        )
        token = self.policy.credential("HF_TOKEN")
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise RuntimeError("huggingface_hub is required for the free-credit test") from exc

        resolved_root = self.root.resolve()
        resolved_output = output.resolve()
        if not resolved_output.is_relative_to(resolved_root):
            raise GenerationPolicyError("the promotional-credit output must stay inside the project")

        client = InferenceClient(provider=self.ROUTING_PROVIDER, api_key=token, timeout=300)
        output.parent.mkdir(parents=True, exist_ok=True)
        started_at = datetime.now(UTC)
        audit: dict[str, Any] = {
            "status": "reserved",
            "timestamp": started_at.isoformat(),
            "provider": "huggingface",
            "routing_provider": self.ROUTING_PROVIDER,
            "model": self.MODEL,
            "operation": operation,
            "estimated_list_cost_usd": self.LIST_COST_USD,
            "cash_cost_inr": 0,
            "paid_or_free": "free promotional credit",
            "fal_key_used": False,
            "output": str(output),
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        }
        # Reserve before the request. Any ambiguous failure blocks retries because a
        # provider may have started work before returning an error.
        write_credit_ledger(ledger, audit)
        try:
            video = client.text_to_video(
                prompt,
                model=self.MODEL,
                num_frames=81,
                seed=4050,
                extra_body={
                    "resolution": "720p",
                    "aspect_ratio": "9:16",
                    "frames_per_second": 16,
                    "go_fast": True,
                    "optimize_prompt": False,
                },
            )
        except Exception as exc:
            audit.update({
                "status": "failed_or_ambiguous",
                "finished_at": datetime.now(UTC).isoformat(),
                "failure_type": type(exc).__name__,
            })
            write_credit_ledger(ledger, audit)
            raise
        output.write_bytes(video)
        digest = hashlib.sha256(video).hexdigest()
        audit.update({
            "status": "succeeded",
            "finished_at": datetime.now(UTC).isoformat(),
            "output_bytes": len(video),
            "sha256": digest,
        })
        write_credit_ledger(ledger, audit)
        return audit


def write_credit_ledger(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
