from pathlib import Path

import pytest
from approval.models import ApprovalRequest
from patch_generation.models import PatchFile, PatchProposal
from validation.engine import ValidationEngine
from validation.models import ValidationResult
from remediation.models import RemediationProposal
from hypothesis.models import Hypothesis
from patch_generation.generator import PatchGenerator
from remediation.safety import RemediationSafetyPolicy
from approval.gate import HumanApprovalGate

def test_security_no_hypothesis_blocks_remediation():
    allowed, reason = RemediationSafetyPolicy.evaluate(
        hypothesis=None,
        evidence_summary={"code": []},
    )

    assert allowed is False
    assert "hypothesis" in reason.lower()


def test_security_non_root_cause_blocks_remediation():
    hypothesis = Hypothesis(
        name="Possible application error",
        category="application_error",
        role="candidate",
        confidence=0.95,
        score=0.95,
        explanation="Candidate hypothesis.",
    )

    allowed, reason = RemediationSafetyPolicy.evaluate(
        hypothesis=hypothesis,
        evidence_summary={"code": [{"path": "app.py"}]},
    )

    assert allowed is False
    assert "root-cause" in reason.lower()

def test_security_low_confidence_blocks_remediation():
    hypothesis = Hypothesis(
        name="Possible application error",
        category="application_error",
        role="root_cause",
        confidence=0.74,
        score=0.74,
        explanation="Low-confidence hypothesis.",
    )

    allowed, reason = RemediationSafetyPolicy.evaluate(
        hypothesis=hypothesis,
        evidence_summary={"code": [{"path": "app.py"}]},
    )

    assert allowed is False
    assert "confidence" in reason.lower()

def test_security_missing_evidence_blocks_remediation():
    hypothesis = Hypothesis(
        name="Application error",
        category="application_error",
        role="root_cause",
        confidence=0.95,
        score=0.95,
        explanation="Confirmed application error.",
    )

    allowed, reason = RemediationSafetyPolicy.evaluate(
        hypothesis=hypothesis,
        evidence_summary={},
    )

    assert allowed is False
    assert "evidence" in reason.lower()

@pytest.mark.parametrize(
    "action_type",
    [
        "delete_production_data",
        "drop_database",
        "disable_authentication",
        "disable_authorization",
        "expose_secret",
        "rotate_production_credentials",
        "execute_arbitrary_command",
    ],
)
def test_security_forbidden_actions_are_blocked(action_type):
    allowed, reason = RemediationSafetyPolicy.validate_action_type(
        action_type
    )

    assert allowed is False
    assert action_type in reason

def test_security_permitted_action_is_allowed():
    allowed, reason = RemediationSafetyPolicy.validate_action_type(
        "correct_application_exception"
    )

    assert allowed is True
    assert "permitted" in reason.lower()

def test_security_patch_requires_allowed_proposal():
    generator = PatchGenerator()

    proposal = RemediationProposal(
        hypothesis="Application validation failure",
        category="application_validation",
        summary="Invalid payment input.",
        rationale="Input validation is required.",
        actions=[],
        affected_files=["services/payment_service/main.py"],
        risk_level="low",
        confidence=0.95,
        requires_human_approval=True,
        patch_generation_allowed=False,
        validation_requirements=[],
        safety_constraints=[],
    )

    result = generator.generate(
        proposal,
        code_evidence=[
            {
                "path": "services/payment_service/main.py",
                "content": "def process_payment(amount):\n    return amount\n",
            }
        ],
    )

    assert result.allowed is False
    assert result.patches == []

def test_security_patch_requires_patch_generation_permission():
    generator = PatchGenerator()

    proposal = RemediationProposal(
        hypothesis="Application validation failure",
        category="application_validation",
        summary="Invalid payment input.",
        rationale="Input validation is required.",
        actions=[],
        affected_files=["services/payment_service/main.py"],
        risk_level="low",
        confidence=0.95,
        requires_human_approval=True,
        patch_generation_allowed=False,
        validation_requirements=[],
        safety_constraints=[],
    )

    result = generator.generate(
        proposal,
        code_evidence=[
            {
                "path": "services/payment_service/main.py",
                "content": "def process_payment(amount):\n    return amount\n",
            }
        ],
    )

    assert result.allowed is False
    assert result.patches == []

def test_security_patch_requires_code_evidence():
    generator = PatchGenerator()

    proposal = RemediationProposal(
        hypothesis="Application validation failure",
        category="application_validation",
        summary="Invalid payment input.",
        rationale="Input validation is required.",
        actions=[],
        affected_files=["services/payment_service/main.py"],
        risk_level="low",
        confidence=0.95,
        requires_human_approval=True,
        patch_generation_allowed=True,
        validation_requirements=[],
        safety_constraints=[],
    )

    result = generator.generate(
        proposal,
        code_evidence=[],
    )

    assert result.allowed is False
    assert result.patches == []

@pytest.mark.parametrize(
    "path",
    [
        "../../etc/passwd",
        "../secrets.env",
        "../../.env",
        "../../../config.yaml",
    ],
)
def test_security_patch_rejects_path_traversal(path):
    generator = PatchGenerator()

    proposal = RemediationProposal(
        hypothesis="Application validation failure",
        category="application_validation",
        summary="Invalid payment input.",
        rationale="Input validation is required.",
        actions=[],
        affected_files=[path],
        risk_level="low",
        confidence=0.95,
        requires_human_approval=True,
        patch_generation_allowed=True,
        validation_requirements=[],
        safety_constraints=[],
    )

    result = generator.generate(
        proposal,
        code_evidence=[
            {
                "path": path,
                "content": "secret=true\n",
            }
        ],
    )

    assert result.allowed is False
    assert result.patches == []


def test_security_database_failure_does_not_generate_patch():
    generator = PatchGenerator()

    proposal = RemediationProposal(
        hypothesis="Database outage",
        category="database_failure",
        summary="Database connectivity failure.",
        rationale="Database connectivity must be restored.",
        actions=[],
        affected_files=[],
        risk_level="high",
        confidence=0.95,
        requires_human_approval=True,
        patch_generation_allowed=False,
        validation_requirements=[],
        safety_constraints=[],
    )

    result = generator.generate(
        proposal,
        code_evidence=[],
    )

    assert result.allowed is False
    assert result.patches == []

def test_security_valid_application_patch_is_allowed():
    generator = PatchGenerator()

    proposal = RemediationProposal(
        hypothesis="Application validation failure",
        category="application_validation",
        summary="Invalid payment input.",
        rationale="Payment amount must be validated.",
        actions=[],
        affected_files=["services/payment_service/main.py"],
        risk_level="low",
        confidence=0.95,
        requires_human_approval=True,
        patch_generation_allowed=True,
        validation_requirements=[],
        safety_constraints=[],
    )

    result = generator.generate(
        proposal,
        code_evidence=[
            {
                "path": "services/payment_service/main.py",
                "content": (
                    "def process_payment(amount):\n"
                    "    return amount\n"
                ),
            }
        ],
    )

    assert result.allowed is True
    assert len(result.patches) > 0


@pytest.mark.parametrize(
    "path",
    [
        "../outside.py",
        "../../outside.py",
        "../../../outside.py",
    ],
)
def test_security_validation_rejects_path_traversal(path):
    engine = ValidationEngine()
    proposal = PatchProposal(
        allowed=True,
        reason="Security validation test.",
        patches=[
            PatchFile(
                path=path,
                original_content="",
                patched_content="print('unsafe')\n",
                diff="",
            )
        ],
    )
    result = engine.validate(proposal)
    assert result.passed is False
    assert any(
        check.passed is False
        and "escapes the validation workspace" in check.message
        for check in result.checks
    )


def test_security_validation_rejects_absolute_path():
    engine = ValidationEngine()
    absolute_path = str(Path.cwd() / "unsafe.py")
    proposal = PatchProposal(
        allowed=True,
        reason="Security validation test.",
        patches=[
            PatchFile(
                path=absolute_path,
                original_content="",
                patched_content="print('unsafe')\n",
                diff="",
            )
        ],
    )
    result = engine.validate(proposal)
    assert result.passed is False
    assert any(
        check.passed is False
        and "escapes the validation workspace" in check.message
        for check in result.checks
    )


def test_security_validation_rejects_invalid_python():
    engine = ValidationEngine()
    proposal = PatchProposal(
        allowed=True,
        reason="Security validation test.",
        patches=[
            PatchFile(
                path="services/payment_service/main.py",
                original_content="",
                patched_content=(
                    "def broken(:\n"
                    "    this is invalid python\n"
                ),
                diff="",
            )
        ],
    )
    result = engine.validate(proposal)
    assert result.passed is False
    assert result.status == "FAILED"


def test_security_validation_accepts_valid_python():
    engine = ValidationEngine()
    proposal = PatchProposal(
        allowed=True,
        reason="Security validation test.",
        patches=[
            PatchFile(
                path="services/payment_service/main.py",
                original_content="",
                patched_content=(
                    "def process_payment(amount):\n"
                    "    return amount\n"
                ),
                diff="",
            )
        ],
    )
    result = engine.validate(proposal)
    assert result.passed is True
    assert result.status == "PASSED"


def test_security_validation_does_not_modify_real_repository(tmp_path):
    engine = ValidationEngine()
    protected_file = Path("validation_security_canary.txt")
    original_content = "DO NOT MODIFY"
    protected_file.write_text(
        original_content,
        encoding="utf-8",
    )
    try:
        proposal = PatchProposal(
            allowed=True,
            reason="Security isolation test.",
            patches=[
                PatchFile(
                    path="validation_security_canary.txt",
                    original_content="",
                    patched_content="ATTACKER CONTENT",
                    diff="",
                )
            ],
        )
        result = engine.validate(proposal)
        assert result.passed is True
        assert protected_file.read_text(
            encoding="utf-8"
        ) == original_content
    finally:
        protected_file.unlink(missing_ok=True)


def test_security_validation_rejects_empty_patch():
    engine = ValidationEngine()
    proposal = PatchProposal(
        allowed=True,
        reason="Security validation test.",
        patches=[],
    )
    result = engine.validate(proposal)
    assert result.passed is False
    assert result.status == "REJECTED"


def test_security_validation_rejects_disallowed_patch():
    engine = ValidationEngine()
    proposal = PatchProposal(
        allowed=False,
        reason="Unsafe remediation.",
        patches=[
            PatchFile(
                path="services/payment_service/main.py",
                original_content="",
                patched_content="print('should never execute')\n",
                diff="",
            )
        ],
    )
    result = engine.validate(proposal)
    assert result.passed is False
    assert result.status == "REJECTED"
    assert result.error == "Unsafe remediation."

def test_security_approval_requires_validation():
    gate = HumanApprovalGate()

    request = ApprovalRequest(
        request_id="security-001",
        incident="payment failure",
        hypothesis="application validation",
        summary="Unsafe patch",
        risk_level="high",
        affected_files=["services/payment_service/main.py"],
        patch_count=1,
        validation_passed=False,
        requires_human_approval=True,
    )

    result = gate.approve(
        request,
        approved_by="security-reviewer",
        reason="Attempted bypass.",
    )

    assert result.approved is False

def test_security_approval_requires_identity():
    gate = HumanApprovalGate()

    request = ApprovalRequest(
        request_id="security-002",
        incident="payment failure",
        hypothesis="application validation",
        summary="Patch validated.",
        risk_level="low",
        affected_files=["services/payment_service/main.py"],
        patch_count=1,
        validation_passed=True,
        requires_human_approval=True,
    )

    result = gate.approve(
        request,
        approved_by="",
        reason="Attempted approval.",
    )

    assert result.approved is False

def test_security_approval_requires_reason():
    gate = HumanApprovalGate()

    request = ApprovalRequest(
        request_id="security-003",
        incident="payment failure",
        hypothesis="application validation",
        summary="Patch validated.",
        risk_level="low",
        affected_files=["services/payment_service/main.py"],
        patch_count=1,
        validation_passed=True,
        requires_human_approval=True,
    )

    result = gate.approve(
        request,
        approved_by="security-reviewer",
        reason="",
    )

    assert result.approved is False

def test_security_rejected_request_cannot_be_approved():
    gate = HumanApprovalGate()

    request = ApprovalRequest(
        request_id="security-004",
        incident="payment failure",
        hypothesis="application validation",
        summary="Patch validated.",
        risk_level="low",
        affected_files=["services/payment_service/main.py"],
        patch_count=1,
        validation_passed=True,
        requires_human_approval=True,
    )

    rejection = gate.reject(
        request,
        rejected_by="security-reviewer",
        reason="Risk unacceptable.",
    )

    assert rejection.approved is False
    assert rejection.status == "REJECTED"

def test_security_validation_does_not_use_shell_injection():
    engine = ValidationEngine()

    malicious_path = "test.py; echo SECURITY_BREACH"

    proposal = PatchProposal(
        allowed=True,
        reason="Command injection test.",
        patches=[
            PatchFile(
                path=malicious_path,
                original_content="",
                patched_content="print('safe')\n",
                diff="",
            )
        ],
    )

    result = engine.validate(proposal)

    # The filename must be treated as a path,
    # never as a shell command.
    assert "SECURITY_BREACH" not in (
        result.test_output or ""
    )
