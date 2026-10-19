from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent.models import InvestigationResult
from hypothesis.models import Hypothesis

from remediation.engine import RemediationEngine
from remediation.models import RemediationDecision

from patch_generation.generator import PatchGenerator
from patch_generation.models import PatchProposal

from validation.engine import ValidationEngine
from validation.models import ValidationResult

from approval.gate import HumanApprovalGate
from approval.models import ApprovalDecision, ApprovalRequest

from github_workflow.workflow import GitHubPRWorkflow
from github_workflow.models import GitHubWorkflowResult


@dataclass
class RemediationWorkflowResult:
    """
    Result of the complete DevRescue remediation lifecycle.
    """

    status: str
    message: str
    investigation: InvestigationResult

    remediation: RemediationDecision | None = None
    patch: PatchProposal | None = None
    validation: ValidationResult | None = None
    approval_request: ApprovalRequest | None = None
    approval: ApprovalDecision | None = None
    github: GitHubWorkflowResult | None = None

    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.status == "COMPLETED"


class RemediationWorkflow:
    """
    Coordinates:

        Investigation
            ↓
        Remediation proposal
            ↓
        Patch generation
            ↓
        Validation
            ↓
        Human approval
            ↓
        GitHub PR

    This class does not bypass any safety boundary.
    """

    def __init__(
        self,
        remediation_engine: RemediationEngine | None = None,
        patch_generator: PatchGenerator | None = None,
        validation_engine: ValidationEngine | None = None,
        approval_gate: HumanApprovalGate | None = None,
        github_workflow: GitHubPRWorkflow | None = None,
    ):
        self.remediation_engine = (
            remediation_engine
            or RemediationEngine()
        )

        self.patch_generator = (
            patch_generator
            or PatchGenerator()
        )

        self.validation_engine = (
            validation_engine
            or ValidationEngine()
        )

        self.approval_gate = (
            approval_gate
            or HumanApprovalGate()
        )

        self.github_workflow = github_workflow

    # ==========================================================
    # PREPARE REMEDIATION
    # ==========================================================

    def prepare(
        self,
        investigation: InvestigationResult,
        code_evidence: list[dict[str, Any]] | None = None,
        run_tests: bool = False,
    ) -> RemediationWorkflowResult:
        """
        Execute the remediation pipeline up to the approval boundary.

        No GitHub mutation occurs here.
        """

        if not self._investigation_is_actionable(
            investigation
        ):
            return RemediationWorkflowResult(
                status="BLOCKED",
                message=(
                    "Investigation did not establish a sufficiently "
                    "supported root cause."
                ),
                investigation=investigation,
            )

        hypothesis = self._build_hypothesis(
            investigation
        )

        evidence_summary = dict(
            investigation.evidence_summary or {}
        )

        if code_evidence:
            evidence_summary["code"] = code_evidence

        # ------------------------------------------------------
        # 1. Remediation proposal
        # ------------------------------------------------------

        remediation = self.remediation_engine.propose(
            hypothesis=hypothesis,
            evidence_summary=evidence_summary,
        )

        if not remediation.allowed:
            return RemediationWorkflowResult(
                status="BLOCKED",
                message=remediation.reason,
                investigation=investigation,
                remediation=remediation,
            )

        proposal = remediation.proposal

        if proposal is None:
            return RemediationWorkflowResult(
                status="FAILED",
                message=(
                    "Remediation engine returned an allowed decision "
                    "without a proposal."
                ),
                investigation=investigation,
                remediation=remediation,
                errors=[
                    "Invalid remediation decision."
                ],
            )

        # ------------------------------------------------------
        # 2. Patch generation
        # ------------------------------------------------------

        if not proposal.patch_generation_allowed:
            blocked_patch = PatchProposal(
                allowed=False,
                reason=(
                    "Patch generation is not allowed by the "
                    "remediation proposal."
                ),
                patches=[],
                rationale=proposal.rationale,
                validation_requirements=(
                    proposal.validation_requirements
                ),
                safety_checks=proposal.safety_constraints,
            )
            return RemediationWorkflowResult(
                status="BLOCKED",
                message=(
                    "Patch generation is not allowed by the "
                    "remediation proposal."
                ),
                investigation=investigation,
                remediation=remediation,
                patch=blocked_patch,
                validation=None,
                approval_request=None,
                approval=None,
                github=None,
                errors=[],
            )

        patch = self.patch_generator.generate(
            proposal=proposal,
            code_evidence=code_evidence or [],
        )

        if not patch.allowed:
            return RemediationWorkflowResult(
                status="BLOCKED",
                message=patch.reason,
                investigation=investigation,
                remediation=remediation,
                patch=patch,
            )

        # ------------------------------------------------------
        # 3. Validation
        # ------------------------------------------------------

        validation = self.validation_engine.validate(
            patch_proposal=patch,
            run_tests=run_tests,
        )

        if not validation.passed:
            return RemediationWorkflowResult(
                status="VALIDATION_FAILED",
                message=validation.summary,
                investigation=investigation,
                remediation=remediation,
                patch=patch,
                validation=validation,
            )

        # ------------------------------------------------------
        # 4. Create human approval request
        # ------------------------------------------------------

        approval_request = ApprovalRequest(
            request_id=self._build_request_id(
                investigation
            ),
            incident=investigation.incident,
            hypothesis=proposal.hypothesis,
            summary=proposal.summary,
            risk_level=proposal.risk_level,
            affected_files=list(
                proposal.affected_files
            ),
            patch_count=len(patch.patches),
            validation_passed=validation.passed,
            requires_human_approval=(
                proposal.requires_human_approval
            ),
        )

        approval = self.approval_gate.request(
            approval_request
        )

        if approval.status != "PENDING":
            return RemediationWorkflowResult(
                status="BLOCKED",
                message=approval.reason,
                investigation=investigation,
                remediation=remediation,
                patch=patch,
                validation=validation,
                approval_request=approval_request,
                approval=approval,
            )

        return RemediationWorkflowResult(
            status="PENDING_APPROVAL",
            message=(
                "Remediation is validated and awaiting "
                "explicit human approval."
            ),
            investigation=investigation,
            remediation=remediation,
            patch=patch,
            validation=validation,
            approval_request=approval_request,
            approval=approval,
        )

    # ==========================================================
    # APPROVAL + GITHUB
    # ==========================================================

    def approve_and_create_pr(
        self,
        prepared: RemediationWorkflowResult,
        approved_by: str,
        reason: str,
        branch: str,
        files: list[dict[str, str]],
        title: str,
        body: str,
        base: str = "main",
    ) -> RemediationWorkflowResult:
        """
        Continue a prepared workflow after explicit approval.
        """

        if prepared.status != "PENDING_APPROVAL":
            return self._failure(
                prepared,
                "Workflow is not awaiting approval.",
            )

        if prepared.approval_request is None:
            return self._failure(
                prepared,
                "Approval request is missing.",
            )

        if prepared.validation is None:
            return self._failure(
                prepared,
                "Validation result is missing.",
            )

        if not prepared.validation.passed:
            return self._failure(
                prepared,
                "Cannot approve a failed validation.",
            )

        # ------------------------------------------------------
        # Explicit human approval
        # ------------------------------------------------------

        approval = self.approval_gate.approve(
            request=prepared.approval_request,
            approved_by=approved_by,
            reason=reason,
        )

        prepared.approval = approval

        if not approval.approved:
            prepared.status = "BLOCKED"
            prepared.message = approval.reason
            return prepared

        # ------------------------------------------------------
        # GitHub workflow must be explicitly configured
        # ------------------------------------------------------

        if self.github_workflow is None:
            return self._failure(
                prepared,
                "GitHub workflow is not configured.",
            )

        # ------------------------------------------------------
        # GitHub mutation
        # ------------------------------------------------------

        github_result = self.github_workflow.execute(
            patch_proposal=prepared.patch,
            validation_result=prepared.validation,
            approval_decision=approval,
            branch=branch,
            commit_message=f"Apply remediation for {prepared.investigation.service}",
            pr_title=title,
            pr_body=body,
            base_branch=base,
        )

        prepared.github = github_result

        if not github_result.success:
            prepared.status = "FAILED"
            prepared.message = github_result.message
            return prepared

        prepared.status = "COMPLETED"
        prepared.message = (
            "Remediation validated, approved, and "
            "pull request created."
        )

        return prepared

    # ==========================================================
    # HELPERS
    # ==========================================================

    @staticmethod
    def _investigation_is_actionable(
        investigation: InvestigationResult,
    ) -> bool:
        """
        Only a concluded investigation with sufficient
        root-cause confidence may enter remediation.
        """

        if not investigation.root_cause:
            return False

        if investigation.confidence < 0.75:
            return False

        decision = investigation.decision or {}

        return decision.get("decision") == "CONCLUDE"

    @staticmethod
    def _build_hypothesis(
        investigation: InvestigationResult,
    ) -> Hypothesis:
        """
        Recover the actual Hypothesis from the investigation
        result instead of inventing a new hypothesis when possible.
        """

        for item in investigation.hypotheses:

            if isinstance(item, Hypothesis):
                if item.name == investigation.root_cause:
                    return item
                continue

            if (
                item.get("name")
                == investigation.root_cause
            ):
                return Hypothesis(
                    name=item["name"],
                    category=item["category"],
                    role=item.get(
                        "role",
                        "root_cause",
                    ),
                    confidence=float(
                        item.get(
                            "confidence",
                            investigation.confidence,
                        )
                    ),
                    score=float(
                        item.get(
                            "score",
                            investigation.confidence,
                        )
                    ),
                    explanation=(
                        investigation.explanation
                        or ""
                    ),
                )

        for item in investigation.hypotheses:
            if isinstance(item, Hypothesis):
                if item.role == "root_cause":
                    return item
                continue

            if item.get("role") == "root_cause":
                return Hypothesis(
                    name=item["name"],
                    category=item["category"],
                    role=item["role"],
                    confidence=float(
                        item.get(
                            "confidence",
                            investigation.confidence,
                        )
                    ),
                    score=float(
                        item.get(
                            "score",
                            investigation.confidence,
                        )
                    ),
                    explanation=(
                        investigation.explanation
                        or ""
                    ),
                )

        # This fallback is deliberately conservative.
        return Hypothesis(
            name=investigation.root_cause,
            category="application_error",
            role="root_cause",
            confidence=investigation.confidence,
            score=investigation.confidence,
            explanation=(
                investigation.explanation
                or ""
            ),
        )

    @staticmethod
    def _build_request_id(
        investigation: InvestigationResult,
    ) -> str:

        return (
            f"devrescue-{investigation.service}-"
            f"{investigation.iterations}"
        )

    @staticmethod
    def _failure(
        prepared: RemediationWorkflowResult,
        message: str,
    ) -> RemediationWorkflowResult:

        prepared.status = "FAILED"
        prepared.message = message
        prepared.errors.append(message)

        return prepared
