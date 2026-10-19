from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ApprovalRequest:
    request_id: str
    incident: str
    hypothesis: str
    summary: str
    risk_level: str
    affected_files: list[str]
    patch_count: int
    validation_passed: bool
    requires_human_approval: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "incident": self.incident,
            "hypothesis": self.hypothesis,
            "summary": self.summary,
            "risk_level": self.risk_level,
            "affected_files": list(self.affected_files),
            "patch_count": self.patch_count,
            "validation_passed": self.validation_passed,
            "requires_human_approval": self.requires_human_approval,
        }


@dataclass(frozen=True)
class ApprovalDecision:
    request_id: str
    approved: bool
    decided_by: str | None
    reason: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "approved": self.approved,
            "decided_by": self.decided_by,
            "reason": self.reason,
            "status": self.status,
        }
