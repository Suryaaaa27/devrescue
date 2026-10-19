from dataclasses import dataclass

from github_workflow import (
    GitHubPRWorkflow,
    GitHubWorkflowStatus,
)


@dataclass
class MockPatchFile:
    path: str
    content: str


@dataclass
class MockPatch:
    files: list[MockPatchFile]


@dataclass
class MockValidation:
    status: str


@dataclass
class MockApproval:
    status: str


def make_workflow(
    calls: list,
):
    def create_branch(**kwargs):
        calls.append(("branch", kwargs))
        return {"status": "success"}

    def create_file(**kwargs):
        calls.append(("file", kwargs))
        return {"status": "success"}

    def create_pr(**kwargs):
        calls.append(("pr", kwargs))
        return {
            "status": "success",
            "pull_request": {
                "number": 42,
                "html_url": "https://github.com/example/pr/42",
            },
        }

    return GitHubPRWorkflow(
        create_branch=create_branch,
        create_or_update_file=create_file,
        create_pull_request=create_pr,
    )


def make_patch():
    return MockPatch(
        files=[
            MockPatchFile(
                path="services/payment_service/main.py",
                content="print('patched')\n",
            )
        ]
    )


def test_validation_failure_blocks_workflow():
    calls = []
    workflow = make_workflow(calls)

    result = workflow.execute(
        patch_proposal=make_patch(),
        validation_result=MockValidation("failed"),
        approval_decision=MockApproval("approved"),
        branch="devrescue/fix-payment",
        commit_message="fix: payment validation",
        pr_title="fix: payment validation",
        pr_body="Automated remediation.",
    )

    assert result.status == GitHubWorkflowStatus.BLOCKED
    assert result.validation_passed is False
    assert calls == []


def test_missing_validation_blocks_workflow():
    calls = []
    workflow = make_workflow(calls)

    result = workflow.execute(
        patch_proposal=make_patch(),
        validation_result=None,
        approval_decision=MockApproval("approved"),
        branch="devrescue/fix-payment",
        commit_message="fix: payment validation",
        pr_title="fix: payment validation",
        pr_body="Automated remediation.",
    )

    assert result.status == GitHubWorkflowStatus.BLOCKED
    assert calls == []


def test_approval_rejection_blocks_workflow():
    calls = []
    workflow = make_workflow(calls)

    result = workflow.execute(
        patch_proposal=make_patch(),
        validation_result=MockValidation("passed"),
        approval_decision=MockApproval("rejected"),
        branch="devrescue/fix-payment",
        commit_message="fix: payment validation",
        pr_title="fix: payment validation",
        pr_body="Automated remediation.",
    )

    assert result.status == GitHubWorkflowStatus.BLOCKED
    assert result.validation_passed is True
    assert result.approval_granted is False
    assert calls == []


def test_missing_approval_blocks_workflow():
    calls = []
    workflow = make_workflow(calls)

    result = workflow.execute(
        patch_proposal=make_patch(),
        validation_result=MockValidation("passed"),
        approval_decision=None,
        branch="devrescue/fix-payment",
        commit_message="fix: payment validation",
        pr_title="fix: payment validation",
        pr_body="Automated remediation.",
    )

    assert result.status == GitHubWorkflowStatus.BLOCKED
    assert calls == []


def test_empty_patch_blocks_workflow():
    calls = []
    workflow = make_workflow(calls)

    result = workflow.execute(
        patch_proposal=MockPatch(files=[]),
        validation_result=MockValidation("passed"),
        approval_decision=MockApproval("approved"),
        branch="devrescue/fix-payment",
        commit_message="fix: payment validation",
        pr_title="fix: payment validation",
        pr_body="Automated remediation.",
    )

    assert result.status == GitHubWorkflowStatus.BLOCKED
    assert calls == []


def test_approved_workflow_creates_branch_files_and_pr():
    calls = []
    workflow = make_workflow(calls)

    result = workflow.execute(
        patch_proposal=make_patch(),
        validation_result=MockValidation("passed"),
        approval_decision=MockApproval("approved"),
        branch="devrescue/fix-payment",
        commit_message="fix: payment validation",
        pr_title="fix: payment validation",
        pr_body="Automated remediation.",
    )

    assert result.status == GitHubWorkflowStatus.COMPLETED
    assert result.success is True
    assert result.validation_passed is True
    assert result.approval_granted is True

    assert result.branch == "devrescue/fix-payment"

    assert result.written_files == [
        "services/payment_service/main.py"
    ]

    assert result.pull_request["number"] == 42

    assert [call[0] for call in calls] == [
        "branch",
        "file",
        "pr",
    ]


def test_branch_failure_stops_workflow():
    calls = []

    def create_branch(**kwargs):
        calls.append("branch")
        return {
            "status": "error",
            "error": {
                "message": "branch already exists",
            },
        }

    workflow = GitHubPRWorkflow(
        create_branch=create_branch,
        create_or_update_file=lambda **kwargs: calls.append("file"),
        create_pull_request=lambda **kwargs: calls.append("pr"),
    )

    result = workflow.execute(
        patch_proposal=make_patch(),
        validation_result=MockValidation("passed"),
        approval_decision=MockApproval("approved"),
        branch="devrescue/fix-payment",
        commit_message="fix: payment validation",
        pr_title="fix: payment validation",
        pr_body="Automated remediation.",
    )

    assert result.status == GitHubWorkflowStatus.FAILED
    assert "branch already exists" in result.errors[0]
    assert calls == ["branch"]


def test_file_failure_stops_before_pull_request():
    calls = []

    def create_branch(**kwargs):
        calls.append("branch")
        return {"status": "success"}

    def create_file(**kwargs):
        calls.append("file")
        return {
            "status": "error",
            "error": {
                "message": "write denied",
            },
        }

    def create_pr(**kwargs):
        calls.append("pr")
        return {"status": "success"}

    workflow = GitHubPRWorkflow(
        create_branch=create_branch,
        create_or_update_file=create_file,
        create_pull_request=create_pr,
    )

    result = workflow.execute(
        patch_proposal=make_patch(),
        validation_result=MockValidation("passed"),
        approval_decision=MockApproval("approved"),
        branch="devrescue/fix-payment",
        commit_message="fix: payment validation",
        pr_title="fix: payment validation",
        pr_body="Automated remediation.",
    )

    assert result.status == GitHubWorkflowStatus.FAILED
    assert result.written_files == []
    assert calls == ["branch", "file"]


def test_pull_request_failure_returns_failed():
    calls = []

    def create_branch(**kwargs):
        calls.append("branch")
        return {"status": "success"}

    def create_file(**kwargs):
        calls.append("file")
        return {"status": "success"}

    def create_pr(**kwargs):
        calls.append("pr")
        return {
            "status": "error",
            "error": {
                "message": "PR creation denied",
            },
        }

    workflow = GitHubPRWorkflow(
        create_branch=create_branch,
        create_or_update_file=create_file,
        create_pull_request=create_pr,
    )

    result = workflow.execute(
        patch_proposal=make_patch(),
        validation_result=MockValidation("passed"),
        approval_decision=MockApproval("approved"),
        branch="devrescue/fix-payment",
        commit_message="fix: payment validation",
        pr_title="fix: payment validation",
        pr_body="Automated remediation.",
    )

    assert result.status == GitHubWorkflowStatus.FAILED
    assert result.written_files == [
        "services/payment_service/main.py"
    ]
    assert "PR creation denied" in result.errors[0]
    assert calls == ["branch", "file", "pr"]

def test_protected_branch_is_blocked():
    calls = []
    workflow = make_workflow(calls)

    result = workflow.execute(
        patch_proposal=make_patch(),
        validation_result=MockValidation("passed"),
        approval_decision=MockApproval("approved"),
        branch="main",
        commit_message="fix: payment validation",
        pr_title="fix: payment validation",
        pr_body="Automated remediation.",
    )

    assert result.status == GitHubWorkflowStatus.BLOCKED
    assert calls == []
