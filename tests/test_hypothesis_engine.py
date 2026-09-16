import json
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
    )
)

from evidence.engine import EvidenceEngine
from hypothesis.engine import HypothesisEngine


def build_test_evidence():
    evidence_engine = EvidenceEngine()

    log_result = {
        "results": [
            {
                "timestamp": "2026-09-08T10:00:02Z",
                "service": "payment-service",
                "level": "INFO",
                "message": (
                    "payment_request "
                    "request_id=req-59266 "
                    "amount=-10"
                ),
                "trace_id": (
                    "f83d1eadb5451abfe8f913cead3922d9"
                ),
                "span_id": "1004bb8f5fedc21b",
                "request_id": "req-59266",
            }
        ]
    }

    metric_results = [
        {
            "metric": {
                "__name__": "payment_failures_total",
            },
            "value": [
                1788947489.053,
                "1",
            ],
            "query": "payment_failures_total",
        }
    ]

    trace_result = {
        "results": [
            {
                "trace_id": (
                    "f83d1eadb5451abfe8f913cead3922d9"
                ),
                "spans": [
                    {
                        "span_id": "1004bb8f5fedc21b",
                        "operation": "process_payment",
                        "start_time": 1788947370253688,
                        "duration": 2152901,
                        "tags": {
                            "payment.amount": -10,
                            "payment.request_id": "req-59266",
                            "payment.status": "failed",
                            "span.kind": "internal",
                            "otel.status_code": "ERROR",
                            "error": True,
                        },
                        "logs": [
                            {
                                "timestamp": 1788947372406590,
                                "fields": {
                                    "event": "exception",
                                    "exception.type": (
                                        "fastapi.exceptions.HTTPException"
                                    ),
                                    "exception.message": (
                                        "400: Payment amount "
                                        "must be greater than zero."
                                    ),
                                },
                            }
                        ],
                    }
                ],
            }
        ]
    }

    return evidence_engine.build(
        service="payment-service",
        log_result=log_result,
        metric_results=metric_results,
        trace_result=trace_result,
    )


def test_payment_input_hypothesis():

    evidence = build_test_evidence()

    engine = HypothesisEngine()

    hypotheses = engine.analyze(
        evidence
    )

    assert hypotheses

    root_causes = [
        hypothesis
        for hypothesis in hypotheses
        if hypothesis.role == "root_cause"
    ]

    assert root_causes

    selected = root_causes[0]

    assert selected.name == "Invalid payment input"

    assert selected.confidence >= 0.75

    assert "invalid_input" in (
        selected.matched_signals
    )


def main():

    evidence = build_test_evidence()

    engine = HypothesisEngine()

    hypotheses = engine.analyze(
        evidence
    )

    output = {
        "hypothesis_count": len(
            hypotheses
        ),
        "hypotheses": [
            hypothesis.to_dict()
            for hypothesis in hypotheses
        ],
    }

    print(
        json.dumps(
            output,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()


def test_database_dependency_hypothesis():

    evidence_engine = EvidenceEngine()

    log_result = {
        "results": [
            {
                "timestamp": "2026-09-10T16:30:00Z",
                "service": "payment-service",
                "level": "ERROR",
                "message": (
                    "database connection refused "
                    "postgresql://payments-db"
                ),
                "trace_id": "trace-db-001",
                "span_id": "span-db-001",
                "request_id": "req-db-001",
            }
        ]
    }

    evidence = evidence_engine.build(
        service="payment-service",
        log_result=log_result,
        metric_results=[],
        trace_result={},
    )

    # Simulate the normalized domain evidence
    # produced by InvestigationAgent v1.2.
    domain_evidence = [
        {
            "tool": "investigate_database",
            "service": "payment-service",
            "database": "payments-db",
            "status": "unavailable",
            "error": "connection refused",
        }
    ]

    evidence.summary["domain_evidence"] = (
        domain_evidence
    )

    evidence.summary["domain_evidence_count"] = 1

    evidence.summary["domain_tools"] = [
        "investigate_database"
    ]

    evidence.signals.extend(
        [
            "database_unavailable",
            "database_connection_failure",
        ]
    )

    engine = HypothesisEngine()

    hypotheses = engine.analyze(
        evidence
    )

    assert hypotheses

    root_causes = [
        hypothesis
        for hypothesis in hypotheses
        if hypothesis.role == "root_cause"
    ]

    assert root_causes

    selected = root_causes[0]

    assert selected.name == (
        "Database dependency unavailable"
    )

    assert selected.category == (
        "database_failure"
    )

    assert selected.role == "root_cause"

    assert selected.confidence >= 0.75

    assert (
        "database_connection_failure"
        in selected.matched_signals
    )

    assert (
        "database_unavailable"
        in selected.matched_signals
    )