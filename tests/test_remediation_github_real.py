from __future__ import annotations

import os
import time

import pytest

from agent.models import InvestigationResult
from evidence.models import CodeEvidence
from github_workflow.models import GitHubWorkflowStatus
from github_workflow.workflow import GitHubPRWorkflow
from mcp_servers.github.registry import build_github_write_tools
from remediation.engine import RemediationEngine
from patch_generation.generator import PatchGenerator
from validation.engine import ValidationEngine
from approval.gate import HumanApprovalGate
from workflow.remediation_workflow import RemediationWorkflow
from evidence.models import CodeEvidence

RUN_REAL = os.getenv("DEVRESCUE_RUN_REAL_GITHUB_E2E") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_REAL,
    reason="Set DEVRESCUE_RUN_REAL_GITHUB_E2E=1 to run the real GitHub E2E test.",
)


def build_investigation() -> InvestigationResult:
    return InvestigationResult(
        incident="Payment validation failure",
        service="payment-service",
        status="COMPLETED",
        root_cause="Invalid payment amount reaches payment processing",
        confidence=0.95,
        explanation=(
            "Negative payment amounts are not rejected before "
            "processing."
        ),
        iterations=1,
        decision={"decision": "CONCLUDE"},
        tools_called=["controlled-test"],
        evidence_summary={
            "summary": "Negative payment amount reaches payment processing."
        },
        hypotheses=[
            {
                "name": "Invalid payment amount reaches payment processing",
                "category": "application_validation",
                "role": "root_cause",
                "confidence": 0.95,
                "evidence": [
                    "Negative payment amount reaches payment processing."
                ],
            }
        ],
        planning_history=[],
        investigation_notes=[],
        hypothesis_history=[],
        evidence_gaps=[],
        action_outcomes=[],
        uncertainty={},
        llm_reasoning=[],
        llm_reasoning_history=[],
    )


def build_code_evidence(path: str) -> CodeEvidence:
    return CodeEvidence(
        repository="Suryaaaa27/devrescue",
        path=path,
        content=(
            "def process_payment(amount):\n"
            "    return amount\n"
        ),
    )


def test_real_github_remediation_e2e():
    tools = build_github_write_tools()

    github_workflow = GitHubPRWorkflow(
        create_branch=tools["create_branch"],
        create_or_update_file=tools["create_or_update_file"],
        create_pull_request=tools["create_pull_request"],
    )

    remediation_workflow = RemediationWorkflow(
        remediation_engine=RemediationEngine(),
        patch_generator=PatchGenerator(),
        validation_engine=ValidationEngine(),
        approval_gate=HumanApprovalGate(),
        github_workflow=github_workflow,
    )

    investigation = build_investigation()

    timestamp = int(time.time())
    branch = f"devrescue/real-remediation-{timestamp}"
    fixture_path = f"tests/devrescue_real_e2e_{timestamp}.py"

    code_evidence = [
        build_code_evidence(fixture_path)
    ]

    prepared = remediation_workflow.prepare(
        investigation=investigation,
        code_evidence=code_evidence,
        run_tests=False,
    )

    assert prepared.status == "PENDING_APPROVAL"
    assert prepared.patch is not None
    assert prepared.validation is not None
    assert prepared.validation.passed is True
    assert prepared.approval_request is not None

    completed = None

    try:
        completed = remediation_workflow.approve_and_create_pr(
            prepared=prepared,
            approved_by="devrescue-e2e",
            reason="Approved controlled real GitHub E2E test.",
            branch=branch,
            files=prepared.patch.patches,
            title="test: DevRescue real remediation E2E",
            body=(
                "Automated DevRescue real GitHub E2E test.\n\n"
                "This PR validates the complete remediation workflow "
                "against the real GitHub repository.\n\n"
                "The PR is closed automatically after verification."
            ),
            base="main",
        )

        assert completed.status == "COMPLETED"
        assert completed.github is not None

        github_result = completed.github

        assert github_result.status == GitHubWorkflowStatus.COMPLETED
        assert github_result.branch == branch
        assert github_result.pull_request is not None

        pr_number = github_result.pull_request.get("number")

        assert pr_number is not None

        print()
        print("=" * 60)
        print("REAL GITHUB REMEDIATION E2E PASSED")
        print("=" * 60)
        print(f"Branch: {branch}")
        print(f"PR Number: #{pr_number}")
        print(f"Written files: {github_result.written_files}")
        print("=" * 60)

    finally:
        if completed is not None and completed.github is not None:
            github_result = completed.github

            pr = github_result.pull_request

            if pr and pr.get("number"):
                tools["close_pull_request"](pr["number"])

            tools["delete_branch"](branch)

def test_extracts_affected_files_from_code_evidence_objects():
    evidence = {
        "code": [
            CodeEvidence(
                repository="Suryaaaa27/devrescue",
                path="tests/example.py",
                content="def example():\n    pass\n",
            )
        ]
    }

    files = RemediationEngine._extract_affected_files(evidence)

    assert files == ["tests/example.py"]
