import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
    )
)

from evidence.engine import EvidenceEngine
from evidence.code_relevance import CodeRelevanceEngine


def test_code_relevance_matches_exception_and_diff():

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
                    "trace_id": "trace-relevance-001",
                    "spans": [
                        {
                            "span_id": "span-relevance-001",
                            "operation": "process_payment",
                            "start_time": None,
                            "duration": None,
                            "tags": {},
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
                "commit_sha": "abc123",
                "files": [
                    {
                        "path": (
                            "services/payment_service/main.py"
                        ),
                        "patch": (
                            "+ raise ValueError("
                            '"payment processing failed")'
                        ),
                    }
                ],
            }
        ],
    )

    engine = CodeRelevanceEngine()

    relevance = engine.analyze(
        code=evidence.code,
        diffs=evidence.diffs,
        traces=evidence.traces,
        logs=evidence.logs,
    )

    assert relevance

    selected = relevance[0]

    assert (
        selected.path
        == "services/payment_service/main.py"
    )

    assert selected.score > 0.0

    assert any(
        "payment" in term.lower()
        for term in selected.matched_terms
    )

    assert any(
        "GitHub diff" in reason
        for reason in selected.reasons
    )


def test_unrelated_code_has_no_relevance():

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
                    "trace_id": "trace-unrelated-001",
                    "spans": [
                        {
                            "span_id": "span-unrelated-001",
                            "operation": "process_payment",
                            "start_time": None,
                            "duration": None,
                            "tags": {},
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
                    "path": "utils/formatting.py",
                    "content": (
                        "def format_currency(value):\n"
                        "    return f'${value}'"
                    ),
                },
            }
        ],
    )

    engine = CodeRelevanceEngine()

    relevance = engine.analyze(
        code=evidence.code,
        diffs=evidence.diffs,
        traces=evidence.traces,
        logs=evidence.logs,
    )

    assert relevance == []
    
def test_evidence_engine_builds_code_relevance():

    engine = EvidenceEngine()

    evidence = engine.build(
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
                    "trace_id": "trace-integration-001",
                    "spans": [
                        {
                            "span_id": "span-integration-001",
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
                "commit_sha": "abc123",
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

    assert evidence.code_relevance

    relevance = evidence.code_relevance[0]

    assert (
        relevance.path
        == "services/payment_service/main.py"
    )

    assert relevance.score > 0

    assert evidence.summary[
        "code_relevance_count"
    ] == 1
    
def test_code_relevance_is_stored_in_investigation_evidence():

    engine = EvidenceEngine()

    evidence = engine.build(
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
                    "trace_id": "trace-model-001",
                    "spans": [
                        {
                            "span_id": "span-model-001",
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
    )

    assert evidence.code_relevance
    assert (
        evidence.code_relevance[0].score > 0
    )