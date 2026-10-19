from dataclasses import dataclass

from github_workflow import GitHubPRWorkflow
from mcp_servers.github.registry import build_github_write_tools


@dataclass
class PatchFile:
    path: str
    content: str


@dataclass
class PatchProposal:
    files: list[PatchFile]


@dataclass
class ValidationResult:
    status: str


@dataclass
class ApprovalDecision:
    status: str


def test_workflow_uses_github_write_tools():
    tools = build_github_write_tools()

    assert "create_branch" in tools
    assert "create_or_update_file" in tools
    assert "create_pull_request" in tools

    workflow = GitHubPRWorkflow(
        create_branch=tools["create_branch"],
        create_or_update_file=tools["create_or_update_file"],
        create_pull_request=tools["create_pull_request"],
    )

    assert workflow.create_branch is tools["create_branch"]
    assert workflow.create_or_update_file is tools["create_or_update_file"]
    assert workflow.create_pull_request is tools["create_pull_request"]


def test_approved_workflow_executes_with_mocked_github_tools():
    calls = []

    def create_branch(**kwargs):
        calls.append(("create_branch", kwargs))
        return {"status": "success"}

    def create_file(**kwargs):
        calls.append(("create_file", kwargs))
        return {"status": "success"}

    def create_pr(**kwargs):
        calls.append(("create_pr", kwargs))
        return {
            "status": "success",
            "pull_request": {
                "number": 999,
                "html_url": "https://example.com/pr/999",
            },
        }

    workflow = GitHubPRWorkflow(
        create_branch=create_branch,
        create_or_update_file=create_file,
        create_pull_request=create_pr,
    )

    patch = PatchProposal(
        files=[
            PatchFile(
                path="services/payment_service/main.py",
                content="patched content",
            )
        ]
    )

    result = workflow.execute(
        patch_proposal=patch,
        validation_result=ValidationResult(status="passed"),
        approval_decision=ApprovalDecision(status="approved"),
        branch="devrescue/fix-payment-validation",
        commit_message="fix: payment validation",
        pr_title="fix: payment validation",
        pr_body="DevRescue automated remediation.",
        base_branch="main",
        owner="Suryaaaa27",
        repository="devrescue",
    )

    assert result.success is True
    assert result.status.value == "completed"
    assert result.branch == "devrescue/fix-payment-validation"

    assert result.written_files == [
        "services/payment_service/main.py"
    ]

    assert result.pull_request["number"] == 999

    assert [call[0] for call in calls] == [
        "create_branch",
        "create_file",
        "create_pr",
    ]

    assert calls[0][1]["branch"] == "devrescue/fix-payment-validation"
    assert calls[0][1]["from_branch"] == "main"

    assert calls[1][1]["path"] == "services/payment_service/main.py"
    assert calls[1][1]["branch"] == "devrescue/fix-payment-validation"

    assert calls[2][1]["head"] == "devrescue/fix-payment-validation"
    assert calls[2][1]["base"] == "main"
