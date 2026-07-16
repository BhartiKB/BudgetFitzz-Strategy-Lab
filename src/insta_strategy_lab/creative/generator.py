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
        draw.rounded_rectangle((895, 50, 1008, 96), radius=22, fill=LIME)
        draw.text((921, 57), f"DAY {day}", font=font(19, True), fill=INK)


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


POST_BUILDERS: dict[str, Callable[[PlanItem], Image.Image]] = {
    "day01_capsule_formula.png": capsule_post,
    "day03_colour_vote.png": vote_post,
    "day04_budget_priority.png": budget_post,
    "day06_sneaker_scorecard.png": sneaker_post,
    "day07_wardrobe_audit.png": audit_post,
}

ALT_TEXT = {
    "day01_capsule_formula.png": "BudgetFitzz capsule wardrobe graphic showing an overshirt, solid tee and dark trouser as a three-piece system for seven outfits.",
    "day03_colour_vote.png": "Three illustrated date-night outfits labeled A, B and C in forest-cream, navy-stone and burgundy-charcoal combinations.",
    "day04_budget_priority.png": "Receipt-style BudgetFitzz graphic ranking a dark trouser, solid tee and textured overshirt within an illustrative ₹1,999 planning cap.",
    "day06_sneaker_scorecard.png": "Original sneaker silhouettes ranked by versatility, walking comfort and statement value without brand logos.",
    "day07_wardrobe_audit.png": "Five-item wardrobe purchase checklist asking about outfit combinations, fit, gaps, wear frequency and discount influence.",
}


def generate_posts(plan: list[PlanItem], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    alt_payload: dict[str, str] = {}
    for item in plan:
        if item.format != "post":
            continue
        builder = POST_BUILDERS[item.asset_filename]
        image = builder(item)
        path = output_dir / item.asset_filename
        info = PngImagePlugin.PngInfo()
        info.add_text("Title", item.hook)
        info.add_text("Description", ALT_TEXT[item.asset_filename])
        info.add_text("Creator", "BudgetFitzz procedural local pipeline")
        image.save(path, "PNG", pnginfo=info, optimize=True)
        outputs.append(path)
        alt_payload[item.asset_filename] = ALT_TEXT[item.asset_filename]
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


def generate_video_scenes(plan: list[PlanItem], output_dir: Path) -> dict[str, list[Path]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    scenes: dict[str, list[Path]] = {}
    definitions = {
        "day02_one_shirt_three_ways.mp4": [
            ("ONE SHIRT.", "FIRST-SECOND HOOK", "Office to date in 10 seconds.", LIME, "shirt"),
            ("01 / COMMUTE", "TEE + OPEN LAYER", "Easy movement. Clean neutral base.", FOREST, "shirt"),
            ("02 / OFFICE", "BUTTON + TROUSER", "Quiet palette. Sharper structure.", BLUE, "shirt"),
            ("SAVE THE 3 SWAPS", "TRY IT TONIGHT", "@budgetfitzz  •  budget-first style", LIME, "check"),
        ],
        "day05_fit_mistakes.mp4": [
            ("STOP BLAMING THE SHIRT", "FIT CHECK", "Fix these three mistakes first.", LIME, "fit"),
            ("01 / SHOULDER", "SEAM AT THE EDGE", "Too low makes the whole top collapse.", FOREST, "fit"),
            ("02 / TROUSER BREAK", "ONE CLEAN LINE", "Heavy stacking shortens the silhouette.", BLUE, "fit"),
            ("SCREENSHOT THE CHECKS", "FIX ONE TODAY", "@budgetfitzz  •  practical fit guidance", LIME, "check"),
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
