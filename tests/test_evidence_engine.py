import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
    )
)

import json

from evidence.engine import EvidenceEngine


def main():
    log_result = {
        "results": [
            {
                "timestamp": "1788947372406590",
                "service": "payment-service",
                "level": "INFO",
                "message": (
                    "invalid_payment "
                    "request_id=req-59266 "
                    "amount=-10"
                ),
                "trace_id": (
                    "f83d1eadb5451abfe8f913cead3922d9"
                ),
                "span_id": "1004bb8f5fedc21b",
                "request_id": "req-59266",
            },
            {
                "timestamp": "1788947372406590",
                "service": "payment-service",
                "level": "INFO",
                "message": (
                    "invalid_payment "
                    "request_id=req-59266 "
                    "amount=-10"
                ),
                "trace_id": (
                    "f83d1eadb5451abfe8f913cead3922d9"
                ),
                "span_id": "1004bb8f5fedc21b",
                "request_id": "req-59266",
            },
        ]
    }

    metric_results = [
        {
            "query": "payment_failures_total",
            "metric": {
                "__name__": "payment_failures_total",
                "otel_scope_name": "payment-service",
            },
            "value": [
                1788947489.053,
                "1",
            ],
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
                            "otel.status_code": "ERROR",
                            "error": True,
                        },
                        "logs": [],
                    }
                ],
            }
        ]
    }

    engine = EvidenceEngine()

    result = engine.build(
        service="payment-service",
        log_result=log_result,
        metric_results=metric_results,
        trace_result=trace_result,
    )

    output = {
    "service": result.service,
    "request_ids": sorted(result.request_ids),
    "trace_ids": sorted(result.trace_ids),
    "span_ids": sorted(result.span_ids),
    "log_count": len(result.logs),
    "metric_count": len(result.metrics),
    "trace_count": len(result.traces),
    "correlation_count": len(result.correlations),
    "temporal_correlation_count": len(
        result.temporal_correlations
    ),
    "signals": result.signals,
    "summary": result.summary,
    "temporal_correlations": [
        {
            "source": item.source,
            "target": item.target,
            "delta_seconds": item.delta_seconds,
            "description": item.description,
        }
        for item in result.temporal_correlations
    ],
    "correlations": [
        {
            "source": item.source,
            "target": item.target,
            "key": item.key,
            "value": item.value,
        }
        for item in result.correlations
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