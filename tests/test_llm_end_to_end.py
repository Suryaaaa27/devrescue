import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from agent.llm.reasoner import LLMReasoner


class FakeLLMClient:

    def __init__(self):
        self.calls = []

    def generate(
        self,
        *,
        system_prompt,
        user_prompt,
    ):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
            }
        )

        return {
            "conclusion": (
                "Invalid payment input is the most likely "
                "root cause."
            ),
            "reasoning": (
                "The deterministic evidence contains multiple "
                "signals directly supporting invalid input."
            ),
            "supporting_evidence": [
                "invalid_input",
                "failure_metric",
                "trace_error",
                "trace_status_error",
                "failed_operation",
            ],
            "contradicting_evidence": [],
            "missing_evidence": [
                "Additional evidence is needed to increase "
                "separation from competing hypotheses."
            ],
            "confidence": 0.82,
        }


def test_llm_reasoning_end_to_end():

    client = FakeLLMClient()

    reasoner = LLMReasoner(client)

    result = reasoner.reason(
        incident=(
            "Payment request req-59266 failed "
            "with an HTTP 400 response."
        ),
        service="payment-service",
        evidence_summary={
            "service": "payment-service",
            "log_count": 1,
            "metric_count": 1,
            "trace_count": 1,
            "signals": [
                "error_log",
                "failure_log",
                "failure_metric",
                "trace_error",
                "trace_status_error",
                "failed_operation",
                "invalid_input",
            ],
        },
        hypotheses=[
            {
                "name": "Invalid payment input",
                "category": "application_validation",
                "role": "root_cause",
                "confidence": 0.82,
                "score": 0.82,
            },
            {
                "name": "Application exception",
                "category": "application_error",
                "role": "mechanism",
                "confidence": 0.69,
                "score": 0.69,
            },
        ],
        uncertainty={
            "leading_hypothesis": "Invalid payment input",
            "leading_confidence": 0.82,
            "runner_up_hypothesis": "Application exception",
            "runner_up_confidence": 0.69,
            "confidence_gap": 0.13,
            "uncertainty": 0.46,
            "independent_evidence_count": 3,
            "sufficient_confidence": True,
            "sufficient_separation": False,
            "should_continue": True,
        },
        investigation_history={},
    )

    assert result.conclusion == (
        "Invalid payment input is the most likely "
        "root cause."
    )

    assert result.confidence == 0.82

    assert "invalid_input" in (
        result.supporting_evidence
    )

    assert result.missing_evidence

    assert client.calls