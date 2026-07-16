# Insta Strategy Lab - BudgetFitzz

Production-quality offline platform for Intern Task 2: Performance Analysis and Strategy Revision.

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

Equivalent Python command:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe app\server.py --port 8501
```

## Reproduce

```powershell
.\setup.ps1
.\generate_submission.ps1
.\validate_submission.ps1
```

The pipeline is idempotent. Workflow state is stored in `logs/workflow.db`; concise decision traces are appended to `logs/execution_trace.jsonl`. Use `--resume` with `scripts/run_pipeline.py` to skip completed stages in the active run where their outputs remain valid.

Credentials may be stored only in the ignored `.env` file. One user-confirmed Hugging Face promotional-credit call supplied the realistic Day 2 source clip at INR 0 cash cost (USD 0.025 credit value). Gemini image generation was not called because its image tier was not free. `FAL_KEY` is deliberately ignored.

## Architecture

Eleven named agents operate through a lightweight state machine. Deterministic analytical tools own calculations; agents own decisions and evidence-linked handoffs. Static assets and final compositing are local; Day 2 uses the audited HF promotional-credit source clip. The source CSV/DOCX remain immutable.

## Important interpretation

Future ranges are targets and hypotheses, not achieved post-publication results. Video views are plays, not unique people. The extreme video outlier is preserved and robust summaries are reported separately.
