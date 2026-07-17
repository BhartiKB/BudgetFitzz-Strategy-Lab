"""Procedural BudgetFitzz creatives using original vector-like garment geometry."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

from insta_strategy_lab.schemas import PlanItem


CANVAS = "#F6F2E9"
INK = "#17211B"
FOREST = "#0F6B4F"
LIME = "#B7F34A"
CORAL = "#FF7A45"
BLUE = "#4285F4"
MUTED = "#627067"
ROOT = Path(__file__).resolve().parents[3]
PHOTO_SOURCES = {
    "day01_capsule_formula.png": ROOT / "assets/source_media/posts/day01_capsule_formula_hf.jpg",
    "day03_colour_vote.png": ROOT / "assets/source_media/posts/day03_colour_vote_hf.jpg",
    "day04_budget_priority.png": ROOT / "assets/source_media/posts/day04_budget_priority_hf.jpg",
    "day06_sneaker_scorecard.png": ROOT / "assets/source_media/posts/day06_sneaker_scorecard_hf.jpg",
    "day07_wardrobe_audit.png": ROOT / "assets/source_media/posts/day07_wardrobe_audit_hf.jpg",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / ("seguisb.ttf" if bold else "segoeui.ttf")), size)


def wrap(draw: ImageDraw.ImageDraw, text: str, selected_font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=selected_font)[2] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def text_block(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int, width: int, fill: str = INK, bold: bool = False, spacing: int = 10) -> int:
    selected = font(size, bold)
    x, y = xy
    line_h = size + spacing
    for line in wrap(draw, text, selected, width):
        draw.text((x, y), line, font=selected, fill=fill)
        y += line_h
    return y


def wordmark(draw: ImageDraw.ImageDraw, light: bool = False, day: int | None = None) -> None:
    color = "#FFFFFF" if light else INK
    draw.text((72, 56), "budgetfitzz", font=font(30, True), fill=color)
    if day is not None:
        badge = (895, 50, 1008, 96)
        label = f"DAY {day}"
        selected_font = font(18, True)
        bounds = draw.textbbox((0, 0), label, font=selected_font)
        x = badge[0] + ((badge[2] - badge[0]) - (bounds[2] - bounds[0])) // 2
        y = badge[1] + ((badge[3] - badge[1]) - (bounds[3] - bounds[1])) // 2 - bounds[1]
        draw.rounded_rectangle(badge, radius=22, fill=LIME)
        draw.text((x, y), label, font=selected_font, fill=INK)


def shirt(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: str, outline: str = INK, open_front: bool = False) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    points = [(x0 + .25*w, y0), (x0 + .43*w, y0 + .08*h), (x0 + .57*w, y0 + .08*h), (x0 + .75*w, y0), (x1, y0 + .28*h), (x0 + .82*w, y0 + .48*h), (x0 + .72*w, y0 + .37*h), (x0 + .72*w, y1), (x0 + .28*w, y1), (x0 + .28*w, y0 + .37*h), (x0 + .18*w, y0 + .48*h), (x0, y0 + .28*h)]
    draw.polygon(points, fill=color, outline=outline, width=5)
    draw.line((x0 + .5*w, y0 + .10*h, x0 + .5*w, y1), fill=outline, width=4)
    if open_front:
        draw.polygon([(x0 + .43*w, y0 + .08*h), (x0 + .5*w, y0 + .28*h), (x0 + .36*w, y0 + .18*h)], fill=CANVAS, outline=outline)
        draw.polygon([(x0 + .57*w, y0 + .08*h), (x0 + .5*w, y0 + .28*h), (x0 + .64*w, y0 + .18*h)], fill=CANVAS, outline=outline)
    else:
        for ratio in (.34, .49, .64, .79):
            draw.ellipse((x0 + .485*w, y0 + ratio*h, x0 + .515*w, y0 + ratio*h + 7), fill=outline)


def trousers(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: str) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    points = [(x0, y0), (x1, y0), (x0 + .86*w, y1), (x0 + .54*w, y1), (x0 + .5*w, y0 + .32*h), (x0 + .46*w, y1), (x0 + .14*w, y1)]
    draw.polygon(points, fill=color, outline=INK, width=5)
    draw.line((x0, y0 + 20, x1, y0 + 20), fill=INK, width=4)


def sneaker(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: str, style: int = 0) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    pts = [(x0, y0 + .58*h), (x0 + .18*w, y0 + .22*h), (x0 + .5*w, y0 + .28*h), (x0 + .68*w, y0 + .52*h), (x1, y0 + .63*h), (x0 + .96*w, y0 + .86*h), (x0 + .14*w, y0 + .86*h)]
    draw.polygon(pts, fill=color, outline=INK, width=5)
    draw.line((x0 + .14*w, y0 + .68*h, x0 + .94*w, y0 + .68*h), fill=INK, width=4)
    if style == 1:
        for i in range(4):
            draw.line((x0 + (.35+i*.08)*w, y0 + .35*h, x0 + (.42+i*.08)*w, y0 + .55*h), fill=INK, width=3)
    elif style == 2:
        draw.rounded_rectangle((x0 + .35*w, y0 + .38*h, x0 + .7*w, y0 + .58*h), radius=12, outline=INK, width=4)


def base_post(day: int, dark: bool = False) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (1080, 1350), FOREST if dark else CANVAS)
    draw = ImageDraw.Draw(image)
    wordmark(draw, dark, day)
    return image, draw


def cta(draw: ImageDraw.ImageDraw, text: str, dark: bool = False) -> None:
    fill = LIME if dark else INK
    text_color = INK if dark else "#FFFFFF"
    draw.rounded_rectangle((72, 1184, 1008, 1282), radius=30, fill=fill)
    lines = wrap(draw, text, font(28, True), 820)
    y = 1201 if len(lines) == 2 else 1215
    for line in lines[:2]:
        draw.text((112, y), line, font=font(28, True), fill=text_color)
        y += 34


def photo_available(filename: str) -> bool:
    """Return whether the audited HF photographic layer exists for a post."""
    return PHOTO_SOURCES[filename].is_file()


def paste_photo(
    image: Image.Image,
    filename: str,
    box: tuple[int, int, int, int],
    *,
    radius: int = 34,
    focus_y: float = 0.5,
) -> None:
    """Cover-crop an HF photograph into a rounded editorial frame."""
    x0, y0, x1, y1 = box
    target_w, target_h = x1 - x0, y1 - y0
    with Image.open(PHOTO_SOURCES[filename]) as opened:
        source = opened.convert("RGB")
    scale = max(target_w / source.width, target_h / source.height)
    resized = source.resize(
        (math.ceil(source.width * scale), math.ceil(source.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = max(0, (resized.width - target_w) // 2)
    available_y = max(0, resized.height - target_h)
    top = round(available_y * min(1.0, max(0.0, focus_y)))
    crop = resized.crop((left, top, left + target_w, top + target_h))
    mask = Image.new("L", (target_w, target_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, target_w, target_h), radius=radius, fill=255)
    image.paste(crop, (x0, y0), mask)


def capsule_post(item: PlanItem) -> Image.Image:
    image, draw = base_post(item.day)
    y = text_block(draw, (72, 145), "3 PIECES. 7 CLEAN FITS.", 66, 900, INK, True, 6)
    draw.text((74, y + 10), "Build a system before you buy more.", font=font(29), fill=MUTED)
    cards = [(76, 390, 350, 925), (403, 390, 677, 925), (730, 390, 1004, 925)]
    labels = [("01", "TEXTURED", "OVERSHIRT"), ("02", "SOLID", "TEE"), ("03", "DARK", "TROUSER")]
    for idx, box in enumerate(cards):
        draw.rounded_rectangle(box, radius=32, fill="#FFFFFF", outline="#D7D7CE", width=3)
        draw.rounded_rectangle((box[0]+24, box[1]+24, box[0]+88, box[1]+67), radius=21, fill=LIME)
        draw.text((box[0]+43, box[1]+32), labels[idx][0], font=font(18, True), fill=INK)
        draw.text((box[0]+24, box[3]-112), labels[idx][1], font=font(22, True), fill=INK)
        draw.text((box[0]+24, box[3]-78), labels[idx][2], font=font(22, True), fill=INK)
    shirt(draw, (118, 505, 310, 785), FOREST, open_front=True)
    shirt(draw, (450, 525, 630, 780), "#E7E2D4")
    trousers(draw, (792, 505, 942, 790), "#323A36")
    draw.rounded_rectangle((72, 982, 1008, 1122), radius=28, fill="#E5EEDC")
    draw.text((105, 1010), "SWAP THE LAYER  •  CHANGE THE TUCK  •  REPEAT", font=font(28, True), fill=FOREST)
    draw.text((105, 1058), "One strong base beats five impulse buys.", font=font(25), fill=INK)
    cta(draw, item.cta)
    return image


def vote_post(item: PlanItem) -> Image.Image:
    image, draw = base_post(item.day, dark=True)
    text_block(draw, (72, 148), "DATE NIGHT:", 58, 900, "#FFFFFF", True)
    text_block(draw, (72, 214), "A, B OR C?", 84, 900, LIME, True)
    palettes = [(FOREST, "#EAE1CA", "A"), ("#203A63", "#D8D4C7", "B"), ("#7B243B", "#343A36", "C")]
    for idx, (top, bottom, label) in enumerate(palettes):
        x = 80 + idx * 330
        draw.rounded_rectangle((x, 370, x+290, 1035), radius=34, fill="#FFFFFF")
        draw.ellipse((x+98, 414, x+192, 508), fill="#E0B798", outline=INK, width=4)
        shirt(draw, (x+55, 500, x+235, 760), top)
        trousers(draw, (x+86, 740, x+204, 970), bottom)
        draw.ellipse((x+18, 392, x+82, 456), fill=LIME)
        draw.text((x+39, 401), label, font=font(29, True), fill=INK)
    draw.text((126, 1072), "FOREST + CREAM", font=font(19, True), fill="#FFFFFF")
    draw.text((444, 1072), "NAVY + STONE", font=font(19, True), fill="#FFFFFF")
    draw.text((763, 1072), "BURGUNDY + CHARCOAL", font=font(19, True), fill="#FFFFFF")
    cta(draw, item.cta, dark=True)
    return image


def budget_post(item: PlanItem) -> Image.Image:
    image, draw = base_post(item.day)
    text_block(draw, (72, 145), "₹1,999 TO LOOK SHARPER", 60, 900, INK, True)
    draw.text((74, 222), "BUY IN THIS ORDER  •  ILLUSTRATIVE BUDGET CAPS", font=font(23, True), fill=CORAL)
    rows = [
        ("01", "DARK STRAIGHT TROUSER", "₹899 cap", "Fix the base first", "#26302B"),
        ("02", "HEAVY SOLID TEE", "₹599 cap", "Works alone or layered", "#E7E2D4"),
        ("03", "TEXTURED OVERSHIRT", "₹501 cap", "Only if money remains", FOREST),
    ]
    for idx, row in enumerate(rows):
        y = 330 + idx * 245
        draw.rounded_rectangle((72, y, 1008, y+205), radius=30, fill="#FFFFFF", outline="#D8D8CF", width=3)
        draw.rounded_rectangle((98, y+28, 176, y+106), radius=22, fill=LIME if idx == 0 else "#E9EEE4")
        draw.text((121, y+48), row[0], font=font(28, True), fill=INK)
        draw.text((210, y+38), row[1], font=font(29, True), fill=INK)
        draw.text((210, y+90), row[3], font=font(24), fill=MUTED)
        draw.rounded_rectangle((765, y+52, 955, y+118), radius=28, fill=row[4])
        draw.text((802, y+70), row[2], font=font(24, True), fill="#FFFFFF" if idx != 1 else INK)
        draw.line((210, y+148, 950, y+148), fill="#D6D9D0", width=2)
        draw.text((210, y+160), "VALUE BEFORE VOLUME", font=font(17, True), fill=FOREST)
    cta(draw, item.cta)
    return image


def sneaker_post(item: PlanItem) -> Image.Image:
    image, draw = base_post(item.day, dark=True)
    text_block(draw, (72, 148), "RANK BY USE.", 72, 900, "#FFFFFF", True)
    text_block(draw, (72, 225), "NOT HYPE.", 72, 900, LIME, True)
    labels = [("NEUTRAL COURT", "VERSATILITY", "9/10", "#ECE6D7"), ("RETRO RUNNER", "WALKING", "9/10", BLUE), ("CHUNKY", "STATEMENT", "8/10", CORAL)]
    for idx, (name, job, score, color) in enumerate(labels):
        y = 390 + idx * 235
        draw.rounded_rectangle((72, y, 1008, y+190), radius=32, fill="#FFFFFF")
        sneaker(draw, (105, y+25, 365, y+165), color, idx)
        draw.text((405, y+34), name, font=font(30, True), fill=INK)
        draw.text((405, y+82), f"BEST FOR  {job}", font=font(21, True), fill=MUTED)
        draw.rounded_rectangle((790, y+55, 955, y+125), radius=28, fill=FOREST)
        draw.text((833, y+72), score, font=font(27, True), fill="#FFFFFF")
    cta(draw, item.cta, dark=True)
    return image


def audit_post(item: PlanItem) -> Image.Image:
    image, draw = base_post(item.day)
    text_block(draw, (72, 145), "PASS THE 5-POINT", 60, 900, INK, True)
    text_block(draw, (72, 212), "WARDROBE AUDIT", 70, 900, FOREST, True)
    questions = ["Creates 3 outfits with what I own", "Fits my body now", "Solves a real wardrobe gap", "Gets worn 2× a month", "Still wanted without the discount"]
    for idx, question in enumerate(questions):
        y = 380 + idx * 134
        draw.rounded_rectangle((72, y, 1008, y+105), radius=26, fill="#FFFFFF", outline="#D8D8CF", width=3)
        draw.rounded_rectangle((100, y+24, 158, y+82), radius=14, outline=FOREST, width=5)
        draw.text((194, y+31), question, font=font(28, idx in (0, 2)), fill=INK)
    draw.rounded_rectangle((72, 1065, 1008, 1150), radius=26, fill=LIME)
    draw.text((110, 1087), "4 YES = CONSIDER  •  3 OR FEWER = WAIT 48H", font=font(25, True), fill=INK)
    cta(draw, item.cta)
    return image


def photo_capsule_post(item: PlanItem) -> Image.Image:
    image, draw = base_post(item.day)
    y = text_block(draw, (72, 145), "3 PIECES. 7 CLEAN FITS.", 66, 900, INK, True, 6)
    draw.text((74, y + 10), "Build a system before you buy more.", font=font(29), fill=MUTED)
    paste_photo(image, item.asset_filename, (72, 310, 1008, 948), focus_y=0.48)
    draw.rounded_rectangle((72, 970, 1008, 1150), radius=30, fill="#E5EEDC")
    draw.text((105, 996), "01  TEXTURED OVERSHIRT", font=font(24, True), fill=FOREST)
    draw.text((105, 1041), "02  SOLID TEE", font=font(24, True), fill=INK)
    draw.text((515, 1041), "03  DARK TROUSER", font=font(24, True), fill=INK)
    draw.text((105, 1092), "SWAP THE LAYER  •  CHANGE THE TUCK  •  REPEAT", font=font(25, True), fill=FOREST)
    cta(draw, item.cta)
    return image


def photo_vote_post(item: PlanItem) -> Image.Image:
    image, draw = base_post(item.day, dark=True)
    text_block(draw, (72, 148), "DATE NIGHT:", 58, 900, "#FFFFFF", True)
    text_block(draw, (72, 214), "A, B OR C?", 84, 900, LIME, True)
    paste_photo(image, item.asset_filename, (230, 340, 850, 1093), focus_y=0.0)
    for idx, label in enumerate(("A", "B", "C")):
        x = 255 + idx * 196
        draw.ellipse((x, 365, x + 66, 431), fill=LIME)
        draw.text((x + 22, 373), label, font=font(29, True), fill=INK)
    labels = ("FOREST + CREAM", "NAVY + STONE", "BURGUNDY + CHARCOAL")
    for idx, label in enumerate(labels):
        x = 72 + idx * 312
        draw.rounded_rectangle((x, 1108, x + 290, 1164), radius=18, fill="#FFFFFF")
        draw.text((x + 16, 1122), label, font=font(17, True), fill=INK)
    cta(draw, item.cta, dark=True)
    return image


def photo_budget_post(item: PlanItem) -> Image.Image:
    image, draw = base_post(item.day)
    text_block(draw, (72, 145), "₹1,999 TO LOOK SHARPER", 60, 900, INK, True)
    draw.text((74, 222), "BUY IN THIS ORDER  •  ILLUSTRATIVE BUDGET CAPS", font=font(23, True), fill=CORAL)
    paste_photo(image, item.asset_filename, (72, 292, 1008, 812), focus_y=0.48)
    rows = (
        ("01", "DARK STRAIGHT TROUSER", "₹899 cap"),
        ("02", "HEAVY SOLID TEE", "₹599 cap"),
        ("03", "TEXTURED OVERSHIRT", "₹501 cap"),
    )
    for idx, (number, name, price) in enumerate(rows):
        y = 837 + idx * 103
        draw.rounded_rectangle((72, y, 1008, y + 84), radius=24, fill="#FFFFFF", outline="#D8D8CF", width=2)
        draw.rounded_rectangle((92, y + 13, 152, y + 71), radius=18, fill=LIME if idx == 0 else "#E9EEE4")
        draw.text((108, y + 26), number, font=font(21, True), fill=INK)
        draw.text((178, y + 25), name, font=font(25, True), fill=INK)
        draw.rounded_rectangle((812, y + 14, 984, y + 70), radius=20, fill=FOREST if idx != 1 else "#E7E2D4")
        draw.text((850, y + 28), price, font=font(20, True), fill="#FFFFFF" if idx != 1 else INK)
    cta(draw, item.cta)
    return image


def photo_sneaker_post(item: PlanItem) -> Image.Image:
    image, draw = base_post(item.day, dark=True)
    text_block(draw, (72, 148), "RANK BY USE.", 72, 900, "#FFFFFF", True)
    text_block(draw, (72, 225), "NOT HYPE.", 72, 900, LIME, True)
    paste_photo(image, item.asset_filename, (72, 330, 1008, 920), focus_y=0.48)
    cards = (
        ("NEUTRAL COURT", "VERSATILITY", "9/10"),
        ("RETRO RUNNER", "WALKING", "9/10"),
        ("CHUNKY", "STATEMENT", "8/10"),
    )
    for idx, (name, job, score) in enumerate(cards):
        x = 88 + idx * 304
        draw.rounded_rectangle((x, 605, x + 288, 805), radius=24, fill="#FFFFFF")
        draw.text((x + 18, 643), name, font=font(21, True), fill=INK)
        draw.text((x + 18, 681), f"{job}  •  {score}", font=font(18, True), fill=FOREST)
    draw.rounded_rectangle((72, 952, 1008, 1127), radius=28, fill="#243129")
    draw.text((105, 976), "ONE PAIR FOR THE JOB YOU ACTUALLY DO.", font=font(28, True), fill="#FFFFFF")
    draw.text((105, 1026), "Score versatility, walking comfort and statement value.", font=font(24), fill="#D5DDD7")
    cta(draw, item.cta, dark=True)
    return image


def photo_audit_post(item: PlanItem) -> Image.Image:
    image, draw = base_post(item.day)
    text_block(draw, (72, 145), "PASS THE 5-POINT", 60, 900, INK, True)
    text_block(draw, (72, 212), "WARDROBE AUDIT", 70, 900, FOREST, True)
    paste_photo(image, item.asset_filename, (72, 335, 484, 1084), focus_y=0.42)
    questions = (
        "Creates 3 outfits",
        "Fits my body now",
        "Solves a real gap",
        "Worn 2× a month",
        "Wanted without sale",
    )
    for idx, question in enumerate(questions):
        y = 350 + idx * 132
        draw.rounded_rectangle((516, y, 1008, y + 106), radius=24, fill="#FFFFFF", outline="#D8D8CF", width=2)
        draw.rounded_rectangle((540, y + 25, 594, y + 79), radius=12, outline=FOREST, width=4)
        draw.text((620, y + 32), question, font=font(24, idx in (0, 2)), fill=INK)
    draw.rounded_rectangle((516, 1024, 1008, 1109), radius=24, fill=LIME)
    draw.text((548, 1048), "4 YES = CONSIDER  •  ELSE WAIT 48H", font=font(21, True), fill=INK)
    cta(draw, item.cta)
    return image


POST_BUILDERS: dict[str, Callable[[PlanItem], Image.Image]] = {
    "day01_capsule_formula.png": capsule_post,
    "day03_colour_vote.png": vote_post,
    "day04_budget_priority.png": budget_post,
    "day06_sneaker_scorecard.png": sneaker_post,
    "day07_wardrobe_audit.png": audit_post,
}

PHOTO_POST_BUILDERS: dict[str, Callable[[PlanItem], Image.Image]] = {
    "day01_capsule_formula.png": photo_capsule_post,
    "day03_colour_vote.png": photo_vote_post,
    "day04_budget_priority.png": photo_budget_post,
    "day06_sneaker_scorecard.png": photo_sneaker_post,
    "day07_wardrobe_audit.png": photo_audit_post,
}

ALT_TEXT = {
    "day01_capsule_formula.png": "BudgetFitzz capsule wardrobe graphic showing an overshirt, solid tee and dark trouser as a three-piece system for seven outfits.",
    "day03_colour_vote.png": "Three illustrated date-night outfits labeled A, B and C in forest-cream, navy-stone and burgundy-charcoal combinations.",
    "day04_budget_priority.png": "Receipt-style BudgetFitzz graphic ranking a dark trouser, solid tee and textured overshirt within an illustrative ₹1,999 planning cap.",
    "day06_sneaker_scorecard.png": "Original sneaker silhouettes ranked by versatility, walking comfort and statement value without brand logos.",
    "day07_wardrobe_audit.png": "Five-item wardrobe purchase checklist asking about outfit combinations, fit, gaps, wear frequency and discount influence.",
}

PHOTO_ALT_TEXT = {
    "day01_capsule_formula.png": "Photorealistic flat lay of a textured overshirt, solid tee and dark trouser, presented as a three-piece system for seven outfits.",
    "day03_colour_vote.png": "Three adult Indian men in complete forest-and-cream, navy-and-stone, and burgundy-and-charcoal date-night outfits labeled A, B and C.",
    "day04_budget_priority.png": "Photorealistic flat lay of a dark trouser, solid tee and textured overshirt with an illustrative ₹1,999 purchase-priority breakdown.",
    "day06_sneaker_scorecard.png": "Three unbranded sneaker concepts ranked by versatility, walking comfort and statement value.",
    "day07_wardrobe_audit.png": "A shopper evaluates an overshirt beside a five-item wardrobe purchase checklist.",
}


def generate_posts(plan: list[PlanItem], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    alt_payload: dict[str, str] = {}
    for item in plan:
        if item.format != "post":
            continue
        builder = (
            PHOTO_POST_BUILDERS[item.asset_filename]
            if photo_available(item.asset_filename)
            else POST_BUILDERS[item.asset_filename]
        )
        image = builder(item)
        path = output_dir / item.asset_filename
        uses_hf_photo = photo_available(item.asset_filename)
        description = PHOTO_ALT_TEXT[item.asset_filename] if uses_hf_photo else ALT_TEXT[item.asset_filename]
        info = PngImagePlugin.PngInfo()
        info.add_text("Title", item.hook)
        info.add_text("Description", description)
        info.add_text(
            "Creator",
            "BudgetFitzz deterministic layout with audited Hugging Face photographic layer"
            if uses_hf_photo
            else "BudgetFitzz procedural local pipeline",
        )
        image.save(path, "PNG", pnginfo=info, optimize=True)
        outputs.append(path)
        alt_payload[item.asset_filename] = description
    (output_dir / "alt_text.json").write_text(json.dumps(alt_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return outputs


def video_scene(day: int, title: str, kicker: str, body: str, accent: str, icon: str, index: int, total: int) -> Image.Image:
    image = Image.new("RGB", (1080, 1920), FOREST if index in (0, total-1) else CANVAS)
    draw = ImageDraw.Draw(image)
    dark = index in (0, total-1)
    wordmark(draw, dark, day)
    draw.text((72, 175), kicker.upper(), font=font(28, True), fill=LIME if dark else CORAL)
    y = text_block(draw, (72, 235), title, 78 if len(title) < 28 else 66, 900, "#FFFFFF" if dark else INK, True, 8)
    draw.rounded_rectangle((72, y+42, 1008, y+52), radius=5, fill=LIME if dark else FOREST)
    if icon == "shirt":
        shirt(draw, (280, y+150, 800, y+870), accent, open_front=True)
    elif icon == "fit":
        draw.ellipse((430, y+135, 650, y+355), fill="#DDB18F", outline=INK, width=6)
        shirt(draw, (250, y+330, 830, y+1120), accent)
        draw.line((214, y+425, 316, y+425), fill=CORAL, width=16)
        draw.line((764, y+425, 866, y+425), fill=LIME, width=16)
    elif icon == "check":
        draw.rounded_rectangle((175, y+210, 905, y+900), radius=54, fill="#FFFFFF" if dark else "#E9EFE7")
        draw.line((320, y+565, 455, y+700, 760, y+360), fill=FOREST, width=38, joint="curve")
    if body:
        text_block(draw, (120, 1500), body, 36, 840, "#FFFFFF" if dark else INK, False, 14)
    for i in range(total):
        fill = LIME if i <= index else ("#5D8274" if dark else "#D7DDD5")
        draw.rounded_rectangle((72 + i*110, 1790, 160 + i*110, 1804), radius=7, fill=fill)
    return image


def generate_day02_realistic_overlays(output_dir: Path) -> list[Path]:
    """Create typography-only overlays for the photographic Day 2 footage."""
    output_dir.mkdir(parents=True, exist_ok=True)
    definitions = [
        (
            "ONE OVERSHIRT.",
            "3 SMALL STYLING MOVES",
            "01 / OPEN LAYER",
            "LET THE CREAM TEE STAY VISIBLE.",
        ),
        (
            "BUTTON FOR STRUCTURE.",
            "FIND A CLEANER FRONT LINE",
            "02 / BUTTON",
            "FASTEN LIGHTLY. DON'T PULL THE FABRIC.",
        ),
        (
            "CHECK THE FINISH.",
            "COLLAR • CUFF • HEM",
            "03 / FINAL CHECK",
            "STOP WHEN THE LAYER SITS CLEANLY.",
        ),
    ]
    paths: list[Path] = []
    for index, (title, subtitle, step, takeaway) in enumerate(definitions, start=1):
        image = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 1080, 355), fill=(23, 33, 27, 205))
        draw.rectangle((0, 1385, 1080, 1920), fill=(23, 33, 27, 220))
        wordmark(draw, light=True, day=2)
        draw.text((72, 165), title, font=font(44, True), fill="#FFFFFF")
        draw.text((72, 225), subtitle, font=font(25, True), fill=LIME)
        draw.rounded_rectangle((72, 1460, 350, 1518), radius=22, fill=LIME)
        draw.text((98, 1474), step, font=font(22, True), fill=INK)
        text_block(draw, (72, 1560), takeaway, 40, 900, "#FFFFFF", True, 12)
        draw.text((72, 1812), "@budgetfitzz  •  budget-first style", font=font(22, True), fill="#D8E8DF")
        for progress in range(3):
            fill = LIME if progress < index else "#5D8274"
            draw.rounded_rectangle((72 + progress * 116, 1865, 164 + progress * 116, 1879), radius=7, fill=fill)
        path = output_dir / f"day02_realistic_overlay_{index}.png"
        image.save(path, "PNG", optimize=True)
        paths.append(path)
    return paths


def generate_day05_realistic_overlays(output_dir: Path) -> list[Path]:
    """Create typography-only fit-check overlays for photographic Day 5 footage."""
    output_dir.mkdir(parents=True, exist_ok=True)
    definitions = [
        ("FIT CHECK. NO GUESSING.", "USE THE MIRROR FROM TOP TO BOTTOM", "START / FULL LOOK", "THIS SHOWS A BALANCED FIT. NOT A BEFORE/AFTER."),
        ("CHECK THE SHOULDER LINE.", "THE SLEEVE SEAM SITS NEAR THE SHOULDER", "01 / SHOULDERS", "LOOK FOR A SMOOTH LINE WITHOUT PULLING."),
        ("CHECK THE TEE HEM.", "IT FINISHES CLOSE TO THE WAISTBAND", "02 / TEE LENGTH", "ENOUGH LENGTH TO MOVE. NO EXCESS BUNCHING."),
        ("CHECK THE TROUSER LINE.", "STRAIGHT FALL • CLEAN ANKLE", "03 / TROUSER", "READ THE WHOLE SILHOUETTE BEFORE BUYING."),
    ]
    paths: list[Path] = []
    for index, (title, subtitle, step, takeaway) in enumerate(definitions, start=1):
        image = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 1080, 355), fill=(23, 33, 27, 205))
        draw.rectangle((0, 1385, 1080, 1920), fill=(23, 33, 27, 220))
        wordmark(draw, light=True, day=5)
        draw.text((72, 165), title, font=font(42, True), fill="#FFFFFF")
        draw.text((72, 225), subtitle, font=font(24, True), fill=LIME)
        draw.rounded_rectangle((72, 1460, 410, 1518), radius=22, fill=LIME)
        draw.text((98, 1474), step, font=font(22, True), fill=INK)
        text_block(draw, (72, 1560), takeaway, 40, 900, "#FFFFFF", True, 12)
        draw.text((72, 1812), "@budgetfitzz  •  practical fit guidance", font=font(22, True), fill="#D8E8DF")
        for progress in range(4):
            fill = LIME if progress < index else "#5D8274"
            draw.rounded_rectangle((72 + progress * 116, 1865, 164 + progress * 116, 1879), radius=7, fill=fill)
        path = output_dir / f"day05_realistic_overlay_{index}.png"
        image.save(path, "PNG", optimize=True)
        paths.append(path)
    return paths


def _focus_line(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], width: int = 7) -> None:
    """Draw a high-contrast editorial guide that remains legible over footage."""
    draw.line(points, fill=(10, 18, 13, 210), width=width + 8, joint="curve")
    draw.line(points, fill=LIME, width=width, joint="curve")


def _focus_dot(draw: ImageDraw.ImageDraw, x: int, y: int, radius: int = 15) -> None:
    draw.ellipse((x - radius - 6, y - radius - 6, x + radius + 6, y + radius + 6), fill=(10, 18, 13, 210))
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=LIME)


def _draw_focus_graphic(draw: ImageDraw.ImageDraw, graphic: str) -> None:
    """Illustrate the exact garment detail named by a storyboard beat."""
    if graphic == "open_layer":
        _focus_line(draw, [(425, 520), (480, 825), (455, 1225)])
        _focus_line(draw, [(655, 520), (600, 825), (625, 1225)])
    elif graphic == "button_line":
        _focus_line(draw, [(540, 555), (540, 1240)])
        for y in (735, 885, 1035):
            _focus_dot(draw, 540, y, 11)
    elif graphic == "collar_cuff_hem":
        for x, y in ((540, 505), (790, 1010), (540, 1240)):
            _focus_dot(draw, x, y)
    elif graphic == "silhouette":
        _focus_line(draw, [(315, 475), (285, 475), (285, 1350), (315, 1350)])
        _focus_line(draw, [(765, 475), (795, 475), (795, 1350), (765, 1350)])
    elif graphic == "shoulder_line":
        _focus_line(draw, [(340, 595), (540, 540), (740, 595)])
        _focus_dot(draw, 340, 595)
        _focus_dot(draw, 740, 595)
    elif graphic == "hem_line":
        _focus_line(draw, [(350, 1060), (730, 1060)])
        _focus_line(draw, [(350, 1100), (730, 1100)], width=4)
    elif graphic == "trouser_line":
        _focus_line(draw, [(455, 1005), (465, 1350)])
        _focus_line(draw, [(625, 1005), (615, 1350)])


def generate_agent_video_overlays(brief: dict, output_dir: Path) -> list[Path]:
    """Render transparent, caption-derived overlays from a CreativeDirector brief."""
    output_dir.mkdir(parents=True, exist_ok=True)
    beats = brief.get("beats", [])
    if not beats:
        raise ValueError("Agent video brief has no visual beats")
    day = int(brief["day"])
    paths: list[Path] = []
    for index, beat in enumerate(beats, start=1):
        if int(beat.get("sequence", 0)) != index:
            raise ValueError("Agent video brief beat sequence must be consecutive")
        image = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 1080, 355), fill=(23, 33, 27, 205))
        draw.rectangle((0, 1385, 1080, 1920), fill=(23, 33, 27, 220))
        _draw_focus_graphic(draw, str(beat["focus_graphic"]))
        wordmark(draw, light=True, day=day)
        draw.text((72, 165), str(beat["title"]), font=font(42, True), fill="#FFFFFF")
        draw.text((72, 225), str(beat["subtitle"]), font=font(24, True), fill=LIME)
        draw.rounded_rectangle((72, 1460, 430, 1518), radius=22, fill=LIME)
        draw.text((98, 1474), str(beat["step"]), font=font(22, True), fill=INK)
        text_block(draw, (72, 1560), str(beat["takeaway"]), 40, 900, "#FFFFFF", True, 12)
        draw.text((72, 1812), "@budgetfitzz  /  caption-backed visual", font=font(22, True), fill="#D8E8DF")
        for progress in range(len(beats)):
            fill = LIME if progress < index else "#5D8274"
            draw.rounded_rectangle((72 + progress * 116, 1865, 164 + progress * 116, 1879), radius=7, fill=fill)
        path = output_dir / f"day{day:02d}_agent_overlay_{index}.png"
        image.save(path, "PNG", optimize=True)
        paths.append(path)
    return paths


def generate_video_scenes(plan: list[PlanItem], output_dir: Path) -> dict[str, list[Path]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    scenes: dict[str, list[Path]] = {}
    definitions = {
        "day02_one_shirt_three_ways.mp4": [
            ("ONE OVERSHIRT.", "THREE SMALL MOVES", "Photographic HF footage with local editorial overlays.", LIME, ""),
            ("01 / OPEN", "SHOW THE BASE", "Let the cream tee stay visible.", FOREST, ""),
            ("02 / BUTTON", "ADD STRUCTURE", "Fasten lightly without pulling.", BLUE, ""),
            ("03 / CHECK", "COLLAR • CUFF • HEM", "Stop when the layer sits cleanly.", LIME, ""),
        ],
        "day05_fit_mistakes.mp4": [
            ("FIT CHECK", "TOP TO BOTTOM", "Photographic HF footage with local editorial overlays.", LIME, ""),
            ("01 / SHOULDERS", "SMOOTH LINE", "The sleeve seam sits near the shoulder.", FOREST, ""),
            ("02 / TEE LENGTH", "WAISTBAND", "Enough length without excess bunching.", BLUE, ""),
            ("03 / TROUSER", "STRAIGHT FALL", "Read the whole silhouette before buying.", LIME, ""),
        ],
    }
    for item in plan:
        if item.format != "video":
            continue
        stem = Path(item.asset_filename).stem
        paths: list[Path] = []
        definition = definitions[item.asset_filename]
        for index, (title, kicker, body, accent, icon) in enumerate(definition):
            image = video_scene(item.day, title, kicker, body, accent, icon, index, len(definition))
            path = output_dir / f"{stem}_scene_{index+1}.png"
            image.save(path, "PNG", optimize=True)
            paths.append(path)
        scenes[item.asset_filename] = paths
    return scenes
