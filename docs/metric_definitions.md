# Metric definitions

Raw columns are immutable; every metric below is appended as a derived column.

- **engagements** = `likes + comments + shares + saves`
- **engagement_rate_by_reach** = `engagements / reach * 100`
- **like_rate** = `likes / reach * 100`
- **comment_rate** = `comments / reach * 100`
- **share_rate** = `shares / reach * 100`
- **save_rate** = `saves / reach * 100`
- **impression_frequency** = `impressions / reach`
- **average_watch_time_sec** = `watch_time_sec / video_views`
- **retention_proxy** = `average_watch_time_sec / video_duration_sec * 100`
- **weighted_engagement_score** = `likes*1 + comments*3 + shares*4 + saves*4`
- **weighted_engagement_rate** = `weighted_engagement_score / reach * 100`

## Rules

- **division**: Return missing when denominator is missing or <= 0.
- **static_video_fields**: Missing video metrics on posts are structural NA, never zero-filled.
- **views**: Video views are plays, not unique people; views may exceed reach.
- **outliers**: Raw outliers are preserved; robust summaries and explicit outlier tables are separate.
- **performance_bands**: Within-format quartiles: weak <= Q1; strong >= Q3; otherwise typical.
- **sample_size_language**: n<3 anecdotal; n=3-4 directional; n>=5 cautious; no observational group is called causal.
