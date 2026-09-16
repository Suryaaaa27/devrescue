from agent.models import InvestigationAction
from agent.state import InvestigationState
from agent.strategies import (
    BootstrapPlanningStrategy,
    InvestigationPlanningEngine,
)


def test_bootstrap_strategy_starts_with_health():

    state = InvestigationState(
        incident="payment failures",
        service="payment-service",
    )

    strategy = BootstrapPlanningStrategy()

    action = strategy.plan(
        state=state,
        available_tools={
            "get_service_health",
            "search_logs",
        },
    )

    assert action is not None
    assert action.tool == "get_service_health"


def test_bootstrap_strategy_detects_database_domain():

    state = InvestigationState(
        incident="payment-service database failures",
        service="payment-service",
    )

    state.tool_history = [
        "get_service_health",
        "search_logs",
    ]

    strategy = BootstrapPlanningStrategy()

    action = strategy.plan(
        state=state,
        available_tools={
            "get_service_health",
            "search_logs",
            "investigate_database",
        },
    )

    assert action is not None
    assert action.tool == "investigate_database"

    assert "database dependency failure" in (
        action.reason.lower()
    )


def test_bootstrap_strategy_does_not_require_unavailable_tools():

    state = InvestigationState(
        incident="payment failures",
        service="payment-service",
    )

    state.tool_history = [
        "get_service_health",
        "search_logs",
    ]

    strategy = BootstrapPlanningStrategy()

    action = strategy.plan(
        state=state,
        available_tools={
            "get_service_health",
            "search_logs",
        },
    )

    assert action is None


def test_planning_engine_uses_bootstrap_without_hypothesis():

    state = InvestigationState(
        incident="payment failures",
        service="payment-service",
    )

    engine = InvestigationPlanningEngine()

    action = engine.plan(
        state=state,
        available_tools={
            "get_service_health",
        },
    )

    assert action is not None
    assert action.tool == "get_service_health"