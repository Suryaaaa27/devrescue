import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1]),
)
import importlib


def load_server():
    return importlib.import_module(
        "mcp_servers.database.server"
    )


def test_check_database_health():
    server = load_server()

    result = server.check_database_health(
        service="payment-service"
    )

    assert result["service"] == "payment-service"
    assert result["database"] == "payments"
    assert result["status"] == "available"
    assert result["error"] is None


def test_investigate_database():
    server = load_server()

    result = server.investigate_database(
        service="payment-service"
    )

    assert result["service"] == "payment-service"
    assert result["database"] == "payments"
    assert result["status"] == "available"
    assert result["user"] == "devrescue"
    assert "PostgreSQL" in result["server_version"]
    assert result["error"] is None


def test_get_database_metadata():
    server = load_server()

    result = server.get_database_metadata(
        service="payment-service"
    )

    assert result["service"] == "payment-service"
    assert result["database"] == "payments"
    assert result["status"] == "available"
    assert result["user"] == "devrescue"
    assert "PostgreSQL" in result["server_version"]


def test_database_tools_reject_empty_service():
    server = load_server()

    health = server.check_database_health(
        service=""
    )

    investigation = server.investigate_database(
        service=" "
    )

    metadata = server.get_database_metadata(
        service=""
    )

    assert health["status"] == "error"
    assert investigation["status"] == "error"
    assert metadata["status"] == "error"
