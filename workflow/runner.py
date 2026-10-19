from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agent.investigator import InvestigationAgent
from agent.models import InvestigationResult

from workflow.remediation_workflow import (
    RemediationWorkflow,
    RemediationWorkflowResult,
)


@dataclass
class DevRescueRunResult:
    """
    Top-level result returned by DevRescue.

    The runner deliberately keeps the investigation result and
    remediation result separate so callers can inspect exactly
    where the workflow stopped.
    """

    investigation: InvestigationResult | None = None
    remediation: RemediationWorkflowResult | None = None

    status: str = "FAILED"
    message: str = ""

    @property
    def success(self) -> bool:
        return self.status == "COMPLETED"


class DevRescueRemediationRunner:
    """
    Top-level orchestration layer for DevRescue remediation.

    Responsibility:

        Incident
            ↓
        InvestigationAgent
            ↓
        RemediationWorkflow.prepare()
            ↓
        Human approval
            ↓
        RemediationWorkflow.approve_and_create_pr()

    This class does NOT implement:
    - investigation logic
    - hypothesis scoring
    - remediation policy
    - patch generation
    - validation
    - approval policy
    - GitHub operations

    Those responsibilities remain in their dedicated components.
    """

    def __init__(
        self,
        investigator: InvestigationAgent,
        remediation_workflow: RemediationWorkflow,
    ) -> None:
        self.investigator = investigator
        self.remediation_workflow = remediation_workflow

    # ---------------------------------------------------------
    # PHASE 1 — Investigation + Remediation Preparation
    # ---------------------------------------------------------

    def investigate_and_prepare(
        self,
        *,
        incident: str,
        service: str,
        code_evidence: list[dict[str, str]] | None = None,
        run_tests: bool = False,
    ) -> DevRescueRunResult:
        """
        Investigate an incident and prepare a remediation.

        IMPORTANT:
        This method NEVER approves anything and NEVER mutates GitHub.
        """

        if not incident or not incident.strip():
            return DevRescueRunResult(
                status="BLOCKED",
                message="Incident description is required.",
            )

        if not service or not service.strip():
            return DevRescueRunResult(
                status="BLOCKED",
                message="Service name is required.",
            )

        # -----------------------------------------------------
        # Real investigation
        # -----------------------------------------------------

        try:
            investigation = self.investigator.investigate(
                incident=incident,
                service=service,
            )
        except Exception as exc:
            return DevRescueRunResult(
                status="FAILED",
                message=f"Investigation failed: {exc}",
            )

        if investigation is None:
            return DevRescueRunResult(
                status="FAILED",
                message="Investigation returned no result.",
            )

        # -----------------------------------------------------
        # Remediation preparation
        # -----------------------------------------------------

        try:
            remediation = self.remediation_workflow.prepare(
                investigation=investigation,
                code_evidence=code_evidence,
                run_tests=run_tests,
            )
        except Exception as exc:
            return DevRescueRunResult(
                investigation=investigation,
                status="FAILED",
                message=f"Remediation preparation failed: {exc}",
            )

        # -----------------------------------------------------
        # Map workflow status
        # -----------------------------------------------------

        if remediation.status == "PENDING_APPROVAL":
            return DevRescueRunResult(
                investigation=investigation,
                remediation=remediation,
                status="PENDING_APPROVAL",
                message=(
                    "Investigation completed and remediation "
                    "is awaiting human approval."
                ),
            )

        if remediation.status == "BLOCKED":
            return DevRescueRunResult(
                investigation=investigation,
                remediation=remediation,
                status="BLOCKED",
                message=remediation.message,
            )

        if remediation.status == "FAILED":
            return DevRescueRunResult(
                investigation=investigation,
                remediation=remediation,
                status="FAILED",
                message=remediation.message,
            )

        return DevRescueRunResult(
            investigation=investigation,
            remediation=remediation,
            status=remediation.status,
            message=remediation.message,
        )

    # ---------------------------------------------------------
    # PHASE 2 — Explicit Human Approval + GitHub
    # ---------------------------------------------------------

    def approve_and_create_pr(
        self,
        *,
        prepared: DevRescueRunResult,
        approved_by: str,
        reason: str,
        branch: str,
        title: str,
        body: str,
        base: str = "main",
    ) -> DevRescueRunResult:
        """
        Continue a prepared DevRescue remediation after explicit
        human approval.

        This method cannot bypass the approval gate.
        """

        if prepared.investigation is None:
            return DevRescueRunResult(
                status="BLOCKED",
                message="Investigation result is missing.",
            )

        if prepared.remediation is None:
            return DevRescueRunResult(
                investigation=prepared.investigation,
                status="BLOCKED",
                message="Remediation result is missing.",
            )

        if prepared.remediation.status != "PENDING_APPROVAL":
            return DevRescueRunResult(
                investigation=prepared.investigation,
                remediation=prepared.remediation,
                status="BLOCKED",
                message=(
                    "Remediation is not awaiting human approval."
                ),
            )

        if not approved_by or not approved_by.strip():
            return DevRescueRunResult(
                investigation=prepared.investigation,
                remediation=prepared.remediation,
                status="BLOCKED",
                message="Approver identity is required.",
            )

        if not reason or not reason.strip():
            return DevRescueRunResult(
                investigation=prepared.investigation,
                remediation=prepared.remediation,
                status="BLOCKED",
                message="Approval reason is required.",
            )

        if not branch or not branch.strip():
            return DevRescueRunResult(
                investigation=prepared.investigation,
                remediation=prepared.remediation,
                status="BLOCKED",
                message="Remediation branch is required.",
            )

        if prepared.remediation.patch is None:
            return DevRescueRunResult(
                investigation=prepared.investigation,
                remediation=prepared.remediation,
                status="BLOCKED",
                message="Generated patch is missing.",
            )

        # -----------------------------------------------------
        # Use the existing remediation workflow.
        #
        # It owns:
        #   - approval
        #   - validation gate
        #   - GitHub workflow
        # -----------------------------------------------------

        remediation = self.remediation_workflow.approve_and_create_pr(
            prepared=prepared.remediation,
            approved_by=approved_by,
            reason=reason,
            branch=branch,
            files=prepared.remediation.patch.patches,
            title=title,
            body=body,
            base=base,
        )

        if remediation.status == "COMPLETED":
            return DevRescueRunResult(
                investigation=prepared.investigation,
                remediation=remediation,
                status="COMPLETED",
                message=(
                    "DevRescue remediation completed and "
                    "pull request created."
                ),
            )

        return DevRescueRunResult(
            investigation=prepared.investigation,
            remediation=remediation,
            status=remediation.status,
            message=remediation.message,
        )
