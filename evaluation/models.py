from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EvaluationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    name: str
    description: str

    expected_root_cause_category: str | None = None
    expected_remediation_allowed: bool | None = None
    expected_patch_generated: bool | None = None
    expected_validation_passed: bool | None = None
    expected_human_approval_required: bool | None = None
    expected_github_pr: bool | None = None

    minimum_confidence: float | None = None

    tags: list[str] = field(default_factory=list)


@dataclass
class EvaluationCheck:
    name: str
    passed: bool
    expected: Any
    actual: Any
    details: str = ""


@dataclass
class EvaluationResult:
    case_id: str
    case_name: str
    status: EvaluationStatus
    checks: list[EvaluationCheck] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == EvaluationStatus.PASS

    @property
    def score(self) -> float:
        if not self.checks:
            return 0.0

        passed = sum(check.passed for check in self.checks)
        return passed / len(self.checks)


@dataclass
class EvaluationReport:
    results: list[EvaluationResult] = field(default_factory=list)

    @property
    def total_cases(self) -> int:
        return len(self.results)

    @property
    def passed_cases(self) -> int:
        return sum(result.passed for result in self.results)

    @property
    def failed_cases(self) -> int:
        return self.total_cases - self.passed_cases

    @property
    def pass_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0

        return self.passed_cases / self.total_cases

    @property
    def overall_score(self) -> float:
        if not self.results:
            return 0.0

        return sum(result.score for result in self.results) / len(self.results)

    @property
    def passed(self) -> bool:
        return self.failed_cases == 0
