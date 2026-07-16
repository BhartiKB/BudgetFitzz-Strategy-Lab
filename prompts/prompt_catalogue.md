# Prompt catalogue

Prompts preserve the agent-authored plan context. Only visual fashion descriptions were sent to Hugging Face; dataset rows, metrics, captions, prices, and credentials were not included in prompts. All text and final compositing remain local and deterministic.

## PROMPT-POST-01 / capsule-grid
Generate an unbranded photorealistic three-piece flat lay. Composite it locally into a clean 1080x1350 capsule wardrobe card with the original hook, takeaway, BudgetFitzz wordmark, and save CTA.

## PROMPT-POST-02 / abc-vote
Generate exactly three full-body adult Indian male models in forest-and-cream, navy-and-stone, and burgundy-and-charcoal outfits. Add the A/B/C labels and occasion CTA only during local compositing.

## PROMPT-POST-03 / priority-receipt
Generate an unbranded trouser, tee, and overshirt flat lay. Composite it into a receipt-inspired value-first buying priority with all amounts labelled as illustrative planning caps, not live prices.

## PROMPT-POST-04 / use-case-scorecard
Generate three distinct unbranded sneaker concepts. Add practical-use rankings, trade-offs, synthetic-mark coverage, and the qualified comment CTA during local compositing.

## PROMPT-POST-05 / checklist-audit
Generate a shopper evaluating an overshirt beside a wardrobe. Until promotional credit permits that final call, retain the original five-question checklist with large safe checkboxes and a four-yes decision rule.

## PROMPT-VIDEO-01 / three-scene-swap
Create a 12-second vertical motion graphic with hook visible from frame one, three meaningful outfit states, short captions, progress indicators, and a 3-second save end card.

## PROMPT-VIDEO-02 / before-after-fix
Create a 12-second vertical fit-check graphic with red-to-green corrections, one concept per scene, readable captions, and screenshot CTA.

## Schema repair rule
Validate content against `PlanItem`. If required fields are absent, reissue the deterministic payload with only missing fields repaired; never invent measured future performance.
