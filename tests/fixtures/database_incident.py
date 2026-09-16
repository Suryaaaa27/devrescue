DATABASE_INCIDENT = (
    "Payment failures are occurring because "
    "the payments database is unavailable."
)


DATABASE_LOG_RESULT = {
    "query": "database connection refused",
    "service": "payment-service",
    "count": 1,
    "results": [
        {
            "timestamp": "2026-09-15T16:30:00Z",
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
    ],
}


DATABASE_INVESTIGATION_RESULT = {
    "service": "payment-service",
    "database": "payments-db",
    "status": "unavailable",
    "error": "connection refused",
}