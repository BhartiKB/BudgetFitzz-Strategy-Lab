"""Agent-backed, machine-readable video storyboards.

The ContentPlanner supplies the claim and caption.  The CreativeDirector turns
those claims into bounded visual beats that can be checked before rendering.
"""

from __future__ import annotations

from typing import Any

from insta_strategy_lab.schemas import PlanItem


def _beat(
    sequence: int,
    *,
    title: str,
    subtitle: str,
    step: str,
    takeaway: str,
    caption_evidence: str,
    source_window_sec: tuple[float, float],
    zoom: float,
    crop_y: int,
    focus_graphic: str,
) -> dict[str, Any]:
    return {
        "sequence": sequence,
        "duration_sec": 2.5,
        "title": title,
        "subtitle": subtitle,
        "step": step,
        "takeaway": takeaway,
        "caption_evidence": caption_evidence,
        "source_window_sec": list(source_window_sec),
        "zoom": zoom,
        "crop_y": crop_y,
        "focus_graphic": focus_graphic,
    }


def _day_two(item: PlanItem) -> dict[str, Any]:
    beats = [
        _beat(
            1,
            title="ONE OVERSHIRT.",
            subtitle="KEEP THE BASE LAYER VISIBLE",
            step="01 / OPEN LAYER",
            takeaway="LET THE CREAM TEE FRAME THE OUTFIT.",
            caption_evidence="wear it open",
            source_window_sec=(0.9, 2.15),
            zoom=1.08,
            crop_y=45,
            focus_graphic="open_layer",
        ),
        _beat(
            2,
            title="BUTTON FOR STRUCTURE.",
            subtitle="WATCH THE FRONT LINE",
            step="02 / BUTTON",
            takeaway="FASTEN LIGHTLY. DON'T PULL THE FABRIC.",
            caption_evidence="button it lightly",
            source_window_sec=(0.0, 1.25),
            zoom=1.18,
            crop_y=80,
            focus_graphic="button_line",
        ),
        _beat(
            3,
            title="CHECK THE FINISH.",
            subtitle="COLLAR / CUFF / HEM",
            step="03 / FINAL CHECK",
            takeaway="STOP WHEN THE LAYER SITS CLEANLY.",
            caption_evidence="check the collar, cuff and hem",
            source_window_sec=(2.8, 4.05),
            zoom=1.08,
            crop_y=55,
            focus_graphic="collar_cuff_hem",
        ),
    ]
    for beat in beats:
        beat["duration_sec"] = round(10 / len(beats), 6)
    return _brief(item, "assets/source_media/day02_hf_wan.mp4", beats)


def _day_five(item: PlanItem) -> dict[str, Any]:
    beats = [
        _beat(
            1,
            title="START WITH THE WHOLE FIT.",
            subtitle="READ THE SILHOUETTE FIRST",
            step="START / FULL LOOK",
            takeaway="THIS IS A MIRROR CHECKLIST, NOT A TRANSFORMATION.",
            caption_evidence="mirror checklist",
            source_window_sec=(3.65, 4.9),
            zoom=1.0,
            crop_y=0,
            focus_graphic="silhouette",
        ),
        _beat(
            2,
            title="CHECK THE SHOULDER LINE.",
            subtitle="FIND THE SLEEVE SEAM",
            step="01 / SHOULDER",
            takeaway="THE SEAM SHOULD SIT NEAR THE SHOULDER.",
            caption_evidence="sleeve seam sits near the shoulder",
            source_window_sec=(0.0, 1.25),
            zoom=1.22,
            crop_y=0,
            focus_graphic="shoulder_line",
        ),
        _beat(
            3,
            title="CHECK THE TEE HEM.",
            subtitle="COMPARE IT WITH THE WAISTBAND",
            step="02 / TEE HEM",
            takeaway="ENOUGH LENGTH TO MOVE. NO EXCESS BUNCHING.",
            caption_evidence="tee hem finishes close to the waistband",
            source_window_sec=(1.25, 2.5),
            zoom=1.22,
            crop_y=190,
            focus_graphic="hem_line",
        ),
        _beat(
            4,
            title="FOLLOW THE TROUSER LINE.",
            subtitle="STRAIGHT FALL TO A CLEAN ANKLE",
            step="03 / TROUSER",
            takeaway="READ THE LINE ALL THE WAY TO THE SHOE.",
            caption_evidence="follow the trouser line down to a clean ankle and shoe",
            source_window_sec=(2.5, 3.75),
            zoom=1.14,
            crop_y=265,
            focus_graphic="trouser_line",
        ),
    ]
    return _brief(item, "assets/source_media/day05_hf_wan.mp4", beats)


def _brief(item: PlanItem, source_video: str, beats: list[dict[str, Any]]) -> dict[str, Any]:
    caption = item.full_proposed_caption.lower()
    missing = [beat["caption_evidence"] for beat in beats if beat["caption_evidence"].lower() not in caption]
    if missing:
        raise ValueError(f"Video storyboard contains claims absent from the ContentPlanner caption: {missing}")
    return {
        "day": item.day,
        "asset_filename": item.asset_filename,
        "source_video": source_video,
        "content_planner_inputs": {
            "topic": item.topic,
            "hook": item.hook,
            "content_idea": item.content_idea,
            "visual_direction": item.visual_direction,
            "caption_direction": item.caption_direction,
            "full_proposed_caption": item.full_proposed_caption,
            "cta": item.cta,
            "baseline_insight": item.baseline_insight,
        },
        "creative_director_decision": {
            "approach": "caption-first editorial demonstration",
            "why": (
                "Each visual beat quotes a claim from the approved caption, uses a matching source-time "
                "window, and adds a restrained garment callout. The renderer does not ask one generic "
                "loop to represent several unrelated actions."
            ),
            "realism_rules": [
                "Preserve the photographic person and garment source.",
                "Use reframing and typography; do not synthesize new anatomy locally.",
                "Show only a detail that is visible in the selected source window.",
                "Treat the fit guidance as a checklist, not a fabricated before-and-after.",
            ],
        },
        "beats": beats,
    }


def build_video_generation_briefs(plan: list[PlanItem]) -> dict[str, Any]:
    """Build and validate exactly two caption-derived video storyboards."""
    videos = {item.day: item for item in plan if item.format == "video"}
    if set(videos) != {2, 5}:
        raise ValueError(f"Expected video plan days 2 and 5, received {sorted(videos)}")
    briefs = [_day_two(videos[2]), _day_five(videos[5])]
    return {
        "schema_version": "1.0",
        "generated_by": ["ContentPlannerAgent", "CreativeDirectorAgent"],
        "briefs": briefs,
    }
