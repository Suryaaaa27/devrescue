import json

from agent.state import InvestigationState


def build_llm_context(
    state: InvestigationState,
    uncertainty,
) -> dict:

    evidence_summary = {}

    if state.evidence is not None:
        evidence_summary = state.evidence.summary

    hypotheses = [
        {
            "name": hypothesis.name,
            "category": hypothesis.category,
            "role": hypothesis.role,
            "confidence": hypothesis.confidence,
            "score": hypothesis.score,
            "severity": hypothesis.severity,
            "explanation": hypothesis.explanation,
            "matched_signals": hypothesis.matched_signals,
            "missing_signals": hypothesis.missing_signals,
        }
        for hypothesis in state.hypotheses
    ]

    uncertainty_data = {
        "leading_hypothesis": uncertainty.leading_hypothesis,
        "leading_confidence": uncertainty.leading_confidence,
        "runner_up_hypothesis": uncertainty.runner_up_hypothesis,
        "runner_up_confidence": uncertainty.runner_up_confidence,
        "confidence_gap": uncertainty.confidence_gap,
        "uncertainty": uncertainty.uncertainty,
        "independent_evidence_count": (
            uncertainty.independent_evidence_count
        ),
        "sufficient_confidence": (
            uncertainty.sufficient_confidence
        ),
        "sufficient_separation": (
            uncertainty.sufficient_separation
        ),
        "should_continue": uncertainty.should_continue,
        "reason": uncertainty.reason,
    }

    return {
        "incident": state.incident,
        "service": state.service,
        "evidence_summary": evidence_summary,
        "hypotheses": hypotheses,
        "uncertainty": uncertainty_data,
        "investigation_history": {
            "planning_history": state.planning_history,
            "hypothesis_history": state.hypothesis_history,
            "evidence_gaps": state.evidence_gaps,
            "action_outcomes": state.action_outcomes,
        },
    }