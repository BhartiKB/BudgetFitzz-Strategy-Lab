"""Motion-graphics video generation with NVENC and libx264 fallback."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from insta_strategy_lab.creative import generate_day02_realistic_overlays, generate_day05_realistic_overlays


def ffmpeg_paths(root: Path) -> tuple[Path, Path]:
    candidates = list((root / "tools" / "ffmpeg").glob("**/bin/ffmpeg.exe"))
    probes = list((root / "tools" / "ffmpeg").glob("**/bin/ffprobe.exe"))
    if not candidates or not probes:
        raise FileNotFoundError("Project-local FFmpeg/ffprobe build is missing")
    # Prefer FFmpeg 7.1: it targets NVENC API 13.0 and is compatible with the installed 581.86 driver.
    candidates.sort(key=lambda path: ("n7.1" not in str(path), str(path)))
    probes.sort(key=lambda path: ("n7.1" not in str(path), str(path)))
    return candidates[0], probes[0]


def probe_video(ffprobe: Path, path: Path) -> dict[str, Any]:
    command = [
        str(ffprobe), "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_name,width,height,avg_frame_rate,pix_fmt",
        "-of", "json", str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    return json.loads(completed.stdout)


def encode_video(ffmpeg: Path, scenes: list[Path], output: Path, encoder: str) -> tuple[bool, str, float]:
    command = [str(ffmpeg), "-y", "-hide_banner", "-loglevel", "warning"]
    for scene in scenes:
        # A still image is one input frame; zoompan expands it to exactly 90 frames (3 s at 30 fps).
        command.extend(["-i", str(scene)])
    filters = []
    for index in range(len(scenes)):
        filters.append(
            f"[{index}:v]scale=1080:1920,zoompan="
            f"z='min(zoom+0.00045,1.04)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d=90:s=1080x1920:fps=30,fade=t=in:st=0:d=0.18,fade=t=out:st=2.72:d=0.28,"
            f"setpts=PTS-STARTPTS[v{index}]"
        )
    concat_inputs = "".join(f"[v{i}]" for i in range(len(scenes)))
    filters.append(f"{concat_inputs}concat=n={len(scenes)}:v=1:a=0,format=yuv420p[outv]")
    command.extend(["-filter_complex", ";".join(filters), "-map", "[outv]"])
    if encoder == "h264_nvenc":
        command.extend(["-c:v", encoder, "-preset", "p4", "-tune", "hq", "-rc", "vbr", "-cq", "20", "-b:v", "5M", "-maxrate", "9M"])
    else:
        command.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "19"])
    command.extend(["-r", "30", "-movflags", "+faststart", "-metadata", "comment=Generated locally at INR 0; no copyrighted music", str(output)])
    started = time.perf_counter()
    completed = subprocess.run(command, capture_output=True, text=True)
    elapsed = time.perf_counter() - started
    return completed.returncode == 0, completed.stderr[-4000:], elapsed


def encode_ai_assisted_video(
    ffmpeg: Path,
    hook_scene: Path,
    source_video: Path,
    cta_scene: Path,
    output: Path,
    encoder: str,
) -> tuple[bool, str, float]:
    """Combine branded local cards with a user-approved promotional-credit clip."""
    command = [
        str(ffmpeg), "-y", "-hide_banner", "-loglevel", "warning",
        "-i", str(hook_scene), "-i", str(source_video), "-i", str(cta_scene),
    ]
    filters = [
        "[0:v]scale=1080:1920,zoompan="
        "z='min(zoom+0.00045,1.04)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        "d=75:s=1080x1920:fps=30,fade=t=out:st=2.3:d=0.2,setpts=PTS-STARTPTS,setsar=1[v0]",
        "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,fps=30,fade=t=in:st=0:d=0.18,fade=t=out:st=4.82:d=0.2,"
        "setpts=PTS-STARTPTS,setsar=1[v1]",
        "[2:v]scale=1080:1920,zoompan="
        "z='min(zoom+0.00035,1.03)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        "d=75:s=1080x1920:fps=30,fade=t=in:st=0:d=0.18,setpts=PTS-STARTPTS,setsar=1[v2]",
        "[v0][v1][v2]concat=n=3:v=1:a=0,format=yuv420p[outv]",
    ]
    command.extend(["-filter_complex", ";".join(filters), "-map", "[outv]"])
    if encoder == "h264_nvenc":
        command.extend([
            "-c:v", encoder, "-preset", "p4", "-tune", "hq", "-rc", "vbr",
            "-cq", "20", "-b:v", "5M", "-maxrate", "9M",
        ])
    else:
        command.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "19"])
    command.extend([
        "-r", "30", "-movflags", "+faststart",
        "-metadata", "comment=HF promotional-credit source; locally composited; cash cost INR 0",
        str(output),
    ])
    started = time.perf_counter()
    completed = subprocess.run(command, capture_output=True, text=True)
    elapsed = time.perf_counter() - started
    return completed.returncode == 0, completed.stderr[-4000:], elapsed


def encode_photographic_hf_video(
    ffmpeg: Path,
    source_video: Path,
    overlays: list[Path],
    output: Path,
    encoder: str,
) -> tuple[bool, str, float]:
    """Build a continuous photographic sequence with timed editorial overlays."""
    duration = 10 / len(overlays)
    command = [
        str(ffmpeg), "-y", "-hide_banner", "-loglevel", "warning",
        "-stream_loop", "-1", "-i", str(source_video),
    ]
    for overlay in overlays:
        command.extend(["-loop", "1", "-framerate", "30", "-i", str(overlay)])
    filters: list[str] = [
        "[0:v]trim=duration=10,setpts=PTS-STARTPTS,"
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        "fps=30,setsar=1[base]"
    ]
    for index in range(len(overlays)):
        filters.append(
            f"[{index + 1}:v]trim=duration=10,setpts=PTS-STARTPTS,"
            f"scale=1080:1920,format=rgba[overlay{index}]"
        )
    current = "base"
    for index in range(len(overlays)):
        start = index * duration
        end = (index + 1) * duration
        output_label = "outv" if index == len(overlays) - 1 else f"stage{index}"
        filters.append(
            f"[{current}][overlay{index}]overlay=shortest=0:"
            f"enable='gte(t,{start:.3f})*lt(t,{end:.3f})'[{output_label}]"
        )
        current = output_label
    filters.append("[outv]format=yuv420p[final]")
    command.extend(["-filter_complex", ";".join(filters), "-map", "[final]", "-t", "10"])
    if encoder == "h264_nvenc":
        command.extend([
            "-c:v", encoder, "-preset", "p4", "-tune", "hq", "-rc", "vbr",
            "-cq", "20", "-b:v", "5M", "-maxrate", "9M",
        ])
    else:
        command.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "19"])
    command.extend([
        "-r", "30", "-movflags", "+faststart",
        "-metadata", "comment=Photographic HF promotional-credit source; locally caption-composited; cash cost INR 0",
        str(output),
    ])
    started = time.perf_counter()
    completed = subprocess.run(command, capture_output=True, text=True)
    elapsed = time.perf_counter() - started
    return completed.returncode == 0, completed.stderr[-4000:], elapsed


def extract_frame(ffmpeg: Path, video: Path, output: Path) -> None:
    subprocess.run(
        [str(ffmpeg), "-y", "-hide_banner", "-loglevel", "error", "-ss", "6.2", "-i", str(video), "-frames:v", "1", str(output)],
        check=True,
    )


def generate_videos(root: Path, scene_map: dict[str, list[Path]], output_dir: Path, frame_dir: Path) -> dict[str, Any]:
    ffmpeg, ffprobe = ffmpeg_paths(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    frame_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {"ffmpeg": str(ffmpeg), "selected_encoder": "h264_nvenc", "videos": {}}
    for filename, scenes in scene_map.items():
        output = output_dir / filename
        hf_sources = {
            "day02_one_shirt_three_ways.mp4": root / "assets/source_media/day02_hf_wan.mp4",
            "day05_fit_mistakes.mp4": root / "assets/source_media/day05_hf_wan.mp4",
        }
        hf_source = hf_sources.get(filename)
        uses_hf_source = hf_source is not None and hf_source.exists()
        if uses_hf_source:
            overlays = (
                generate_day02_realistic_overlays(frame_dir)
                if filename == "day02_one_shirt_three_ways.mp4"
                else generate_day05_realistic_overlays(frame_dir)
            )
            ok, error, elapsed = encode_photographic_hf_video(
                ffmpeg, hf_source, overlays, output, "h264_nvenc"
            )
        else:
            ok, error, elapsed = encode_video(ffmpeg, scenes, output, "h264_nvenc")
        encoder = "h264_nvenc"
        if not ok:
            if uses_hf_source:
                ok, fallback_error, elapsed = encode_photographic_hf_video(
                    ffmpeg, hf_source, overlays, output, "libx264"
                )
            else:
                ok, fallback_error, elapsed = encode_video(ffmpeg, scenes, output, "libx264")
            error = f"NVENC failed: {error}\nFallback: {fallback_error}"
            encoder = "libx264"
            results["selected_encoder"] = "libx264"
        if not ok:
            raise RuntimeError(f"Video encoding failed for {filename}: {error}")
        frame_path = frame_dir / f"{Path(filename).stem}_preview.png"
        extract_frame(ffmpeg, output, frame_path)
        results["videos"][filename] = {
            "encoder": encoder,
            "elapsed_sec": round(elapsed, 3),
            "probe": probe_video(ffprobe, output),
            "preview_frame": str(frame_path.relative_to(root)).replace("\\", "/"),
            "scenes": [str(path.relative_to(root)).replace("\\", "/") for path in scenes],
            "source_video": (
                str(hf_source.relative_to(root)).replace("\\", "/") if uses_hf_source else None
            ),
            "photographic_overlays": (
                [str(path.relative_to(root)).replace("\\", "/") for path in overlays]
                if uses_hf_source else []
            ),
            "cash_cost_inr": 0,
        }
    return results
