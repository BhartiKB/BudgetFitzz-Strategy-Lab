# Architecture

Run ID: `budgetfitzz-20260716T221956Z`

The state machine in `orchestration/workflow.py` invokes eleven named agent roles: DataAudit, Metrics, PerformanceAnalyst, FailureDiagnosis, Strategy, ContentPlanner, CreativeDirector, AssetGeneration, QualityAssurance, Packaging, and Orchestrator. Pydantic models validate plan, evidence, spend, and trace boundaries. SQLite stores runs, agent state, checkpoints, spend, and trace summaries; JSONL retains append-only audit entries.

Reasoning agents consume evidence objects. Deterministic analytics calculate metrics and robust summaries. Procedural Pillow renderers create the static graphics and branded video cards. Day 2 combines one audited HF/Wan promotional-credit source with those cards. FFmpeg creates/probes H.264 files with NVENC-first fallback. ReportLab creates the PDF. The standard-library HTTP server hosts the offline dashboard.

Retries are bounded at two. Stages are idempotent and persistent. Four explicit checkpoints are auto-approved only because `auto_approve_demo=true`; every approval and reason is logged.
