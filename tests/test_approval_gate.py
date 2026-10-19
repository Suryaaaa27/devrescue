from approval.gate import HumanApprovalGate
from approval.models import ApprovalRequest


def valid_request():
    return ApprovalRequest(
        request_id="approval-001",
        incident="Payment failed with HTTP 400",
        hypothesis="Invalid payment input",
        summary="Add validation before payment processing.",
        risk_level="medium",
        affected_files=["services/payment.py"],
        patch_count=1,
        validation_passed=True,
    )


def test_approval_request_starts_pending():
    result = HumanApprovalGate().request(valid_request())

    assert result.status == "PENDING"
    assert result.approved is False


def test_valid_human_approval():
    request = valid_request()

    result = HumanApprovalGate().approve(
        request,
        approved_by="surya",
        reason="Reviewed the generated patch and validation results.",
    )

    assert result.status == "APPROVED"
    assert result.approved is True
    assert result.decided_by == "surya"


def test_approval_requires_identity():
    result = HumanApprovalGate().approve(
        valid_request(),
        approved_by="",
        reason="Looks good.",
    )

    assert result.approved is False
    assert result.status == "REJECTED"


def test_approval_requires_reason():
    result = HumanApprovalGate().approve(
        valid_request(),
        approved_by="surya",
        reason="",
    )

    assert result.approved is False
    assert result.status == "REJECTED"


def test_unvalidated_patch_cannot_be_approved():
    request = ApprovalRequest(
        request_id="approval-002",
        incident="Payment failure",
        hypothesis="Application exception",
        summary="Fix exception.",
        risk_level="medium",
        affected_files=["services/payment.py"],
        patch_count=1,
        validation_passed=False,
    )

    result = HumanApprovalGate().approve(
        request,
        approved_by="surya",
        reason="Reviewed.",
    )

    assert result.approved is False
    assert result.status == "REJECTED"


def test_rejection():
    result = HumanApprovalGate().reject(
        valid_request(),
        rejected_by="surya",
        reason="Patch requires further investigation.",
    )

    assert result.approved is False
    assert result.status == "REJECTED"
    assert result.decided_by == "surya"


def test_rejection_requires_identity():
    result = HumanApprovalGate().reject(
        valid_request(),
        rejected_by="",
        reason="No.",
    )

    assert result.status == "REJECTED"
    assert result.decided_by is None


def test_approval_serialization():
    result = HumanApprovalGate().approve(
        valid_request(),
        approved_by="surya",
        reason="Reviewed.",
    )

    payload = result.to_dict()

    assert payload["approved"] is True
    assert payload["status"] == "APPROVED"
