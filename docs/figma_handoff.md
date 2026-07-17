# BudgetFitzz design/frontend handoff

This legacy filename now points to the active Version 11 design contract. The primary design exploration for this revision lives in the private Google Stitch project **BudgetFitzz Social Strategy Workspace**. Earlier Figma work remains separate and was not modified by this revision.

## Frontend counterparts

- Shell: `app/index.html`
- Route renderers and interactions: `app/app.js`
- Tokens: `app/tokens.css`
- Components/layout: `app/styles.css`
- Responsive behavior: `app/responsive.css`
- Generated presentation contract: `app/data/platform_manifest.json`

## Token contract

| Role | CSS variable | Value |
| --- | --- | --- |
| Warm canvas | `--bf-canvas` | `#F7F3EA` |
| Paper surface | `--bf-paper` | `#FFFDF8` |
| Charcoal text | `--bf-ink` | `#1F2621` |
| Forest action | `--bf-forest` | `#496657` |
| Sage support | `--bf-sage` | `#CBD8C7` |
| Terracotta accent | `--bf-terracotta` | `#B65435` |
| Pale-citrus status | `--bf-citrus` | `#DDF58B` |

Headings use Newsreader with Georgia/Times fallbacks; interface and data use Inter with Segoe UI/Arial fallbacks. Controls use 8 px radii, cards 12–16 px, and elevation is primarily a fine border.

## Component mapping

| Design pattern | Browser implementation |
| --- | --- |
| Route rail / bottom navigation | `.app-rail`, `.mobile-nav`, `.sheet-dialog` |
| Evidence/status labels | `.value-kind--*` |
| Observed signals | `.signal-card`, `.metric-card`, `.source-note` |
| Weekly planner | `.week-strip`, `.day-card`, `.plan-detail` |
| Media/caption review | `.studio-gallery`, `.preview-dialog`, `.agent-rationale` |
| Strategy comparison | `.strategy-card`, `.comparison-card` |
| Agent trace | `.agent-flow`, `.agent-node` |
| Validation and package | `.validation-group`, `.file-card` |

## Data rules

The browser reads the generated manifest and performs no metric calculations. Observed values retain sources and sample sizes. Targets and hypotheses use separate labels and colors. Machine-readable formulas remain in `data/processed/metric_contract.json` and are not shown in the website.

See `docs/design/` for Stitch prompts, direction comparison, selected-direction reasoning, design-system notes, responsive rules, screenshots, and visual QA.
