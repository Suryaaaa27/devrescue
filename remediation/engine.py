from __future__ import annotations

from typing import Any

from hypothesis.models import Hypothesis

from remediation.models import (
    RemediationAction,
    RemediationDecision,
    RemediationProposal,
)
from remediation.safety import RemediationSafetyPolicy
from remediation.strategies import (
    ApplicationExceptionStrategy,
    DatabaseFailureStrategy,
    InvalidInputStrategy,
    RemediationStrategy,
)


class RemediationEngine:
    """
    Converts an established root-cause hypothesis into a
    controlled remediation proposal.

    This engine is proposal-only.

    It does NOT:
        - modify files
        - execute commands
        - modify infrastructure
        - commit changes
        - create pull requests
    """

    def __init__(
        self,
        strategies: list[RemediationStrategy] | None = None,
    ):

        self.strategies = strategies or [
            DatabaseFailureStrategy(),
            InvalidInputStrategy(),
            ApplicationExceptionStrategy(),
        ]

    def propose(
        self,
        hypothesis: Hypothesis | None,
        evidence_summary: dict[str, Any] | None = None,
    ) -> RemediationDecision:

        evidence_summary = evidence_summary or {}

        allowed, reason = (
            RemediationSafetyPolicy.evaluate(
                hypothesis,
                evidence_summary,
            )
        )

        if not allowed:
            return RemediationDecision(
                allowed=False,
                reason=reason,
                proposal=None,
            )

        strategy = self._find_strategy(
            hypothesis
        )

        if strategy is None:
            return RemediationDecision(
                allowed=False,
                reason=(
                    "No remediation strategy exists for "
                    f"hypothesis category "
                    f"'{hypothesis.category}'."
                ),
                proposal=None,
            )

        actions = strategy.build_actions(
            hypothesis,
            evidence_summary,
        )

        safe_actions: list[RemediationAction] = []

        for action in actions:

            valid, action_reason = (
                RemediationSafetyPolicy.validate_action_type(
                    action.action_type
                )
            )

            if not valid:
                return RemediationDecision(
                    allowed=False,
                    reason=action_reason,
                    proposal=None,
                )

            safe_actions.append(action)

        affected_files = (
            self._extract_affected_files(
                evidence_summary
            )
        )

        patchable = any(
            action.patchable
            for action in safe_actions
        )

        validation_requirements = (
            self._build_validation_requirements(
                hypothesis,
                safe_actions,
            )
        )

        safety_constraints = [
            "Human approval is required before applying remediation.",
            "No production mutation is permitted by this engine.",
            "Generated patches must be validated before PR creation.",
            "Secrets and credentials must never be inserted into patches.",
        ]

        proposal = RemediationProposal(
            hypothesis=hypothesis.name,
            category=hypothesis.category,
            summary=self._build_summary(
                hypothesis
            ),
            rationale=hypothesis.explanation,
            actions=safe_actions,
            affected_files=affected_files,
            risk_level=self._calculate_risk(
                hypothesis,
                safe_actions,
            ),
            confidence=hypothesis.confidence,
            requires_human_approval=True,
            patch_generation_allowed=(
                patchable
                and bool(affected_files)
            ),
            validation_requirements=(
                validation_requirements
            ),
            safety_constraints=safety_constraints,
        )

        return RemediationDecision(
            allowed=True,
            reason=(
                "Remediation proposal generated successfully."
            ),
            proposal=proposal,
        )

    def _find_strategy(
        self,
        hypothesis: Hypothesis,
    ) -> RemediationStrategy | None:

        for strategy in self.strategies:

            if strategy.supports(hypothesis):
                return strategy

        return None

    @staticmethod
    def _extract_affected_files(
        evidence_summary: dict[str, Any],
    ) -> list[str]:

        files: list[str] = []

        for item in evidence_summary.get(
            "code",
            [],
        ):

            if isinstance(item, dict):
                path = item.get("path")
            else:
                path = getattr(item, "path", None)

            if path and path not in files:
                files.append(str(path))

        return files

    @staticmethod
    def _build_summary(
        hypothesis: Hypothesis,
    ) -> str:

        return (
            f"Remediate the confirmed root cause: "
            f"{hypothesis.name}."
        )

    @staticmethod
    def _calculate_risk(
        hypothesis: Hypothesis,
        actions: list[RemediationAction],
    ) -> str:

        if hypothesis.category == "database_failure":
            return "high"

        if any(
            action.action_type
            == "correct_application_exception"
            for action in actions
        ):
            return "medium"

        return "medium"

    @staticmethod
    def _build_validation_requirements(
        hypothesis: Hypothesis,
        actions: list[RemediationAction],
    ) -> list[str]:

        requirements = [
            "Run the relevant automated test suite.",
            "Verify that the original failure condition no longer occurs.",
        ]

        if hypothesis.category == "database_failure":
            requirements.extend(
                [
                    "Verify database connectivity.",
                    "Verify the affected service health endpoint.",
                    "Verify no new database connection errors appear in telemetry.",
                ]
            )

        if hypothesis.category == "application_validation":
            requirements.append(
                "Test both valid and invalid request inputs."
            )

        if any(
            action.patchable
            for action in actions
        ):
            requirements.append(
                "Review the generated diff before approval."
            )

        return requirements
