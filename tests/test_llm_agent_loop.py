import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)

from agent.investigator import InvestigationAgent


class FakeReasoning:

    def __init__(
        self,
        conclusion,
        reasoning,
        supporting_evidence,
        missing_evidence,
        confidence,
    ):
        self.conclusion = conclusion
        self.reasoning = reasoning
        self.supporting_evidence = (
            supporting_evidence
        )
        self.contradicting_evidence = []
        self.missing_evidence = (
            missing_evidence
        )
        self.confidence = confidence

    def to_dict(self):
        return {
            "conclusion": self.conclusion,
            "reasoning": self.reasoning,
            "supporting_evidence": (
                self.supporting_evidence
            ),
            "contradicting_evidence": (
                self.contradicting_evidence
            ),
            "missing_evidence": (
                self.missing_evidence
            ),
            "confidence": self.confidence,
        }


class FakeLLMReasoner:

    def __init__(self):
        self.calls = 0

    def reason(self, **kwargs):
        self.calls += 1

        if self.calls == 1:
            return FakeReasoning(
                conclusion=(
                    "Application exception is the "
                    "leading hypothesis, but database "
                    "evidence is missing."
                ),
                reasoning=(
                    "The trace confirms an application "
                    "exception. Direct database evidence "
                    "is needed to determine whether the "
                    "exception originated from a database "
                    "dependency failure."
                ),
                supporting_evidence=[
                    "trace_error",
                ],
                missing_evidence=[
                    "Direct database health evidence",
                ],
                confidence=0.70,
            )

        return FakeReasoning(
            conclusion=(
                "Database dependency unavailable"
            ),
            reasoning=(
                "Direct database investigation confirms "
                "that the database is unavailable."
            ),
            supporting_evidence=[
                "database_connection_failure",
                "database_unavailable",
            ],
            missing_evidence=[],
            confidence=0.95,
        )


def fake_health():
    return {
        "service": "payment-service",
        "status": "degraded",
    }


def fake_search_logs(**kwargs):
    return {
        "query": "",
        "service": kwargs.get(
            "service",
            "payment-service",
        ),
        "count": 1,
        "results": [
            {
                "timestamp": (
                    "2026-09-15T16:30:00Z"
                ),
                "service": "payment-service",
                "level": "ERROR",
                "message": (
                    "application exception while "
                    "processing payment"
                ),
                "trace_id": "trace-app-001",
                "span_id": "span-app-001",
                "request_id": "req-app-001",
            }
        ],
    }


def fake_traces(**kwargs):
    return {
        "service": kwargs.get(
            "service",
            "payment-service",
        ),
        "results": [
            {
                "trace_id": "trace-app-001",
                "spans": [
                    {
                        "span_id": "span-app-001",
                        "operation": (
                            "process_payment"
                        ),
                        "start_time": 1000,
                        "duration": 100,
                        "tags": {
                            "otel.status_code": "ERROR",
                            "error": True,
                        },
                        "logs": [
                            {
                                "timestamp": 1050,
                                "fields": {
                                    "exception.message": (
                                        "database operation "
                                        "failed"
                                    ),
                                },
                            }
                        ],
                    }
                ],
            }
        ],
    }


def fake_database_investigation(**kwargs):
    return {
        "service": kwargs.get(
            "service",
            "payment-service",
        ),
        "database": "payments-db",
        "status": "unavailable",
        "error": "connection refused",
    }


def test_llm_reasoning_guides_next_investigation():

    llm = FakeLLMReasoner()

    tools = {
        "get_service_health": fake_health,
        "search_logs": fake_search_logs,
        "find_traces": fake_traces,
        "investigate_database": (
            fake_database_investigation
        ),
    }

    agent = InvestigationAgent(
        tools=tools,
        max_iterations=5,
        llm_reasoner=llm,
    )

    result = agent.investigate(
        incident=(
            "Payment processing is failing "
            "with an application exception."
        ),
        service="payment-service",
    )

    assert llm.calls >= 2
    print("\nTOOLS CALLED:")
    print(result.tools_called)

    print("\nPLANNING HISTORY:")
    for plan in result.planning_history:
        print(plan)

    print("\nLLM REASONING:")
    for reasoning in result.llm_reasoning_history:
        print(reasoning)
    assert (
        "investigate_database"
        in result.tools_called
    )

    assert len(
        result.llm_reasoning_history
    ) >= 2

    # The LLM should have explicitly requested
    # database evidence.
    first_llm_reasoning = (
        result.llm_reasoning_history[0]
        ["reasoning"]
    )

    assert (
        "Direct database health evidence"
        in first_llm_reasoning[
            "missing_evidence"
        ]
    )

    # Confirm that the database investigation
    # occurred after the initial investigation.
    database_index = (
        result.tools_called.index(
            "investigate_database"
        )
    )

    assert database_index > 0

    # The final deterministic hypothesis is
    # authoritative.
    assert result.root_cause == (
        "Database dependency unavailable"
    )

    assert result.confidence >= 0.75

    # LLM confidence is retained separately and
    # must not overwrite deterministic confidence.
    assert (
        result.llm_reasoning_history[-1]
        ["reasoning"]["confidence"]
        == 0.95
    )

    assert (
        result.uncertainty["should_continue"]
        is False
    )