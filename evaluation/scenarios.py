from dataclasses import dataclass
from typing import Any, Callable

@dataclass(frozen=True)
class EvaluationScenario:
    case_id: str
    description: str
    execute: Callable[[], Any]


class ScenarioRegistry:
    def __init__(self):
        self._scenarios: dict[str, EvaluationScenario] = {}

    def register(self, scenario: EvaluationScenario) -> None:
        if scenario.case_id in self._scenarios:
            raise ValueError(
                f"Scenario already registered: {scenario.case_id}"
            )

        self._scenarios[scenario.case_id] = scenario

    def get(self, case_id: str) -> EvaluationScenario:
        try:
            return self._scenarios[case_id]
        except KeyError:
            raise KeyError(
                f"No evaluation scenario registered for {case_id}"
            )

    def all(self) -> list[EvaluationScenario]:
        return list(self._scenarios.values())


class FakeEvaluationGitHub:
    """
    Side-effect-free GitHub backend used by evaluation scenarios.

    The real GitHub workflow is exercised, but no external GitHub
    resources are created.
    """

    def __init__(self):
        self.branches: list[str] = []
        self.files: list[dict[str, Any]] = []
        self.pull_requests: list[dict[str, Any]] = []

    def create_branch(
        self,
        branch,
        from_branch=None,
        **kwargs,
    ):
        self.branches.append(branch)

        return {
            "status": "success",
            "branch": branch,
            "sha": "evaluation-sha",
        }

    def create_or_update_file(
        self,
        path,
        content,
        branch,
        message,
        sha=None,
        **kwargs,
    ):
        self.files.append(
            {
                "path": path,
                "content": content,
                "branch": branch,
                "message": message,
            }
        )

        return {
            "status": "success",
            "path": path,
            "branch": branch,
        }

    def create_pull_request(
        self,
        title,
        body,
        head,
        base=None,
        **kwargs,
    ):
        pull_request = {
            "number": len(self.pull_requests) + 1,
            "title": title,
            "body": body,
            "head": head,
            "base": base or "main",
        }

        self.pull_requests.append(pull_request)

        return {
            "status": "success",
            "pull_request": pull_request,
        }

def build_default_registry():
    from .executors import (
        execute_ev01,
        execute_ev02,
        execute_ev03,
        execute_ev04,
        execute_ev05,
        execute_ev06,
        execute_ev07,
        execute_ev08,
        execute_ev09,
        execute_ev10,
    )

    registry = ScenarioRegistry()

    registry.register(
        EvaluationScenario(
            case_id="EV-01",
            description="Real application validation remediation workflow.",
            execute=execute_ev01,
        )
    )

    registry.register(
        EvaluationScenario(
            case_id="EV-02",
            description="Real application exception remediation workflow.",
            execute=execute_ev02,
        )
    )

    registry.register(
        EvaluationScenario(
            case_id="EV-03",
            description="Real database failure remediation workflow.",
            execute=execute_ev03,
        )
    )

    registry.register(
        EvaluationScenario(
            case_id="EV-04",
            description="Insufficient evidence evaluation.",
            execute=execute_ev04,
        )
    )


    registry.register(
        EvaluationScenario(
            case_id="EV-05",
            description="Low-confidence hypothesis evaluation.",
            execute=execute_ev05,
        )
    )

    registry.register(
        EvaluationScenario(
            case_id="EV-06",
            description="Unsafe remediation is rejected by the safety policy.",
            execute=execute_ev06,
        )
    )

    registry.register(
        EvaluationScenario(
            case_id="EV-07",
            description="Valid remediation is rejected by the human reviewer.",
            execute=execute_ev07,
       )
    )

    registry.register(
        EvaluationScenario(
            case_id="EV-08",
            description="Invalid generated patch is rejected by validation.",
            execute=execute_ev08,
        )
    )

    registry.register(
        EvaluationScenario(
            case_id="EV-09",
            description="GitHub write failure is handled safely.",
            execute=execute_ev09,
        )
    )

    registry.register(
        EvaluationScenario(
            case_id="EV-10",
            description="Complete successful remediation lifecycle.",
            execute=execute_ev10,
        )
    )

    return registry
