from agent.models import InvestigationResult
from github_workflow.workflow import GitHubPRWorkflow
from workflow.remediation_workflow import RemediationWorkflow


def build_realistic_investigation():
    """
    Represents the output of a successful DevRescue investigation.

    The investigation has already:
    - identified the root cause
    - reached CONCLUDE
    - achieved sufficient confidence
    - classified the failure as application_validation
    """

    return InvestigationResult(
        incident="Payment request failed with HTTP 400.",
        service="payment-service",
        status="completed",
        root_cause="Invalid payment amount",
        confidence=0.92,
        explanation=(
            "The payment request contained an invalid amount. "
            "The application should reject non-positive payment amounts "
            "before processing the payment."
        ),
        iterations=3,
        decision={
            "decision": "CONCLUDE",
            "reason": "Root cause identified with sufficient evidence.",
        },
        hypotheses=[
            {
                "name": "Invalid payment amount",
                "category": "application_validation",
                "role": "root_cause",
                "confidence": 0.92,
                "score": 0.92,
                "explanation": (
                    "The payment amount violates the application's "
                    "expected validation constraints."
                ),
            }
        ],
        evidence_summary={
            "logs": [
                {
                    "message": (
                        "Payment amount must be greater than zero."
                    )
                }
            ],
            "traces": [
                {
                    "trace_id": "f83d1eadb5451abfe8f913cead3922d9",
                    "status": "error",
                }
            ],
            "metrics": [],
            "code": [],
        },
    )


def build_mock_github_workflow(calls):
    """
    Build a GitHub workflow whose mutation operations are mocked.

    No real GitHub branch, file, or PR is created.
    """

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

    def fake_create_or_update_file(
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

    def fake_create_pull_request(
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

    return GitHubPRWorkflow(
        create_branch=fake_create_branch,
        create_or_update_file=fake_create_or_update_file,
        create_pull_request=fake_create_pull_request,
    )


def test_full_remediation_e2e():
    """
    Full DevRescue remediation workflow:

        Investigation
            ↓
        Root Cause
            ↓
        Remediation Proposal
            ↓
        Patch Generation
            ↓
        Validation
            ↓
        Human Approval
            ↓
        GitHub Branch
            ↓
        Patch Write
            ↓
        Pull Request

    GitHub mutations are mocked.
    """

    # ---------------------------------------------------------
    # 1. Investigation result
    # ---------------------------------------------------------

    investigation = build_realistic_investigation()

    assert investigation.root_cause == "Invalid payment amount"
    assert investigation.confidence >= 0.75
    assert investigation.decision["decision"] == "CONCLUDE"

    # ---------------------------------------------------------
    # 2. Code evidence discovered by investigation
    # ---------------------------------------------------------

    code_evidence = [
        {
            "path": "services/payment_service/main.py",
            "content": (
                "def process_payment(amount):\n"
                "    return amount\n"
            ),
        }
    ]

    # ---------------------------------------------------------
    # 3. Build workflow
    # ---------------------------------------------------------

    workflow = RemediationWorkflow()

    github_calls = {
        "branches": [],
        "files": [],
        "prs": [],
    }

    workflow.github_workflow = build_mock_github_workflow(
        github_calls
    )

    # ---------------------------------------------------------
    # 4. Prepare remediation
    # ---------------------------------------------------------

    prepared = workflow.prepare(
        investigation=investigation,
        code_evidence=code_evidence,
        run_tests=False,
    )

    # Investigation must be actionable.
    assert prepared.status == "PENDING_APPROVAL"

    # Remediation proposal.
    assert prepared.remediation is not None
    assert prepared.remediation.allowed is True

    # Patch generation.
    assert prepared.patch is not None
    assert prepared.patch.allowed is True
    assert len(prepared.patch.patches) > 0

    # Validation.
    assert prepared.validation is not None
    assert prepared.validation.passed is True

    # Human approval request.
    assert prepared.approval_request is not None
    assert prepared.approval_request.validation_passed is True

    # Nothing should have touched GitHub yet.
    assert github_calls["branches"] == []
    assert github_calls["files"] == []
    assert github_calls["prs"] == []

    # ---------------------------------------------------------
    # 5. Human approval + GitHub workflow
    # ---------------------------------------------------------

    result = workflow.approve_and_create_pr(
        prepared=prepared,
        approved_by="e2e-test-user",
        reason=(
            "Remediation was validated and approved "
            "for the E2E test."
        ),
        branch="devrescue/e2e-payment-validation",
        files=prepared.patch.patches,
        title="Fix payment amount validation",
        body=(
            "This PR was generated by the DevRescue "
            "remediation E2E test."
        ),
        base="main",
    )

    # ---------------------------------------------------------
    # 6. Final workflow result
    # ---------------------------------------------------------

    assert result.status == "COMPLETED"

    assert result.message == (
        "Remediation validated, approved, and "
        "pull request created."
    )

    # ---------------------------------------------------------
    # 7. Approval verification
    # ---------------------------------------------------------

    assert result.approval is not None
    assert result.approval.approved is True
    assert result.approval.decided_by == "e2e-test-user"

    # ---------------------------------------------------------
    # 8. GitHub workflow verification
    # ---------------------------------------------------------

    assert result.github is not None
    assert result.github.success is True

    assert result.github.validation_passed is True
    assert result.github.approval_granted is True

    assert (
        result.github.branch
        == "devrescue/e2e-payment-validation"
    )

    # ---------------------------------------------------------
    # 9. Verify branch creation
    # ---------------------------------------------------------

    assert len(github_calls["branches"]) == 1

    assert github_calls["branches"][0]["branch"] == (
        "devrescue/e2e-payment-validation"
    )

    assert github_calls["branches"][0]["from_branch"] == "main"

    # ---------------------------------------------------------
    # 10. Verify patch was written
    # ---------------------------------------------------------

    assert len(github_calls["files"]) > 0

    written_paths = [
        item["path"]
        for item in github_calls["files"]
    ]

    assert (
        "services/payment_service/main.py"
        in written_paths
    )

    for file_call in github_calls["files"]:
        assert (
            file_call["branch"]
            == "devrescue/e2e-payment-validation"
        )

        assert file_call["content"]

        assert file_call["message"] == (
            "Apply remediation for payment-service"
        )

    # ---------------------------------------------------------
    # 11. Verify PR creation
    # ---------------------------------------------------------

    assert len(github_calls["prs"]) == 1

    pr = github_calls["prs"][0]

    assert pr["title"] == "Fix payment amount validation"

    assert pr["head"] == (
        "devrescue/e2e-payment-validation"
    )

    assert pr["base"] == "main"

    assert (
        result.github.pull_request["number"]
        == 999
    )

    assert (
        result.github.pull_request["html_url"]
        == "https://example.com/pr/999"
    )

    # ---------------------------------------------------------
    # 12. Final safety assertion
    # ---------------------------------------------------------

    # Exactly one branch, file write(s), and PR should have
    # occurred in the mocked GitHub layer.
    assert len(github_calls["branches"]) == 1
    assert len(github_calls["files"]) >= 1
    assert len(github_calls["prs"]) == 1
