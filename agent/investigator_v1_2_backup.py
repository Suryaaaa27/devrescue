from __future__ import annotations

from typing import Any, Callable

from agent.decision import InvestigationDecisionEngine
from agent.models import InvestigationAction, InvestigationResult
from agent.state import InvestigationState
from evidence.engine import EvidenceEngine
from hypothesis.engine import HypothesisEngine


Tool = Callable[..., dict[str, Any]]


class InvestigationAgent:
    """
    Deterministic adaptive investigation agent.

    The agent repeatedly:
    1. inspects the current investigation state
    2. chooses the highest-value next action
    3. executes the tool
    4. updates evidence
    5. evaluates hypotheses
    6. stops when a sufficiently supported root cause exists
    """

    def __init__(
        self,
        tools: dict[str, Tool],
        max_iterations: int = 8,
    ):
        self.tools = tools
        self.max_iterations = max_iterations

        self.evidence_engine = EvidenceEngine()
        self.hypothesis_engine = HypothesisEngine()

    def investigate(
        self,
        incident: str,
        service: str,
    ) -> InvestigationResult:

        state = InvestigationState(
            incident=incident,
            service=service,
            max_iterations=self.max_iterations,
        )

        while not state.completed and state.iteration < state.max_iterations:

            state.iteration += 1

            action = self._plan_next_action(state)

            if action is None:
                state.completed = True
                break

            self._execute_action(state, action)

            self._update_evidence(state)

            self._evaluate_hypotheses(state)

            decision = self.decision_engine.decide(state)
            
            state.decision = decision.to_dict()

            state.investigation_notes.append(
                (
                    f"Decision: {decision.decision}. "
                    f"{decision.reason}"
                )
            )

            if decision.decision in {
                InvestigationDecisionEngine.CONCLUDE,
                InvestigationDecisionEngine.INSUFFICIENT_EVIDENCE,
            }:
                state.completed = True
                break
            
            if self._has_sufficient_evidence(state):
                state.completed = True
                break
        return self._build_result(state)

    # ------------------------------------------------------------------
    # Adaptive planner
    # ------------------------------------------------------------------

    def _plan_next_action(
        self,
        state: InvestigationState,
    ) -> InvestigationAction | None:

        called = set(state.tool_history)

        # --------------------------------------------------------------
        # 1. Establish baseline service health
        # --------------------------------------------------------------

        if "get_service_health" not in called:

            return InvestigationAction(
                tool="get_service_health",
                arguments={},
                reason=(
                    "Establish the current health state of the affected "
                    "service before deeper investigation."
                ),
            )

        # --------------------------------------------------------------
        # 2. Discover initial evidence
        # --------------------------------------------------------------

        if "search_logs" not in called:

            return InvestigationAction(
                tool="search_logs",
                arguments={
                    "query": "",
                    "service": state.service,
                    "limit": 50,
                },
                reason=(
                    "Inspect recent service logs to discover failures, "
                    "request identifiers, trace identifiers, and clues "
                    "about the failure domain."
                ),
            )

        # --------------------------------------------------------------
        # 3. Adaptive evidence-driven investigation
        # --------------------------------------------------------------

        signals = self._collect_signal_text(state)

        # Database-related evidence
        if (
            self._contains_any(
                signals,
                [
                    "database",
                    "db connection",
                    "connection refused",
                    "postgres",
                    "postgresql",
                    "mysql",
                    "mongodb",
                    "mongo",
                    "sql",
                    "deadlock",
                    "timeout",
                ],
            )
            and "investigate_database" not in called
        ):

            if "investigate_database" in self.tools:

                return InvestigationAction(
                    tool="investigate_database",
                    arguments={
                        "service": state.service,
                    },
                    reason=(
                        "Logs contain database-related failure signals. "
                        "Investigate the database dependency before "
                        "continuing with generic diagnostics."
                    ),
                )

        # Deployment / code-change evidence
        if (
            self._contains_any(
                signals,
                [
                    "deployment",
                    "deployed",
                    "release",
                    "commit",
                    "revision",
                    "version changed",
                ],
            )
            and "github" not in called
        ):

            if "search_code_changes" in self.tools:

                return InvestigationAction(
                    tool="search_code_changes",
                    arguments={
                        "service": state.service,
                    },
                    reason=(
                        "Evidence suggests a recent deployment or code "
                        "change. Investigate repository history and "
                        "recent changes."
                    ),
                )

        # Downstream dependency evidence
        if (
            self._contains_any(
                signals,
                [
                    "downstream",
                    "upstream",
                    "http 5",
                    "status_code=500",
                    "status_code=502",
                    "status_code=503",
                    "dependency failure",
                ]
            )
            and "downstream" not in called
        ):

            if "find_downstream_service" in self.tools:

                return InvestigationAction(
                    tool="find_downstream_service",
                    arguments={
                        "service": state.service,
                    },
                    reason=(
                        "Evidence indicates a downstream dependency "
                        "failure. Identify and investigate the affected "
                        "dependency."
                    ),
                )

        # --------------------------------------------------------------
        # 4. Trace investigation
        # --------------------------------------------------------------

        trace_id = self._select_trace_id(state)

        if trace_id and "find_traces" not in called:

            return InvestigationAction(
                tool="find_traces",
                arguments={
                    "service": state.service,
                    "trace_id": trace_id,
                    "limit": 10,
                },
                reason=(
                    "A trace identifier was discovered in the evidence. "
                    "Inspect the distributed trace for the failing "
                    "operation and structured error information."
                ),
            )

        # --------------------------------------------------------------
        # 5. Metrics investigation
        # --------------------------------------------------------------

        if "query_metrics" not in called:

            return InvestigationAction(
                tool="query_metrics",
                arguments={
                    "query": "payment_failures_total",
                },
                reason=(
                    "No sufficiently supported root cause has been "
                    "established. Check application failure metrics for "
                    "service-level confirmation."
                ),
            )

        # --------------------------------------------------------------
        # 6. Nothing useful left to investigate
        # --------------------------------------------------------------

        return None

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    def _execute_action(
        self,
        state: InvestigationState,
        action: InvestigationAction,
    ) -> None:

        tool = self.tools.get(action.tool)

        if tool is None:

            state.add_note(
                f"Tool '{action.tool}' is not available."
            )

            state.record_tool_call(
                action.tool,
                {
                    "error": f"Tool '{action.tool}' is not available."
                },
            )

            return

        try:

            result = tool(**action.arguments)

        except Exception as exc:

            result = {
                "error": str(exc),
            }

        state.record_tool_call(
            action.tool,
            result,
        )

        if action.tool == "search_logs":

            state.log_result = result

        elif action.tool == "query_metrics":

            query = action.arguments.get("query", "")

            for metric_result in result.get("results", []):

                state.metric_results.append(
                    {
                        "metric": metric_result.get(
                            "metric",
                            {},
                        ),
                        "value": metric_result.get(
                            "value",
                        ),
                        "query": query,
                    }
                )

        elif action.tool == "find_traces":

            state.trace_result = result

    # ------------------------------------------------------------------
    # Evidence
    # ------------------------------------------------------------------

    def _update_evidence(
        self,
        state: InvestigationState,
    ) -> None:

        state.evidence = self.evidence_engine.build(
            service=state.service,
            log_result=state.log_result,
            metric_results=state.metric_results,
            trace_result=state.trace_result,
        )

        # Normalize results from domain-specific investigation tools into
        # first-class hypothesis signals without pretending they are logs,
        # metrics, or traces.
        self._normalize_domain_evidence(state)

    def _normalize_domain_evidence(
        self,
        state: InvestigationState,
    ) -> None:
        if state.evidence is None:
            return

        domain_evidence = []

        for tool_name, results in state.tool_results.items():
            if tool_name == "investigate_database":
                for result in results:
                    if not isinstance(result, dict):
                        continue

                    normalized = {
                        "tool": tool_name,
                        "service": result.get("service", state.service),
                        "database": result.get("database"),
                        "status": result.get("status"),
                        "error": result.get("error"),
                    }
                    domain_evidence.append(normalized)

                    status = str(result.get("status", "")).lower()
                    error = str(result.get("error", "")).lower()

                    if status == "unavailable":
                        if "database_unavailable" not in state.evidence.signals:
                            state.evidence.signals.append(
                                "database_unavailable"
                            )

                    if any(
                        phrase in error
                        for phrase in (
                            "connection refused",
                            "connection failed",
                            "could not connect",
                            "unable to connect",
                        )
                    ):
                        if (
                            "database_connection_failure"
                            not in state.evidence.signals
                        ):
                            state.evidence.signals.append(
                                "database_connection_failure"
                            )

        if domain_evidence:
            state.evidence.summary["domain_evidence"] = domain_evidence
            state.evidence.summary["domain_evidence_count"] = len(
                domain_evidence
            )

            # Domain evidence is a separate source, but individual domain
            # tool results must not be counted multiple times.
            state.evidence.summary["domain_tools"] = sorted(
                {item["tool"] for item in domain_evidence}
            )

    # ------------------------------------------------------------------
    # Hypothesis evaluation
    # ------------------------------------------------------------------

    def _evaluate_hypotheses(
        self,
        state: InvestigationState,
    ) -> None:

        if state.evidence is None:
            return

        state.hypotheses = (
            self.hypothesis_engine.analyze(
                state.evidence
            )
        )

        if state.hypotheses:

            state.selected_hypothesis = (
                state.hypotheses[0]
            )

    # ------------------------------------------------------------------
    # Sufficiency
    # ------------------------------------------------------------------

    def _has_sufficient_evidence(
        self,
        state: InvestigationState,
    ) -> bool:

        if state.evidence is None:
            return False

        hypothesis = state.selected_hypothesis

        if hypothesis is None:
            return False

        if hypothesis.role != "root_cause":
            return False

        if hypothesis.confidence < 0.75:
            return False

        independent_sources = 0

        if state.evidence.logs:
            independent_sources += 1

        if state.evidence.metrics:
            independent_sources += 1

        if state.evidence.traces:
            independent_sources += 1

        if state.evidence.summary.get("domain_evidence_count", 0) > 0:
            independent_sources += 1

        return independent_sources >= 2

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _select_trace_id(
        state: InvestigationState,
    ) -> str | None:

        if state.evidence and state.evidence.trace_ids:

            return sorted(
                state.evidence.trace_ids
            )[0]

        for item in state.log_result.get(
            "results",
            [],
        ):

            trace_id = item.get("trace_id")

            if trace_id:
                return trace_id

        return None

    @staticmethod
    def _collect_signal_text(
        state: InvestigationState,
    ) -> list[str]:

        text: list[str] = []

        # Primary evidence source: normalized log messages.
        for item in state.log_result.get(
            "results",
            [],
        ):

            message = item.get(
                "message",
                "",
            )

            if message:
                text.append(
                    str(message).lower()
                )

        # Derived evidence signals from the Evidence Engine.
        if state.evidence:

            text.extend(
                signal.lower()
                for signal in state.evidence.signals
            )

        # Results returned by adaptive/domain-specific tools are also
        # investigation evidence. The state already records every tool
        # result, so the planner can reason over newly discovered facts
        # instead of repeatedly issuing the same action.
        for tool_results in state.tool_results.values():

            for result in tool_results:

                if not isinstance(result, dict):
                    continue

                for key, value in result.items():

                    if key in {"service", "query"}:
                        continue

                    if value is None:
                        continue

                    text.append(
                        f"{key}={value}".lower()
                    )

        return text

    @staticmethod
    def _contains_any(
        values: list[str],
        keywords: list[str],
    ) -> bool:

        for value in values:

            for keyword in keywords:

                if keyword in value:
                    return True

        return False

    # ------------------------------------------------------------------
    # Result
    # ------------------------------------------------------------------

    def _build_result(
        self,
        state: InvestigationState,
    ) -> InvestigationResult:

        hypothesis = (
            state.selected_hypothesis
        )

        if hypothesis:

            status = "ROOT_CAUSE_IDENTIFIED"

            root_cause = hypothesis.name
            confidence = hypothesis.confidence
            explanation = hypothesis.explanation

        else:

            status = "INVESTIGATION_INCOMPLETE"

            root_cause = None
            confidence = 0.0
            explanation = None

        evidence_summary = {}

        if state.evidence:

            evidence_summary = (
                state.evidence.summary
            )

        return InvestigationResult(
            incident=state.incident,
            service=state.service,
            status=status,
            root_cause=root_cause,
            confidence=confidence,
            explanation=explanation,
            iterations=state.iteration,
            tools_called=state.tool_history,
            evidence_summary=evidence_summary,
            hypotheses=[
                hypothesis.to_dict()
                for hypothesis in state.hypotheses
            ],
        )