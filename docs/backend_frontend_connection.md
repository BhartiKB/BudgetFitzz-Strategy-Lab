# Backend-to-frontend connection

## Verified architecture

`User-provided dataset → analytical and agent workflow → generated outputs → platform manifest → Python server → frontend application`

The raw CSV and DOCX remain immutable under `data/raw/`; their checksums are recorded in `docs/source_checksums.sha256`. The repository does not contain a verified Apify or Selenium collection implementation, so no collection method is claimed here.

## 1. Analytical and agent workflow

`scripts/run_pipeline.py` starts the Python workflow. Its agents audit the data, calculate derived metrics, analyse performance, form an evidence-linked diagnosis and strategy, create the seven-day plan, generate assets, validate the result, and package the approved files. The workflow writes JSON, CSV, charts, media, traces, validation reports, and other derived outputs into the project.

## 2. Platform manifest

`src/insta_strategy_lab/reporting/builder.py` builds `app/data/platform_manifest.json`. It is the structured content index for the interface: it carries navigation, observed KPIs, strategy, plan items, asset references, workflow trace entries, validation, submission-file metadata, and the architecture description. This keeps calculated values out of browser source code and avoids manually duplicating dashboard data.

## 3. Python backend

`app/server.py` starts a `ThreadingHTTPServer`. `/` redirects to `/app/index.html`; `/app/` serves the frontend tree; `/analysis/charts/` and `/assets/` expose approved visual outputs; selected report, submission, and validation routes expose final deliverables. The handler rejects traversal attempts and returns 404 for paths outside this allowlist, so source files, `.env`, raw data, and unapproved files are not public.

`/api/status` returns a small readiness JSON response: `{"status": "ready", "platform": "BudgetFitzz Strategy Lab", "offline": true}`. It is used as the Render health check; the browser interface does not depend on it for analytical content.

## 4. Frontend application

`app/index.html` loads the page shell, styles, and `app/app.js`. `loadManifest()` in `app/app.js` fetches `data/platform_manifest.json` with `cache: "no-store"`, checks the required sections, and then renders the Home, Insights, Diagnosis, Strategy, Content Plan, Studio, Agents, Validation, and Submission views. Charts, post images, videos, PDFs, and submission links are loaded through public URLs referenced by the manifest rather than by copying their values into JavaScript.

## 5. Deployment and synchronization

`render.yaml` starts the same `app/server.py` entry point on `0.0.0.0:$PORT` and checks `/api/status`, so the deployed Render service uses the same server and frontend architecture as local use. Re-running the workflow or finalizer rebuilds the authoritative manifest from the current project outputs; refreshing the application then renders that current structured state.

## Public paths shown in the explainer

- Manifest: `app/data/platform_manifest.json`
- Backend entry point: `app/server.py`
- Frontend data-loading entry point: `app/app.js`
- Health endpoint: `/api/status`
- Output categories: metrics and evidence, derived CSV and charts, strategy and plan, post images and videos, traces and validation, reports and submission files
