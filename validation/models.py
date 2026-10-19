from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ValidationCheck:
    name: str
    passed: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
        }


@dataclass
class ValidationResult:
    passed: bool
    status: str
    summary: str
    checks: list[ValidationCheck] = field(default_factory=list)
    test_output: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "status": self.status,
            "summary": self.summary,
            "checks": [check.to_dict() for check in self.checks],
            "test_output": self.test_output,
            "error": self.error,
        }
