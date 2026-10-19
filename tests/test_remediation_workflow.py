from agent.models import InvestigationResult

from workflow.remediation_workflow import (
    RemediationWorkflow,
)


def build_investigation(
    *,
    root_cause="Invalid payment amount",
    confidence=0.90,
    decision="CONCLUDE",
    category="application_validation",
):
    return InvestigationResult(
        incident="Payment request failed with HTTP 400.",
        service="payment-service",
        status="completed",
        root_cause=root_cause,
        confidence=confidence,
        explanation=(
            "Payment validation accepted an invalid amount."
        ),
        iterations=3,
        decision={
            "decision": decision,
        },
        hypotheses=[
            {
                "name": root_cause,
                "category": category,
                "role": "root_cause",
                "confidence": confidence,
                "score": confidence,
            }
        ],
        evidence_summary={
            "logs": [],
            "traces": [],
            "metrics": [],
        },
    )


def test_workflow_blocks_investigation_without_root_cause():

    investigation = build_investigation(
        root_cause=None,
    )

    result = RemediationWorkflow().prepare(
        investigation
    )

    assert result.status == "BLOCKED"
    assert result.remediation is None


def test_workflow_blocks_low_confidence_investigation():

    investigation = build_investigation(
        confidence=0.60,
    )

    result = RemediationWorkflow().prepare(
        investigation
    )

    assert result.status == "BLOCKED"


def test_workflow_blocks_non_concluded_investigation():

    investigation = build_investigation(
        decision="INVESTIGATE",
    )

    result = RemediationWorkflow().prepare(
        investigation
    )

    assert result.status == "BLOCKED"

def test_workflow_reaches_pending_approval_for_valid_patch():

    investigation = build_investigation()

    code_evidence = [
        {
            "path": "services/payment_service/main.py",
            "content": (
                "def process_payment(amount):\n"
                "    return amount\n"
            ),
        }
    ]

    result = RemediationWorkflow().prepare(
        investigation=investigation,
        code_evidence=code_evidence,
    )

    assert result.status == "PENDING_APPROVAL"

    assert result.remediation is not None
    assert result.remediation.allowed is True
    assert result.remediation.proposal is not None

    assert result.patch is not None
    assert result.patch.allowed is True
    assert len(result.patch.patches) > 0

    assert result.validation is not None
    assert result.validation.passed is True

    assert result.approval_request is not None
    assert result.approval_request.validation_passed is True

    assert result.approval is not None
    assert result.approval.status == "PENDING"

def test_workflow_blocks_unsafe_patch_before_validation():
    investigation = build_investigation()

    code_evidence = [
        {
            "path": "../escape.py",
            "content": (
                "def process_payment(amount):\n"
                "    return amount\n"
            ),
        }
    ]

    result = RemediationWorkflow().prepare(
        investigation=investigation,
        code_evidence=code_evidence,
    )

    assert result.status == "BLOCKED"
    assert result.message == "Path traversal is not allowed."

    assert result.patch is not None
    assert result.patch.allowed is False

    # Validation must never run after patch generation rejects the patch.
    assert result.validation is None

    # Approval must never be created.
    assert result.approval_request is None
    assert result.approval is None

def test_workflow_stops_when_human_rejects():
    investigation = build_investigation()

    code_evidence = [
        {
            "path": "services/payment_service/main.py",
            "content": (
                "def process_payment(amount):\n"
                "    return amount\n"
            ),
        }
    ]

    workflow = RemediationWorkflow()

    prepared = workflow.prepare(
        investigation=investigation,
        code_evidence=code_evidence,
    )

    assert prepared.status == "PENDING_APPROVAL"
    assert prepared.validation is not None
    assert prepared.validation.passed is True
    assert prepared.approval_request is not None

    decision = workflow.approval_gate.reject(
        prepared.approval_request,
        rejected_by="test-user",
        reason="Do not apply this remediation.",
    )

    assert decision.approved is False
    assert decision.status == "REJECTED"

    # GitHub must never be touched.
    assert prepared.github is None

def test_workflow_approval_handoff_to_github():
    investigation = build_investigation()

    code_evidence = [
        {
            "path": "services/payment_service/main.py",
            "content": (
                "def process_payment(amount):\n"
                "    return amount\n"
            ),
        }
    ]

    workflow = RemediationWorkflow()

    prepared = workflow.prepare(
        investigation=investigation,
        code_evidence=code_evidence,
    )

    assert prepared.status == "PENDING_APPROVAL"
    assert prepared.validation is not None
    assert prepared.validation.passed is True
    assert prepared.approval_request is not None

    calls = {
        "branches": [],
        "files": [],
        "prs": [],
    }

    def fake_create_branch(
        branch,
        from_branch=None,
        owner=None,
        repository=None,
    ):
        calls["branches"].append(
            {
                "branch": branch,
                "from_branch": from_branch,
            }
        )
        return {
            "status": "success",
            "branch": branch,
        }

    def fake_write_file(
        path,
        content,
        branch,
        message,
        sha=None,
        owner=None,
        repository=None,
    ):
        calls["files"].append(
            {
                "path": path,
                "content": content,
                "branch": branch,
                "message": message,
            }
        )
        return {
            "status": "success",
            "path": path,
        }

    def fake_create_pr(
        title,
        body,
        head,
        base=None,
        owner=None,
        repository=None,
    ):
        calls["prs"].append(
            {
                "title": title,
                "body": body,
                "head": head,
                "base": base,
            }
        )
        return {
            "status": "success",
            "pull_request": {
                "number": 999,
                "html_url": "https://example.com/pr/999",
            },
        }

    from github_workflow.workflow import GitHubPRWorkflow

    workflow.github_workflow = GitHubPRWorkflow(
        create_branch=fake_create_branch,
        create_or_update_file=fake_write_file,
        create_pull_request=fake_create_pr,
    )

    result = workflow.approve_and_create_pr(
        prepared=prepared,
        approved_by="test-user",
        reason="Validated remediation approved for testing.",
        branch="devrescue/test-remediation",
        files=prepared.patch.patches,
        title="Fix payment validation",
        body="Automated remediation test.",
        base="main",
    )

    assert result.status == "COMPLETED", (
        f"status={result.status}, "
        f"message={result.message}, "
        f"errors={result.errors}, "
        f"github={result.github}"
    )

    assert result.approval is not None
    assert result.approval.approved is True

    assert result.github is not None
    assert result.github.success is True

    assert len(calls["branches"]) == 1
    assert len(calls["files"]) > 0
    assert len(calls["prs"]) == 1

    assert calls["branches"][0]["branch"] == "devrescue/test-remediation"
    assert calls["branches"][0]["from_branch"] == "main"

    assert calls["prs"][0]["head"] == "devrescue/test-remediation"
    assert calls["prs"][0]["base"] == "main"
