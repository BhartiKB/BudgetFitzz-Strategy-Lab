"""Evidence-linked diagnosis, revised strategy, and exact seven-day content plan."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from insta_strategy_lab.schemas import PlanItem


def build_failure_diagnosis(results: dict[str, Any]) -> dict[str, Any]:
    facts = results["verified_facts"]
    return {
        "selected_diagnosis": (
            "The failed baseline is best explained by content-system imbalance: 90% promotional and "
            "91.3% static output concentrated in two topics, reinforced by repetitive or missing CTAs. "
            "The issue is not that every promotion underperformed; rather, the mix left too little room "
            "for the educational, saveable, community, and retention-led formats that can build repeat demand."
        ),
        "hypothesis_result": "Supported with qualification",
        "support": ["E01", "E02", "E03", "E06", "E07", "E09"],
        "counterevidence": [
            f"Promotion median engagement remains close to the overall median, so promotion is not intrinsically ineffective.",
            f"Video median engagement ({facts['video_median_er_pct']:.2f}%) is only slightly above post median ({facts['post_median_er_pct']:.2f}%).",
            "The community pillar has only two observations and is anecdotal, not proof of superiority.",
        ],
        "outlier_caveat": (
            f"The video mean is {facts['video_mean_er_pct']:.2f}% but falls to "
            f"{facts['video_mean_er_without_extreme_pct']:.2f}% after removing one extreme video. "
            "This is directional evidence for testing video, not a causal claim."
        ),
        "decision": "Shift from promotion-first repetition to a balanced, value-first test portfolio while preserving two commercial slots.",
    }


def build_strategy(results: dict[str, Any]) -> dict[str, Any]:
    facts = results["verified_facts"]
    changes = [
        {
            "finding": "Promotion occupies 90.0% of the baseline.", "evidence": "E01",
            "interpretation": "The brand asks for action more often than it earns attention through utility.",
            "strategy_change": "Cap promotional/value-first commercial items at 2 of 7; allocate 3 education and 2 community items.",
            "expected_behavioural_effect": "More saves, shares, repeat visits, and higher-quality comments.",
            "success_metric": "Pillar mix compliance; education median save rate; qualitative comment coding.",
            "confidence_or_limitation": "Strong concentration evidence; performance effect remains a forward test.",
        },
        {
            "finding": f"Education median save rate is {facts['education_median_save_rate_pct']:.3f}% vs promotion {facts['promotion_median_save_rate_pct']:.3f}%.", "evidence": "E03",
            "interpretation": "Useful explanations appear more saveable, though education has only 13 records.",
            "strategy_change": "Make the takeaway visible on-frame: formulas, checklists, comparisons, and avoidable mistakes.",
            "expected_behavioural_effect": "Users can understand and save the value without opening a long caption.",
            "success_metric": "Save rate target 0.45-0.70% on education posts.",
            "confidence_or_limitation": "Cautious association; no causal attribution.",
        },
        {
            "finding": "Posts are 91.3% of the baseline; video has n=13 and one extreme outlier.", "evidence": "E02,E04,E05",
            "interpretation": "Video is under-tested and its mean is unreliable, but the format deserves controlled trials.",
            "strategy_change": "Use exactly two short videos with first-second hooks, 3-scene pacing, captions, and explicit end cards.",
            "expected_behavioural_effect": "Improved watch-through and more interpretable retention data.",
            "success_metric": f"Retention proxy target 60-70% vs observed median {facts['video_median_retention_proxy_pct']:.1f}%.",
            "confidence_or_limitation": "Directional; views are plays and not unique reach.",
        },
        {
            "finding": "Outfit Ideas and Budget Finds account for 66.7% of all records.", "evidence": "E06",
            "interpretation": "Repeated topic territory limits discovery and audience learning.",
            "strategy_change": "Add wardrobe systems, fit diagnosis, colour voting, and wardrobe-audit topics while retaining familiar commercial anchors.",
            "expected_behavioural_effect": "Broader reasons to save, share, and return.",
            "success_metric": "No topic repeated more than twice in the seven-day cycle.",
            "confidence_or_limitation": "Concentration is certain; audience response must be tested.",
        },
        {
            "finding": "Fourteen CTAs are missing and two rows use @aristostyling.", "evidence": "E07",
            "interpretation": "CTA and handle inconsistency reduce measurement clarity and brand trust.",
            "strategy_change": "Use one primary CTA per asset, rotate save/share/vote/link-request intents, and standardize @budgetfitzz.",
            "expected_behavioural_effect": "Cleaner attribution and less repetitive comment bait.",
            "success_metric": "100% CTA coverage; 0 wrong-handle occurrences; at least 4 CTA styles across 7 items.",
            "confidence_or_limitation": "Direct quality-control fix; behavioral lift is a hypothesis.",
        },
    ]
    return {
        "objective": "Increase qualified saves, shares, profile actions, link-request comments, and repeat audience growth by making BudgetFitzz immediately useful.",
        "audience_focus": "Delhi NCR men aged about 18-30: college students, early-career professionals, and budget-sensitive style explorers (assumed context).",
        "value_proposition": "Practical Indian menswear decisions that look considered without overspending.",
        "content_mix": {"Education": 3, "Value-first commercial": 2, "Community": 2},
        "format_mix": {"post": 5, "video": 2},
        "format_rules": ["Posts must deliver a complete takeaway on-frame.", "Videos use a first-second hook, three meaningful scenes, readable captions, and a CTA end card."],
        "hook_principles": ["Promise a specific outcome.", "Use numbers or tension only when the body pays it off.", "Lead with the decision the audience needs to make."],
        "cta_principles": ["One primary action per item.", "Rotate save, share, vote, audit, and link-request intents.", "Never use a wrong account handle."],
        "posting_time_guidance": "Treat historical timing as exploratory because cells are uneven. Start with 19:15-21:00 IST for interaction-led items and 12:30-13:15 IST for quick utility, then measure by comparable pillar/format.",
        "visual_identity": "Warm off-white editorial canvas, deep forest ink, electric lime utility highlights, coral commercial accents, modular cards, and original garment geometry.",
        "video_retention_rules": ["Hook visible by frame 1.", "New visual idea every 2.5-4 seconds.", "No caption line over 8 words.", "Final CTA card remains visible for at least 1.5 seconds."],
        "community_rules": ["Ask bounded questions people can answer quickly.", "Respond using a reusable comment taxonomy: preference, fit problem, budget intent, and link intent."],
        "promotion_limit": "Maximum 2 of 7 items; every commercial item must teach a selection rule before presenting the product shortlist.",
        "experimentation_plan": "Run this as a seven-day pilot. Pre-register item-level primary KPI, compare only within format/pillar, retain raw outliers, and review median plus quartiles after the cycle.",
        "measurement_framework": ["Engagement rate by reach", "Save rate", "Share rate", "Comment quality", "Average watch time", "Retention proxy", "Profile actions", "Link-request comments", "Pillar balance", "Publishing consistency"],
        "evidence_linked_changes": changes,
    }


def build_plan(start: date | None = None) -> list[PlanItem]:
    start = start or date(2026, 7, 17)
    raw = [
        {
            "format": "post", "content_pillar": "Education", "topic": "Three-piece wardrobe formula",
            "target_audience_segment": "College students building a first versatile wardrobe",
            "hook": "3 pieces. 7 clean fits. No wardrobe haul.",
            "content_idea": "Show one overshirt, one solid tee, and one dark trouser as a repeatable outfit system.",
            "visual_direction": "Editorial capsule grid with original overshirt, tee, and trouser illustrations; lime numbered chips.",
            "caption_direction": "Teach the formula, list swaps, and normalize repeating clothes.",
            "full_proposed_caption": "A bigger wardrobe is not the same as a better wardrobe. Start with one textured overshirt, one solid tee and one dark straight-fit trouser. Wear the tee alone, layer the overshirt, switch the tuck, roll the sleeves, or swap in clean sneakers. That is already a week of useful combinations. Build systems before you buy more. Save this for your next wardrobe reset. Follow @budgetfitzz for practical style that respects your budget.",
            "cta": "Save this 3-piece formula before your next purchase.",
            "recommended_publication_time": "19:30 IST", "baseline_insight": "E01 + E03: education is scarce but has a 2.2x higher median save rate than promotion.",
            "primary_kpi": "Save rate", "secondary_kpi": "Share rate", "reasoned_target_range": "Save rate 0.50-0.70%; share rate 0.15-0.25% (targets, not observed results).",
            "asset_filename": "day01_capsule_formula.png", "generation_prompt_or_template_reference": "PROMPT-POST-01 / capsule-grid",
        },
        {
            "format": "video", "content_pillar": "Education", "topic": "One shirt, three situations",
            "target_audience_segment": "Early-career men moving between commute, office, and evening plans",
            "hook": "One overshirt. Commute to evening in 10 seconds.",
            "content_idea": "Use one forest textured overshirt, cream tee, and straight dark trouser across commute, office, and evening styling moves.",
            "visual_direction": "Three all-photographic vertical scenes from the approved HF footage, with editorial captions and no illustrated garments.",
            "caption_direction": "Emphasize versatility and fit choices instead of constant buying.",
            "full_proposed_caption": "One textured overshirt can carry a commute, office and evening plan without a full outfit swap. Scene 1: keep it open over a cream tee and straight dark trouser for the commute. Scene 2: button it and clean up the cuff for work. Scene 3: open it back up and keep the same quiet palette for the evening. Save the three styling moves, then try them with what you already own. Follow @budgetfitzz for budget-first menswear systems.",
            "cta": "Save the three transitions and test one tonight.",
            "recommended_publication_time": "20:15 IST", "baseline_insight": "E02 + E05 + E09: video is under-tested; mean performance is outlier-driven and median retention is about 55%.",
            "primary_kpi": "Retention proxy", "secondary_kpi": "Saves per reach", "reasoned_target_range": "Retention proxy 62-70%; engagement rate 6.5-8.0% (targets).",
            "asset_filename": "day02_one_shirt_three_ways.mp4", "generation_prompt_or_template_reference": "PROMPT-VIDEO-01 / three-scene-swap",
        },
        {
            "format": "post", "content_pillar": "Community", "topic": "Colour-combo vote",
            "target_audience_segment": "Followers who want quick feedback before a date or college event",
            "hook": "Date night: A, B or C? Pick one.",
            "content_idea": "Three original outfit colourways with a bounded vote and one-line styling rationale.",
            "visual_direction": "Three side-by-side illustrated outfits labeled A/B/C with high-contrast vote footer.",
            "caption_direction": "Invite a low-friction vote and ask respondents to name their setting.",
            "full_proposed_caption": "You have one evening plan and three clean options. A: forest + cream for a warm, relaxed look. B: navy + stone for the safest smart-casual balance. C: burgundy + charcoal when you want more contrast. Comment A, B or C and tell us whether it is a café, dinner or college event. We will reply with the best shoe colour. Follow @budgetfitzz for useful outfit decisions, not random hauls.",
            "cta": "Comment A, B or C plus the occasion.",
            "recommended_publication_time": "20:30 IST", "baseline_insight": "E01 + E06: only two community items exist and topic territory is concentrated.",
            "primary_kpi": "Qualified comment rate", "secondary_kpi": "Share rate", "reasoned_target_range": "Qualified comments 1.2-2.0% of reach; share rate 0.15-0.25% (targets; community baseline is anecdotal).",
            "asset_filename": "day03_colour_vote.png", "generation_prompt_or_template_reference": "PROMPT-POST-02 / abc-vote",
        },
        {
            "format": "post", "content_pillar": "Value-first commercial", "topic": "₹1,999 college upgrade",
            "target_audience_segment": "Price-sensitive college students with a fixed monthly clothing budget",
            "hook": "₹1,999 to look sharper: buy in this order.",
            "content_idea": "Teach a prioritized basket: trouser first, solid tee second, overshirt third; show budget guardrails without claiming live prices.",
            "visual_direction": "Receipt-inspired priority stack with original garment drawings and price-cap labels marked as illustrative targets.",
            "caption_direction": "Give a decision rule before a link-request CTA; label price examples as budget targets.",
            "full_proposed_caption": "If your upgrade budget is ₹1,999, do not split it across five weak pieces. Priority 1: one dark straight-fit trouser because it fixes the base of more outfits. Priority 2: one heavyweight solid tee in white, stone or black. Priority 3: only if money remains, add an overshirt. The displayed amounts are planning caps, not live product prices. Comment LINK only if you want a shortlist that follows this order. Follow @budgetfitzz for value-first recommendations.",
            "cta": "Comment LINK for a shortlist built around the ₹1,999 cap.",
            "recommended_publication_time": "13:00 IST", "baseline_insight": "E01 + E07: retain commercial intent but make it useful and replace repetitive link bait with one explicit, qualified CTA.",
            "primary_kpi": "Link-request comment rate", "secondary_kpi": "Save rate", "reasoned_target_range": "Link-request comments 0.8-1.5% of reach; save rate 0.35-0.55% (targets).",
            "asset_filename": "day04_budget_priority.png", "generation_prompt_or_template_reference": "PROMPT-POST-03 / priority-receipt",
        },
        {
            "format": "video", "content_pillar": "Education", "topic": "Three fit mistakes",
            "target_audience_segment": "Men whose outfits feel off despite buying current trends",
            "hook": "Stop blaming the shirt. Fix these 3 fit mistakes.",
            "content_idea": "Animate before/after silhouettes for shoulder seam, trouser break, and top-to-bottom proportion.",
            "visual_direction": "Fast red-to-green fit corrections, one concept per scene, end card with screenshot cue.",
            "caption_direction": "Diagnose fit in plain language and avoid product dependence.",
            "full_proposed_caption": "Most outfits look off for three fixable reasons. One: the shoulder seam falls too far down your arm. Two: the trouser stacks heavily over the shoe. Three: the top and bottom are both oversized, so the shape disappears. Fix one variable at a time before buying another trend. Screenshot the checklist, test it in the mirror, and share it with the friend who keeps blaming his wardrobe. Follow @budgetfitzz for practical fit guidance.",
            "cta": "Screenshot the three checks and fix one today.",
            "recommended_publication_time": "20:00 IST", "baseline_insight": "E03 + E09: education is more saveable and current video retention leaves room for faster, explicit progression.",
            "primary_kpi": "Retention proxy", "secondary_kpi": "Share rate", "reasoned_target_range": "Retention proxy 60-68%; share rate 0.20-0.35% (targets).",
            "asset_filename": "day05_fit_mistakes.mp4", "generation_prompt_or_template_reference": "PROMPT-VIDEO-02 / before-after-fix",
        },
        {
            "format": "post", "content_pillar": "Value-first commercial", "topic": "Sneaker use-case ranking",
            "target_audience_segment": "First-job professionals choosing one versatile shoe",
            "hook": "One sneaker budget? Rank by use, not hype.",
            "content_idea": "Rank neutral court, retro runner, and chunky sneaker by versatility, comfort, and outfit compatibility without using brand logos.",
            "visual_direction": "Original sneaker silhouettes on a three-row scorecard; coral highlights for trade-offs.",
            "caption_direction": "Make the purchase framework the main value; product links are optional follow-up.",
            "full_proposed_caption": "If you can buy one pair, rank the job before the hype. Neutral court sneaker: best for maximum outfit compatibility. Retro runner: best when walking comfort matters most. Chunky sneaker: strongest statement, but the least flexible with smart-casual trousers. Score your week across college or office, walking time and dress code before choosing. Comment SHOES if you want a no-logo shortlist by use case and budget. Follow @budgetfitzz for practical buying filters.",
            "cta": "Comment SHOES with your budget and daily use case.",
            "recommended_publication_time": "12:45 IST", "baseline_insight": "E06: Sneaker Review has only five records while two topics dominate; test adjacent commercial utility.",
            "primary_kpi": "Qualified link-intent comments", "secondary_kpi": "Save rate", "reasoned_target_range": "Qualified comments 0.7-1.3% of reach; save rate 0.35-0.55% (targets).",
            "asset_filename": "day06_sneaker_scorecard.png", "generation_prompt_or_template_reference": "PROMPT-POST-04 / use-case-scorecard",
        },
        {
            "format": "post", "content_pillar": "Community", "topic": "Wardrobe audit checklist",
            "target_audience_segment": "Returning followers ready to reduce impulse purchases",
            "hook": "Before Sunday checkout: pass this 5-point audit.",
            "content_idea": "A saveable checklist asking whether a purchase creates three outfits, fits now, and replaces a real gap.",
            "visual_direction": "Large checkboxes, lime pass/fail band, open space, and a comment prompt for the hardest rule.",
            "caption_direction": "Close the week with reflection, audience input, and a measurable follow-up habit.",
            "full_proposed_caption": "Before you check out, ask five things. Can I build three outfits with pieces I own? Does it fit my body now? Does it solve a real wardrobe gap? Will I wear it at least twice a month? Would I still want it without the discount label? Four yes answers means consider it. Three or fewer means wait 48 hours. Save the audit and comment the rule that saves you the most money. Follow @budgetfitzz for a smarter budget wardrobe.",
            "cta": "Save the audit and comment your hardest rule.",
            "recommended_publication_time": "19:15 IST", "baseline_insight": "E01 + E03 + E07: close with useful community interaction instead of another generic promotion or missing CTA.",
            "primary_kpi": "Save rate", "secondary_kpi": "Qualified comment rate", "reasoned_target_range": "Save rate 0.50-0.75%; qualified comments 0.8-1.5% of reach (targets).",
            "asset_filename": "day07_wardrobe_audit.png", "generation_prompt_or_template_reference": "PROMPT-POST-05 / checklist-audit",
        },
    ]
    items = []
    for index, item in enumerate(raw, start=1):
        items.append(PlanItem(day=index, date=(start + timedelta(days=index - 1)).isoformat(), **item))
    formats = [item.format for item in items]
    if len(items) != 7 or formats.count("post") != 5 or formats.count("video") != 2:
        raise ValueError("Plan contract violated: exactly seven items, five posts and two videos are required")
    return items
