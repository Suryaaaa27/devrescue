from dataclasses import dataclass
from typing import Any
from agent.evidence_value import EvidenceValueScorer
from agent.models import InvestigationAction
from agent.state import InvestigationState
from hypothesis.models import Hypothesis


@dataclass(frozen=True)
class EvidenceGap:
    name: str
    description: str
    priority: int
    tool: str
    arguments: dict[str, Any]


class HypothesisPlanner:
    """
    Deterministic planner that selects the highest-value missing evidence
    for the currently leading hypothesis.
    """

    def __init__(self, max_actions: int = 3):
        self.max_actions = max_actions
        self.value_scorer = EvidenceValueScorer()
    
    
    
    def identify_llm_guided_gaps(
        self,
        hypothesis: Hypothesis,
        state: InvestigationState,
    ) -> list[EvidenceGap]:
        """
        Translate unresolved LLM-reported missing evidence into
        deterministic evidence gaps.

        The LLM does not select tools directly.
        Only known, available investigation tools can
        be returned here.

        Missing-evidence requests remain actionable until
        the corresponding investigation tool has been called.
        """

        if not state.llm_reasoning_history:
            return []

        called = set(state.tool_history)

        # ---------------------------------------------------------
        # Collect unresolved missing evidence from LLM history.
        # Newer reasoning is considered first, while older requests
        # remain valid until their corresponding evidence is gathered.
        # ---------------------------------------------------------

        missing_evidence: list[str] = []

        for entry in reversed(state.llm_reasoning_history):
            reasoning = entry.get("reasoning", {})
            requests = reasoning.get(
                "missing_evidence",
                [],
            )

            for item in requests:
                item_text = str(item)

                if item_text not in missing_evidence:
                    missing_evidence.append(item_text)

        if not missing_evidence:
            return []

        text = " ".join(
            missing_evidence
        ).lower()

        gaps: list[EvidenceGap] = []

        # ---------------------------------------------------------
        # Database evidence
        # ---------------------------------------------------------

        database_keywords = (
            "database",
            "postgres",
            "postgresql",
            "mysql",
            "db",
            "connection",
        )

        if (
            any(
                keyword in text
                for keyword in database_keywords
            )
            and "investigate_database" not in called
            and (
                not state.available_tools
                or "investigate_database"
                in state.available_tools
            )
        ):
            gaps.append(
                EvidenceGap(
                    name="llm_database_evidence",
                    description=(
                        "The LLM identified unresolved missing "
                        "database evidence. Directly investigate "
                        "the database dependency using the "
                        "deterministic database investigation."
                    ),
                    priority=120,
                    tool="investigate_database",
                    arguments={
                        "service": state.service,
                    },
                )
            )

        # ---------------------------------------------------------
        # Trace evidence
        # ---------------------------------------------------------

        trace_keywords = (
            "trace",
            "span",
            "request lifecycle",
            "request path",
            "stack trace",
        )

        if (
            any(
                keyword in text
                for keyword in trace_keywords
            )
            and "find_traces" not in called
            and (
                not state.available_tools
                or "find_traces" in state.available_tools
            )
        ):
            gaps.append(
                EvidenceGap(
                    name="llm_trace_evidence",
                    description=(
                        "The LLM identified unresolved missing "
                        "request-level trace evidence. Inspect "
                        "traces to validate the causal path."
                    ),
                    priority=115,
                    tool="find_traces",
                    arguments={
                        "service": state.service,
                    },
                )
            )

        # ---------------------------------------------------------
        # Application log evidence
        # ---------------------------------------------------------

        log_keywords = (
            "log",
            "logs",
            "error message",
            "validation log",
            "application log",
        )

        if (
            any(
                keyword in text
                for keyword in log_keywords
            )
            and "search_logs" not in called
            and (
                not state.available_tools
                or "search_logs" in state.available_tools
            )
        ):
            gaps.append(
                EvidenceGap(
                    name="llm_application_logs",
                    description=(
                        "The LLM identified unresolved missing "
                        "application log evidence. Correlate "
                        "logs with the current hypothesis."
                    ),
                    priority=110,
                    tool="search_logs",
                    arguments={
                        "service": state.service,
                    },
                )
            )

        # ---------------------------------------------------------
        # Metric evidence
        # ---------------------------------------------------------

        metric_keywords = (
            "metric",
            "metrics",
            "failure rate",
            "request rate",
        )

        if (
            any(
                keyword in text
                for keyword in metric_keywords
            )
            and "query_metrics" not in called
            and (
                not state.available_tools
                or "query_metrics" in state.available_tools
            )
        ):
            gaps.append(
                EvidenceGap(
                    name="llm_failure_metrics",
                    description=(
                        "The LLM identified unresolved missing "
                        "metric evidence. Inspect service-level "
                        "failure metrics."
                    ),
                    priority=100,
                    tool="query_metrics",
                    arguments={
                        "query": "payment_failures_total",
                    },
                )
            )

        return gaps

    def identify_gaps(
        self,
        hypothesis: Hypothesis,
        state: InvestigationState,
    ) -> list[EvidenceGap]:

        gaps: list[EvidenceGap] = []

        evidence = state.evidence
        signals = set(evidence.signals if evidence else [])
        called = set(state.tool_history)

        # ---------------------------------------------------------
        # Database failure
        # ---------------------------------------------------------
        if hypothesis.category == "database_failure":

            if (
                "investigate_database" not in called
                and (
                    not state.available_tools
                    or "investigate_database" in state.available_tools
                )
            ):
                gaps.append(
                    EvidenceGap(
                        name="database_health",
                        description=(
                            "Directly investigate the database dependency "
                            "to determine whether it is available and "
                            "whether the connection failure is genuine."
                        ),
                        priority=100,
                        tool="investigate_database",
                        arguments={
                            "service": state.service,
                        },
                    )
                )

            if (
                "search_logs" not in called
                and (
                    not state.available_tools
                    or "search_logs" in state.available_tools
                )
            ):
                gaps.append(
                    EvidenceGap(
                        name="database_error_logs",
                        description=(
                            "Correlate application logs with the suspected "
                            "database failure."
                        ),
                        priority=70,
                        tool="search_logs",
                        arguments={
                            "service": state.service,
                        },
                    )
                )

            if (
               "find_traces" not in called
                and (
                    not state.available_tools
                    or "find_traces" in state.available_tools
                )
            ):
                gaps.append(
                    EvidenceGap(
                        name="database_request_trace",
                        description=(
                            "Inspect traces to determine whether requests "
                            "are failing while communicating with the "
                            "database dependency."
                        ),
                        priority=60,
                        tool="find_traces",
                        arguments={
                            "service": state.service,
                        },
                    )
                )

            if (
               "query_metrics" not in called
                and (
                    not state.available_tools
                    or "query_metrics" in state.available_tools
                )
            ):
                gaps.append(
                    EvidenceGap(
                        name="database_failure_metrics",
                        description=(
                            "Inspect failure metrics to determine whether "
                            "the suspected database failure is associated "
                            "with a broader service-level pattern."
                        ),
                        priority=40,
                        tool="query_metrics",
                        arguments={
                            "query": "payment_failures_total",
                        },
                    )
                )

        # ---------------------------------------------------------
        # Application validation failure
        # ---------------------------------------------------------
        elif hypothesis.category == "application_validation":

            if (
                "invalid_input" in signals
                and "find_traces" not in called
            ):
                gaps.append(
                    EvidenceGap(
                        name="failure_trace",
                        description=(
                            "Invalid input has been detected. A trace is "
                            "needed to verify that the failing operation "
                            "and request lifecycle match the hypothesis."
                        ),
                        priority=90,
                        tool="find_traces",
                        arguments={"service": state.service},
                    )
                )

        # ---------------------------------------------------------
        # Generic application error
        # ---------------------------------------------------------
        elif hypothesis.category == "application_error":

            if (
                "trace_error" in signals
                and "search_logs" not in called
            ):
                gaps.append(
                    EvidenceGap(
                        name="application_logs",
                        description=(
                            "The trace contains an error, but application "
                            "logs have not yet been correlated with it."
                        ),
                        priority=80,
                        tool="search_logs",
                        arguments={"service": state.service},
                    )
                )

        # ---------------------------------------------------------
        # Generic fallback investigation
        # ---------------------------------------------------------
        if not gaps:

            if "search_logs" not in called:
                gaps.append(
                    EvidenceGap(
                        name="application_logs",
                        description=(
                            "Logs provide broad evidence about the failure "
                            "and are useful for identifying the first "
                            "observable error."
                        ),
                        priority=50,
                        tool="search_logs",
                        arguments={"service": state.service},
                    )
                )

            elif "find_traces" not in called:
                gaps.append(
                    EvidenceGap(
                        name="request_trace",
                        description=(
                            "A request trace can establish the failing "
                            "operation and connect errors to a specific "
                            "request."
                        ),
                        priority=40,
                        tool="find_traces",
                        arguments={"service": state.service},
                    )
                )

            elif "query_metrics" not in called:
                gaps.append(
                    EvidenceGap(
                        name="failure_metrics",
                        description=(
                            "Failure metrics can establish whether the "
                            "observed error is isolated or part of a "
                            "broader service-level pattern."
                        ),
                        priority=30,
                        tool="query_metrics",
                        arguments={
                            "query": "payment_failures_total"
                        },
                    )
                )

        gaps.sort(
            key=lambda gap: gap.priority,
            reverse=True,
        )

        return gaps[: self.max_actions]

    def identify_discriminating_gaps(
        self,
        hypotheses: list[Hypothesis],
        state: InvestigationState,
    ) -> list[EvidenceGap]:
        """
        Identify evidence that can distinguish between competing
        hypotheses rather than simply strengthening the current leader.
        """

        if len(hypotheses) < 2:
            return []

        ranked = sorted(
            hypotheses,
            key=lambda h: (
                h.score,
                h.confidence,
            ),
            reverse=True,
        )

        leader = ranked[0]
        challenger = ranked[1]

        gaps: list[EvidenceGap] = []

        # Database vs application error.
        if {
            leader.category,
            challenger.category,
        } == {
            "database_failure",
            "application_error",
        }:
            if "investigate_database" not in state.tool_history:
                gaps.append(
                    EvidenceGap(
                        name="database_vs_application",
                        description=(
                            "The leading hypotheses are a database "
                            "dependency failure and an application error. "
                            "Direct database investigation provides "
                            "discriminating evidence between them."
                        ),
                        priority=110,
                        tool="investigate_database",
                        arguments={"service": state.service},
                    )
                )

        return gaps

    def plan_for_hypothesis(
        self,
        hypothesis: Hypothesis,
        state: InvestigationState,
    ) -> InvestigationAction | None:

        ranked_actions = self.rank_actions(
            hypothesis=hypothesis,
            state=state,
        )

        if not ranked_actions:
            return None

        gap, value_score, value_reason = ranked_actions[0]

        return InvestigationAction(
            tool=gap.tool,
            arguments=gap.arguments,
            reason=(
                f"Selected '{gap.name}' for hypothesis "
                f"'{hypothesis.name}'. "
                f"Evidence value={value_score:.2f}. "
                f"{value_reason} "
                f"{gap.description}"
            ),
        )
        
    def rank_actions(self, hypothesis, state):
        gaps = self.identify_gaps(
            hypothesis=hypothesis,
            state=state,
        )
        
        
        llm_gaps = self.identify_llm_guided_gaps(
            state=state,
            hypothesis=hypothesis,
        )

        existing = {
            (gap.tool, gap.name)
            for gap in gaps
        }

        for gap in llm_gaps:
            key = (gap.tool, gap.name)

            if key not in existing:
                gaps.append(gap)
        ranked = []

        for gap in gaps:
            value = self.value_scorer.score(
                tool=gap.tool,
                hypothesis=hypothesis,
                state=state,
            )

            final_score = value.score
            final_reason = value.reason

        # LLM-requested evidence receives a bounded
        # planning bonus. The LLM does not execute
        # tools or override deterministic evidence;
        # it only tells the planner which missing
        # evidence may be valuable.
            if gap.name.startswith("llm_"):
                final_score += 0.25

                final_reason = (
                    "LLM-guided evidence request. "
                    + value.reason
                )

            ranked.append(
               (
                    gap,
                    final_score,
                    final_reason,
               )
            )
        ranked.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return ranked