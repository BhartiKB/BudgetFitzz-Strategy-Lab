"""Dependency-light, publication-ready analytical charts rendered with Pillow."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


BG = "#F6F2E9"
INK = "#17211B"
MUTED = "#627067"
GREEN = "#0F6B4F"
LIME = "#B7F34A"
ORANGE = "#FF7A45"
BLUE = "#4285F4"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "seguisb.ttf" if bold else "segoeui.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (1400, 900), BG)
    return image, ImageDraw.Draw(image)


def header(draw: ImageDraw.ImageDraw, title: str, subtitle: str) -> None:
    draw.text((72, 54), title, font=font(42, True), fill=INK)
    draw.text((72, 112), subtitle, font=font(22), fill=MUTED)
    draw.rounded_rectangle((72, 154, 240, 164), radius=5, fill=LIME)


def footer(draw: ImageDraw.ImageDraw, source: str = "Source: user-provided local evaluation dataset; provenance unspecified.") -> None:
    draw.line((72, 840, 1328, 840), fill="#D6D8CF", width=2)
    draw.text((72, 853), source, font=font(17), fill=MUTED)


def horizontal_bars(
    rows: Iterable[tuple[str, float, int]], title: str, subtitle: str, unit: str,
    output: Path, colors: list[str] | None = None,
) -> None:
    rows = list(rows)
    image, draw = canvas()
    header(draw, title, subtitle)
    max_value = max((value for _, value, _ in rows), default=1) or 1
    top = 215
    gap, bar_h = (78, 38) if len(rows) > 6 else (92, 46)
    for index, (label, value, n) in enumerate(rows[:7]):
        y = top + index * gap
        draw.text((72, y), label[:34], font=font(23, True), fill=INK)
        draw.text((1160, y), f"{value:.2f}{unit}  |  n={n}", font=font(20, True), fill=INK)
        draw.rounded_rectangle((420, y + 5, 1120, y + bar_h), radius=16, fill="#DFE3DA")
        width = max(4, int(700 * value / max_value))
        color = (colors or [GREEN, ORANGE, BLUE, LIME])[index % len(colors or [GREEN, ORANGE, BLUE, LIME])]
        draw.rounded_rectangle((420, y + 5, 420 + width, y + bar_h), radius=16, fill=color)
    draw.text((420, 795), f"Unit: {unit or 'count'}", font=font(18), fill=MUTED)
    footer(draw)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "PNG", optimize=True)


def histogram(values: np.ndarray, title: str, subtitle: str, output: Path) -> None:
    values = values[np.isfinite(values)]
    image, draw = canvas()
    header(draw, title, subtitle)
    counts, edges = np.histogram(values, bins=12)
    plot = (115, 225, 1280, 760)
    draw.line((plot[0], plot[3], plot[2], plot[3]), fill=INK, width=3)
    draw.line((plot[0], plot[1], plot[0], plot[3]), fill=INK, width=3)
    max_count = max(counts) or 1
    width = (plot[2] - plot[0]) / len(counts)
    for i, count in enumerate(counts):
        x0 = int(plot[0] + i * width + 6)
        x1 = int(plot[0] + (i + 1) * width - 6)
        height = int((plot[3] - plot[1] - 20) * count / max_count)
        draw.rounded_rectangle((x0, plot[3] - height, x1, plot[3]), radius=8, fill=GREEN)
        if count:
            draw.text((x0, plot[3] - height - 30), str(int(count)), font=font(16, True), fill=INK)
    draw.text((115, 785), f"Engagement rate by reach (%) | n={len(values)} | full raw distribution retained", font=font(18), fill=MUTED)
    footer(draw)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "PNG", optimize=True)


def heatmap(frame: pd.DataFrame, output: Path) -> None:
    image, draw = canvas()
    header(draw, "Timing map: median engagement rate", "Day-of-week x time bucket; sample count shown in each cell")
    order_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    order_times = ["Morning", "Afternoon", "Evening", "Night", "Late night"]
    grouped = frame.groupby(["day_of_week", "time_of_day"], observed=False)["engagement_rate_by_reach"].agg(["median", "size"])
    medians = grouped["median"].dropna()
    low, high = (float(medians.min()), float(medians.max())) if len(medians) else (0, 1)
    left, top, cell_w, cell_h = 270, 230, 190, 78
    for col, bucket in enumerate(order_times):
        draw.text((left + col * cell_w + 20, 188), bucket, font=font(18, True), fill=INK)
    for row, day in enumerate(order_days):
        draw.text((72, top + row * cell_h + 20), day, font=font(20, True), fill=INK)
        for col, bucket in enumerate(order_times):
            x0, y0 = left + col * cell_w, top + row * cell_h
            if (day, bucket) in grouped.index:
                value = float(grouped.loc[(day, bucket), "median"])
                n = int(grouped.loc[(day, bucket), "size"])
                ratio = 0.5 if high == low else (value - low) / (high - low)
                color = (
                    int(235 - 165 * ratio), int(229 - 95 * ratio), int(210 - 95 * ratio)
                )
                draw.rounded_rectangle((x0 + 4, y0 + 4, x0 + cell_w - 8, y0 + cell_h - 8), radius=13, fill=color)
                text_color = "#FFFFFF" if ratio > 0.58 else INK
                draw.text((x0 + 18, y0 + 14), f"{value:.2f}%", font=font(20, True), fill=text_color)
                draw.text((x0 + 115, y0 + 19), f"n={n}", font=font(15), fill=text_color)
            else:
                draw.rounded_rectangle((x0 + 4, y0 + 4, x0 + cell_w - 8, y0 + cell_h - 8), radius=13, fill="#E8E6DE")
                draw.text((x0 + 60, y0 + 22), "No data", font=font(15), fill=MUTED)
    draw.text((270, 795), "Unit: median engagement rate by reach (%)", font=font(18), fill=MUTED)
    footer(draw)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "PNG", optimize=True)


def missing_matrix(frame: pd.DataFrame, output: Path) -> None:
    missing = frame.isna().sum().sort_values(ascending=False)
    rows = [(str(label), float(value), len(frame)) for label, value in missing.head(10).items()]
    horizontal_bars(rows, "Missing-value profile", f"Top affected columns | dataset n={len(frame)}", "", output, [ORANGE])


def generate_charts(frame: pd.DataFrame, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []

    for filename, group, metric, title, subtitle in [
        ("format_comparison.png", "format", "engagement_rate_by_reach", "Format comparison", "Median engagement rate by reach; mean can be distorted by a video outlier"),
        ("pillar_comparison.png", "pillar", "save_rate", "Pillar comparison", "Median save rate highlights usefulness; sample sizes are not balanced"),
        ("topic_comparison.png", "topic", "engagement_rate_by_reach", "Topic comparison", "Median engagement rate by reach across historical topics"),
        ("hook_comparison.png", "hook_style", "engagement_rate_by_reach", "Hook-style comparison", "Automatically classified hooks; original text remains in the derived dataset"),
        ("cta_comparison.png", "cta_style", "engagement_rate_by_reach", "CTA-style comparison", "Automatically classified calls to action; groups below n=5 are uncertain"),
    ]:
        grouped = frame.groupby(group, dropna=False, observed=False)[metric].agg(["median", "size"]).sort_values("median", ascending=False)
        rows = [(str(index), float(row["median"]), int(row["size"])) for index, row in grouped.iterrows()]
        path = output_dir / filename
        horizontal_bars(rows, title, subtitle, "%", path)
        outputs.append(path)

    mix = frame["pillar"].value_counts()
    path = output_dir / "content_mix.png"
    horizontal_bars([(str(i), float(v), int(v)) for i, v in mix.items()], "Historical content mix", f"Pillar counts and concentration | n={len(frame)}", "", path)
    outputs.append(path)

    path = output_dir / "engagement_distribution.png"
    histogram(frame["engagement_rate_by_reach"].to_numpy(float), "Engagement-rate distribution", f"Raw distribution including outliers | n={len(frame)}", path)
    outputs.append(path)

    save_share = frame.groupby("pillar", observed=False).agg(save_rate=("save_rate", "median"), share_rate=("share_rate", "median"), n=("id", "size"))
    rows = []
    for label, row in save_share.iterrows():
        rows.append((f"{label} saves", float(row["save_rate"]), int(row["n"])))
        rows.append((f"{label} shares", float(row["share_rate"]), int(row["n"])))
    path = output_dir / "save_share.png"
    horizontal_bars(rows, "Save and share behavior", "Median rates by pillar; useful actions are separated from likes", "%", path)
    outputs.append(path)

    video = frame[frame["format"].str.lower().eq("video")].sort_values("retention_proxy", ascending=False)
    rows = [(f"Video ID {int(row.id)}", float(row.retention_proxy), 1) for row in video.itertuples()]
    path = output_dir / "video_retention.png"
    horizontal_bars(rows, "Video retention proxy", f"Average watch time / duration; n={len(video)}; views are plays", "%", path)
    outputs.append(path)

    path = output_dir / "timing_heatmap.png"
    heatmap(frame, path)
    outputs.append(path)

    path = output_dir / "missing_values.png"
    missing_matrix(frame, path)
    outputs.append(path)
    return outputs
