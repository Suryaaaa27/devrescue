from dataclasses import dataclass, field
from typing import Optional

from agent.state import InvestigationState
from hypothesis.models import Hypothesis


@dataclass(frozen=True)
class InvestigationDecision:
    """
    Decision produced after evaluating the current investigation state.

    The decision determines whether DevRescue should conclude,
    investigate further, or stop because evidence is insufficient.
    """

    decision: str
    reason: str
    selected_hypothesis: Optional[str] = None
    confidence: float = 0.0
    evidence_gaps: list[str] = field(default_factory=list)
    next_action: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "reason": self.reason,
            "selected_hypothesis": self.selected_hypothesis,
            "confidence": self.confidence,
            "evidence_gaps": list(self.evidence_gaps),
            "next_action": self.next_action,
        }


class InvestigationDecisionEngine:
    """
    Determines the next investigation decision.

    Decision states:

        CONCLUDE
            Sufficient evidence exists for the current root-cause
            hypothesis.

        INVESTIGATE
            Additional useful evidence should be collected.

        INSUFFICIENT_EVIDENCE
            The investigation budget has been exhausted or no
            useful evidence path remains.
    """

    CONCLUDE = "CONCLUDE"
    INVESTIGATE = "INVESTIGATE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

    ROOT_CAUSE_CONFIDENCE_THRESHOLD = 0.75

    def decide(
        self,
        state: InvestigationState,
    ) -> InvestigationDecision:

        hypothesis = state.selected_hypothesis

        # ----------------------------------------------------------
        # No hypothesis yet
        # ----------------------------------------------------------

        if hypothesis is None:

            if state.iteration >= state.max_iterations:
                return InvestigationDecision(
                    decision=self.INSUFFICIENT_EVIDENCE,
                    reason=(
                        "No root-cause hypothesis was established "
                        "within the investigation budget."
                    ),
                    confidence=0.0,
                )

            next_action = self._select_discovery_action(
                state
            )

            if next_action:
                return InvestigationDecision(
                    decision=self.INVESTIGATE,
                    reason=(
                        "No hypothesis has been established yet. "
                        "The available runtime evidence should be "
                        "followed into the most relevant next evidence "
                        "source."
                    ),
                    confidence=0.0,
                    next_action=next_action,
                )

            return InvestigationDecision(
                decision=self.INVESTIGATE,
                reason=(
                    "No hypothesis has been established yet. "
                    "Additional evidence is required."
                ),
                confidence=0.0,
                next_action=None,
            )

        # ----------------------------------------------------------
        # Root-cause hypothesis with sufficient confidence
        # ----------------------------------------------------------

        if self._is_sufficient_root_cause(
            hypothesis=hypothesis,
            state=state,
        ):
            return InvestigationDecision(
                decision=self.CONCLUDE,
                reason=(
                    "A root-cause hypothesis has sufficient confidence "
                    "and independent supporting evidence."
                ),
                selected_hypothesis=hypothesis.name,
                confidence=hypothesis.confidence,
            )

        # ----------------------------------------------------------
        # Evidence gaps remain
        # ----------------------------------------------------------

        gaps = list(state.evidence_gaps)

        if gaps and state.iteration < state.max_iterations:

            next_gap = self._select_next_gap(
                state=state,
                gaps=gaps,
            )

            return InvestigationDecision(
                decision=self.INVESTIGATE,
                reason=(
                    "The current hypothesis does not yet meet the "
                    "evidence threshold. Useful evidence gaps remain."
                ),
                selected_hypothesis=hypothesis.name,
                confidence=hypothesis.confidence,
                evidence_gaps=[
                    self._gap_name(gap)
                    for gap in gaps
                ],
                next_action=(
                    next_gap.tool
                    if next_gap
                    else None
                ),
            )

        # ----------------------------------------------------------
        # Budget exhausted
        # ----------------------------------------------------------

        if state.iteration >= state.max_iterations:
            return InvestigationDecision(
                decision=self.INSUFFICIENT_EVIDENCE,
                reason=(
                    "The investigation budget has been exhausted "
                    "without sufficient evidence for a root cause."
                ),
                selected_hypothesis=hypothesis.name,
                confidence=hypothesis.confidence,
                evidence_gaps=[
                    self._gap_name(gap)
                    for gap in gaps
                ],
            )

        # ----------------------------------------------------------
        # Hypothesis exists, but evidence is insufficient
        # ----------------------------------------------------------

        return InvestigationDecision(
            decision=self.INSUFFICIENT_EVIDENCE,
            reason=(
                "A hypothesis exists, but the available evidence "
                "does not justify concluding the investigation."
            ),
            selected_hypothesis=hypothesis.name,
            confidence=hypothesis.confidence,
            evidence_gaps=[
                self._gap_name(gap)
                for gap in gaps
            ],
        )

    # ==============================================================
    # Discovery action selection
    # ==============================================================

    def _select_discovery_action(
        self,
        state: InvestigationState,
    ) -> Optional[str]:
        """
        Select the most useful available tool when no hypothesis
        exists yet.

        Runtime evidence determines the priority rather than blindly
        following a fixed tool order.
        """

        available_tools = set(
            getattr(
                state,
                "available_tools",
                set(),
            )
        )

        called = set(state.tool_history)

        evidence = state.evidence

        # ----------------------------------------------------------
        # Application error already observed:
        # investigate source code.
        # ----------------------------------------------------------

        if (
            evidence
            and evidence.signals
            and "search_code" in available_tools
            and "search_code" not in called
        ):
            application_error_signals = {
                "error_log",
                "trace_error",
                "exception",
                "http_error",
            }

            if any(
                signal in application_error_signals
                for signal in evidence.signals
            ):
                return "search_code"
        # ----------------------------------------------------------
        # LLM reasoning may identify a specific missing evidence
        # source. Prefer that explicit investigation request.
        # ----------------------------------------------------------

        if (
            "investigate_database" in available_tools
            and "investigate_database" not in called
            and "search_logs" in called
        ):
            llm_history = getattr(
                state,
                "llm_reasoning_history",
                [],
            )

            if llm_history:
                latest_reasoning = (
                    llm_history[-1].get(
                        "reasoning",
                        {},
                    )
                )

                missing_evidence = (
                    latest_reasoning.get(
                        "missing_evidence",
                        [],
                    )
                )

                database_requested = any(
                    "database" in str(item).lower()
                    for item in missing_evidence
                )

                if database_requested:
                    return "investigate_database"
        # ----------------------------------------------------------
        # Traces can reveal the failing operation.
        # ----------------------------------------------------------

        if (
            evidence
            and evidence.logs
            and "find_traces" in available_tools
            and "find_traces" not in called
        ):
            return "find_traces"

        # ----------------------------------------------------------
        # Metrics can establish whether the failure is systemic.
        # ----------------------------------------------------------

        if (
            "query_metrics" in available_tools
            and "query_metrics" not in called
        ):
            return "query_metrics"

        # ----------------------------------------------------------
        # Database investigation when explicitly available.
        # ----------------------------------------------------------

        if (
            "investigate_database" in available_tools
            and "investigate_database" not in called
            and "search_logs" in called
        ):
            return "investigate_database"

        return None

    # ==============================================================
    # Root-cause sufficiency
    # ==============================================================

    def _is_sufficient_root_cause(
        self,
        hypothesis: Hypothesis,
        state: InvestigationState,
    ) -> bool:

        if hypothesis.role != "root_cause":
            return False

        if (
            hypothesis.confidence
            < self.ROOT_CAUSE_CONFIDENCE_THRESHOLD
        ):
            return False

        independent_sources = (
            self._count_independent_sources(state)
        )

        return independent_sources >= 2

    # ==============================================================
    # Independent evidence sources
    # ==============================================================

    def _count_independent_sources(
        self,
        state: InvestigationState,
    ) -> int:

        evidence = state.evidence

        if evidence is None:
            return 0

        sources = 0

        if evidence.logs:
            sources += 1

        if evidence.metrics:
            sources += 1

        if evidence.traces:
            sources += 1

        if evidence.code:
            sources += 1

        if evidence.commits:
            sources += 1

        if evidence.diffs:
            sources += 1

        return sources

    # ==============================================================
    # Evidence-gap selection
    # ==============================================================

    def _select_next_gap(
        self,
        state: InvestigationState,
        gaps: list,
    ):

        called = set(state.tool_history)

        for gap in gaps:

            tool = getattr(
                gap,
                "tool",
                None,
            )

            if tool and tool not in called:
                return gap

        return None

    # ==============================================================
    # Helpers
    # ==============================================================

    @staticmethod
    def _gap_name(gap) -> str:

        name = getattr(
            gap,
            "name",
            None,
        )

        if name:
            return name

        tool = getattr(
            gap,
            "tool",
            None,
        )

        if tool:
            return tool

        return "unknown_evidence_gap"