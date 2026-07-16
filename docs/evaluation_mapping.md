# Evaluation mapping

| Criterion | Implementation evidence |
| --- | --- |
| Functional correctness | Unit tests, asset/video probes, final validator |
| Agentic architecture | Eleven named agents, Pydantic boundaries, state machine |
| Autonomy | Auto-approved demo checkpoints with logged reasons and repair gates |
| Modularity/scalability | Separate analytics, agents, providers, creative, video, storage, reporting, validation, UI |
| Code quality | Typed modules, deterministic outputs, isolated raw/derived layers |
| Prompt engineering | Prompt catalogue with schema repair and deterministic fallback |
| Error recovery | Bounded retries, NVENC-to-libx264 fallback, persisted errors |
| Documentation | README plus task, architecture, data, metrics, GPU, limitations, user/developer guides |
| Observability | SQLite, application log, JSONL decision trace, timing/retry/hardware/spend reports |
| Creativity/justification | Original procedural fashion graphics tied to baseline evidence |
