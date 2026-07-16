"""Concise exploratory profile for the immutable BudgetFitzz source CSV."""

from __future__ import annotations

import pandas as pd
import numpy as np

PATH = r"C:\Users\bhart\Documents\Task2\data\raw\budgetfitzz_dataset_fixed.csv"

d = pd.read_csv(PATH)
d["engagements"] = d[["likes", "comments", "shares", "saves"]].sum(axis=1)
d["er"] = np.where(d["reach"] > 0, d["engagements"] / d["reach"] * 100, np.nan)
d["save_rate"] = np.where(d["reach"] > 0, d["saves"] / d["reach"] * 100, np.nan)
d["share_rate"] = np.where(d["reach"] > 0, d["shares"] / d["reach"] * 100, np.nan)
d["avg_watch"] = np.where(d["video_views"] > 0, d["watch_time_sec"] / d["video_views"], np.nan)
d["retention"] = np.where(d["video_duration_sec"] > 0, d["avg_watch"] / d["video_duration_sec"] * 100, np.nan)

print("shape", d.shape)
for col in ["format", "pillar", "topic"]:
    print("\n", col)
    print(d[col].value_counts(dropna=False).to_string())
print("\nmissing CTA", int(d["cta"].isna().sum()))
print("date range", d["date"].min(), d["date"].max())
print("aristostyling rows", int(d.astype(str).apply(lambda s: s.str.contains("@aristostyling", case=False, regex=False)).any(axis=1).sum()))
print("video views > reach", int((d["video_views"] > d["reach"]).fillna(False).sum()))
print("\nformat summary")
print(d.groupby("format").agg(n=("id", "size"), median_er=("er", "median"), mean_er=("er", "mean"), median_save=("save_rate", "median"), median_share=("share_rate", "median"), max_er=("er", "max")).to_string())
print("\npillar summary")
print(d.groupby("pillar").agg(n=("id", "size"), median_er=("er", "median"), median_save=("save_rate", "median"), median_share=("share_rate", "median")).sort_values("median_er", ascending=False).to_string())
print("\ntopic summary")
print(d.groupby("topic").agg(n=("id", "size"), median_er=("er", "median"), median_save=("save_rate", "median"), median_share=("share_rate", "median")).sort_values(["n", "median_er"], ascending=[False, False]).to_string())
print("\ntop ER")
print(d.nlargest(10, "er")[["id", "date", "format", "pillar", "topic", "reach", "video_views", "engagements", "er", "avg_watch", "retention"]].to_string(index=False))
print("\nvideo detail")
print(d[d["format"].str.lower().eq("video")][["id", "date", "topic", "reach", "video_views", "engagements", "er", "avg_watch", "retention"]].sort_values("er", ascending=False).to_string(index=False))
