from agent.state import InvestigationState
from agent.uncertainty import UncertaintyAnalyzer
from evidence.models import InvestigationEvidence
from hypothesis.models import Hypothesis


def make_hypothesis(
    name,
    category,
    confidence,
    score,
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
        evidence_score=0.8,
        specificity_score=0.8,
        temporal_score=0.8,
        contradiction_penalty=0.0,
        supporting_evidence=[],
        contradicting_evidence=[],
    )


def test_close_hypotheses_require_more_investigation():

    state = InvestigationState(
        incident="payment failure",
        service="payment-service",
    )

    state.hypotheses = [
        make_hypothesis(
            "Database dependency unavailable",
            "database_failure",
            confidence=0.62,
            score=0.62,
        ),
        make_hypothesis(
            "Application exception",
            "application_error",
            confidence=0.60,
            score=0.60,
            role="mechanism",
        ),
    ]

    analyzer = UncertaintyAnalyzer()

    result = analyzer.assess(state)

    assert result.confidence_gap == 0.02
    assert result.sufficient_confidence is False
    assert result.sufficient_separation is False
    assert result.should_continue is True


def test_strong_root_cause_with_separation_can_stop():

    state = InvestigationState(
        incident="database failure",
        service="payment-service",
    )

    state.hypotheses = [
        make_hypothesis(
            "Database dependency unavailable",
            "database_failure",
            confidence=0.91,
            score=0.91,
        ),
        make_hypothesis(
            "Application exception",
            "application_error",
            confidence=0.40,
            score=0.40,
            role="mechanism",
        ),
    ]

    state.evidence = InvestigationEvidence(
        service="payment-service",
        logs=[object()],
        metrics=[object()],
    )

    analyzer = UncertaintyAnalyzer()

    result = analyzer.assess(state)

    assert result.leading_hypothesis == (
        "Database dependency unavailable"
    )

    assert result.confidence_gap == 0.51
    assert result.sufficient_confidence is True
    assert result.sufficient_separation is True
    assert result.independent_evidence_count == 2
    assert result.should_continue is False


def test_high_confidence_alone_is_not_enough():

    state = InvestigationState(
        incident="database failure",
        service="payment-service",
    )

    state.hypotheses = [
        make_hypothesis(
            "Database dependency unavailable",
            "database_failure",
            confidence=0.90,
            score=0.90,
        ),
        make_hypothesis(
            "Application exception",
            "application_error",
            confidence=0.84,
            score=0.84,
            role="mechanism",
        ),
    ]

    state.evidence = InvestigationEvidence(
        service="payment-service",
        logs=[object()],
        metrics=[object()],
    )

    analyzer = UncertaintyAnalyzer()

    result = analyzer.assess(state)

    assert result.sufficient_confidence is True
    assert result.sufficient_separation is False
    assert result.should_continue is True


def test_no_hypotheses_means_maximum_uncertainty():

    state = InvestigationState(
        incident="unknown failure",
        service="payment-service",
    )

    analyzer = UncertaintyAnalyzer()

    result = analyzer.assess(state)

    assert result.leading_hypothesis is None
    assert result.uncertainty == 1.0
    assert result.should_continue is True