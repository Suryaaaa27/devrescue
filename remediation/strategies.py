from __future__ import annotations

from typing import Any

from hypothesis.models import Hypothesis

from remediation.models import RemediationAction


class RemediationStrategy:
    def supports(
        self,
        hypothesis: Hypothesis,
    ) -> bool:
        raise NotImplementedError

    def build_actions(
        self,
        hypothesis: Hypothesis,
        evidence_summary: dict[str, Any],
    ) -> list[RemediationAction]:
        raise NotImplementedError


class DatabaseFailureStrategy(RemediationStrategy):

    def supports(
        self,
        hypothesis: Hypothesis,
    ) -> bool:

        return hypothesis.category == "database_failure"

    def build_actions(
        self,
        hypothesis: Hypothesis,
        evidence_summary: dict[str, Any],
    ) -> list[RemediationAction]:

        database = "unknown database"

        database_entries = evidence_summary.get(
            "database",
            [],
        )

        if database_entries:
            database = str(
                database_entries[0].get(
                    "database",
                    database,
                )
            )

        return [
            RemediationAction(
                action_type="restore_database_connectivity",
                description=(
                    f"Restore connectivity between the "
                    f"affected service and '{database}'."
                ),
                target=database,
                rationale=(
                    "The investigation established a database "
                    "dependency failure as the root cause."
                ),
                patchable=False,
                requires_approval=True,
            ),
            RemediationAction(
                action_type="verify_database_configuration",
                description=(
                    "Verify database host, port, credentials "
                    "source, and connection configuration."
                ),
                target=database,
                rationale=(
                    "Database connectivity remediation should "
                    "verify configuration before any code change."
                ),
                patchable=True,
                requires_approval=True,
            ),
        ]


class ApplicationExceptionStrategy(RemediationStrategy):

    def supports(
        self,
        hypothesis: Hypothesis,
    ) -> bool:

        return hypothesis.category == "application_error"

    def build_actions(
        self,
        hypothesis: Hypothesis,
        evidence_summary: dict[str, Any],
    ) -> list[RemediationAction]:

        return [
            RemediationAction(
                action_type="correct_application_exception",
                description=(
                    "Modify the application code responsible "
                    "for the confirmed exception."
                ),
                target=None,
                rationale=(
                    "The root cause is an application-level "
                    "exception supported by investigation evidence."
                ),
                patchable=True,
                requires_approval=True,
            ),
        ]


class InvalidInputStrategy(RemediationStrategy):

    def supports(
        self,
        hypothesis: Hypothesis,
    ) -> bool:

        return hypothesis.category == "application_validation"

    def build_actions(
        self,
        hypothesis: Hypothesis,
        evidence_summary: dict[str, Any],
    ) -> list[RemediationAction]:

        return [
            RemediationAction(
                action_type="improve_input_validation",
                description=(
                    "Strengthen request validation and return "
                    "a controlled validation response for invalid input."
                ),
                target=None,
                rationale=(
                    "Invalid input was identified as the root cause "
                    "of the observed payment failure."
                ),
                patchable=True,
                requires_approval=True,
            ),
        ]
