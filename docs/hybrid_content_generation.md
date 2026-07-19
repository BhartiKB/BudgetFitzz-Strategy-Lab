# Hybrid content-generation workflow

`ContentPlannerAgent` and `CreativeDirectorAgent` produce a visible final brief and exact generation prompt for every planned asset. The prompt is exported as JSON and Markdown, or copied directly from Content Studio.

The routing order is explicit selection first, then Veo API only when enabled, credentialed, budget-allowed and approved; Hugging Face when it is enabled and usable; manual provider workflow; and deterministic local fallback. No provider is reported as connected without a successful verified request.

Manual workflow: prompt → user generates in a provider website → user imports through Content Studio → secure validation/quarantine → local post-processing → human approval → active version, provenance and manifest update.

Current demonstration mode is `MANUAL_PROVIDER`, recommends Google Flow / Veo, reports INR 0 actual paid spend, leaves Veo API disabled, retains Hugging Face as a guarded fallback, and retains local compositing as the final fallback.
