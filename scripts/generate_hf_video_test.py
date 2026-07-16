"""Generate one bounded Hugging Face promotional-credit video for visual QA."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from insta_strategy_lab.providers import HuggingFaceVideoClient  # noqa: E402


PROMPT = (
    "Photorealistic vertical smartphone fashion video of a young Indian man in a bright modern "
    "Delhi apartment, wearing a forest-green textured overshirt over a cream heavyweight tee and "
    "charcoal straight-leg trousers. He calmly buttons the overshirt, adjusts one cuff, and turns "
    "slightly toward the window. Natural human movement, realistic hands and fabric physics, soft "
    "daylight, authentic affordable menswear editorial, subtle slow camera push-in, clean background, "
    "no text, no logos, no watermark, no duplicated limbs."
)


def main() -> None:
    output = ROOT / "tmp/hf_free_credit/day02_wan_test.mp4"
    result = HuggingFaceVideoClient(ROOT).generate_test(PROMPT, output)
    print(json.dumps({
        "status": result["status"],
        "output": str(output),
        "cash_cost_inr": 0,
        "estimated_list_cost_usd": result["estimated_list_cost_usd"],
        "fal_key_used": False,
        "sha256": result["sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
