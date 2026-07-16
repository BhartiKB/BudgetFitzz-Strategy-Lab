# Developer guide

The project uses Python 3.12, standard library services, pandas/numpy, Pydantic, Pillow, ReportLab, and a project-local FFmpeg build. `setup.ps1` creates `.venv` with access to the bundled base packages. Use `PYTHONPATH=src`.

- Full workflow: `python scripts/run_pipeline.py`
- Resume: `python scripts/run_pipeline.py --resume`
- Tests: `python -m unittest discover -s tests -v`
- Validation: `python scripts/validate_submission.py --final`
- App: `python app/server.py --port 8501`

Generated outputs are deterministic for seed 4050. Never change raw inputs; rerun the relevant stage instead.
