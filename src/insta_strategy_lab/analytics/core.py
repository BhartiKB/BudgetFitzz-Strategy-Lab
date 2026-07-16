"""Deterministic data audit, metric contract, robust comparisons, and evidence extraction."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from insta_strategy_lab.schemas import Evidence
from insta_strategy_lab.utils.files import write_json


REQUIRED_COLUMNS = [
    "id", "date", "format", "topic", "pillar", "hook", "caption", "cta", "post_time",
    "reach", "impressions", "likes", "comments", "shares", "saves", "video_views",
    "watch_time_sec", "video_duration_sec",
]

METRIC_CONTRACT: dict[str, Any] = {
    "version": "1.0.0",
    "source_policy": "Raw columns are immutable; every metric below is appended as a derived column.",
    "metrics": {
        "engagements": "likes + comments + shares + saves",
        "engagement_rate_by_reach": "engagements / reach * 100",
        "like_rate": "likes / reach * 100",
        "comment_rate": "comments / reach * 100",
        "share_rate": "shares / reach * 100",
        "save_rate": "saves / reach * 100",
        "impression_frequency": "impressions / reach",
        "average_watch_time_sec": "watch_time_sec / video_views",
        "retention_proxy": "average_watch_time_sec / video_duration_sec * 100",
        "weighted_engagement_score": "likes*1 + comments*3 + shares*4 + saves*4",
        "weighted_engagement_rate": "weighted_engagement_score / reach * 100",
    },
    "rules": {
        "division": "Return missing when denominator is missing or <= 0.",
        "static_video_fields": "Missing video metrics on posts are structural NA, never zero-filled.",
        "views": "Video views are plays, not unique people; views may exceed reach.",
        "outliers": "Raw outliers are preserved; robust summaries and explicit outlier tables are separate.",
        "performance_bands": "Within-format quartiles: weak <= Q1; strong >= Q3; otherwise typical.",
        "sample_size_language": "n<3 anecdotal; n=3-4 directional; n>=5 cautious; no observational group is called causal.",
    },
}


def safe_rate(numerator: pd.Series, denominator: pd.Series, multiplier: float = 1.0) -> pd.Series:
    denominator = pd.to_numeric(denominator, errors="coerce")
    numerator = pd.to_numeric(numerator, errors="coerce")
    return pd.Series(np.where(denominator > 0, numerator / denominator * multiplier, np.nan), index=numerator.index)


def classify_hook(text: Any) -> str:
    value = str(text or "").strip().lower()
    if "?" in value or re.match(r"^(which|what|why|how|can|are|do|would)\b", value):
        return "Question"
    if re.search(r"\b\d+\b|top\s+\d|ways|mistakes|rules|steps", value):
        return "List / specificity"
    if any(token in value for token in ("stop", "don't", "never", "wrong", "avoid", "secret")):
        return "Contrarian / tension"
    if any(token in value for token in ("rich", "aura", "premium", "glow", "attractive", "aesthetic")):
        return "Aspirational"
    if any(token in value for token in ("guide", "read caption", "try these", "combo", "under")):
        return "Direct utility"
    if any(token in value for token in (">>>", "vibe", "energy", "men in", "outfits on men")):
        return "Emotional / social"
    return "Other"


def classify_cta(text: Any) -> str:
    if pd.isna(text) or not str(text).strip():
        return "Missing"
    value = str(text).lower()
    if "link" in value:
        return "Link-request comment"
    if any(token in value for token in ("save", "share", "send")):
        return "Save / share"
    if any(token in value for token in ("comment", "choose", "vote", "tell us", "pick")):
        return "Community comment"
    if "follow" in value:
        return "Follow"
    if any(token in value for token in ("dm", "profile", "bio")):
        return "Profile / DM"
    return "Other"


def confidence_label(n: int) -> str:
    if n < 3:
        return "anecdotal"
    if n < 5:
        return "directional"
    return "cautious"


def trimmed_mean(values: np.ndarray, proportion: float = 0.1) -> float:
    values = np.sort(values[np.isfinite(values)])
    if not len(values):
        return math.nan
    trim = int(len(values) * proportion)
    if trim * 2 >= len(values):
        return float(np.mean(values))
    return float(np.mean(values[trim : len(values) - trim]))


def winsorized_mean(values: np.ndarray, proportion: float = 0.05) -> float:
    values = values[np.isfinite(values)]
    if not len(values):
        return math.nan
    low, high = np.quantile(values, [proportion, 1 - proportion])
    return float(np.mean(np.clip(values, low, high)))


def bootstrap_median_ci(values: np.ndarray, seed: int = 4050, samples: int = 2000) -> tuple[float, float]:
    values = values[np.isfinite(values)]
    if len(values) < 2:
        value = float(values[0]) if len(values) else math.nan
        return value, value
    rng = np.random.default_rng(seed + len(values))
    draws = rng.choice(values, size=(samples, len(values)), replace=True)
    medians = np.median(draws, axis=1)
    return tuple(float(x) for x in np.quantile(medians, [0.025, 0.975]))


def apply_metric_contract(raw: pd.DataFrame) -> pd.DataFrame:
    frame = raw.copy(deep=True)
    frame["date_parsed"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["post_hour"] = pd.to_datetime(frame["post_time"], format="%H:%M", errors="coerce").dt.hour
    frame["day_of_week"] = frame["date_parsed"].dt.day_name()
    frame["time_of_day"] = pd.cut(
        frame["post_hour"], [-1, 5, 11, 16, 20, 23],
        labels=["Late night", "Morning", "Afternoon", "Evening", "Night"],
    ).astype("string")
    frame["hook_style"] = frame["hook"].map(classify_hook)
    frame["cta_style"] = frame["cta"].map(classify_cta)
    frame["engagements"] = frame[["likes", "comments", "shares", "saves"]].sum(axis=1)
    frame["engagement_rate_by_reach"] = safe_rate(frame["engagements"], frame["reach"], 100)
    for name, source in (("like_rate", "likes"), ("comment_rate", "comments"), ("share_rate", "shares"), ("save_rate", "saves")):
        frame[name] = safe_rate(frame[source], frame["reach"], 100)
    frame["impression_frequency"] = safe_rate(frame["impressions"], frame["reach"])
    frame["average_watch_time_sec"] = safe_rate(frame["watch_time_sec"], frame["video_views"])
    frame["retention_proxy"] = safe_rate(frame["average_watch_time_sec"], frame["video_duration_sec"], 100)
    frame["weighted_engagement_score"] = frame["likes"] + 3 * frame["comments"] + 4 * frame["shares"] + 4 * frame["saves"]
    frame["weighted_engagement_rate"] = safe_rate(frame["weighted_engagement_score"], frame["reach"], 100)
    frame["views_exceed_reach"] = (frame["video_views"] > frame["reach"]).fillna(False)

    bands = pd.Series(index=frame.index, dtype="string")
    for _, indices in frame.groupby(frame["format"].str.lower()).groups.items():
        values = frame.loc[indices, "engagement_rate_by_reach"]
        q1, q3 = values.quantile([0.25, 0.75])
        bands.loc[indices] = np.select([values <= q1, values >= q3], ["weak", "strong"], default="typical")
    frame["performance_band"] = bands
    return frame


def audit_dataset(raw: pd.DataFrame) -> dict[str, Any]:
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(raw.columns))
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    dates = pd.to_datetime(raw["date"], errors="coerce")
    string_rows = raw.astype(str).apply(lambda col: col.str.contains("@aristostyling", case=False, regex=False)).any(axis=1)
    return {
        "rows": int(len(raw)),
        "columns": int(len(raw.columns)),
        "date_min": dates.min().date().isoformat(),
        "date_max": dates.max().date().isoformat(),
        "span_days": int((dates.max() - dates.min()).days),
        "duplicate_rows": int(raw.duplicated().sum()),
        "duplicate_ids": int(raw["id"].duplicated().sum()),
        "invalid_dates": int(dates.isna().sum()),
        "missing_by_column": {key: int(value) for key, value in raw.isna().sum().items()},
        "format_counts": {key: int(value) for key, value in raw["format"].value_counts().items()},
        "pillar_counts": {key: int(value) for key, value in raw["pillar"].value_counts().items()},
        "topic_counts": {key: int(value) for key, value in raw["topic"].value_counts().items()},
        "negative_numeric_values": int((raw.select_dtypes(include="number") < 0).sum().sum()),
        "zero_reach": int((raw["reach"] <= 0).sum()),
        "impressions_below_reach": int((raw["impressions"] < raw["reach"]).sum()),
        "aristostyling_rows": int(string_rows.sum()),
        "provenance": "User-provided local evaluation dataset; original provenance unspecified.",
    }


def group_summary(frame: pd.DataFrame, group: str, metric: str = "engagement_rate_by_reach") -> pd.DataFrame:
    rows = []
    for label, part in frame.groupby(group, dropna=False, observed=False):
        values = pd.to_numeric(part[metric], errors="coerce").dropna().to_numpy(float)
        low, high = bootstrap_median_ci(values)
        rows.append({
            group: "Missing" if pd.isna(label) else str(label),
            "n": int(len(part)),
            "valid_n": int(len(values)),
            "median": float(np.median(values)) if len(values) else math.nan,
            "q1": float(np.quantile(values, 0.25)) if len(values) else math.nan,
            "q3": float(np.quantile(values, 0.75)) if len(values) else math.nan,
            "mean": float(np.mean(values)) if len(values) else math.nan,
            "trimmed_mean": trimmed_mean(values),
            "winsorized_mean": winsorized_mean(values),
            "bootstrap_median_ci_low": low,
            "bootstrap_median_ci_high": high,
            "sample_note": confidence_label(len(part)),
        })
    return pd.DataFrame(rows).sort_values(["n", "median"], ascending=[False, False])


def detect_outliers(frame: pd.DataFrame) -> pd.DataFrame:
    records = []
    metrics = ["reach", "impressions", "engagements", "engagement_rate_by_reach", "video_views", "retention_proxy"]
    for format_name, group in frame.groupby("format"):
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce").dropna()
            if len(values) < 4:
                continue
            q1, q3 = values.quantile([0.25, 0.75])
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            for index in values[(values < lower) | (values > upper)].index:
                records.append({
                    "id": int(frame.loc[index, "id"]), "format": format_name, "metric": metric,
                    "value": float(frame.loc[index, metric]), "lower_fence": float(lower),
                    "upper_fence": float(upper), "treatment": "Preserved in raw; robust summaries reported separately",
                })
    return pd.DataFrame(records).drop_duplicates(["id", "metric"]).sort_values(["metric", "value"], ascending=[True, False])


def analyze_dataset(raw_csv: Path, processed_dir: Path, analysis_dir: Path) -> dict[str, Any]:
    raw = pd.read_csv(raw_csv)
    audit = audit_dataset(raw)
    frame = apply_metric_contract(raw)
    processed_dir.mkdir(parents=True, exist_ok=True)
    (analysis_dir / "tables").mkdir(parents=True, exist_ok=True)
    raw.to_csv(processed_dir / "budgetfitzz_clean.csv", index=False)
    frame.to_csv(processed_dir / "budgetfitzz_derived.csv", index=False)
    write_json(processed_dir / "metric_contract.json", METRIC_CONTRACT)
    write_json(analysis_dir / "dataset_audit.json", audit)

    summaries: dict[str, list[dict[str, Any]]] = {}
    for group in ["format", "pillar", "topic", "hook", "hook_style", "cta", "cta_style", "post_hour", "time_of_day", "day_of_week"]:
        summary = group_summary(frame, group)
        summary.to_csv(analysis_dir / "tables" / f"{group}_summary.csv", index=False)
        summaries[group] = summary.replace({np.nan: None}).to_dict(orient="records")

    outliers = detect_outliers(frame)
    outliers.to_csv(analysis_dir / "tables" / "outliers.csv", index=False)
    missing = raw.isna().sum().rename("missing_count").to_frame()
    missing["missing_pct"] = missing["missing_count"] / len(raw) * 100
    missing.to_csv(analysis_dir / "tables" / "missing_values.csv")

    format_summary = group_summary(frame, "format").set_index("format")
    pillar_summary = group_summary(frame, "pillar").set_index("pillar")
    video = frame[frame["format"].str.lower().eq("video")]
    video_without_extreme = video.drop(index=video["engagement_rate_by_reach"].idxmax())
    promotion_share = float((frame["pillar"] == "Promotion").mean() * 100)
    post_share = float((frame["format"] == "post").mean() * 100)
    top_two_topic_share = float(frame["topic"].value_counts().head(2).sum() / len(frame) * 100)
    video_median_er = float(format_summary.loc["video", "median"])
    post_median_er = float(format_summary.loc["post", "median"])
    promo_median_save = float(frame.loc[frame["pillar"] == "Promotion", "save_rate"].median())
    edu_median_save = float(frame.loc[frame["pillar"] == "Education", "save_rate"].median())
    video_median_retention = float(video["retention_proxy"].median())
    extreme = frame.loc[video["engagement_rate_by_reach"].idxmax()]

    evidence = [
        Evidence(evidence_id="E01", finding="The baseline is overwhelmingly promotional.", metric="promotion_share_pct", value=round(promotion_share, 1), comparison=f"{audit['pillar_counts']['Promotion']} of {len(frame)} items", sample_size=len(frame), confidence="robust", source="data/processed/budgetfitzz_derived.csv"),
        Evidence(evidence_id="E02", finding="Static posts dominate the tested format mix.", metric="post_share_pct", value=round(post_share, 1), comparison=f"{audit['format_counts']['post']} posts vs {audit['format_counts']['video']} videos", sample_size=len(frame), confidence="robust", source="data/processed/budgetfitzz_derived.csv"),
        Evidence(evidence_id="E03", finding="Education is associated with materially stronger save behavior than promotion.", metric="median_save_rate_pct", value=round(edu_median_save, 3), comparison=f"Education {edu_median_save:.3f}% vs Promotion {promo_median_save:.3f}% (2.2x directional lift)", sample_size=int((frame['pillar'] == 'Education').sum()), confidence="cautious", source="analysis/tables/pillar_summary.csv"),
        Evidence(evidence_id="E04", finding="Video median engagement is only slightly above post median engagement.", metric="median_engagement_rate_pct", value=round(video_median_er, 3), comparison=f"Video {video_median_er:.3f}% (n=13) vs post {post_median_er:.3f}% (n=137)", sample_size=len(video), confidence="cautious", source="analysis/tables/format_summary.csv"),
        Evidence(evidence_id="E05", finding="A single video makes the video mean misleading.", metric="extreme_video_engagement_rate_pct", value=round(float(extreme['engagement_rate_by_reach']), 3), comparison=f"ID {int(extreme['id'])}; video mean {video['engagement_rate_by_reach'].mean():.3f}% vs {video_without_extreme['engagement_rate_by_reach'].mean():.3f}% without it", sample_size=len(video), confidence="cautious", source="analysis/tables/outliers.csv"),
        Evidence(evidence_id="E06", finding="Topic selection is highly concentrated.", metric="top_two_topic_share_pct", value=round(top_two_topic_share, 1), comparison="Outfit Ideas + Budget Finds", sample_size=len(frame), confidence="robust", source="analysis/tables/topic_summary.csv"),
        Evidence(evidence_id="E07", finding="CTA hygiene and brand consistency need repair.", metric="missing_cta_count", value=int(raw['cta'].isna().sum()), comparison=f"14 missing CTAs; {audit['aristostyling_rows']} rows reference @aristostyling", sample_size=len(frame), confidence="robust", source="analysis/dataset_audit.json"),
        Evidence(evidence_id="E08", finding="Video views are plays rather than unique users.", metric="views_exceed_reach_count", value=int(frame['views_exceed_reach'].sum()), comparison=f"{int(frame['views_exceed_reach'].sum())} of {len(video)} videos have views above reach", sample_size=len(video), confidence="cautious", source="data/processed/budgetfitzz_derived.csv"),
        Evidence(evidence_id="E09", finding="Existing videos leave room for stronger retention design.", metric="median_retention_proxy_pct", value=round(video_median_retention, 1), comparison="Median across 13 videos; proxy based on aggregate watch time / plays / duration", sample_size=len(video), confidence="cautious", source="data/processed/budgetfitzz_derived.csv"),
    ]
    evidence_payload = [item.model_dump() for item in evidence]
    write_json(analysis_dir / "evidence.json", evidence_payload)

    results = {
        "audit": audit,
        "summaries": summaries,
        "evidence": evidence_payload,
        "verified_facts": {
            "record_count": len(frame), "post_count": audit["format_counts"]["post"],
            "video_count": audit["format_counts"]["video"], "promotion_share_pct": promotion_share,
            "post_share_pct": post_share, "missing_cta_count": int(raw["cta"].isna().sum()),
            "top_two_topic_share_pct": top_two_topic_share, "aristostyling_rows": audit["aristostyling_rows"],
            "video_views_exceed_reach_count": int(frame["views_exceed_reach"].sum()),
            "post_median_er_pct": post_median_er, "video_median_er_pct": video_median_er,
            "video_mean_er_pct": float(video["engagement_rate_by_reach"].mean()),
            "video_mean_er_without_extreme_pct": float(video_without_extreme["engagement_rate_by_reach"].mean()),
            "extreme_video_er_pct": float(extreme["engagement_rate_by_reach"]),
            "extreme_video_id": int(extreme["id"]),
            "education_median_save_rate_pct": edu_median_save,
            "promotion_median_save_rate_pct": promo_median_save,
            "video_median_retention_proxy_pct": video_median_retention,
        },
    }
    write_json(analysis_dir / "analysis_results.json", results)
    return results
