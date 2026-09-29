from typing import Any, Callable, Optional

from agent.models import (
    InvestigationAction,
    InvestigationResult,
)
from agent.state import InvestigationState

from evidence.engine import EvidenceEngine

from hypothesis.engine import HypothesisEngine
from agent.strategies import InvestigationPlanningEngine
from agent.uncertainty import UncertaintyAnalyzer
from agent.llm.context import build_llm_context
from agent.decision import InvestigationDecisionEngine

Tool = Callable[..., dict[str, Any]]

class InvestigationAgent:
    """
    Adaptive investigation agent.

    v1.3 adds hypothesis-driven planning on top of
    the existing v1.2 investigation workflow.

    Investigation lifecycle:

        Initial evidence
            ↓
        Evidence Engine
            ↓
        Hypothesis Engine
            ↓
        Hypothesis Planner
            ↓
        Missing evidence
            ↓
        MCP investigation
            ↓
        Evidence Engine
            ↓
        Hypothesis Engine
            ↓
        ...
    """

    def __init__(
        self,
        tools: dict[str, Tool],
        max_iterations: int = 8,
        llm_reasoner=None,
    ):

        self.tools = tools

        self.max_iterations = max_iterations

        self.evidence_engine = EvidenceEngine()

        self.hypothesis_engine = HypothesisEngine()

        self.planning_engine = InvestigationPlanningEngine()
        self.uncertainty_analyzer = UncertaintyAnalyzer()
        self.decision_engine = InvestigationDecisionEngine()
        self.llm_reasoner = llm_reasoner
        self.hypothesis_planner = (
            self.planning_engine.hypothesis.planner
        )
    def _assess_uncertainty(self, state):
        return self.uncertainty_analyzer.assess(state)
    # =====================================================
    # PUBLIC API
    # =====================================================

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

        state.available_tools = set(
            self.tools.keys()
        )

        while (
            not state.completed
            and state.iteration < state.max_iterations
        ):

            state.iteration += 1

            # -------------------------------------------------
            # PLAN
            # -------------------------------------------------

            action = self._plan_next_action(state)

            

            if action is None:
                state.completed = True
                break

            # -------------------------------------------------
            # CAPTURE PLANNING DECISION
            # -------------------------------------------------

            current_hypothesis = (
                state.selected_hypothesis
            )

            state.record_plan(
                tool=action.tool,
                reason=action.reason,
                hypothesis=(
                    current_hypothesis.name
                    if current_hypothesis
                    else None
                ),
                mode=(
                    "hypothesis_driven"
                    if current_hypothesis
                    else "discovery"
                ),
            )

            # -------------------------------------------------
            # EXECUTE EXACTLY ONCE
            # -------------------------------------------------

            result = self._execute_action(
                state,
                action,
            )

            # -------------------------------------------------
            # STORE TYPED OBSERVABILITY RESULT
            # -------------------------------------------------

            self._store_typed_result(
                state,
                action.tool,
                result,
            )

            # -------------------------------------------------
            # REBUILD EVIDENCE
            # -------------------------------------------------

            self._update_evidence(
                state
            )

            # -------------------------------------------------
            # RE-EVALUATE HYPOTHESES
            # -------------------------------------------------

            self._evaluate_hypotheses(
                state
            )

            state.record_hypotheses()

            decision = self.decision_engine.decide(
                state
            )

            state.decision = decision.to_dict()

            # state.add_note(
            #     (
            #         f"Decision: {decision.decision}. "
            #         f"{decision.reason}"
            #     )
            # )

            uncertainty = (
                self.uncertainty_analyzer.assess(state)
            )

            llm_result = self._run_llm_reasoning(state)

            if llm_result:
                state.add_llm_reasoning(
                    llm_result
                )

            if decision.decision in {
                InvestigationDecisionEngine.CONCLUDE,
                InvestigationDecisionEngine.INSUFFICIENT_EVIDENCE,
            }:
                state.completed = True
                break

        return self._build_result(
            state
        )

    # =====================================================
    # PLANNING
    # =====================================================

    def _plan_next_action(
        self,
        state: InvestigationState,
    ) -> InvestigationAction | None:

        # -------------------------------------------------
        # Decision-driven continuation
        # -------------------------------------------------

        if state.decision:

            decision_type = state.decision.get(
                "decision"
            )

            next_action = state.decision.get(
                "next_action"
            )

            if (
                decision_type == "INVESTIGATE"
                and next_action
                and next_action in self.tools
                and next_action not in state.tool_history
            ):

                return self._build_decision_action(
                    state,
                    next_action,
                )

        return self.planning_engine.plan(
            state=state,
            available_tools=set(self.tools.keys()),
        )

    def _build_decision_action(
        self,
        state: InvestigationState,
        tool: str,
    ) -> InvestigationAction:

        hypothesis = (
            state.selected_hypothesis
        )

        hypothesis_name = (
            hypothesis.name
            if hypothesis
            else "current investigation"
        )

        if tool == "search_code":

            query = (
                self.hypothesis_planner
                ._build_code_search_query(
                    hypothesis=hypothesis,
                    state=state,
                )
            )

            return InvestigationAction(
                tool="search_code",
                arguments={
                    "query": query,
                },
                reason=(
                    "Investigate source code relevant "
                    f"to hypothesis '{hypothesis_name}'."
                ),
            )

        if tool == "investigate_database":
            return InvestigationAction(
                tool="investigate_database",
                arguments={
                    "service": state.service,
                },
                reason=(
                    "Investigate the database dependency failure "
                    "because database health evidence is needed "
                    "to determine whether the database is the "
                    "underlying cause of the service failure."
                ),
            )
            

        return InvestigationAction(
            tool=tool,
            arguments={
                "service": state.service,
            },
            reason=(
                "Investigate the evidence gap associated "
                f"with hypothesis '{hypothesis_name}'."
            ),
        )
    def _run_llm_reasoning(
        self,
        state: InvestigationState,
    ):

        if self.llm_reasoner is None:
            return None

        uncertainty = (
            self.uncertainty_analyzer.assess(state)
        )

        context = build_llm_context(
            state,
            uncertainty,
        )

        return self.llm_reasoner.reason(
            incident=context["incident"],
            service=context["service"],
            evidence_summary=context["evidence_summary"],
            hypotheses=context["hypotheses"],
            uncertainty=context["uncertainty"],
            investigation_history=(
                context["investigation_history"]
            ),
        )
    def _latest_llm_reasoning(
        self,
        state: InvestigationState,
    ) -> dict[str, Any] | None:

        if not state.llm_reasoning_history:
            return None

        return state.llm_reasoning_history[-1]["reasoning"]
    # =====================================================
    # HYPOTHESIS SELECTION
    # =====================================================

    def _select_best_hypothesis(
        self,
        state: InvestigationState,
    ):

        if not state.hypotheses:

            return None

        ranked = sorted(
            state.hypotheses,
            key=lambda hypothesis: (
                hypothesis.role == "root_cause",
                hypothesis.confidence,
                hypothesis.score,
            ),
            reverse=True,
        )

        return ranked[0]

    # =====================================================
    # EXECUTION
    # =====================================================

    def _execute_action(
        self,
        state: InvestigationState,
        action: InvestigationAction,
    ) -> dict[str, Any]:

        tool = self.tools.get(
            action.tool
        )

        if tool is None:

            result = {
                "status": "tool_unavailable",
                "tool": action.tool,
                "error": (
                    f"Investigation tool "
                    f"'{action.tool}' is not configured."
                ),
            }

            state.record_tool_call(
                action.tool,
                result,
            )

            return result

        try:

            result = tool(
                **action.arguments
            )

        except Exception as exc:

            result = {
                "status": "tool_error",
                "tool": action.tool,
                "error": str(exc),
            }

        state.record_tool_call(
            action.tool,
            result,
        )

        return result
    # =====================================================
    # TYPED TOOL RESULT ROUTING
    # =====================================================

    def _store_typed_result(
        self,
        state: InvestigationState,
        tool: str,
        result: dict[str, Any],
    ):
        """
        Route MCP/tool results into the typed state fields
        consumed by the Evidence Engine.

        Generic tool history is retained separately in
        state.tool_results.
        """

        if tool == "search_logs":

            state.log_result = result

        elif tool == "query_metrics":

            state.metric_results.append(
                result
            )

        elif tool == "find_traces":

            state.trace_result = result

        elif tool in {
            "get_file",
            "search_code",
        }:

            state.code_results.append(
                result
            )

        elif tool in {
            "list_commits",
            "get_commit",
        }:

            state.commit_results.append(
                result
            )

        elif tool == "get_diff":

            state.diff_results.append(
                result
            )
    # =====================================================
    # EVIDENCE
    # =====================================================

    def _update_evidence(
        self,
        state: InvestigationState,
    ):

        state.evidence = (
            self.evidence_engine.build(
                service=state.service,
                log_result=state.log_result,
                metric_results=state.metric_results,
                trace_result=state.trace_result,
                code_results=state.code_results,
                commit_results=state.commit_results,
                diff_results=state.diff_results,
            )
        )

        self._normalize_domain_evidence(
            state
        )

    def _normalize_domain_evidence(
        self,
        state: InvestigationState,
    ):

        if state.evidence is None:

            return

        domain_evidence = []

        database_results = (
            state.tool_results.get(
                "investigate_database",
                [],
            )
        )

        for result in database_results:

            item = {
                "tool": "investigate_database",
                "service": result.get(
                    "service",
                    state.service,
                ),
                "database": result.get(
                    "database"
                ),
                "status": result.get(
                    "status"
                ),
                "error": result.get(
                    "error"
                ),
            }

            domain_evidence.append(
                item
            )

            status = str(
                result.get(
                    "status",
                    "",
                )
            ).lower()

            error = str(
                result.get(
                    "error",
                    "",
                )
            ).lower()

            if status == "unavailable":

                self._add_signal(
                    state,
                    "database_unavailable",
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

                self._add_signal(
                    state,
                    "database_connection_failure",
                )

        if domain_evidence:

            state.evidence.summary[
                "domain_evidence"
            ] = domain_evidence

            state.evidence.summary[
                "domain_evidence_count"
            ] = len(
                domain_evidence
            )

            state.evidence.summary[
                "domain_tools"
            ] = sorted(
                {
                    item["tool"]
                    for item in domain_evidence
                }
            )

    def _add_signal(
        self,
        state: InvestigationState,
        signal: str,
    ):

        if state.evidence is None:

            return

        if signal not in state.evidence.signals:

            state.evidence.signals.append(
                signal
            )

    # =====================================================
    # HYPOTHESIS EVALUATION
    # =====================================================

    def _evaluate_hypotheses(
        self,
        state: InvestigationState,
    ):

        if state.evidence is None:

            return

        state.hypotheses = (
            self.hypothesis_engine.analyze(
                state.evidence
            )
        )

        state.selected_hypothesis = (
            self._select_best_hypothesis(
                state
            )
        )

    # =====================================================
    # SUFFICIENCY
    # =====================================================

    def _should_stop(
        self,
        state: InvestigationState,
    ) -> bool:
        """
        Decide whether the investigation has enough independent evidence
        to safely identify a root cause.
        """

        if state.selected_hypothesis is None:
            return False

        hypothesis = state.selected_hypothesis

        if hypothesis.role != "root_cause":
            return False

        if hypothesis.confidence < 0.75:
            return False

        return self._has_sufficient_evidence(state)

    def _has_sufficient_evidence(
        self,
        state: InvestigationState,
    ) -> bool:

        assessment = self._assess_uncertainty(state)

        return not assessment.should_continue

    # =====================================================
    # SIGNAL EXTRACTION
    # =====================================================

    def _collect_signal_text(
        self,
        state: InvestigationState,
    ) -> str:

        chunks: list[str] = []

        if state.evidence:

            chunks.extend(
                state.evidence.signals
            )

            for log in state.evidence.logs:

                chunks.append(
                    log.message
                )

        for results in (
            state.tool_results.values()
        ):

            for result in results:

                chunks.append(
                    str(result)
                )

        return " ".join(
            chunks
        ).lower()

    def _contains_database_signal(
        self,
        text: str,
    ) -> bool:

        keywords = (
            "database",
            "postgres",
            "postgresql",
            "mysql",
            "connection refused",
            "connection failed",
            "db error",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    def _contains_deployment_signal(
        self,
        text: str,
    ) -> bool:

        keywords = (
            "deployment",
            "deployed",
            "release",
            "rollback",
            "version",
            "commit",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    def _contains_downstream_signal(
        self,
        text: str,
    ) -> bool:

        keywords = (
            "downstream",
            "dependency",
            "upstream",
            "timeout",
            "connection reset",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    # =====================================================
    # TRACE SELECTION
    # =====================================================

    def _select_trace_id(
        self,
        state: InvestigationState,
    ) -> Optional[str]:

        if (
            state.evidence
            and state.evidence.trace_ids
        ):

            return sorted(
                state.evidence.trace_ids
            )[0]

        for log in (
            state.evidence.logs
            if state.evidence
            else []
        ):

            if log.trace_id:

                return log.trace_id

        return None

    # =====================================================
    # RESULT
    # =====================================================

    def _uncertainty_to_dict(
        self,
        assessment,
    ):
        return {
            "leading_hypothesis": assessment.leading_hypothesis,
            "leading_confidence": assessment.leading_confidence,
            "runner_up_hypothesis": assessment.runner_up_hypothesis,
            "runner_up_confidence": assessment.runner_up_confidence,
            "confidence_gap": assessment.confidence_gap,
            "uncertainty": assessment.uncertainty,
            "independent_evidence_count": (
                assessment.independent_evidence_count
            ),
            "sufficient_confidence": (
                assessment.sufficient_confidence
            ),
            "sufficient_separation": (
                assessment.sufficient_separation
            ),
            "should_continue": (
                assessment.should_continue
            ),
            "reason": assessment.reason,
        }

    def _build_result(
        self,
        state: InvestigationState,
    ) -> InvestigationResult:

        hypothesis = (
            state.selected_hypothesis
        )

        if (
            hypothesis
            and hypothesis.role == "root_cause"
            and hypothesis.confidence >= 0.75
        ):

            status = (
                "ROOT_CAUSE_IDENTIFIED"
            )

            root_cause = (
                hypothesis.name
            )

            confidence = (
                hypothesis.confidence
            )

            explanation = (
                hypothesis.explanation
            )

        else:

            status = (
                "INVESTIGATION_INCOMPLETE"
            )

            root_cause = None

            confidence = (
                hypothesis.confidence
                if hypothesis
                else 0.0
            )

            explanation = (
                hypothesis.explanation
                if hypothesis
                else None
            )

        evidence_summary = {}

        if state.evidence:

            evidence_summary = (
                state.evidence.summary
            )

            evidence_summary[
                "signals"
            ] = list(
                state.evidence.signals
            )

        assessment = self._assess_uncertainty(state)

        uncertainty = self._uncertainty_to_dict(
            assessment
        )

        return InvestigationResult(
            incident=state.incident,
            service=state.service,
            status=status,
            root_cause=root_cause,
            confidence=confidence,
            explanation=explanation,
            iterations=state.iteration,
            tools_called=list(
                state.tool_history
            ),
            evidence_summary=evidence_summary,
            hypotheses=[
                hypothesis.to_dict()
                for hypothesis in state.hypotheses
            ],
            planning_history=list(
                state.planning_history
            ),
            investigation_notes=list(
                state.investigation_notes
            ),
            hypothesis_history=list(
                state.hypothesis_history
            ),
            evidence_gaps=list(
                state.evidence_gaps
            ),
            action_outcomes=list(
                state.action_outcomes
            ),
            uncertainty=uncertainty,
            decision=state.decision,
            llm_reasoning=(
                state.llm_reasoning_history[-1]["reasoning"]
                if state.llm_reasoning_history
                else None
            ),
            llm_reasoning_history=list(
                state.llm_reasoning_history
            ),
        )