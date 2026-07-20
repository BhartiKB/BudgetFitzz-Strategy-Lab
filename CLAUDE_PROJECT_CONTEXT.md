# BudgetFitzz Project Context

Project root: `C:\Users\bhart\Documents\Task2`

## Current production system

- 150 historical records: 137 posts and 13 videos.
- Eleven-agent workflow with persistent local state and execution traces.
- Exactly five planned posts and two planned videos.
- Vanilla HTML, CSS and JavaScript frontend, served by Python `ThreadingHTTPServer`.
- Manifest-driven interface: `app/data/platform_manifest.json` is the browser content index.
- Hybrid content-generation workflow with manual-provider import, provenance,
  validation, versioning and human approval.
- Direct paid generation spend is INR 0; the app remains offline-capable.
- Render-compatible local deployment configuration.

## Current UI update scope

- Create an original editorial, cinematic interface with restrained motion.
- Preserve all analysis, strategy, plan content, agent contracts, validations and
  currently approved media.
- Add a production workspace without automating third-party provider websites.
- Keep Veo API disabled unless a valid credential, explicit approval and budget
  controls are configured.
- Preserve Hugging Face and deterministic local fallbacks.
- Treat manually imported media as local/private unless the user explicitly asks
  to package or publish it.

## Safety constraints

Do not expose `.env`, API keys, browser state, or provider credentials. Do not
claim a provider API is connected or tested without a real successful request.
