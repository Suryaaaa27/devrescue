from __future__ import annotations

from typing import Any


investigations: dict[str, dict[str, Any]] = {}


def save_investigation(
    investigation_id: str,
    data: dict[str, Any],
) -> None:
    investigations[investigation_id] = data


def get_investigation(
    investigation_id: str,
) -> dict[str, Any] | None:
    return investigations.get(investigation_id)


def get_all_investigations() -> list[dict[str, Any]]:
    return list(investigations.values())
