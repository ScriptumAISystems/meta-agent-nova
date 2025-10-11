"""Unit tests for the VibeSessionManager orchestration loop."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import pytest

from nova.explainability import ExplainabilityLogger
from nova.vibe_session import VibeSessionManager


@dataclass
class DummyPlanner:
    calls: List[Dict[str, Any]]

    def plan(self, goal: str, style: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append({"goal": goal, "style": style, "parameters": parameters})
        return {"steps": [f"plan-step-{len(self.calls)}"], "goal": goal}


@dataclass
class DummyCoder:
    calls: List[Dict[str, Any]]

    def generate(self, plan: Dict[str, Any], style: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append({"plan": plan, "style": style, "parameters": parameters})
        return {"artifact": f"implementation-{len(self.calls)}", "tokens_used": 120}


@dataclass
class DummyTester:
    scores: List[float]
    calls: List[Dict[str, Any]]

    def evaluate(
        self,
        implementation: Dict[str, Any],
        plan: Dict[str, Any],
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        index = len(self.calls)
        score = self.scores[index]
        payload = {
            "implementation": implementation,
            "plan": plan,
            "parameters": parameters,
            "score": score,
        }
        self.calls.append(payload)
        return {"score": score, "notes": f"iteration-{index + 1}"}


@pytest.fixture()
def explainability_logger(tmp_path):
    return ExplainabilityLogger(log_dir=tmp_path)


def test_vibe_session_manager_runs_three_iterations(explainability_logger):
    planner = DummyPlanner(calls=[])
    coder = DummyCoder(calls=[])
    tester = DummyTester(scores=[0.85, 0.9, 0.95], calls=[])
    manager = VibeSessionManager(
        planner,
        coder,
        tester,
        explainability=explainability_logger,
        config={"use_gpu": True},
        max_iterations=3,
    )

    initial_temperature = manager.parameters.temperature
    session = manager.start_session("Deliver autonomous feature", "collaborative")

    assert len(session["iterations"]) == 3
    assert session["summary"]["iterations"] == 3
    assert session["summary"]["average_score"] > 0.8
    assert manager.gpu_active is True

    records = manager.collect_feedback()
    assert len(records) == 3
    assert len(explainability_logger.records) == 3

    assert manager.parameters.temperature < initial_temperature
    assert manager.parameters.role_bias["tester"] >= 1.2
    assert manager.parameters.token_budget <= 8000


@pytest.mark.parametrize("score", [-0.1, 1.1])
def test_adapt_parameters_validates_score(score):
    planner = DummyPlanner(calls=[])
    coder = DummyCoder(calls=[])
    tester = DummyTester(scores=[0.9], calls=[])
    manager = VibeSessionManager(planner, coder, tester)

    with pytest.raises(ValueError):
        manager.adapt_parameters(score)
