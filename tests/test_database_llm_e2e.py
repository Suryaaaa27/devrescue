import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from agent.llm.reasoner import LLMReasoner


class FakeDatabaseLLMClient:

    def generate(
        self,
        *,
        system_prompt,
        user_prompt,
    ):
        return {
            "conclusion": (
                "Database dependency unavailable is the "
                "most likely root cause."
            ),
            "reasoning": (
                "The investigation contains direct evidence "
                "that the payments database is unavailable "
                "because the connection was refused. This "
                "provides a more specific explanation than "
                "the service-level failure."
            ),
            "supporting_evidence": [
                "database_connection_failure",
                "database_unavailable",
                "error_log",
            ],
            "contradicting_evidence": [],
            "missing_evidence": [],
            "confidence": 0.95,
        }


def test_database_llm_reasoning_end_to_end():

    reasoner = LLMReasoner(
        FakeDatabaseLLMClient()
    )

    result = reasoner.reason(
        incident=(
            "Payment failures are occurring because "
            "the payments database is unavailable."
        ),
        service="payment-service",
        evidence_summary={
            "service": "payment-service",
            "log_count": 1,
            "metric_count": 0,
            "trace_count": 0,
            "signals": [
                "error_log",
                "database_unavailable",
                "database_connection_failure",
            ],
            "domain_evidence_count": 1,
        },
        hypotheses=[
            {
                "name": (
                    "Database dependency unavailable"
                ),
                "category": "database_failure",
                "role": "root_cause",
                "confidence": 0.95,
                "score": 0.95,
                "severity": "high",
                "matched_signals": [
                    "database_connection_failure",
                    "database_unavailable",
                ],
                "missing_signals": [],
            },
            {
                "name": "Service-level failure",
                "category": "service_failure",
                "role": "symptom",
                "confidence": 0.60,
                "score": 0.60,
                "severity": "high",
                "matched_signals": [
                    "error_log",
                ],
                "missing_signals": [],
            },
        ],
        uncertainty={
            "leading_hypothesis": (
                "Database dependency unavailable"
            ),
            "leading_confidence": 0.95,
            "runner_up_hypothesis": (
                "Service-level failure"
            ),
            "runner_up_confidence": 0.60,
            "confidence_gap": 0.35,
            "uncertainty": 0.29,
            "independent_evidence_count": 3,
            "sufficient_confidence": True,
            "sufficient_separation": True,
            "should_continue": False,
            "reason": (
                "The database hypothesis has strong "
                "confidence and separation."
            ),
        },
        investigation_history={},
    )

    assert result.conclusion == (
        "Database dependency unavailable is the "
        "most likely root cause."
    )

    assert result.confidence == 0.95

    assert (
        "database_connection_failure"
        in result.supporting_evidence
    )

    assert result.missing_evidence == []