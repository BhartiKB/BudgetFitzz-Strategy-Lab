"""Create a truthful walkthrough MP4 from actual application screenshots."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from insta_strategy_lab.video.generator import ffmpeg_paths, probe_video  # noqa: E402
from insta_strategy_lab.utils.files import write_json  # noqa: E402


def font(size: int, bold: bool = False):
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / ("seguisb.ttf" if bold else "segoeui.ttf")), size)


def title_card(path: Path, title: str, subtitle: str) -> None:
    image = Image.new("RGB", (1920, 1080), "#1F2621")
    draw = ImageDraw.Draw(image)
    draw.text((110, 96), "BUDGETFITZZ / EDITORIAL CREATOR ATELIER", font=font(30, True), fill="#DDF58B")
    draw.text((110, 340), title, font=font(86, True), fill="#FFFFFF")
    draw.text((114, 455), subtitle, font=font(34), fill="#CBD8C7")
    draw.rounded_rectangle((110, 820, 1810, 830), radius=5, fill="#B65435")
    draw.text((110, 870), "Actual local platform states • no mock interface", font=font(24, True), fill="#FFFFFF")
    image.save(path, "PNG", optimize=True)


def main() -> None:
    screenshot_dir = ROOT / "tmp/demo_screens"
    screenshots = sorted(screenshot_dir.glob("*.png"))
    if len(screenshots) < 4:
        raise SystemExit("At least four actual application screenshots are required in tmp/demo_screens")
    title = screenshot_dir / "00_title.png"
    end = screenshot_dir / "99_end.png"
    title_card(title, "Evidence to editorial action.", "A manifest-driven creator workspace walkthrough")
    title_card(end, "Validated. Packaged. Ready.", "5 posts • 2 videos • INR 0 direct paid spend")
    inputs = [title, *screenshots, end]
    # Avoid recursively including generated cards when rerun.
    ordered = []
    seen = set()
    for item in inputs:
        if item not in seen:
            ordered.append(item); seen.add(item)
    ffmpeg, ffprobe = ffmpeg_paths(ROOT)
    output = ROOT / "submission/final/platform_walkthrough.mp4"
    command = [str(ffmpeg), "-y", "-hide_banner", "-loglevel", "warning"]
    for path in ordered:
        command += ["-loop", "1", "-t", "4", "-i", str(path)]
    filters = []
    for index in range(len(ordered)):
        filters.append(
            f"[{index}:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x17211B,"
            f"setsar=1,fps=30,fade=t=in:st=0:d=0.3,fade=t=out:st=3.6:d=0.4,"
            f"setpts=PTS-STARTPTS[v{index}]"
        )
    concat = "".join(f"[v{i}]" for i in range(len(ordered)))
    filters.append(f"{concat}concat=n={len(ordered)}:v=1:a=0,format=yuv420p[outv]")
    command += ["-filter_complex", ";".join(filters), "-map", "[outv]", "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20", "-b:v", "5M", "-r", "30", "-movflags", "+faststart", str(output)]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        fallback = command.copy()
        fallback[fallback.index("h264_nvenc")] = "libx264"
        fallback[fallback.index("p4")] = "veryfast"
        fallback[fallback.index("-cq")] = "-crf"
        completed = subprocess.run(fallback, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr)
    write_json(ROOT / "logs/demo_video_probe.json", probe_video(ffprobe, output))
    print(output)


if __name__ == "__main__":
    main()
