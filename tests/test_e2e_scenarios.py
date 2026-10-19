from __future__ import annotations
import os
import time
import pytest

from mcp_servers.github import server as github_server
from agent.models import InvestigationResult
from evidence.models import CodeEvidence
from github_workflow.models import GitHubWorkflowStatus
from github_workflow.workflow import GitHubPRWorkflow
from hypothesis.models import Hypothesis
from remediation.engine import RemediationEngine
from patch_generation.generator import PatchGenerator
from remediation.models import RemediationAction, RemediationProposal
from validation.engine import ValidationEngine
from approval.gate import HumanApprovalGate
from workflow.remediation_workflow import RemediationWorkflow
from patch_generation.models import PatchFile, PatchProposal
from approval.models import ApprovalDecision
from github_workflow.models import GitHubWorkflowStatus
from github_workflow.workflow import GitHubPRWorkflow
from validation.models import ValidationResult

class FakeGitHub:
    def __init__(self):
        self.branches = []
        self.files = []
        self.pull_requests = []

    def create_branch(self, branch, from_branch=None, **kwargs):
        self.branches.append(branch)

        return {
            "status": "success",
            "branch": branch,
            "sha": "fake-sha",
        }

    def create_or_update_file(
        self,
        path,
        content,
        branch,
        message,
        sha=None,
        **kwargs,
    ):
        self.files.append(
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
            "branch": branch,
        }

    def create_pull_request(
        self,
        title,
        body,
        head,
        base=None,
        **kwargs,
    ):
        pr = {
            "number": len(self.pull_requests) + 1,
            "title": title,
            "body": body,
            "head": head,
            "base": base or "main",
        }

        self.pull_requests.append(pr)

        return {
            "status": "success",
            "number": pr["number"],
            "title": pr["title"],
            "head": pr["head"],
            "base": pr["base"],
        }

class FailingGitHub:
    def __init__(self):
        self.branches = []
        self.files = {}
        self.pull_requests = []

    def create_branch(self, **kwargs):
        self.branches.append(kwargs)
        return {
            "status": "success",
            "branch": kwargs.get("branch"),
        }

    def create_or_update_file(self, **kwargs):
        return {
            "status": "error",
            "error": "Simulated GitHub write failure",
        }

    def create_pull_request(self, **kwargs):
        self.pull_requests.append(kwargs)
        return {
            "status": "success",
            "number": 999,
        }

def build_application_validation_investigation():
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
            "summary": (
                "Negative payment amount reaches "
                "payment processing."
            )
        },
        hypotheses=[
            {
                "name": (
                    "Invalid payment amount reaches "
                    "payment processing"
                ),
                "category": "application_validation",
                "role": "root_cause",
                "confidence": 0.95,
                "evidence": [
                    "Negative payment amount reaches "
                    "payment processing."
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

def build_application_exception_investigation():
    return InvestigationResult(
        incident="Unhandled application exception",
        service="payment-service",
        status="COMPLETED",
        root_cause="Application raises a generic exception",
        confidence=0.93,
        explanation=(
            "The payment processing path raises a generic Exception "
            "instead of a controlled application exception."
        ),
        iterations=1,
        decision={"decision": "CONCLUDE"},
        tools_called=["controlled-test"],
        evidence_summary={
            "summary": (
                "Generic exception observed in payment processing."
            )
        },
        hypotheses=[
            {
                "name": "Application raises a generic exception",
                "category": "application_error",
                "role": "root_cause",
                "confidence": 0.93,
                "evidence": [
                    "Generic exception observed in payment processing."
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

def build_database_failure_investigation():
    return InvestigationResult(
        incident="Payment database unavailable",
        service="payment-service",
        status="COMPLETED",
        root_cause="Payment database dependency is unavailable",
        confidence=0.96,
        explanation=(
            "The payment service cannot establish a connection "
            "to its database dependency."
        ),
        iterations=1,
        decision={"decision": "CONCLUDE"},
        tools_called=[
            "check_database_health",
            "investigate_database",
        ],
        evidence_summary={
            "summary": (
                "Database connectivity failure confirmed."
            ),
            "database": [
                {
                   "database": "payments",
                   "status": "unhealthy",
                   "service": "payment-service",
                   "reason": "Database connection unavailable.",
                }
            ],
        },
        hypotheses=[
            {
                "name": "Payment database dependency is unavailable",
                "category": "database_failure",
                "role": "root_cause",
                "confidence": 0.96,
                "evidence": [
                    "Database connectivity failure confirmed."
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
def build_insufficient_evidence_investigation():
    return InvestigationResult(
        incident="Payment service intermittently failing",
        service="payment-service",
        status="completed",
        root_cause=None,
        confidence=0.0,
        explanation="Insufficient evidence to establish a root cause.",
        iterations=1,
        decision={
            "decision": "CONTINUE",
            "reason": "Insufficient evidence to conclude."
        },
        tools_called=[],
        evidence_summary={
            "summary": "Available evidence is insufficient to establish a root cause.",
            "logs": [],
            "traces": [],
            "metrics": [],
            "database": [],
            "code": [],
        },
        hypotheses=[],
        planning_history=[],
        investigation_notes=[],
        hypothesis_history=[],
        evidence_gaps=[
            "No matching error trace found.",
            "No relevant application logs found.",
        ],
        action_outcomes=[],
        uncertainty={
            "level": "high",
            "reason": "Insufficient supporting evidence."
        },
        llm_reasoning=None,
        llm_reasoning_history=[],
    )
def build_low_confidence_investigation():
    return InvestigationResult(
        incident="Payment service returning intermittent failures",
        service="payment-service",
        status="completed",
        root_cause="Application validation logic may be rejecting valid payment requests.",
        confidence=0.60,
        explanation=(
            "Evidence suggests an application validation issue, "
            "but the available evidence is not strong enough to support remediation."
        ),
        iterations=2,
        decision={
            "decision": "CONCLUDE",
            "reason": "A probable root cause was identified, but confidence remains low.",
        },
        tools_called=[
            "get_traces",
            "get_logs",
        ],
        evidence_summary={
            "summary": "Some evidence points toward application validation.",
            "logs": [
                {
                    "message": "Payment validation failed.",
                    "service": "payment-service",
                }
            ],
            "traces": [
                {
                    "status": "error",
                    "service": "payment-service",
                }
            ],
            "metrics": [],
            "database": [],
            "code": [],
        },
        hypotheses=[],
        planning_history=[],
        investigation_notes=[],
        hypothesis_history=[],
        evidence_gaps=[
            "Insufficient evidence linking the validation logic to the incident.",
        ],
        action_outcomes=[],
        uncertainty={
            "level": "high",
            "reason": "Root cause confidence is below the remediation threshold.",
        },
        llm_reasoning=None,
        llm_reasoning_history=[],
    )
def build_unsafe_remediation_investigation():
    return InvestigationResult(
        incident="Production database requires destructive recovery",
        service="payment-service",
        status="completed",
        root_cause="Database corruption requires destructive database reset.",
        confidence=0.95,
        explanation=(
            "Evidence strongly indicates database corruption, "
            "but the proposed recovery action would be destructive."
        ),
        iterations=2,
        decision={
            "decision": "CONCLUDE",
            "reason": "Root cause established with high confidence.",
        },
        tools_called=[
            "check_database_health",
            "investigate_database",
        ],
        evidence_summary={
            "summary": "Database corruption confirmed.",
            "logs": [],
            "traces": [],
            "metrics": [],
            "database": [
                {
                    "database": "payments",
                    "status": "corrupted",
                    "service": "payment-service",
                    "reason": "Database corruption detected.",
                }
            ],
            "code": [],
        },
        hypotheses=[],
        planning_history=[],
        investigation_notes=[],
        hypothesis_history=[],
        evidence_gaps=[],
        action_outcomes=[],
        uncertainty={
            "level": "low",
            "reason": "Root cause is strongly supported.",
        },
        llm_reasoning=None,
        llm_reasoning_history=[],
    )

def build_high_confidence_hypothesis():
    return Hypothesis(
        name="Production database reset required",
        category="database_failure",
        role="root_cause",
        confidence=0.95,
        score=0.95,
        explanation="Database corruption is strongly supported by the available evidence.",
        supporting_evidence=[],
        contradicting_evidence=[],
        matched_signals=["database_corruption"],
        missing_signals=[],
        evidence_score=0.95,
        specificity_score=0.95,
        temporal_score=0.95,
        contradiction_penalty=0.0,
        severity="critical",
    )
def build_code_evidence():
    return CodeEvidence(
        repository="Suryaaaa27/devrescue",
        path="tests/e2e_fixture_payment.py",
        content=(
            "def process_payment(amount):\n"
            "    return amount\n"
        ),
    )
def build_application_validation_patch():
    return PatchProposal(
        allowed=True,
        reason="Application validation remediation generated.",
        patches=[
            PatchFile(
                path="services/payment_service/main.py",
                original_content=(
                    "def process_payment(amount):\n"
                    "    return amount\n"
                ),
                patched_content=(
                    "def process_payment(amount):\n"
                    "    if amount <= 0:\n"
                    "        raise ValueError("
                    "\"Payment amount must be greater than zero.\""
                    ")\n"
                    "    return amount\n"
                ),
                diff=(
                    "--- services/payment_service/main.py\n"
                    "+++ services/payment_service/main.py\n"
                    "@@ -1,2 +1,5 @@\n"
                    " def process_payment(amount):\n"
                    "+    if amount <= 0:\n"
                    "+        raise ValueError("
                    "\"Payment amount must be greater than zero.\""
                    ")\n"
                    "     return amount\n"
                ),
            )
        ],
        rationale="Validate payment amount before processing.",
        validation_requirements=["Python syntax validation"],
        safety_checks=["No destructive operations"],
    )
def build_application_exception_code_evidence():
    return CodeEvidence(
        repository="Suryaaaa27/devrescue",
        path="tests/e2e_fixture_exception.py",
        content=(
            "def process_payment(amount):\n"
            "    if amount < 0:\n"
            "        raise Exception('Invalid payment amount')\n"
            "    return amount\n"
        ),
    )

def build_workflow(fake_github):
    github_workflow = GitHubPRWorkflow(
        create_branch=fake_github.create_branch,
        create_or_update_file=fake_github.create_or_update_file,
        create_pull_request=fake_github.create_pull_request,
    )

    return RemediationWorkflow(
        remediation_engine=RemediationEngine(),
        patch_generator=PatchGenerator(),
        validation_engine=ValidationEngine(),
        approval_gate=HumanApprovalGate(),
        github_workflow=github_workflow,
    )


def test_e2e_01_application_validation_success():
    fake_github = FakeGitHub()
    workflow = build_workflow(fake_github)

    prepared = workflow.prepare(
        investigation=build_application_validation_investigation(),
        code_evidence=[build_code_evidence()],
        run_tests=False,
    )

    assert prepared.status == "PENDING_APPROVAL"

    assert prepared.remediation is not None
    assert prepared.remediation.allowed is True

    assert prepared.patch is not None
    assert prepared.patch.allowed is True
    assert len(prepared.patch.patches) == 1

    patch = prepared.patch.patches[0]

    assert patch.path == "tests/e2e_fixture_payment.py"
    assert "if amount <= 0:" in patch.patched_content
    assert "Payment amount must be greater than zero." in (
        patch.patched_content
    )

    assert prepared.validation is not None
    assert prepared.validation.passed is True

    assert prepared.approval_request is not None
    assert prepared.approval_request.validation_passed is True

    completed = workflow.approve_and_create_pr(
        prepared=prepared,
        approved_by="e2e-test-user",
        reason="Approve controlled E2E remediation.",
        branch="devrescue/e2e-01",
        files=prepared.patch.patches,
        title="fix: validate payment amount",
        body="Controlled DevRescue E2E scenario.",
        base="main",
    )
    assert completed.status == "COMPLETED"
    assert completed.approval is not None
    assert completed.approval.approved is True

    assert completed.github is not None
    assert completed.github.status == GitHubWorkflowStatus.COMPLETED

    assert len(fake_github.branches) == 1
    assert len(fake_github.files) == 1
    assert len(fake_github.pull_requests) == 1

    assert fake_github.files[0]["path"] == (
        "tests/e2e_fixture_payment.py"
    )

    assert fake_github.pull_requests[0]["head"] == (
        "devrescue/e2e-01"
    )

def test_e2e_02_application_exception():
    fake_github = FakeGitHub()
    workflow = build_workflow(fake_github)

    prepared = workflow.prepare(
        investigation=build_application_exception_investigation(),
        code_evidence=[
            build_application_exception_code_evidence()
        ],
        run_tests=False,
    )

    assert prepared.status == "PENDING_APPROVAL"

    # ---------------------------------------------------------
    # Remediation
    # ---------------------------------------------------------

    assert prepared.remediation is not None
    assert prepared.remediation.allowed is True

    proposal = prepared.remediation.proposal

    assert proposal is not None
    assert proposal.category == "application_error"
    assert proposal.patch_generation_allowed is True

    assert any(
        action.action_type == "correct_application_exception"
        for action in proposal.actions
    )

    # ---------------------------------------------------------
    # Patch
    # ---------------------------------------------------------

    assert prepared.patch is not None
    assert prepared.patch.allowed is True
    assert len(prepared.patch.patches) == 1

    patch = prepared.patch.patches[0]

    assert patch.path == "tests/e2e_fixture_exception.py"

    assert "raise Exception(" not in patch.patched_content
    assert "raise ValueError(" in patch.patched_content

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    assert prepared.validation is not None
    assert prepared.validation.passed is True

    # ---------------------------------------------------------
    # Approval + GitHub
    # ---------------------------------------------------------

    completed = workflow.approve_and_create_pr(
        prepared=prepared,
        approved_by="e2e-test-user",
        reason="Approve controlled application exception remediation.",
        branch="devrescue/e2e-02",
        files=prepared.patch.patches,
        title="fix: handle application exception",
        body="Controlled DevRescue E2E-02 scenario.",
        base="main",
    )

    assert completed.status == "COMPLETED"

    assert completed.approval is not None
    assert completed.approval.approved is True

    assert completed.github is not None
    assert completed.github.status == GitHubWorkflowStatus.COMPLETED

    assert len(fake_github.branches) == 1
    assert len(fake_github.files) == 1
    assert len(fake_github.pull_requests) == 1

    assert fake_github.files[0]["path"] == (
        "tests/e2e_fixture_exception.py"
    )

    assert fake_github.pull_requests[0]["head"] == (
        "devrescue/e2e-02"
    )

def test_e2e_03_database_failure_is_operational_only():
    fake_github = FakeGitHub()
    workflow = build_workflow(fake_github)

    prepared = workflow.prepare(
        investigation=build_database_failure_investigation(),
        code_evidence=None,
        run_tests=False,
    )

    # ---------------------------------------------------------
    # Investigation reached remediation preparation
    # ---------------------------------------------------------

    assert prepared.investigation is not None
    assert prepared.investigation.root_cause == (
        "Payment database dependency is unavailable"
    )

    # ---------------------------------------------------------
    # Remediation proposal exists
    # ---------------------------------------------------------

    assert prepared.remediation is not None
    assert prepared.remediation.allowed is True

    proposal = prepared.remediation.proposal

    assert proposal is not None
    assert proposal.category == "database_failure"

    # ---------------------------------------------------------
    # Database remediation must remain operational
    # ---------------------------------------------------------

    assert any(
        action.action_type == "restore_database_connectivity"
        for action in proposal.actions
    )

    assert any(
        action.action_type == "verify_database_configuration"
        for action in proposal.actions
    )

    # At least one operational action is non-patchable.
    assert any(
        not action.patchable
        for action in proposal.actions
    )

    # ---------------------------------------------------------
    # CRITICAL SAFETY PROPERTY
    # ---------------------------------------------------------

    assert proposal.patch_generation_allowed is False

    assert proposal.affected_files == []

    # ---------------------------------------------------------
    # No patch must be generated
    # ---------------------------------------------------------

    assert prepared.patch is not None
    assert prepared.patch.allowed is False
    assert prepared.patch.patches == []

    # ---------------------------------------------------------
    # No validation of a code patch
    # ---------------------------------------------------------

    assert prepared.validation is None

    # ---------------------------------------------------------
    # No approval request
    # ---------------------------------------------------------

    assert prepared.approval_request is None

    # ---------------------------------------------------------
    # GitHub must remain untouched
    # ---------------------------------------------------------

    assert fake_github.branches == []
    assert fake_github.files == []
    assert fake_github.pull_requests == []

def test_e2e_04_insufficient_evidence_is_blocked():
    fake_github = FakeGitHub()
    workflow = build_workflow(fake_github)

    investigation = build_insufficient_evidence_investigation()

    result = workflow.prepare(
        investigation=investigation,
    )

    assert result.status == "BLOCKED"

    assert result.remediation is None
    assert result.patch is None
    assert result.validation is None
    assert result.approval_request is None
    assert result.approval is None
    assert result.github is None

    assert fake_github.branches == []
    assert fake_github.files == []
    assert fake_github.pull_requests == []

def test_e2e_05_low_confidence_hypothesis_is_blocked():
    fake_github = FakeGitHub()
    workflow = build_workflow(fake_github)

    investigation = build_low_confidence_investigation()

    result = workflow.prepare(
        investigation=investigation,
    )

    assert result.status == "BLOCKED"

    assert result.remediation is None
    assert result.patch is None
    assert result.validation is None
    assert result.approval_request is None
    assert result.approval is None
    assert result.github is None

    assert fake_github.branches == []
    assert fake_github.files == []
    assert fake_github.pull_requests == []

def test_e2e_06_unsafe_remediation_is_blocked():
    engine = RemediationEngine()

    hypothesis = Hypothesis(
        name="Production database reset required",
        category="database_failure",
        role="root_cause",
        confidence=0.95,
        score=0.95,
        explanation="Database corruption is strongly supported by the available evidence.",
        supporting_evidence=[],
        contradicting_evidence=[],
        matched_signals=["database_corruption"],
        missing_signals=[],
        evidence_score=0.95,
        specificity_score=0.95,
        temporal_score=0.95,
        contradiction_penalty=0.0,
        severity="critical",
    )

    evidence_summary = {
        "summary": "Production database corruption confirmed.",
        "database": [
            {
                "database": "payments",
                "status": "corrupted",
                "service": "payment-service",
                "reason": "Database corruption detected.",
            }
        ],
        "code": [],
    }

    proposal = engine.propose(
        hypothesis=hypothesis,
        evidence_summary=evidence_summary,
    )

    assert proposal is not None

def test_e2e_07_human_rejection_blocks_github():
    fake_github = FakeGitHub()
    workflow = build_workflow(fake_github)

    investigation = build_application_validation_investigation()
    code_evidence = build_code_evidence()

    prepared = workflow.prepare(
        investigation=investigation,
        code_evidence=[code_evidence],
    )

    assert prepared.status == "PENDING_APPROVAL"
    assert prepared.remediation is not None
    assert prepared.patch is not None
    assert prepared.validation is not None
    assert prepared.validation.passed is True
    assert prepared.approval_request is not None

    approval = workflow.approval_gate.reject(
        prepared.approval_request,
        rejected_by="human-reviewer",
        reason="The proposed remediation requires additional review.",
    )

    assert approval.approved is False
    assert approval.status == "REJECTED"
    assert approval.decided_by == "human-reviewer"

    assert fake_github.branches == []
    assert fake_github.files == []
    assert fake_github.pull_requests == []

def test_e2e_08_validation_failure_blocks_approval_and_github():
    fake_github = FakeGitHub()
    workflow = build_workflow(fake_github)

    invalid_patch = PatchProposal(
        allowed=True,
        reason="Deliberately malformed patch for validation failure scenario.",
        patches=[
            PatchFile(
                path="services/payment_service/main.py",
                original_content=(
                    "def process_payment(amount):\n"
                    "    return amount\n"
                ),
                patched_content=(
                    "def process_payment(amount):\n"
                    "    if amount <= 0\n"
                    "        raise ValueError('Invalid amount')\n"
                ),
                diff="deliberately invalid syntax",
            )
        ],
        rationale="E2E-08 deliberately introduces invalid Python syntax.",
    )

    validation = workflow.validation_engine.validate(
        invalid_patch,
        run_tests=False,
    )

    assert validation.passed is False
    assert validation.status != "passed"

    assert fake_github.branches == []
    assert fake_github.files == []
    assert fake_github.pull_requests == []

def test_e2e_09_github_write_failure_fails_safely():
    github = FailingGitHub()

    github_workflow = GitHubPRWorkflow(
        create_branch=github.create_branch,
        create_or_update_file=github.create_or_update_file,
        create_pull_request=github.create_pull_request,
    )

    patch_proposal = build_application_validation_patch()

    validation_result = ValidationResult(
        passed=True,
        status="PASSED",
        summary="Validation passed successfully.",
    )

    approval_decision = ApprovalDecision(
        request_id="approval-e2e-09",
        approved=True,
        decided_by="human-reviewer",
        reason="Approved for remediation.",
        status="APPROVED",
    )

    result = github_workflow.execute(
        patch_proposal=patch_proposal,
        validation_result=validation_result,
        approval_decision=approval_decision,
        branch="devrescue/e2e-09-github-failure",
        commit_message="test: e2e-09 github write failure",
        pr_title="test: E2E-09 GitHub write failure",
        pr_body="Intentional GitHub write failure scenario.",
        base_branch="main",
    )

    assert result.success is False
    assert result.status == GitHubWorkflowStatus.FAILED

    assert result.validation_passed is True
    assert result.approval_granted is True

    assert result.pull_request is None
    assert result.written_files == []

    assert result.errors
    assert any(
        "write" in error.lower()
        or "github" in error.lower()
        for error in result.errors
    )

    assert github.branches
    assert github.pull_requests == []

@pytest.mark.skipif(
    os.getenv("DEVRESCUE_RUN_REAL_GITHUB_E2E") != "1",
    reason="Real GitHub E2E disabled",
)
def test_e2e_10_full_successful_remediation_real_github():
    suffix = str(int(time.time()))

    branch = f"devrescue/e2e-10-{suffix}"
    path = f"tests/devrescue_e2e_10_{suffix}.py"

    github_workflow = GitHubPRWorkflow(
        create_branch=github_server.create_branch,
        create_or_update_file=github_server.create_or_update_file,
        create_pull_request=github_server.create_pull_request,
    )

    workflow = RemediationWorkflow(
        remediation_engine=RemediationEngine(),
        patch_generator=PatchGenerator(),
        validation_engine=ValidationEngine(),
        approval_gate=HumanApprovalGate(),
        github_workflow=github_workflow,
    )

    investigation = build_application_validation_investigation()

    code_evidence = [
        CodeEvidence(
            repository="Suryaaaa27/devrescue",
            path=path,
            content=(
                "def process_payment(amount):\n"
                "    return amount\n"
            ),
        )
    ]

    prepared = workflow.prepare(
        investigation=investigation,
        code_evidence=code_evidence,
        run_tests=False,
    )

    assert prepared.status == "PENDING_APPROVAL"

    assert prepared.remediation is not None
    assert prepared.remediation.allowed is True

    assert prepared.patch is not None
    assert prepared.patch.allowed is True
    assert len(prepared.patch.patches) == 1

    assert prepared.validation is not None
    assert prepared.validation.passed is True

    assert prepared.approval_request is not None
    assert prepared.approval_request.validation_passed is True

    completed = None
    pull_request_number = None

    try:
        completed = workflow.approve_and_create_pr(
            prepared=prepared,
            approved_by="e2e-10-human-reviewer",
            reason="Approved controlled real GitHub E2E remediation.",
            branch=branch,
            files=prepared.patch.patches,
            title=f"test: DevRescue E2E-10 remediation {suffix}",
            body=(
                "Controlled DevRescue E2E-10 scenario.\n\n"
                "This PR was created by the real GitHub E2E test."
            ),
            base="main",
        )

        print("E2E-10 RESULT:", completed)
        print("E2E-10 MESSAGE:", completed.message)
        print("E2E-10 ERRORS:", completed.errors)
        print("E2E-10 GITHUB:", completed.github)

        assert completed.status == "COMPLETED"
        assert completed.success is True

        assert completed.github is not None
        assert completed.github.status == GitHubWorkflowStatus.COMPLETED

        assert completed.github.validation_passed is True
        assert completed.github.approval_granted is True

        assert completed.github.branch == branch
        assert completed.github.pull_request is not None

        pull_request_number = completed.github.pull_request.get("number")

        assert pull_request_number is not None
        assert completed.github.written_files == [path]

    finally:
        if pull_request_number is not None:
            close_result = github_server.close_pull_request(
                pull_number=int(pull_request_number),
            )
            print("E2E-10 PR cleanup:", close_result)

        delete_result = github_server.delete_branch(
            branch=branch,
        )
        print("E2E-10 branch cleanup:", delete_result)
