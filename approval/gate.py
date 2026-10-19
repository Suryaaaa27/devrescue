from __future__ import annotations

from .models import ApprovalDecision, ApprovalRequest


class HumanApprovalGate:

    def request(
        self,
        request: ApprovalRequest,
    ) -> ApprovalDecision:

        if not request.requires_human_approval:
            return ApprovalDecision(
                request_id=request.request_id,
                approved=False,
                decided_by=None,
                reason="Approval bypass is not permitted.",
                status="REJECTED",
            )

        if not request.validation_passed:
            return ApprovalDecision(
                request_id=request.request_id,
                approved=False,
                decided_by=None,
                reason="Approval cannot be requested before validation passes.",
                status="REJECTED",
            )

        return ApprovalDecision(
            request_id=request.request_id,
            approved=False,
            decided_by=None,
            reason="Awaiting explicit human approval.",
            status="PENDING",
        )

    def approve(
        self,
        request: ApprovalRequest,
        approved_by: str,
        reason: str,
    ) -> ApprovalDecision:

        if not approved_by.strip():
            return ApprovalDecision(
                request_id=request.request_id,
                approved=False,
                decided_by=None,
                reason="An approver identity is required.",
                status="REJECTED",
            )

        if not request.validation_passed:
            return ApprovalDecision(
                request_id=request.request_id,
                approved=False,
                decided_by=approved_by,
                reason="Cannot approve a patch that has not passed validation.",
                status="REJECTED",
            )

        if not reason.strip():
            return ApprovalDecision(
                request_id=request.request_id,
                approved=False,
                decided_by=approved_by,
                reason="An approval reason is required.",
                status="REJECTED",
            )

        return ApprovalDecision(
            request_id=request.request_id,
            approved=True,
            decided_by=approved_by,
            reason=reason,
            status="APPROVED",
        )

    def reject(
        self,
        request: ApprovalRequest,
        rejected_by: str,
        reason: str,
    ) -> ApprovalDecision:

        if not rejected_by.strip():
            return ApprovalDecision(
                request_id=request.request_id,
                approved=False,
                decided_by=None,
                reason="A reviewer identity is required.",
                status="REJECTED",
            )

        return ApprovalDecision(
            request_id=request.request_id,
            approved=False,
            decided_by=rejected_by,
            reason=reason or "Patch rejected by reviewer.",
            status="REJECTED",
        )
