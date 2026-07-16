"""Generate five context-locked post photographs using confirmed HF promotional credit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from insta_strategy_lab.providers import HuggingFaceImageClient  # noqa: E402


COMMON = (
    "Use case: photorealistic-natural. Asset type: Instagram menswear editorial photo layer. "
    "Authentic affordable menswear for young Indian men in Delhi NCR. Natural daylight, realistic "
    "fabric texture, subtle everyday imperfections, restrained forest green, cream, charcoal and "
    "stone palette. Vertical 4:5 composition. No text, no letters, no numbers, no logos, no brands, "
    "no watermark, no product packaging. "
)

PROMPTS = {
    "day01_capsule_formula_hf.jpg": COMMON + (
        "Top-down editorial flat lay showing exactly three separate wardrobe pieces: one textured "
        "forest-green overshirt, one heavyweight cream crew-neck tee, and one charcoal straight-leg "
        "trouser. Arrange the three pieces cleanly on a warm off-white linen surface with generous "
        "spacing, true-to-life folds and soft window shadows. No shoes and no extra garments."
    ),
    "day03_colour_vote_hf.jpg": COMMON + (
        "Studio lookbook photograph of exactly three adult Indian male models standing side by side, "
        "full body and clearly separated, each wearing exactly one date-night outfit. Left model: "
        "forest-green overshirt, cream tee and cream trousers. Centre model: navy overshirt and stone "
        "trousers. Right model: burgundy overshirt and charcoal trousers. Natural poses, accurate "
        "hands and shoes, neutral warm-grey studio wall. No extra people and no extra garments."
    ),
    "day04_budget_priority_hf.jpg": COMMON + (
        "Realistic top-down budget wardrobe selection on a simple bed: dark straight-leg trousers "
        "placed first and most prominent, a heavyweight cream solid tee second, a textured forest "
        "overshirt third. Exactly these three garments, neatly arranged in a clear priority sequence, "
        "modest student apartment, warm morning light, practical rather than luxury styling."
    ),
    "day06_sneaker_scorecard_hf.jpg": COMMON + (
        "Clean product-style photograph of exactly three separate unbranded men's sneakers arranged "
        "in one horizontal row on a pale stone studio floor: a minimal off-white neutral court shoe, "
        "a blue-grey retro runner, and a tasteful burnt-orange chunky sneaker. Accurate laces, soles "
        "and material texture, each shoe fully visible, no feet, no boxes, no duplicate shoes."
    ),
    "day07_wardrobe_audit_hf.jpg": COMMON + (
        "Candid editorial photograph of a young Indian man in a modest bright apartment standing at "
        "an open wardrobe, thoughtfully holding one forest-green overshirt while comparing it with "
        "the clothes he already owns. Natural hands, calm expression, realistic lived-in wardrobe, "
        "cream tee and charcoal trousers, practical purchase-decision mood, uncluttered framing."
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-after-credit-restored", action="store_true")
    args = parser.parse_args()
    output_dir = ROOT / "assets/source_media/posts"
    client = HuggingFaceImageClient(ROOT)
    if args.resume_after_credit_restored:
        resume_names = {
            "day03_colour_vote_hf.jpg",
            "day04_budget_priority_hf.jpg",
            "day06_sneaker_scorecard_hf.jpg",
            "day07_wardrobe_audit_hf.jpg",
        }
        result = client.resume_after_credit_restored(
            {name: prompt for name, prompt in PROMPTS.items() if name in resume_names},
            output_dir,
        )
        completed = result["credit_restored_resume"]["completed_outputs"]
        outputs = result["credit_restored_resume"]["outputs"]
        estimated_cost = result["credit_restored_resume"]["estimated_list_cost_usd"]
    else:
        result = client.generate_batch(PROMPTS, output_dir)
        completed = result["completed_outputs"]
        outputs = result["outputs"]
        estimated_cost = result["estimated_batch_list_cost_usd"]
    print(json.dumps({
        "status": result["status"],
        "completed_outputs": completed,
        "estimated_batch_list_cost_usd": estimated_cost,
        "cash_cost_inr": 0,
        "fal_key_used": False,
        "fal_routing_used": False,
        "outputs": [entry["output"] for entry in outputs],
    }, indent=2))


if __name__ == "__main__":
    main()
