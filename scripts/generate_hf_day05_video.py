"""Generate the user-confirmed zero-cash-cost HF source for the realistic Day 5 video."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from insta_strategy_lab.providers import HuggingFaceVideoClient  # noqa: E402


PROMPT = (
    "Photorealistic vertical smartphone fashion fit-check video, full-body young Indian man in a clean "
    "bright apartment wearing a simple fitted off-white crew-neck t-shirt, straight charcoal trousers, and "
    "white low-top sneakers. Editorial three-part demonstration in one continuous shot: first he points to a "
    "dropped shoulder seam, then adjusts the shirt so the seam ends at his natural shoulder; next the camera "
    "shows trousers with heavy stacking at the shoe, then a clean single trouser break; finally he steps back "
    "to show a balanced top-to-bottom silhouette. Natural skin, realistic hands, realistic fabric physics, "
    "subtle camera movement, daylight, no text, no logos, no watermark, no animation, no cartoon, no sketch, "
    "no distorted limbs."
)


def main() -> None:
    output = ROOT / "assets/source_media/day05_hf_wan.mp4"
    result = HuggingFaceVideoClient(ROOT).generate_day_five(PROMPT, output)
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
