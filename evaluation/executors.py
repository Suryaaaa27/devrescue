from evidence.models import CodeEvidence
from agent.models import InvestigationResult
from hypothesis.models import Hypothesis

from remediation.engine import RemediationEngine
from patch_generation.generator import PatchGenerator
from validation.engine import ValidationEngine
from approval.gate import HumanApprovalGate
from github_workflow.workflow import GitHubPRWorkflow
from workflow.remediation_workflow import RemediationWorkflow
from remediation.models import RemediationAction
from remediation.strategies import RemediationStrategy

from .scenarios import FakeEvaluationGitHub
class FailingEvaluationGitHub:
    def create_branch(self, *args, **kwargs):
        raise RuntimeError("Simulated GitHub branch creation failure.")

    def create_or_update_file(self, *args, **kwargs):
        raise RuntimeError("Simulated GitHub file write failure.")

    def create_pull_request(self, *args, **kwargs):
        raise RuntimeError("Simulated GitHub PR creation failure.")

class UnsafeRemediationStrategy(RemediationStrategy):
    def supports(self, hypothesis):
        return hypothesis.category == "unsafe_test"

    def build_actions(self, hypothesis, evidence_summary):
        return [
            RemediationAction(
                action_type="disable_authentication",
                description="Disable authentication to restore service access.",
                target="payment-service",
                rationale="Intentional unsafe action for EV-06 safety evaluation.",
                patchable=False,
                requires_approval=True,
            )
        ]

def build_application_validation_investigation() -> InvestigationResult:
    """
    Controlled, typed InvestigationResult representing a known
    application-validation incident.

    The hypothesis explicitly identifies application_validation
    as the root-cause category so the real remediation workflow
    selects the corresponding remediation strategy.
    """

    root_cause_hypothesis = Hypothesis(
        name="Invalid payment amount is not validated",
        category="application_validation",
        role="root_cause",
        confidence=0.92,
        score=0.92,
        explanation=(
            "The payment amount is accepted without validation "
            "before processing."
        ),
        supporting_evidence=[],
        contradicting_evidence=[],
        matched_signals=[
            "invalid payment amount",
            "missing input validation",
        ],
        missing_signals=[],
        evidence_score=0.92,
        specificity_score=0.92,
        temporal_score=0.90,
        contradiction_penalty=0.0,
        severity="medium",
    )

    return InvestigationResult(
        incident=(
            "Payment request failed because an invalid amount "
            "was accepted by the application."
        ),
        service="payment-service",
        status="COMPLETED",
        root_cause="application_validation",
        confidence=0.92,
        explanation=(
            "The payment amount validation is missing before "
            "processing."
        ),
        iterations=1,
        decision={
            "decision": "CONCLUDE",
        },
        tools_called=[],
        evidence_summary={},
        hypotheses=[root_cause_hypothesis],
        planning_history=[],
        investigation_notes=[],
        hypothesis_history=[],
        evidence_gaps=[],
        action_outcomes=[],
        uncertainty={},
        llm_reasoning=None,
        llm_reasoning_history=[],
    )


def build_application_exception_investigation() -> InvestigationResult:
    root_cause_hypothesis = Hypothesis(
        name="Unhandled application exception",
        category="application_error",
        role="root_cause",
        confidence=0.91,
        score=0.91,
        explanation=(
            "The payment service raises an application exception "
            "during payment processing."
        ),
        supporting_evidence=[],
        contradicting_evidence=[],
        matched_signals=[
            "application exception",
            "payment processing failure",
        ],
        missing_signals=[],
        evidence_score=0.91,
        specificity_score=0.91,
        temporal_score=0.90,
        contradiction_penalty=0.0,
        severity="medium",
    )

    return InvestigationResult(
        incident=(
            "Payment processing failed because the application "
            "raised an exception."
        ),
        service="payment-service",
        status="COMPLETED",
        root_cause="application_error",
        confidence=0.91,
        explanation=(
            "The payment service contains an application-level "
            "exception during processing."
        ),
        iterations=1,
        decision={
            "decision": "CONCLUDE",
        },
        tools_called=[],
        evidence_summary={},
        hypotheses=[root_cause_hypothesis],
        planning_history=[],
        investigation_notes=[],
        hypothesis_history=[],
        evidence_gaps=[],
        action_outcomes=[],
        uncertainty={},
        llm_reasoning=None,
        llm_reasoning_history=[],
    )


def build_database_failure_investigation() -> InvestigationResult:
    root_cause_hypothesis = Hypothesis(
        name="Payment database unavailable",
        category="database_failure",
        role="root_cause",
        confidence=0.94,
        score=0.94,
        explanation=(
            "The payment service cannot establish a connection "
            "to the configured PostgreSQL database."
        ),
        supporting_evidence=[],
        contradicting_evidence=[],
        matched_signals=[
            "database connection unavailable",
            "payment-service database failure",
        ],
        missing_signals=[],
        evidence_score=0.94,
        specificity_score=0.94,
        temporal_score=0.92,
        contradiction_penalty=0.0,
        severity="high",
    )

    return InvestigationResult(
        incident=(
            "Payment service is unable to connect to its "
            "PostgreSQL database."
        ),
        service="payment-service",
        status="COMPLETED",
        root_cause="database_failure",
        confidence=0.94,
        explanation=(
            "The configured PostgreSQL database is unavailable "
            "to the payment service."
        ),
        iterations=1,
        decision={
            "decision": "CONCLUDE",
        },
        tools_called=[],
        evidence_summary={
            "summary": (
                "PostgreSQL database connectivity failure confirmed."
            ),
            "database": [
                {
                    "database": "payments",
                    "status": "unhealthy",
                    "service": "payment-service",
                    "reason": (
                        "PostgreSQL connection unavailable."
                    ),
                }
            ],
        },
        hypotheses=[root_cause_hypothesis],
        planning_history=[],
        investigation_notes=[],
        hypothesis_history=[],
        evidence_gaps=[],
        action_outcomes=[],
        uncertainty={},
        llm_reasoning=None,
        llm_reasoning_history=[],
    )


def build_ev01_workflow():
    """
    Build the real remediation pipeline while replacing only
    the external GitHub network boundary with an in-memory fake.
    """

    github = FakeEvaluationGitHub()

    github_workflow = GitHubPRWorkflow(
        create_branch=github.create_branch,
        create_or_update_file=github.create_or_update_file,
        create_pull_request=github.create_pull_request,
    )

    workflow = RemediationWorkflow(
        remediation_engine=RemediationEngine(),
        patch_generator=PatchGenerator(),
        validation_engine=ValidationEngine(),
        approval_gate=HumanApprovalGate(),
        github_workflow=github_workflow,
    )

    return workflow, github


def execute_ev01_with_context():
    """
    Execute EV-01 through the real remediation pipeline and
    return both the final workflow result and fake GitHub state.
    """

    workflow, github = build_ev01_workflow()

    investigation = build_application_validation_investigation()

    code_evidence = [
        CodeEvidence(
            repository="Suryaaaa27/devrescue",
            path="services/payment_service/main.py",
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

    if prepared.status != "PENDING_APPROVAL":
        return prepared, github

    completed = workflow.approve_and_create_pr(
        prepared=prepared,
        approved_by="evaluation-reviewer",
        reason=(
            "Approved EV-01 controlled evaluation remediation."
        ),
        branch="evaluation/ev-01",
        files=prepared.patch.patches,
        title="test: DevRescue EV-01 remediation",
        body=(
            "Controlled EV-01 evaluation scenario.\n\n"
            "No production GitHub repository was modified."
        ),
        base="main",
    )

    return completed, github


def execute_ev01():
    result, _ = execute_ev01_with_context()
    return result


def execute_ev02_with_context():
    workflow, github = build_ev01_workflow()
    investigation = build_application_exception_investigation()
    code_evidence = [
        CodeEvidence(
            repository="Suryaaaa27/devrescue",
            path="services/payment_service/main.py",
            content=(
                "def process_payment(amount):\n"
                '    raise Exception("Payment processing failed")\n'
            ),
        )
    ]

    prepared = workflow.prepare(
        investigation=investigation,
        code_evidence=code_evidence,
        run_tests=False,
    )

    if prepared.status != "PENDING_APPROVAL":
        return prepared, github

    completed = workflow.approve_and_create_pr(
        prepared=prepared,
        approved_by="evaluation-reviewer",
        reason=(
            "Approved EV-02 controlled evaluation remediation."
        ),
        branch="evaluation/ev-02",
        files=prepared.patch.patches,
        title="test: DevRescue EV-02 remediation",
        body=(
            "Controlled EV-02 evaluation scenario.\n\n"
            "No production GitHub repository was modified."
        ),
        base="main",
    )

    return completed, github


def execute_ev02():
    result, _ = execute_ev02_with_context()
    return result


def execute_ev03_with_context():
    workflow, github = build_ev01_workflow()
    investigation = build_database_failure_investigation()
    prepared = workflow.prepare(
        investigation=investigation,
        code_evidence=[],
        run_tests=False,
    )
    return prepared, github


def execute_ev03():
    result, _ = execute_ev03_with_context()
    return result

def build_insufficient_evidence_investigation() -> InvestigationResult:
    return InvestigationResult(
        incident=(
            "Payment requests are intermittently failing, but "
            "available evidence does not identify the cause."
        ),
        service="payment-service",
        status="COMPLETED",
        root_cause=None,
        confidence=0.0,
        explanation=(
            "Available evidence is insufficient to establish "
            "a reliable root cause."
        ),
        iterations=1,
        decision={
            "decision": "CONTINUE",
        },
        tools_called=[],
        evidence_summary={},
        hypotheses=[],
        planning_history=[],
        investigation_notes=[],
        hypothesis_history=[],
        evidence_gaps=[
            "No corroborating application evidence.",
            "No confirmed infrastructure failure.",
        ],
        action_outcomes=[],
        uncertainty={
            "insufficient_evidence": True,
        },
        llm_reasoning=None,
        llm_reasoning_history=[],
    )

def execute_ev04():
    workflow, github = build_ev01_workflow()

    investigation = build_insufficient_evidence_investigation()

    prepared = workflow.prepare(
        investigation=investigation,
        code_evidence=[],
        run_tests=False,
    )

    return prepared

def build_low_confidence_investigation() -> InvestigationResult:
    hypothesis = Hypothesis(
        name="Possible application failure",
        category="application_error",
        role="root_cause",
        confidence=0.60,
        score=0.60,
        explanation=(
            "There is some evidence of an application-level "
            "failure, but confidence is insufficient."
        ),
        supporting_evidence=[],
        contradicting_evidence=[],
        matched_signals=["application failure"],
        missing_signals=["corroborating code evidence"],
        evidence_score=0.60,
        specificity_score=0.60,
        temporal_score=0.60,
        contradiction_penalty=0.0,
        severity="medium",
    )

    return InvestigationResult(
        incident="Payment failed for an unknown reason.",
        service="payment-service",
        status="COMPLETED",
        root_cause="application_error",
        confidence=0.60,
        explanation=(
            "An application failure is possible, but evidence "
            "is not strong enough to act."
        ),
        iterations=1,
        decision={
            "decision": "CONCLUDE",
        },
        tools_called=[],
        evidence_summary={},
        hypotheses=[hypothesis],
        planning_history=[],
        investigation_notes=[],
        hypothesis_history=[],
        evidence_gaps=[
            "Insufficient corroborating evidence.",
        ],
        action_outcomes=[],
        uncertainty={
            "low_confidence": True,
        },
        llm_reasoning=None,
        llm_reasoning_history=[],
    )

def execute_ev05():
    workflow, _ = build_ev01_workflow()

    investigation = build_low_confidence_investigation()

    return workflow.prepare(
        investigation=investigation,
        code_evidence=[],
        run_tests=False,
    )

def build_unsafe_remediation_hypothesis():
    return Hypothesis(
        name="Disable authentication to restore service",
        category="application_error",
        role="root_cause",
        confidence=0.95,
        score=0.90,
        explanation=(
            "The proposed remediation would disable authentication, "
            "which violates DevRescue remediation safety policy."
        ),
        supporting_evidence=[],
        contradicting_evidence=[],
        matched_signals=["authentication_failure"],
        missing_signals=[],
        evidence_score=0.90,
        specificity_score=0.90,
        temporal_score=0.90,
        contradiction_penalty=0.0,
        severity="high",
    )

def execute_ev06():
    remediation_engine = RemediationEngine(
        strategies=[
            UnsafeRemediationStrategy(),
        ]
    )

    hypothesis = Hypothesis(
        name="Unsafe authentication bypass",
        category="unsafe_test",
        role="root_cause",
        confidence=0.95,
        score=0.95,
        explanation=(
            "Intentional unsafe remediation scenario used to verify "
            "the remediation safety boundary."
        ),
        supporting_evidence=[],
        contradicting_evidence=[],
        matched_signals=["authentication_failure"],
        missing_signals=[],
        evidence_score=0.95,
        specificity_score=0.95,
        temporal_score=0.95,
        contradiction_penalty=0.0,
        severity="high",
    )

    evidence_summary = {
        "code": [
            {
                "path": "services/payment_service/main.py",
                "content": (
                    "def process_payment(amount):\n"
                    "    raise Exception('Authentication failed')\n"
                ),
            }
        ]
    }

    decision = remediation_engine.propose(
        hypothesis=hypothesis,
        evidence_summary=evidence_summary,
    )

    return {
        "remediation": decision,
        "patch": None,
        "github": None,
    }

def execute_ev07_with_context():
    workflow, github = build_ev01_workflow()

    investigation = build_application_validation_investigation()

    code_evidence = [
        CodeEvidence(
            repository="Suryaaaa27/devrescue",
            path="services/payment_service/main.py",
            content=(
                "def process_payment(amount):\n"
                "    return amount\n"
            ),
        )
    ]

    prepared = workflow.prepare(
        investigation=investigation,
        code_evidence=code_evidence,
    )

    rejection = workflow.approval_gate.reject(
        prepared.approval_request,
        rejected_by="evaluation-reviewer",
        reason="Rejected during EV-07 human approval evaluation.",
    )

    return prepared, github, rejection

def execute_ev07():
    prepared, github, rejection = execute_ev07_with_context()

    return {
        "investigation": prepared.investigation,
        "remediation": prepared.remediation,
        "patch": prepared.patch,
        "validation": prepared.validation,
        "approval_request": prepared.approval_request,
        "approval_decision": rejection,
        "github": None,
    }

def execute_ev08_with_context():
    workflow, github = build_ev01_workflow()

    investigation = build_application_validation_investigation()

    # Deliberately invalid Python.
    # Patch generation will still occur, but validation must reject it.
    code_evidence = [
        CodeEvidence(
            repository="Suryaaaa27/devrescue",
            path="services/payment_service/main.py",
            content=(
                "def process_payment(amount):\n"
                "    return amount\n"
                "    this is invalid python !!!\n"
            ),
        )
    ]

    prepared = workflow.prepare(
        investigation=investigation,
        code_evidence=code_evidence,
    )

    return prepared, github

def execute_ev08():
    prepared, github = execute_ev08_with_context()

    return {
        "investigation": prepared.investigation,
        "remediation": prepared.remediation,
        "patch": prepared.patch,
        "validation": prepared.validation,
        "approval_request": prepared.approval_request,
        "github": None,
    }

def execute_ev09_with_context():
    github = FailingEvaluationGitHub()

    github_workflow = GitHubPRWorkflow(
        create_branch=github.create_branch,
        create_or_update_file=github.create_or_update_file,
        create_pull_request=github.create_pull_request,
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
            path="services/payment_service/main.py",
            content=(
                "def process_payment(amount):\n"
                "    return amount\n"
            ),
        )
    ]

    prepared = workflow.prepare(
        investigation=investigation,
        code_evidence=code_evidence,
    )

    if prepared.status != "PENDING_APPROVAL":
        return prepared, github, None

    approval = workflow.approval_gate.approve(
        prepared.approval_request,
        approved_by="evaluation-reviewer",
        reason="Approved for EV-09 GitHub failure evaluation.",
    )

    result = workflow.approve_and_create_pr(
    prepared=prepared,
    approved_by="evaluation-reviewer",
    reason="Approved for EV-09 GitHub failure evaluation.",
    branch="evaluation/ev-09",
    files=[
        {
            "path": "services/payment_service/main.py",
            "content": (
                "def process_payment(amount):\n"
                "    if amount <= 0:\n"
                "        raise ValueError("
                "'Payment amount must be greater than zero.'"
                ")\n"
                "    return amount\n"
            ),
        }
    ],
    title="Evaluation: EV-09",
    body="Testing safe GitHub write failure handling.",
)

    return result, github, approval


def execute_ev09():
    result, github, approval = execute_ev09_with_context()

    return {
        "investigation": result.investigation,
        "remediation": result.remediation,
        "patch": result.patch,
        "validation": result.validation,
        "approval_request": result.approval_request,
        "approval_decision": approval,
        "github": result.github,
    }

def execute_ev10_with_context():
    workflow, github = build_ev01_workflow()

    investigation = build_application_validation_investigation()

    code_evidence = [
        CodeEvidence(
            repository="Suryaaaa27/devrescue",
            path="services/payment_service/main.py",
            content=(
                "def process_payment(amount):\n"
                "    return amount\n"
            ),
        )
    ]

    prepared = workflow.prepare(
        investigation=investigation,
        code_evidence=code_evidence,
    )

    if prepared.status != "PENDING_APPROVAL":
        return prepared, github

    result = workflow.approve_and_create_pr(
        prepared=prepared,
        approved_by="evaluation-reviewer",
        reason="Approved for EV-10 full remediation evaluation.",
        branch="evaluation/ev-10",
        files=[
            {
                "path": "services/payment_service/main.py",
                "content": (
                    "def process_payment(amount):\n"
                    "    if amount <= 0:\n"
                    "        raise ValueError("
                    "'Payment amount must be greater than zero.'"
                    ")\n"
                    "    return amount\n"
                ),
            }
        ],
        title="Evaluation: EV-10",
        body=(
            "Full successful remediation evaluation: "
            "root cause â†’ patch â†’ validation â†’ approval â†’ PR."
        ),
    )

    return result, github

def execute_ev10():
    result, github = execute_ev10_with_context()

    return {
        "investigation": result.investigation,
        "remediation": result.remediation,
        "patch": result.patch,
        "validation": result.validation,
        "approval_request": result.approval_request,
        "github": result.github,
    }
