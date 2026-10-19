from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PatchFile:
    path: str
    original_content: str
    patched_content: str
    diff: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "original_content": self.original_content,
            "patched_content": self.patched_content,
            "diff": self.diff,
        }


@dataclass
class PatchProposal:
    allowed: bool
    reason: str
    patches: list[PatchFile] = field(default_factory=list)
    rationale: str = ""
    validation_requirements: list[str] = field(default_factory=list)
    safety_checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "patches": [patch.to_dict() for patch in self.patches],
            "rationale": self.rationale,
            "validation_requirements": list(self.validation_requirements),
            "safety_checks": list(self.safety_checks),
        }
