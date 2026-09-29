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
    
def test_github_evidence_increases_application_error_confidence():

    evidence_engine = EvidenceEngine()

    evidence = evidence_engine.build(
        service="payment-service",

        log_result={
            "results": [
                {
                    "timestamp": "2026-09-17T10:00:00Z",
                    "service": "payment-service",
                    "level": "ERROR",
                    "message": "payment processing failed",
                }
            ]
        },

        metric_results=[
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
        ],

        trace_result={
            "results": [
                {
                    "trace_id": "trace-github-001",
                    "spans": [
                        {
                            "span_id": "span-github-001",
                            "operation": "process_payment",
                            "start_time": 1788947370253688,
                            "duration": 2152901,
                            "tags": {
                                "otel.status_code": "ERROR",
                                "error": True,
                            },
                            "logs": [
                                {
                                    "timestamp": 1788947372406590,
                                    "fields": {
                                        "event": "exception",
                                        "exception.type": (
                                            "ValueError"
                                        ),
                                        "exception.message": (
                                            "payment processing failed"
                                        ),
                                    },
                                }
                            ],
                        }
                    ],
                }
            ]
        },

        code_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "file": {
                    "path": (
                        "services/payment_service/main.py"
                    ),
                    "content": (
                        "raise ValueError("
                        "\"payment processing failed\")"
                    ),
                },
            }
        ],

        commit_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "results": [
                    {
                        "sha": "github-commit-001",
                        "message": "fix payment processing",
                        "author": "Surya",
                        "timestamp": (
                            "2026-09-17T09:00:00Z"
                        ),
                    }
                ],
            }
        ],

        diff_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "commit": {
                    "sha": "github-commit-001",
                    "message": "fix payment processing",
                },
                "files": [
                    {
                        "filename": (
                            "services/payment_service/main.py"
                        ),
                        "patch": (
                            "@@ -10,1 +10,1 @@\n"
                            "+raise ValueError("
                            "\"payment processing failed\")"
                        ),
                    }
                ],
            }
        ],
    )

    engine = HypothesisEngine()

    hypotheses = engine.analyze(evidence)

    application_errors = [
        hypothesis
        for hypothesis in hypotheses
        if hypothesis.name == "Application exception"
    ]

    assert application_errors

    selected = application_errors[0]

    assert selected.confidence > 0.0

    assert selected.supporting_evidence

    assert any(
        evidence.evidence_type in {
            "code",
            "commit",
            "diff",
        }
        for evidence in selected.supporting_evidence
    )
    
def test_github_correlated_evidence_influences_confidence():

    evidence_engine = EvidenceEngine()

    base_evidence = evidence_engine.build(
        service="payment-service",
        log_result={
            "results": [
                {
                    "timestamp": "2026-09-17T10:00:00Z",
                    "service": "payment-service",
                    "level": "ERROR",
                    "message": "payment processing failed",
                }
            ]
        },
        metric_results=[
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
        ],
        trace_result={
            "results": [
                {
                    "trace_id": "trace-confidence-001",
                    "spans": [
                        {
                            "span_id": "span-confidence-001",
                            "operation": "process_payment",
                            "start_time": 1788947370253688,
                            "duration": 2152901,
                            "tags": {
                                "otel.status_code": "ERROR",
                                "error": True,
                            },
                            "logs": [
                                {
                                    "timestamp": 1788947372406590,
                                    "fields": {
                                        "event": "exception",
                                        "exception.type": "ValueError",
                                        "exception.message": (
                                            "payment processing failed"
                                        ),
                                    },
                                }
                            ],
                        }
                    ],
                }
            ]
        },
    )

    github_evidence = evidence_engine.build(
        service="payment-service",
        log_result={
            "results": [
                {
                    "timestamp": "2026-09-17T10:00:00Z",
                    "service": "payment-service",
                    "level": "ERROR",
                    "message": "payment processing failed",
                }
            ]
        },
        metric_results=[
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
        ],
        trace_result={
            "results": [
                {
                    "trace_id": "trace-confidence-001",
                    "spans": [
                        {
                            "span_id": "span-confidence-001",
                            "operation": "process_payment",
                            "start_time": 1788947370253688,
                            "duration": 2152901,
                            "tags": {
                                "otel.status_code": "ERROR",
                                "error": True,
                            },
                            "logs": [
                                {
                                    "timestamp": 1788947372406590,
                                    "fields": {
                                        "event": "exception",
                                        "exception.type": "ValueError",
                                        "exception.message": (
                                            "payment processing failed"
                                        ),
                                    },
                                }
                            ],
                        }
                    ],
                }
            ]
        },
        code_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "file": {
                    "path": (
                        "services/payment_service/main.py"
                    ),
                    "content": (
                        "raise ValueError("
                        '"payment processing failed")'
                    ),
                },
            }
        ],
        commit_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "results": [
                    {
                        "sha": "github-confidence-001",
                        "message": "fix payment processing",
                        "author": "Surya",
                        "timestamp": "2026-09-17T09:00:00Z",
                    }
                ],
            }
        ],
        diff_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "commit": {
                    "sha": "github-confidence-001",
                    "message": "fix payment processing",
                },
                "files": [
                    {
                        "filename": (
                            "services/payment_service/main.py"
                        ),
                        "patch": (
                            "@@ -10,1 +10,1 @@\n"
                            '+raise ValueError("payment processing failed")'
                        ),
                    }
                ],
            }
        ],
    )

    engine = HypothesisEngine()

    base_hypotheses = engine.analyze(base_evidence)
    github_hypotheses = engine.analyze(github_evidence)

    base_application = next(
        hypothesis
        for hypothesis in base_hypotheses
        if hypothesis.name == "Application exception"
    )

    github_application = next(
        hypothesis
        for hypothesis in github_hypotheses
        if hypothesis.name == "Application exception"
    )

    assert github_application.confidence >= (
        base_application.confidence
    )

    assert any(
        item.evidence_type in {
            "code",
            "commit",
            "diff",
        }
        for item in github_application.supporting_evidence
    )
    
def test_code_relevance_strengthens_application_hypothesis():

    evidence_engine = EvidenceEngine()

    evidence = evidence_engine.build(
        service="payment-service",
        log_result={
            "results": [
                {
                    "timestamp": "2026-09-17T10:00:00Z",
                    "service": "payment-service",
                    "level": "ERROR",
                    "message": "payment processing failed",
                }
            ]
        },
        metric_results=[],
        trace_result={
            "results": [
                {
                    "trace_id": "trace-hypothesis-code-001",
                    "spans": [
                        {
                            "span_id": "span-hypothesis-code-001",
                            "operation": "process_payment",
                            "start_time": None,
                            "duration": None,
                            "tags": {
                                "otel.status_code": "ERROR",
                                "error": True,
                            },
                            "logs": [
                                {
                                    "timestamp": None,
                                    "fields": {
                                        "exception.type": "ValueError",
                                        "exception.message": (
                                            "payment processing failed"
                                        ),
                                    },
                                }
                            ],
                        }
                    ],
                }
            ]
        },
        code_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "file": {
                    "path": (
                        "services/payment_service/main.py"
                    ),
                    "content": (
                        "def process_payment(amount):\n"
                        "    raise ValueError("
                        '"payment processing failed")'
                    ),
                },
            }
        ],
        diff_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "commit_sha": "abc-code-001",
                "files": [
                    {
                        "path": (
                            "services/payment_service/main.py"
                        ),
                        "patch": (
                            '+ raise ValueError('
                            '"payment processing failed")'
                        ),
                    }
                ],
            }
        ],
    )

    engine = HypothesisEngine()

    hypotheses = engine.analyze(evidence)

    application = next(
        hypothesis
        for hypothesis in hypotheses
        if hypothesis.name == "Application exception"
    )

    assert evidence.code_relevance

    assert application.confidence > 0

    assert any(
        item.evidence_type == "code_relevance"
        for item in application.supporting_evidence
    )