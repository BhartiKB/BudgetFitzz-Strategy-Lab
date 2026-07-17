# Version 11 visual QA report

QA target: `http://127.0.0.1:8501/app/index.html`

## Route sweep

All nine routes were opened in the live local browser at 1280 px. Each produced one visible route heading, the correct active navigation item, zero broken images, no page-level horizontal overflow, and no console warnings/errors.

| Route | Expected primary content | Result |
| --- | --- | --- |
| Home | Diagnosis hero, four sourced signals, seven-item strip | Pass |
| Insights | Data quality, observed metrics, charts, robust tables | Pass |
| Diagnosis | Supported statement, evidence IDs, caveat, counterevidence | Pass |
| Strategy | Evidence-linked changes and observed/proposed comparison | Pass |
| Content Plan | Seven days, exactly five posts/two videos, detail selector | Pass |
| Studio | Seven local assets, filters, caption/CTA preview dialog | Pass |
| Agents | Concise decision trace, timing, tool, retry and evidence | Pass |
| Validation | Grouped production checks and score | Pass |
| Submission | Five live file records and operational status | Pass |

## Responsive checks

| Width | Checks | Result |
| --- | --- | --- |
| 1440 | Fixed rail, evidence hero, four-signal row, no overflow | Pass |
| 1280 | Full route rail, seven-day selector, media/detail split | Pass |
| 768 | Rail collapses, two-column metrics, table scroll regions, bottom nav | Pass |
| 390 | Single-column content, scrollable signals/days, bottom nav and route sheet | Pass |

At 390 px the page visual viewport was 375.2 px after the browser scrollbar. Document scroll width was 375 px. Every visible interactive element measured at least 44×44 px after correcting the brand link and format filters.

## Interaction checks

- Desktop Content Plan navigation activated the correct hash route.
- Day selection changed from a post to Day 2 video with the matching caption and target.
- Mobile Videos filter selects the first matching video rather than leaving a post open.
- Day 5 video shows the realistic photographic preview and matching fit-check caption.
- Studio Day 5 opens a labelled modal with one video and one agent-rationale disclosure.
- Mobile More opens a labelled route sheet containing all nine routes.
- Submission reports five available files with valid local hrefs.

## Accessibility

- Semantic landmarks, route headings, labelled navigation, skip link, native dialogs, native video controls and explicit button states are present.
- Focus indicators use a 3 px high-contrast outline; reduced-motion preferences disable animation and smooth scrolling.
- Text contrast ratios: charcoal/canvas 13.97:1; charcoal/paper 15.22:1; forest/canvas 5.71:1; target label 6.90:1; white/error 6.65:1.
- Images have contextual alt text; decorative SVG icons are hidden from assistive technology.
- Tables retain headers and explicit horizontal scroll containers at narrower widths.

## Captures

Implementation screenshots are stored in `docs/design/screenshots/`. Stitch reference screens are stored separately in `docs/design/stitch/` so generated design intent and implemented output remain distinguishable.
