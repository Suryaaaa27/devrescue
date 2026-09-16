from agent.llm.reasoner import LLMReasoner


class FakeLLMClient:
    def __init__(self, response):
        self.response = response
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

        return self.response


def test_llm_reasoner_returns_structured_result():

    client = FakeLLMClient(
        {
            "conclusion": "Invalid payment input",
            "reasoning": (
                "The request contained a negative payment amount "
                "and the application rejected it."
            ),
            "supporting_evidence": [
                "payment amount was -10",
                "HTTP 400 validation error",
                "trace status was ERROR",
            ],
            "contradicting_evidence": [],
            "missing_evidence": [],
            "confidence": 0.96,
        }
    )

    reasoner = LLMReasoner(client)

    result = reasoner.reason(
        incident="Payment failed",
        service="payment-service",
        evidence_summary={
            "signals": [
                "invalid_input",
                "trace_error",
                "failure_metric",
            ]
        },
        hypotheses=[
            {
                "name": "Invalid payment input",
                "role": "root_cause",
                "confidence": 0.95,
            }
        ],
        uncertainty={
            "uncertainty": 0.08,
            "should_continue": False,
        },
        investigation_history=[],
    )

    assert result.conclusion == "Invalid payment input"

    assert result.confidence == 0.96

    assert len(
        result.supporting_evidence
    ) == 3

    assert client.calls


def test_llm_reasoner_clamps_invalid_confidence():

    client = FakeLLMClient(
        {
            "conclusion": "Test",
            "reasoning": "Test reasoning",
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "missing_evidence": [],
            "confidence": 2.5,
        }
    )

    reasoner = LLMReasoner(client)

    result = reasoner.reason(
        incident="Test",
        service="test-service",
        evidence_summary={},
        hypotheses=[],
        uncertainty={},
        investigation_history=[],
    )

    assert result.confidence == 1.0


def test_llm_reasoner_preserves_uncertainty():

    client = FakeLLMClient(
        {
            "conclusion": "Database failure",
            "reasoning": (
                "The database hypothesis is plausible but "
                "requires additional dependency evidence."
            ),
            "supporting_evidence": [
                "database connection error"
            ],
            "contradicting_evidence": [
                "application validation errors also exist"
            ],
            "missing_evidence": [
                "database health evidence"
            ],
            "confidence": 0.62,
        }
    )

    reasoner = LLMReasoner(client)

    result = reasoner.reason(
        incident="Payment service failure",
        service="payment-service",
        evidence_summary={},
        hypotheses=[
            {
                "name": "Database failure",
                "role": "root_cause",
                "confidence": 0.62,
            },
            {
                "name": "Application error",
                "role": "mechanism",
                "confidence": 0.60,
            },
        ],
        uncertainty={
            "uncertainty": 0.62,
            "should_continue": True,
        },
        investigation_history=[],
    )

    assert result.confidence == 0.62

    assert result.missing_evidence == [
        "database health evidence"
    ]

    assert result.contradicting_evidence == [
        "application validation errors also exist"
    ]