"""Compose a silent architecture segment from real platform captures and repository code.

The user-provided screen recording is treated as an immutable input.  The segment uses
actual browser captures plus short excerpts from the checked-in manifest, server and UI
loader; it never fabricates an application state or API response.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from insta_strategy_lab.video.generator import ffmpeg_paths, probe_video  # noqa: E402
from insta_strategy_lab.utils.files import write_json  # noqa: E402

WIDTH, HEIGHT, FPS, INSERT_AT, SCENE_SECONDS = 1890, 908, 30, 25, 8
COLORS = {
    "canvas": "#F7F3EA", "paper": "#FFFDF8", "forest": "#1F2621", "ink": "#1C2821",
    "muted": "#66736B", "sage": "#DCE8D5", "line": "#D3D8CE", "citrus": "#B7F43C",
    "terracotta": "#B65435", "code": "#17211B", "code_text": "#E5F2DF",
}


def ui_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    filename = "seguisb.ttf" if bold else "segoeui.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / filename), size)


def mono_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    filename = "consolab.ttf" if bold else "consola.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / filename), size)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def lines_for(path: Path, needle: str, before: int = 2, after: int = 6) -> list[tuple[int, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    index = next((i for i, line in enumerate(lines) if needle in line), None)
    if index is None:
        raise ValueError(f"Could not find {needle!r} in {path.relative_to(ROOT)}")
    start, end = max(0, index - before), min(len(lines), index + after + 1)
    return [(number + 1, lines[number]) for number in range(start, end)]


def fit_image(image_path: Path, box: tuple[int, int, int, int]) -> Image.Image:
    image = Image.open(image_path).convert("RGB")
    width, height = box[2] - box[0], box[3] - box[1]
    return ImageOps.contain(image, (width, height), method=Image.Resampling.LANCZOS)


def caption(draw: ImageDraw.ImageDraw, text: str) -> None:
    x, y, w = 112, 781, WIDTH - 224
    draw.rounded_rectangle((x, y, x + w, y + 90), radius=18, fill=COLORS["forest"])
    draw.text((x + 28, y + 19), text, font=ui_font(27, True), fill="#FFFFFF")


def chrome(draw: ImageDraw.ImageDraw, overline: str, title: str) -> None:
    draw.text((112, 59), "BUDGETFITZZ / EDITORIAL CREATOR ATELIER", font=ui_font(19, True), fill=COLORS["forest"])
    draw.rounded_rectangle((1515, 48, 1776, 82), radius=17, fill=COLORS["sage"])
    draw.text((1540, 57), overline.upper(), font=ui_font(13, True), fill=COLORS["forest"])
    draw.text((112, 120), title, font=ui_font(42, True), fill=COLORS["ink"])


def screenshot_scene(destination: Path, screenshot: Path, overline: str, title: str, text: str) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["canvas"])
    draw = ImageDraw.Draw(image)
    chrome(draw, overline, title)
    x1, y1, x2, y2 = 112, 205, WIDTH - 112, 740
    draw.rounded_rectangle((x1, y1, x2, y2), radius=22, fill=COLORS["paper"], outline=COLORS["line"], width=2)
    screen = fit_image(screenshot, (x1 + 16, y1 + 16, x2 - 16, y2 - 16))
    px = x1 + (x2 - x1 - screen.width) // 2
    py = y1 + (y2 - y1 - screen.height) // 2
    image.paste(screen, (px, py))
    caption(draw, text)
    image.save(destination, "PNG", optimize=True)


def code_scene(destination: Path, source: Path, heading: str, title: str, explanation: str, needle: str) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["canvas"])
    draw = ImageDraw.Draw(image)
    chrome(draw, heading, title)
    x1, y1, x2, y2 = 112, 205, WIDTH - 112, 740
    draw.rounded_rectangle((x1, y1, x2, y2), radius=22, fill=COLORS["code"])
    relative = source.relative_to(ROOT).as_posix()
    draw.rounded_rectangle((x1 + 24, y1 + 22, x1 + 340, y1 + 58), radius=9, fill="#26352A")
    draw.text((x1 + 42, y1 + 30), relative, font=mono_font(16, True), fill=COLORS["citrus"])
    code_lines = lines_for(source, needle)
    y = y1 + 104
    target_line = next(number for number, line in code_lines if needle in line)
    for number, line in code_lines:
        if number == target_line:
            draw.rounded_rectangle((x1 + 55, y - 7, x2 - 54, y + 30), radius=8, fill="#34472E")
        draw.text((x1 + 32, y), f"{number:>3}", font=mono_font(17), fill="#778A7B")
        draw.text((x1 + 112, y), line[:124], font=mono_font(17), fill=COLORS["code_text"])
        y += 46
    caption(draw, explanation)
    image.save(destination, "PNG", optimize=True)


def server_scene(destination: Path) -> None:
    """Show the actual threaded server plus status and allowlisted app-route handling."""
    source = ROOT / "app/server.py"
    source_lines = source.read_text(encoding="utf-8").splitlines()
    chosen = [9, *range(20, 34), *range(59, 66), 88]
    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["canvas"])
    draw = ImageDraw.Draw(image)
    chrome(draw, "03 / python backend", "Approved routes, served safely.")
    x1, y1, x2, y2 = 112, 205, WIDTH - 112, 740
    draw.rounded_rectangle((x1, y1, x2, y2), radius=22, fill=COLORS["code"])
    draw.rounded_rectangle((x1 + 24, y1 + 22, x1 + 270, y1 + 58), radius=9, fill="#26352A")
    draw.text((x1 + 42, y1 + 30), "app/server.py", font=mono_font(16, True), fill=COLORS["citrus"])
    y = y1 + 86
    highlights = {9, 24, 60, 64, 88}
    for number in chosen:
        if number in highlights:
            draw.rounded_rectangle((x1 + 55, y - 4, x2 - 54, y + 22), radius=7, fill="#34472E")
        draw.text((x1 + 32, y), f"{number:>3}", font=mono_font(13), fill="#778A7B")
        draw.text((x1 + 96, y), source_lines[number - 1][:150], font=mono_font(13), fill=COLORS["code_text"])
        y += 23
    caption(draw, "The Python backend serves the application and exposes only approved project outputs.")
    image.save(destination, "PNG", optimize=True)


def manifest_scene(destination: Path, manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    categories = manifest["architecture"]["technical_details"]["output_categories"]
    image = Image.new("RGB", (WIDTH, HEIGHT), COLORS["canvas"])
    draw = ImageDraw.Draw(image)
    chrome(draw, "02 / platform manifest", "One structured content index.")
    x1, y1, x2, y2 = 112, 205, WIDTH - 112, 740
    draw.rounded_rectangle((x1, y1, x2, y2), radius=22, fill=COLORS["paper"], outline=COLORS["line"], width=2)
    draw.text((x1 + 42, y1 + 38), "app/data/platform_manifest.json", font=mono_font(20, True), fill=COLORS["forest"])
    draw.text((x1 + 42, y1 + 87), "Approved categories supplied to the interface", font=ui_font(22), fill=COLORS["muted"])
    for index, item in enumerate(categories):
        col, row = index % 2, index // 2
        x, y = x1 + 42 + col * 790, y1 + 155 + row * 88
        draw.rounded_rectangle((x, y, x + 720, y + 60), radius=13, fill=COLORS["sage"])
        draw.ellipse((x + 18, y + 18, x + 42, y + 42), fill=COLORS["citrus"])
        draw.text((x + 60, y + 17), item, font=ui_font(20, True), fill=COLORS["ink"])
    caption(draw, "The platform manifest acts as the single content index used by the interface.")
    image.save(destination, "PNG", optimize=True)


def run(command: list[str]) -> None:
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode:
        raise RuntimeError(completed.stderr[-4000:])


def encode_segment(ffmpeg: Path, scenes: list[Path], output: Path) -> None:
    command = [str(ffmpeg), "-y", "-hide_banner", "-loglevel", "warning"]
    for scene in scenes:
        command += ["-loop", "1", "-t", str(SCENE_SECONDS), "-i", str(scene)]
    filters = []
    for index in range(len(scenes)):
        filters.append(
            f"[{index}:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0xF7F3EA,setsar=1,fps={FPS},"
            f"fade=t=in:st=0:d=0.35,fade=t=out:st=7.55:d=0.45,setpts=PTS-STARTPTS[v{index}]"
        )
    inputs = "".join(f"[v{i}]" for i in range(len(scenes)))
    command += ["-filter_complex", ";".join([*filters, f"{inputs}concat=n={len(scenes)}:v=1:a=0,format=yuv420p[outv]"]), "-map", "[outv]", "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20", "-b:v", "7M", "-r", str(FPS), "-movflags", "+faststart", str(output)]
    try:
        run(command)
    except RuntimeError:
        fallback = command.copy()
        fallback[fallback.index("h264_nvenc")] = "libx264"
        fallback[fallback.index("p4")] = "medium"
        fallback[fallback.index("-cq")] = "-crf"
        run(fallback)


def assemble(ffmpeg: Path, source: Path, segment: Path, output: Path) -> None:
    graph = (
        f"[0:v]split=2[early][late];"
        f"[early]trim=duration={INSERT_AT},setpts=PTS-STARTPTS[opening];"
        f"[1:v]setpts=PTS-STARTPTS[architecture];"
        f"[late]trim=start={INSERT_AT},setpts=PTS-STARTPTS[walkthrough];"
        "[opening][architecture][walkthrough]concat=n=3:v=1:a=0,format=yuv420p[outv]"
    )
    command = [str(ffmpeg), "-y", "-hide_banner", "-loglevel", "warning", "-i", str(source), "-i", str(segment), "-filter_complex", graph, "-map", "[outv]", "-an", "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20", "-b:v", "9M", "-r", str(FPS), "-movflags", "+faststart", "-metadata", "comment=Silent caption-led architecture walkthrough; no narration or music.", str(output)]
    try:
        run(command)
    except RuntimeError:
        fallback = command.copy()
        fallback[fallback.index("h264_nvenc")] = "libx264"
        fallback[fallback.index("p4")] = "medium"
        fallback[fallback.index("-cq")] = "-crf"
        run(fallback)


def extract_frames(ffmpeg: Path, final_video: Path) -> list[str]:
    directory = ROOT / "docs/demo_frames"
    directory.mkdir(parents=True, exist_ok=True)
    frames = [
        ("architecture_overview.png", INSERT_AT + 4), ("manifest_connection.png", INSERT_AT + 12),
        ("backend_connection.png", INSERT_AT + 20), ("frontend_connection.png", INSERT_AT + 28),
        ("rendered_result.png", INSERT_AT + 36),
    ]
    for name, timestamp in frames:
        run([str(ffmpeg), "-y", "-hide_banner", "-loglevel", "error", "-ss", str(timestamp), "-i", str(final_video), "-frames:v", "1", str(directory / name)])
    return [f"docs/demo_frames/{name}" for name, _ in frames]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Immutable user-provided recording")
    parser.add_argument("--architecture-screen", required=True, help="Actual local Agents-route screenshot")
    parser.add_argument("--home-screen", required=True, help="Actual local Home-route screenshot")
    args = parser.parse_args()
    source, architecture_screen, home_screen = map(Path, (args.source, args.architecture_screen, args.home_screen))
    for path in (source, architecture_screen, home_screen):
        if not path.is_file():
            raise FileNotFoundError(path)
    ffmpeg, ffprobe = ffmpeg_paths(ROOT)
    source_probe = probe_video(ffprobe, source)
    source_hash = sha256(source)
    work = ROOT / "tmp/architecture_walkthrough"
    work.mkdir(parents=True, exist_ok=True)
    scenes = [work / f"scene_{number:02}.png" for number in range(1, 6)]
    screenshot_scene(scenes[0], architecture_screen, "01 / architecture", "How the platform connects.", "The frontend is driven by outputs generated by the analytical and agent pipeline.")
    manifest_scene(scenes[1], ROOT / "app/data/platform_manifest.json")
    server_scene(scenes[2])
    code_scene(scenes[3], ROOT / "app/app.js", "04 / frontend loading", "Render from the generated source.", "Frontend JavaScript loads the generated outputs instead of relying on manually typed dashboard values.", "platform_manifest.json")
    screenshot_scene(scenes[4], home_screen, "05 / rendered result", "A current workspace state.", "When pipeline outputs change, the interface can render the updated project state from the same structured source.")
    segment = work / "architecture_segment.mp4"
    encode_segment(ffmpeg, scenes, segment)
    output = ROOT / "submission/final/platform_walkthrough.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)
    assemble(ffmpeg, source, segment, output)
    named_output = ROOT / "deploy/budgetfitzz_platform_walkthrough_with_architecture.mp4"
    named_output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output, named_output)
    final_probe = probe_video(ffprobe, output)
    frames = extract_frames(ffmpeg, output)
    source_hash_after = sha256(source)
    if source_hash != source_hash_after:
        raise RuntimeError("The immutable source recording changed during composition")
    segment_duration = len(scenes) * SCENE_SECONDS
    metadata = {
        "source_filename": source.name,
        "source_sha256": source_hash,
        "source_duration_seconds": float(source_probe["format"]["duration"]),
        "insertion_at_seconds": INSERT_AT,
        "architecture_segment_seconds": segment_duration,
        "output": "submission/final/platform_walkthrough.mp4",
        "deployment_copy": "deploy/budgetfitzz_platform_walkthrough_with_architecture.mp4",
        "audio": "No audio stream by design: silent, caption-led, no narration, TTS, or music.",
        "validation_frames": frames,
        "probe": final_probe,
    }
    write_json(ROOT / "logs/architecture_walkthrough.json", metadata)
    (ROOT / "docs/walkthrough_architecture_update.md").write_text(
        "# Walkthrough architecture update\n\n"
        f"The immutable source recording `{source.name}` is preserved and is not overwritten. "
        f"Its SHA-256 was verified before and after composition: `{source_hash}`.\n\n"
        f"A {segment_duration}-second silent, caption-led architecture section is inserted after {INSERT_AT} seconds. "
        "It uses captured local application states, current manifest categories, and concise excerpts from `app/server.py` and `app/app.js`. "
        "There is deliberately no audio stream, voice narration, text-to-speech, or music.\n\n"
        f"The final file is `submission/final/platform_walkthrough.mp4`; the deployment copy is `{named_output.relative_to(ROOT).as_posix()}`. "
        "Representative frames are in `docs/demo_frames/`. Full probe metadata is stored in `logs/architecture_walkthrough.json`.\n",
        encoding="utf-8",
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
