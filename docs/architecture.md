# Architecture

Run ID: `budgetfitzz-20260716T225356Z`

The state machine in `orchestration/workflow.py` invokes eleven named agent roles: DataAudit, Metrics, PerformanceAnalyst, FailureDiagnosis, Strategy, ContentPlanner, CreativeDirector, AssetGeneration, QualityAssurance, Packaging, and Orchestrator. Pydantic models validate plan, evidence, spend, and trace boundaries. SQLite stores runs, agent state, checkpoints, spend, and trace summaries; JSONL retains append-only audit entries.

Reasoning agents consume evidence objects. Deterministic analytics calculate metrics and robust summaries. Pillow renderers composite audited HF photographs with agent-authored headlines, guidance, prices, and calls to action; Day 7 falls back to the procedural checklist until its source photo is available. Day 2 combines an audited HF/Wan promotional-credit source with branded cards. FFmpeg creates/probes H.264 files with NVENC-first fallback. ReportLab creates the PDF. The standard-library HTTP server hosts the offline dashboard.

Retries are bounded at two. Stages are idempotent and persistent. Four explicit checkpoints are auto-approved only because `auto_approve_demo=true`; every approval and reason is logged.
