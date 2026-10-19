from agent.models import InvestigationResult
from workflow.remediation_workflow import RemediationWorkflow
from workflow.runner import DevRescueRemediationRunner


class FakeInvestigator:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def investigate(self, *, incident, service):
        self.calls.append(
            {
                "incident": incident,
                "service": service,
            }
        )
        return self.result


def build_investigation():
    return InvestigationResult(
        incident="Payment request failed.",
        service="payment-service",
        status="completed",
        root_cause="Invalid payment amount",
        confidence=0.92,
        explanation="Invalid payment amount.",
        iterations=3,
        decision={
            "decision": "CONCLUDE",
        },
        hypotheses=[
            {
                "name": "Invalid payment amount",
                "category": "application_validation",
                "role": "root_cause",
                "confidence": 0.92,
                "score": 0.92,
            }
        ],
        evidence_summary={
            "logs": [],
            "traces": [],
            "metrics": [],
            "code": [],
        },
    )


def build_code_evidence():
    return [
        {
            "path": "services/payment_service/main.py",
            "content": (
                "def process_payment(amount):\n"
                "    return amount\n"
            ),
        }
    ]


def test_runner_investigates_and_prepares():
    investigation = build_investigation()

    investigator = FakeInvestigator(investigation)

    runner = DevRescueRemediationRunner(
        investigator=investigator,
        remediation_workflow=RemediationWorkflow(),
    )

    result = runner.investigate_and_prepare(
        incident="Payment request failed.",
        service="payment-service",
        code_evidence=build_code_evidence(),
    )

    assert result.status == "PENDING_APPROVAL"

    assert result.investigation is investigation

    assert result.remediation is not None

    assert result.remediation.status == "PENDING_APPROVAL"

    assert investigator.calls == [
        {
            "incident": "Payment request failed.",
            "service": "payment-service",
        }
    ]


def test_runner_blocks_empty_incident():
    investigator = FakeInvestigator(build_investigation())

    runner = DevRescueRemediationRunner(
        investigator=investigator,
        remediation_workflow=RemediationWorkflow(),
    )

    result = runner.investigate_and_prepare(
        incident="",
        service="payment-service",
    )

    assert result.status == "BLOCKED"

    assert result.investigation is None

    assert investigator.calls == []


def test_runner_blocks_empty_service():
    investigator = FakeInvestigator(build_investigation())

    runner = DevRescueRemediationRunner(
        investigator=investigator,
        remediation_workflow=RemediationWorkflow(),
    )

    result = runner.investigate_and_prepare(
        incident="Payment failed.",
        service="",
    )

    assert result.status == "BLOCKED"

    assert result.investigation is None

    assert investigator.calls == []


def test_runner_requires_pending_approval():
    investigator = FakeInvestigator(build_investigation())

    runner = DevRescueRemediationRunner(
        investigator=investigator,
        remediation_workflow=RemediationWorkflow(),
    )

    result = runner.investigate_and_prepare(
        incident="Payment failed.",
        service="payment-service",
    )

    assert result.status == "BLOCKED"

    assert result.remediation is not None

    assert result.remediation.status == "BLOCKED"

    assert result.remediation.message == (
        "Patch generation is not allowed by the remediation proposal."
    )


def test_runner_requires_approver_identity():
    investigator = FakeInvestigator(build_investigation())

    runner = DevRescueRemediationRunner(
        investigator=investigator,
        remediation_workflow=RemediationWorkflow(),
    )

    prepared = runner.investigate_and_prepare(
        incident="Payment failed.",
        service="payment-service",
        code_evidence=build_code_evidence(),
    )

    assert prepared.status == "PENDING_APPROVAL"

    result = runner.approve_and_create_pr(
        prepared=prepared,
        approved_by="",
        reason="Valid remediation.",
        branch="devrescue/test",
        title="Fix payment validation",
        body="Test PR",
    )

    assert result.status == "BLOCKED"
