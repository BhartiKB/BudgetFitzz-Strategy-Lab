"""Load the committed, secret-free hybrid-generation configuration.

The file uses JSON syntax, which is also valid YAML, avoiding a new runtime parser
dependency while retaining the requested `.yaml` configuration location.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def load_generation_config(root: Path) -> dict[str, Any]:
    payload = json.loads((root / "config/content_generation.yaml").read_text(encoding="utf-8"))
    generation = payload.setdefault("generation", {})
    generation["default_mode"] = os.environ.get("DEFAULT_GENERATION_MODE", generation.get("default_mode", "MANUAL_PROVIDER"))
    generation["media_budget_inr"] = float(os.environ.get("MEDIA_BUDGET_INR", generation.get("media_budget_inr", 100)))
    veo = payload.setdefault("providers", {}).setdefault("veo", {})
    hf = payload["providers"].setdefault("huggingface", {})
    veo["api_mode_enabled"] = os.environ.get("ENABLE_VEO_API", str(veo.get("api_mode_enabled", False))).lower() == "true"
    hf["api_mode_enabled"] = os.environ.get("ENABLE_HF_API", str(hf.get("api_mode_enabled", True))).lower() == "true"
    return payload
