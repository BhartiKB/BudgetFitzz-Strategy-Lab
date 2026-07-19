# Provider configuration

`config/content_generation.yaml` is a secret-free JSON-compatible YAML configuration. Environment variables may override mode and enable flags: `GOOGLE_API_KEY`, `HF_TOKEN`, `MEDIA_BUDGET_INR`, `ENABLE_VEO_API`, `ENABLE_HF_API`, and `DEFAULT_GENERATION_MODE`.

Veo API remains disabled unless both configuration and credentials permit it. Any paid request requires a per-request human approval and a budget check before submission. Hugging Face preserves its existing `GenerationPolicy` and promotional-credit guard. `FAL_KEY` remains ignored and is never read or displayed.
