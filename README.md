# Insta Strategy Lab - BudgetFitzz

Production-quality offline platform for Intern Task 2: Performance Analysis and Strategy Revision.

**Live website:** [budgetfitzz-strategy-lab.onrender.com](https://budgetfitzz-strategy-lab.onrender.com)

## Verified outcome

- Historical dataset: 150 records (137 posts, 13 videos)
- Promotional baseline: 90.0%
- Revised cycle: exactly 5 static posts and 2 short videos
- Paid revised-content generation spend: INR 0
- Local provider: deterministic-template / budgetfitzz-editorial-v1
- Media policy: free-only; fal disabled; paid or unknown-cost image/video calls fail closed
- Selected encoder: h264_nvenc

The dataset is described truthfully as a user-provided local evaluation dataset with unspecified original provenance. Assumed business context is explicitly labelled.

## Launch

```powershell
.\run_app.ps1
```

Then open `http://127.0.0.1:8501`.

The Version 11 frontend is the **BudgetFitzz Editorial Creator Atelier**: a warm, responsive, manifest-driven workspace with Home, Insights, Diagnosis, Strategy, Content Plan, Studio, Agents, Validation, and Submission routes. The visual system was developed through a private Google Stitch project using only authorized UI labels and summarized findings; no raw inputs, keys, source files, or private media were uploaded.

Equivalent Python command:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe app\server.py --port 8501
```

## Deploy on Render

The root `render.yaml` defines a free Python web service in Singapore. It binds the dependency-free server to Render's public `0.0.0.0:$PORT`, checks `/api/status`, and serves only allowlisted public application, chart, asset, and deliverable routes. Run the finalization workflow before pushing so `deploy/` contains the public report, walkthrough, manifest, validation report, and submission package. Local credentials remain excluded by `.gitignore` and are never required by the hosted site.

## Reproduce

```powershell
.\setup.ps1
.\generate_submission.ps1
.\validate_submission.ps1
```

The pipeline is idempotent. Workflow state is stored in `logs/workflow.db`; concise decision traces are appended to `logs/execution_trace.jsonl`. Use `--resume` with `scripts/run_pipeline.py` to skip completed stages in the active run where their outputs remain valid.

Credentials may be stored only in the ignored `.env` file. User-confirmed Hugging Face promotional credit supplied the realistic Day 2 and Day 5 source clips plus four of five planned post photographs at INR 0 cash cost. The fifth post-photo request was rejected with HTTP 402 and the deterministic Day 7 fallback remains active. Gemini image generation was not called. `FAL_KEY` is deliberately ignored.

## Architecture

Eleven named agents operate through a lightweight state machine. Deterministic analytical tools own calculations; agents own decisions and evidence-linked handoffs. Final compositing is local; four static posts and Days 2 and 5 use audited HF promotional-credit sources. Day 7 retains the deterministic fallback. The source CSV/DOCX remain immutable.

The frontend reads the generated `app/data/platform_manifest.json` rather than duplicating analytical values in browser code. `app/server.py` serves only approved application, asset, chart, report, validation, and package routes. See [backend-to-frontend connection](docs/backend_frontend_connection.md) for the verified request and data flow.

## Important interpretation

Future ranges are targets and hypotheses, not achieved post-publication results. Video views are plays, not unique people. The extreme video outlier is preserved and robust summaries are reported separately.
