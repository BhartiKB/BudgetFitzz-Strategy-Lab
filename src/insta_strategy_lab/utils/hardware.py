"""Hardware and local-generation capability detection."""

from __future__ import annotations

import importlib.util
import subprocess
import time
from pathlib import Path
from typing import Any


def run_text(command: list[str]) -> tuple[int, str]:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=30)
        return completed.returncode, (completed.stdout + completed.stderr).strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)


def hardware_report(root: Path, video_results: dict[str, Any] | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    _, query = run_text(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"])
    _, full_smi = run_text(["nvidia-smi"])
    ffmpeg_candidates = list((root / "tools" / "ffmpeg").glob("**/bin/ffmpeg.exe"))
    encoder_output = "FFmpeg not installed"
    nvenc_available = False
    if ffmpeg_candidates:
        _, encoder_output = run_text([str(ffmpeg_candidates[0]), "-hide_banner", "-encoders"])
        nvenc_available = "h264_nvenc" in encoder_output
    parts = [part.strip() for part in query.split(",")] if "," in query else []
    try:
        import torch  # type: ignore
        torch_available = True
        torch_cuda = bool(torch.cuda.is_available())
        cuda_version = str(torch.version.cuda)
    except Exception:
        torch_available = False
        torch_cuda = False
        cuda_version = "not installed"
    selected_encoder = (video_results or {}).get("selected_encoder", "pending")
    timings = {
        name: details.get("elapsed_sec")
        for name, details in (video_results or {}).get("videos", {}).items()
    }
    return {
        "gpu_name": parts[0] if len(parts) >= 1 else "Unavailable",
        "vram": parts[1] if len(parts) >= 2 else "Unavailable",
        "driver_version": parts[2] if len(parts) >= 3 else "Unavailable",
        "cuda_driver_available": "CUDA Version" in full_smi,
        "pytorch_installed": torch_available,
        "pytorch_cuda_available": torch_cuda,
        "pytorch_cuda_version": cuda_version,
        "ffmpeg_nvenc_available": nvenc_available,
        "selected_video_encoder": selected_encoder,
        "local_model_device": "CPU deterministic fallback (no compatible cached LLM found)",
        "gpu_used_meaningfully": selected_encoder == "h264_nvenc",
        "generation_timings_sec": timings,
        "detection_duration_sec": round(time.perf_counter() - started, 3),
        "nvidia_smi_output": full_smi,
        "ffmpeg_encoder_evidence": "h264_nvenc listed" if nvenc_available else "h264_nvenc unavailable",
        "dependency_presence": {
            name: bool(importlib.util.find_spec(name))
            for name in ["pandas", "numpy", "PIL", "pydantic", "reportlab", "torch"]
        },
    }

