"""Named agent roles with validated, traceable execution boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class BaseAgent:
    name: str
    responsibility: str
    action: Callable[[], Any]

    def run(self) -> Any:
        return self.action()


class DataAuditAgent(BaseAgent):
    pass


class MetricsAgent(BaseAgent):
    pass


class PerformanceAnalystAgent(BaseAgent):
    pass


class FailureDiagnosisAgent(BaseAgent):
    pass


class StrategyAgent(BaseAgent):
    pass


class ContentPlannerAgent(BaseAgent):
    pass


class CreativeDirectorAgent(BaseAgent):
    pass


class AssetGenerationAgent(BaseAgent):
    pass


class QualityAssuranceAgent(BaseAgent):
    pass


class PackagingAgent(BaseAgent):
    pass


class OrchestratorAgent(BaseAgent):
    """Marker role for the state machine that owns dependencies, retries, and repair gates."""

