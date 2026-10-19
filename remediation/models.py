from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RemediationAction:
    action_type: str
    description: str
    target: str | None = None
    rationale: str = ""
    patchable: bool = False
    requires_approval: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "description": self.description,
            "target": self.target,
            "rationale": self.rationale,
            "patchable": self.patchable,
            "requires_approval": self.requires_approval,
        }


@dataclass
class RemediationProposal:
    hypothesis: str
    category: str
    summary: str
    rationale: str
    actions: list[RemediationAction] = field(default_factory=list)
    affected_files: list[str] = field(default_factory=list)
    risk_level: str = "medium"
    confidence: float = 0.0
    requires_human_approval: bool = True
    patch_generation_allowed: bool = False
    validation_requirements: list[str] = field(default_factory=list)
    safety_constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis": self.hypothesis,
            "category": self.category,
            "summary": self.summary,
            "rationale": self.rationale,
            "actions": [
                action.to_dict()
                for action in self.actions
            ],
            "affected_files": list(self.affected_files),
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "requires_human_approval": (
                self.requires_human_approval
            ),
            "patch_generation_allowed": (
                self.patch_generation_allowed
            ),
            "validation_requirements": list(
                self.validation_requirements
            ),
            "safety_constraints": list(
                self.safety_constraints
            ),
        }


@dataclass(frozen=True)
class RemediationDecision:
    allowed: bool
    reason: str
    proposal: RemediationProposal | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "proposal": (
                self.proposal.to_dict()
                if self.proposal
                else None
            ),
        }
