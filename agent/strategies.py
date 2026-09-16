from typing import Optional

from agent.models import InvestigationAction
from agent.state import InvestigationState
from hypothesis.models import Hypothesis
from agent.planner import HypothesisPlanner


class BootstrapPlanningStrategy:
    """
    Handles the initial investigation phase before a reliable
    root-cause hypothesis exists.
    """

    def plan(
        self,
        state: InvestigationState,
        available_tools: set[str],
    ) -> Optional[InvestigationAction]:

        # -----------------------------------------------------
        # Service health
        # -----------------------------------------------------
        if (
            "get_service_health" in available_tools
            and "get_service_health" not in state.tool_history
        ):
            return InvestigationAction(
                tool="get_service_health",
                arguments={
                    "service": state.service,
                },
                reason=(
                    "Start with service health to establish the "
                    "initial state of the affected service."
                ),
            )

        # -----------------------------------------------------
        # Application logs
        # -----------------------------------------------------
        if (
            "search_logs" in available_tools
            and "search_logs" not in state.tool_history
        ):
            return InvestigationAction(
                tool="search_logs",
                arguments={
                    "service": state.service,
                },
                reason=(
                    "Search application logs to identify the first "
                    "observable failure."
                ),
            )

        # -----------------------------------------------------
        # Domain bootstrap
        # -----------------------------------------------------
        incident_text = state.incident.lower()

        database_referenced = any(
            keyword in incident_text
            for keyword in (
                "database",
                "postgres",
                "postgresql",
                "mysql",
                "sql",
            )
        )

        if (
            database_referenced
            and "investigate_database" in available_tools
            and "investigate_database" not in state.tool_history
        ):
            return InvestigationAction(
                tool="investigate_database",
                arguments={
                    "service": state.service,
                },
                reason=(
                    "The incident explicitly references a database "
                    "dependency failure. Directly investigating the "
                    "database dependency provides the domain evidence "
                    "needed to establish or eliminate a database-related "
                    "root cause."
                ),
            )

        # -----------------------------------------------------
        # Distributed traces
        # -----------------------------------------------------
        if (
            "find_traces" in available_tools
            and "find_traces" not in state.tool_history
        ):
            return InvestigationAction(
                tool="find_traces",
                arguments={
                    "service": state.service,
                },
                reason=(
                    "Inspect distributed traces to identify the "
                    "failing operation."
                ),
            )

        # -----------------------------------------------------
        # Metrics
        # -----------------------------------------------------
        if (
            "query_metrics" in available_tools
            and "query_metrics" not in state.tool_history
        ):
            return InvestigationAction(
                tool="query_metrics",
                arguments={
                    "query": "payment_failures_total",
                },
                reason=(
                    "Inspect failure metrics to determine whether "
                    "the incident is isolated or systemic."
                ),
            )

        return None


class HypothesisPlanningStrategy:
    """
    Handles investigation after one or more hypotheses exist.
    """

    def __init__(self):
        self.planner = HypothesisPlanner()

    def plan(
        self,
        hypothesis: Hypothesis,
        state: InvestigationState,
    ) -> Optional[InvestigationAction]:

        return self.planner.plan_for_hypothesis(
            hypothesis=hypothesis,
            state=state,
        )


class InvestigationPlanningEngine:
    """
    Coordinates the available planning strategies.
    """

    def __init__(self):
        self.bootstrap = BootstrapPlanningStrategy()
        self.hypothesis = HypothesisPlanningStrategy()

    def plan(
        self,
        state: InvestigationState,
        available_tools: set[str],
    ) -> Optional[InvestigationAction]:

        # No reliable hypothesis yet.
        if state.selected_hypothesis is None:
            return self.bootstrap.plan(
                state=state,
                available_tools=available_tools,
            )

        # Hypothesis-driven investigation.
        return self.hypothesis.plan(
            hypothesis=state.selected_hypothesis,
            state=state,
        )