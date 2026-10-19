from __future__ import annotations

from typing import Any


class RemediationSafetyPolicy:
    """
    Safety boundary for remediation proposals.

    The remediation engine may propose changes, but it must
    never directly mutate source code, infrastructure, or
    production systems.
    """

    MIN_CONFIDENCE = 0.75

    FORBIDDEN_ACTION_TYPES = {
        "delete_production_data",
        "drop_database",
        "disable_authentication",
        "disable_authorization",
        "expose_secret",
        "rotate_production_credentials",
        "execute_arbitrary_command",
    }

    @classmethod
    def evaluate(
        cls,
        hypothesis: Any,
        evidence_summary: dict[str, Any] | None,
    ) -> tuple[bool, str]:

        if hypothesis is None:
            return (
                False,
                "No established hypothesis is available.",
            )

        role = getattr(
            hypothesis,
            "role",
            None,
        )

        confidence = float(
            getattr(
                hypothesis,
                "confidence",
                0.0,
            )
        )

        if role != "root_cause":
            return (
                False,
                "Remediation requires a root-cause hypothesis.",
            )

        if confidence < cls.MIN_CONFIDENCE:
            return (
                False,
                (
                    "Root-cause confidence is below the "
                    f"remediation threshold of "
                    f"{cls.MIN_CONFIDENCE:.2f}."
                ),
            )

        summary = evidence_summary or {}

        if not summary:
            return (
                False,
                "No evidence summary is available.",
            )

        return (
            True,
            "Root cause and evidence meet the remediation threshold.",
        )

    @classmethod
    def validate_action_type(
        cls,
        action_type: str,
    ) -> tuple[bool, str]:

        if action_type in cls.FORBIDDEN_ACTION_TYPES:
            return (
                False,
                (
                    f"Action '{action_type}' is forbidden "
                    "by the remediation safety policy."
                ),
            )

        return True, "Action type is permitted."
