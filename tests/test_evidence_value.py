from agent.evidence_value import EvidenceValueScorer
from agent.state import InvestigationState
from hypothesis.models import Hypothesis


def make_hypothesis(
    name,
    category,
    confidence=0.70,
    score=0.70,
    role="root_cause",
):
    return Hypothesis(
        name=name,
        category=category,
        role=role,
        confidence=confidence,
        score=score,
        severity="high",
        explanation="test hypothesis",
        matched_signals=[],
        missing_signals=[],
        evidence_score=0.7,
        specificity_score=0.7,
        temporal_score=0.5,
        contradiction_penalty=0.0,
        supporting_evidence=[],
        contradicting_evidence=[],
    )


def test_database_investigation_has_high_relevance():

    state = InvestigationState(
        incident="database failure",
        service="payment-service",
    )

    hypothesis = make_hypothesis(
        "Database dependency unavailable",
        "database_failure",
    )

    scorer = EvidenceValueScorer()

    result = scorer.score(
        tool="investigate_database",
        hypothesis=hypothesis,
        state=state,
    )

    assert result.relevance == 1.0
    assert result.specificity >= 0.8
    assert result.score > 0.7


def test_database_investigation_has_high_discrimination():

    state = InvestigationState(
        incident="payment failure",
        service="payment-service",
    )

    database = make_hypothesis(
        "Database dependency unavailable",
        "database_failure",
        confidence=0.62,
        score=0.62,
    )

    application = make_hypothesis(
        "Application exception",
        "application_error",
        confidence=0.60,
        score=0.60,
        role="mechanism",
    )

    state.hypotheses = [
        database,
        application,
    ]

    scorer = EvidenceValueScorer()

    result = scorer.score(
        tool="investigate_database",
        hypothesis=database,
        state=state,
    )

    assert result.discrimination == 1.0


def test_already_used_tool_has_no_novelty():

    state = InvestigationState(
        incident="payment failure",
        service="payment-service",
    )

    state.tool_history = [
        "investigate_database",
    ]

    hypothesis = make_hypothesis(
        "Database dependency unavailable",
        "database_failure",
    )

    scorer = EvidenceValueScorer()

    result = scorer.score(
        tool="investigate_database",
        hypothesis=hypothesis,
        state=state,
    )

    assert result.novelty == 0.0


def test_database_probe_outvalues_generic_metric_for_database_failure():

    state = InvestigationState(
        incident="database failure",
        service="payment-service",
    )

    database = make_hypothesis(
        "Database dependency unavailable",
        "database_failure",
    )

    state.hypotheses = [
        database,
    ]

    scorer = EvidenceValueScorer()

    database_result = scorer.score(
        tool="investigate_database",
        hypothesis=database,
        state=state,
    )

    metric_result = scorer.score(
        tool="query_metrics",
        hypothesis=database,
        state=state,
    )

    assert (
        database_result.score
        > metric_result.score
    )
    
def test_planner_ranks_database_investigation_above_generic_evidence():

    from agent.planner import HypothesisPlanner

    state = InvestigationState(
        incident="database failure",
        service="payment-service",
    )

    state.available_tools = {
        "investigate_database",
        "search_logs",
        "find_traces",
        "query_metrics",
    }

    database = make_hypothesis(
        "Database dependency unavailable",
        "database_failure",
    )

    state.hypotheses = [
        database,
    ]

    planner = HypothesisPlanner()

    ranked = planner.rank_actions(
        hypothesis=database,
        state=state,
    )

    assert ranked

    assert ranked[0][0].tool == (
        "investigate_database"
    )

    assert (
        ranked[0][1]
        > ranked[1][1]
    )
    
def test_planner_explains_evidence_value():

    from agent.planner import HypothesisPlanner

    state = InvestigationState(
        incident="database failure",
        service="payment-service",
    )

    state.available_tools = {
        "investigate_database",
        "search_logs",
        "query_metrics",
    }

    hypothesis = make_hypothesis(
        "Database dependency unavailable",
        "database_failure",
    )

    planner = HypothesisPlanner()

    action = planner.plan_for_hypothesis(
        hypothesis=hypothesis,
        state=state,
    )

    assert action is not None

    reason = action.reason.lower()

    assert "evidence value" in reason
    assert "investigate_database" in reason