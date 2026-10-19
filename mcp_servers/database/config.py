from __future__ import annotations

import os


def get_database_config() -> dict[str, object]:
    return {
        "host": os.getenv(
            "DEVRESCUE_DATABASE_HOST",
            "localhost",
        ),
        "port": int(
            os.getenv(
                "DEVRESCUE_DATABASE_PORT",
                "5433",
            )
        ),
        "database": os.getenv(
            "DEVRESCUE_DATABASE_NAME",
            "payments",
        ),
        "user": os.getenv(
            "DEVRESCUE_DATABASE_USER",
            "devrescue",
        ),
        "password": os.getenv(
            "DEVRESCUE_DATABASE_PASSWORD",
            "devrescue_dev_password",
        ),
    }
