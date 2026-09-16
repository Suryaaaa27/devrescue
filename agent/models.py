from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class InvestigationAction:

    tool: str

    arguments: dict[str, Any]

    reason: str


@dataclass
class InvestigationResult:

    incident: str

    service: str

    status: str

    root_cause: str | None = None

    confidence: float = 0.0

    explanation: str | None = None

    iterations: int = 0

    tools_called: list[str] = field(
        default_factory=list
    )

    evidence_summary: dict[str, Any] = field(
        default_factory=dict
    )

    hypotheses: list[dict[str, Any]] = field(
        default_factory=list
    )

    planning_history: list[dict[str, Any]] = field(
        default_factory=list
    )

    investigation_notes: list[str] = field(
        default_factory=list
    )

    hypothesis_history: list[dict[str, Any]] = field(
        default_factory=list
    )

    evidence_gaps: list[dict[str, Any]] = field(
        default_factory=list
    )

    action_outcomes: list[dict[str, Any]] = field(
        default_factory=list
    )
    
    uncertainty: dict[str, Any] = field(default_factory=dict)
    llm_reasoning: dict[str, Any] | None = None

    llm_reasoning_history: list[dict[str, Any]] = field(
        default_factory=list
    )
    
    def to_dict(self):

        return {
            "incident": self.incident,
            "service": self.service,
            "status": self.status,
            "root_cause": self.root_cause,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "iterations": self.iterations,
            "tools_called": self.tools_called,
            "evidence_summary": self.evidence_summary,
            "hypotheses": self.hypotheses,
            "planning_history": self.planning_history,
            "investigation_notes": (
                self.investigation_notes
            ),
            "hypothesis_history": self.hypothesis_history,
            "evidence_gaps": self.evidence_gaps,
            "action_outcomes": self.action_outcomes,
            "uncertainty": self.uncertainty,
            "llm_reasoning": self.llm_reasoning, 
            "llm_reasoning_history": self.llm_reasoning_history,
        }