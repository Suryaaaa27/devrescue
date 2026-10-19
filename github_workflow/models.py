from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GitHubWorkflowStatus(str, Enum):
    BLOCKED = "blocked"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass
class GitHubWorkflowResult:
    status: GitHubWorkflowStatus
    message: str

    branch: str | None = None
    pull_request: dict[str, Any] | None = None
    written_files: list[str] = field(default_factory=list)

    validation_passed: bool = False
    approval_granted: bool = False

    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.status == GitHubWorkflowStatus.COMPLETED
