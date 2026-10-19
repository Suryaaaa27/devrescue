from evidence.engine import EvidenceEngine


def test_database_domain_result_becomes_database_evidence():
    engine = EvidenceEngine()

    evidence = engine.build(
        service="payment-service",
        domain_results=[
            {
                "tool": "investigate_database",
                "service": "payment-service",
                "database": "payments",
                "status": "available",
                "error": None,
                "user": "devrescue",
                "server_version": "PostgreSQL 16.15",
            }
        ],
    )

    assert len(evidence.database) == 1

    database = evidence.database[0]

    assert database.tool == "investigate_database"
    assert database.service == "payment-service"
    assert database.database == "payments"
    assert database.status == "available"
    assert database.error is None

    assert evidence.summary["database_count"] == 1
    assert evidence.summary["database"][0]["database"] == "payments"
