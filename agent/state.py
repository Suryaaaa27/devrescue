from dataclasses import dataclass, field
from typing import Any

from evidence.models import InvestigationEvidence
from hypothesis.models import Hypothesis


@dataclass
class InvestigationState:

    incident: str

    service: str

    iteration: int = 0

    max_iterations: int = 8

    completed: bool = False
    
    decision: dict[str, Any] | None = None

    available_tools: set[str] = field(
        default_factory=set
    )

    tool_history: list[str] = field(
        default_factory=list
    )

    tool_results: dict[str, list[dict[str, Any]]] = field(
        default_factory=dict
    )

    log_result: dict[str, Any] = field(
        default_factory=dict
    )

    metric_results: list[dict[str, Any]] = field(
        default_factory=list
    )

    trace_result: dict[str, Any] = field(
        default_factory=dict
    )
    code_results: list[dict[str, Any]] = field(
        default_factory=list
    )

    commit_results: list[dict[str, Any]] = field(
        default_factory=list
    )

    diff_results: list[dict[str, Any]] = field(
        default_factory=list
    )
    evidence: InvestigationEvidence | None = None

    hypotheses: list[Hypothesis] = field(
        default_factory=list
    )

    selected_hypothesis: Hypothesis | None = None

    investigation_notes: list[str] = field(
        default_factory=list
    )

    planning_history: list[dict[str, Any]] = field(
        default_factory=list
    )
    hypothesis_history: list[dict[str, Any]] = field(default_factory=list)

    evidence_gaps: list[dict[str, Any]] = field(default_factory=list)

    action_outcomes: list[dict[str, Any]] = field(default_factory=list)

    llm_reasoning_history: list[dict[str, Any]] = field(
        default_factory=list
    )
    
    def record_tool_call(
        self,
        tool: str,
        result: dict[str, Any],
    ):

        self.tool_history.append(tool)

        self.tool_results.setdefault(
            tool,
            [],
        ).append(result)

    def add_note(
        self,
        note: str,
    ):

        self.investigation_notes.append(
            note
        )

    def add_llm_reasoning(
        self,
        reasoning,
    ):
        reasoning_data = (
            reasoning.to_dict()
            if hasattr(reasoning, "to_dict")
            else dict(reasoning)
        )

        self.llm_reasoning_history.append(
            {
                "iteration": self.iteration,
                "reasoning": reasoning_data,
            }
        )

    def record_plan(
        self,
        tool: str,
        reason: str,
        hypothesis: str | None = None,
        priority: int | None = None,
        mode: str | None = None,
    ):
        """
        Record why the investigator selected a tool.

        mode:
            discovery
            hypothesis_driven

        If mode is not explicitly supplied, infer it
        strictly from whether a hypothesis exists.
        """

        if mode is None:

            if hypothesis is not None:
                mode = "hypothesis_driven"
            else:
                mode = "discovery"

        if mode not in {
            "discovery",
            "hypothesis_driven",
        }:
            raise ValueError(
                "Invalid planning mode: "
                f"{mode}"
            )

        self.planning_history.append(
            {
                "iteration": self.iteration,
                "tool": tool,
                "mode": mode,
                "reason": reason,
                "hypothesis": hypothesis,
                "priority": priority,
            }
        )
    
    def record_hypotheses(self):
        """
        Preserve the hypothesis ranking at the current iteration.
        """

        self.hypothesis_history.append(
            {
                "iteration": self.iteration,
                "hypotheses": [
                    {
                        "name": hypothesis.name,
                        "category": hypothesis.category,
                        "role": hypothesis.role,
                        "confidence": hypothesis.confidence,
                        "score": hypothesis.score,
                    }
                    for hypothesis in self.hypotheses
                ],
            }
        )

    def record_evidence_gap(
        self,
        name: str,
        description: str,
        priority: int,
        tool: str,
    ):
        self.evidence_gaps.append(
            {
                "iteration": self.iteration,
                "name": name,
                "description": description,
                "priority": priority,
                "tool": tool,
            }
        )

    def record_action_outcome(
        self,
        tool: str,
        success: bool,
        evidence_added: int,
    ):
        self.action_outcomes.append(
            {
                "iteration": self.iteration,
                "tool": tool,
                "success": success,
                "evidence_added": evidence_added,
            }
        )