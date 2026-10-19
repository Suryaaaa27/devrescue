from __future__ import annotations

from typing import Any

import psycopg
from mcp.server.fastmcp import FastMCP

from mcp_servers.database.config import get_database_config


mcp = FastMCP("devrescue-database")


def _connect() -> psycopg.Connection:
    config = get_database_config()

    return psycopg.connect(
        host=config["host"],
        port=config["port"],
        dbname=config["database"],
        user=config["user"],
        password=config["password"],
        connect_timeout=3,
    )


@mcp.tool()
def check_database_health(
    service: str = "payment-service",
) -> dict[str, Any]:
    """Check whether the service database is reachable."""

    if not service.strip():
        return {
            "status": "error",
            "error": "service must not be empty",
        }

    config = get_database_config()

    try:
        with _connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

        return {
            "status": "available",
            "service": service,
            "database": config["database"],
            "host": config["host"],
            "port": config["port"],
            "error": None,
        }

    except Exception as exc:
        return {
            "status": "unavailable",
            "service": service,
            "database": config["database"],
            "host": config["host"],
            "port": config["port"],
            "error": str(exc),
        }


@mcp.tool()
def investigate_database(
    service: str = "payment-service",
) -> dict[str, Any]:
    """Perform controlled read-only database diagnostics."""

    if not service.strip():
        return {
            "status": "error",
            "error": "service must not be empty",
        }

    config = get_database_config()

    try:
        with _connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

                cursor.execute(
                    """
                    SELECT
                        current_database(),
                        current_user,
                        version()
                    """
                )

                database_name, current_user, version = cursor.fetchone()

        return {
            "status": "available",
            "service": service,
            "database": database_name,
            "user": current_user,
            "server_version": version,
            "host": config["host"],
            "port": config["port"],
            "error": None,
        }

    except Exception as exc:
        return {
            "status": "unavailable",
            "service": service,
            "database": config["database"],
            "host": config["host"],
            "port": config["port"],
            "error": str(exc),
        }


@mcp.tool()
def get_database_metadata(
    service: str = "payment-service",
) -> dict[str, Any]:
    """Return controlled metadata about the connected database."""

    if not service.strip():
        return {
            "status": "error",
            "error": "service must not be empty",
        }

    config = get_database_config()

    try:
        with _connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        current_database(),
                        current_user,
                        version()
                    """
                )

                database_name, current_user, version = cursor.fetchone()

        return {
            "status": "available",
            "service": service,
            "database": database_name,
            "user": current_user,
            "server_version": version,
            "host": config["host"],
            "port": config["port"],
        }

    except Exception as exc:
        return {
            "status": "unavailable",
            "service": service,
            "database": config["database"],
            "host": config["host"],
            "port": config["port"],
            "error": str(exc),
        }


if __name__ == "__main__":
    mcp.run()
