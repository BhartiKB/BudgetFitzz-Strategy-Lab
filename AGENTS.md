# Repository operating guide

- Never edit files under `data/raw/`; verify them against `docs/source_checksums.sha256`.
- Use the project-local Python environment and set `PYTHONPATH=src`.
- Run the workflow through `scripts/run_pipeline.py`; do not hand-edit generated analytical outputs.
- Preserve raw outliers. Add robust or winsorized summaries rather than deleting observations.
- Keep observed values clearly separate from targets and hypotheses.
- Any paid generation call must be logged in `logs/spend_log.csv` before packaging.
- Every plan revision must retain exactly five `post` and two `video` items.
- Complete asset, video, PDF, app, and package validation before final export.
