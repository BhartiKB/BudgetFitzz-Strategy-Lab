# Insta Strategy Lab - BudgetFitzz

Production-quality offline platform for Intern Task 2: Performance Analysis and Strategy Revision.

## Verified outcome

- Historical dataset: 150 records (137 posts, 13 videos)
- Promotional baseline: 90.0%
- Revised cycle: exactly 5 static posts and 2 short videos
- Paid revised-content generation spend: INR 0
- Local provider: deterministic-template / budgetfitzz-editorial-v1
- Selected encoder: h264_nvenc

The dataset is described truthfully as a user-provided local evaluation dataset with unspecified original provenance. Assumed business context is explicitly labelled.

## Launch

```powershell
.\run_app.ps1
```

Then open `http://127.0.0.1:8501`.

From the extracted submission ZIP, launch the packaged app directly with:

```powershell
.\launch_platform.ps1
```

The packaged launcher uses only Python's standard library; finished assets and reports are already included.

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

## Architecture

Eleven named agents operate through a lightweight state machine. Deterministic analytical tools own calculations; agents own decisions and evidence-linked handoffs. All generation is local and the source CSV/DOCX remain immutable.

## Important interpretation

Future ranges are targets and hypotheses, not achieved post-publication results. Video views are plays, not unique people. The extreme video outlier is preserved and robust summaries are reported separately.
