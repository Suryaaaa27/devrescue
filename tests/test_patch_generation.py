from remediation.engine import RemediationEngine
from remediation.models import RemediationProposal
from hypothesis.models import Hypothesis
from patch_generation.generator import PatchGenerator
from evidence.models import CodeEvidence

def application_validation_hypothesis():
    return Hypothesis(
        name="Invalid payment input",
        category="application_validation",
        role="root_cause",
        confidence=0.90,
        score=0.90,
        explanation="Invalid payment amounts reach the application without validation.",
        severity="high",
    )


def application_exception_hypothesis():
    return Hypothesis(
        name="Application exception",
        category="application_error",
        role="root_cause",
        confidence=0.90,
        score=0.90,
        explanation="The application raises a generic exception.",
        severity="high",
    )


def test_patch_is_generated_for_application_validation():
    hypothesis = application_validation_hypothesis()

    evidence = {
        "code": [
            {
                "path": "services/payment.py",
                "content": (
                    "def process_payment(amount):\n"
                    "    charge_card(amount)\n"
                ),
            }
        ]
    }

    decision = RemediationEngine().propose(
        hypothesis,
        evidence,
    )

    assert decision.allowed is True
    assert decision.proposal is not None

    result = PatchGenerator().generate(
        decision.proposal,
        evidence["code"],
    )

    assert result.allowed is True
    assert len(result.patches) == 1

    patch = result.patches[0]

    assert patch.path == "services/payment.py"
    assert "if amount <= 0:" in patch.patched_content
    assert "--- a/services/payment.py" in patch.diff
    assert "+++ b/services/payment.py" in patch.diff


def test_patch_is_generated_for_application_exception():
    hypothesis = application_exception_hypothesis()

    evidence = {
        "code": [
            {
                "path": "services/payment.py",
                "content": (
                    "def process_payment(amount):\n"
                    "    raise Exception(\"payment failed\")\n"
                ),
            }
        ]
    }

    decision = RemediationEngine().propose(
        hypothesis,
        evidence,
    )

    assert decision.allowed is True

    result = PatchGenerator().generate(
        decision.proposal,
        evidence["code"],
    )

    assert result.allowed is True

    patch = result.patches[0]

    assert "raise ValueError(" in patch.patched_content


def test_patch_generation_rejects_missing_code():
    proposal = RemediationProposal(
        hypothesis="Invalid payment input",
        category="application_validation",
        summary="Validate payment input before processing.",
        rationale="Invalid payment amounts reach the application.",
        affected_files=["services/payment.py"],
        confidence=0.90,
        requires_human_approval=True,
        patch_generation_allowed=True,
        validation_requirements=[
            "Run unit tests for payment processing."
        ],
        safety_constraints=[
            "Human approval required.",
            "No production mutation.",
        ],
    )

    result = PatchGenerator().generate(
        proposal,
        [],
    )

    assert result.allowed is False
    assert "No code evidence" in result.reason


def test_patch_generation_does_not_generate_database_patch_without_code():
    hypothesis = Hypothesis(
        name="Database dependency unavailable",
        category="database_failure",
        role="root_cause",
        confidence=0.90,
        score=0.90,
        explanation="The database is unavailable.",
        severity="high",
    )

    evidence = {
        "code": [
            {
                "path": "services/payment.py",
                "content": "def process_payment(amount):\n    charge_card(amount)\n",
            }
        ]
    }

    decision = RemediationEngine().propose(
        hypothesis,
        evidence,
    )

    assert decision.allowed is True

    result = PatchGenerator().generate(
        decision.proposal,
        evidence["code"],
    )

    assert result.allowed is False


def test_patch_rejects_path_traversal():
    hypothesis = application_validation_hypothesis()

    evidence = {
        "code": [
            {
                "path": "../secrets.py",
                "content": (
                    "def process_payment(amount):\n"
                    "    charge_card(amount)\n"
                ),
            }
        ]
    }

    decision = RemediationEngine().propose(
        hypothesis,
        evidence,
    )

    result = PatchGenerator().generate(
        decision.proposal,
        evidence["code"],
    )

    assert result.allowed is False


def test_patch_rejects_secret_content():
    hypothesis = application_exception_hypothesis()

    evidence = {
        "code": [
            {
                "path": "services/payment.py",
                "content": (
                    'API_KEY = "super-secret"\n'
                    'def process_payment(amount):\n'
                    '    raise Exception("payment failed")\n'
                ),
            }
        ]
    }

    decision = RemediationEngine().propose(
        hypothesis,
        evidence,
    )

    result = PatchGenerator().generate(
        decision.proposal,
        evidence["code"],
    )

    assert result.allowed is False


def test_patch_generation_does_not_modify_original_content():
    hypothesis = application_validation_hypothesis()

    original = (
        "def process_payment(amount):\n"
        "    charge_card(amount)\n"
    )

    evidence = {
        "code": [
            {
                "path": "services/payment.py",
                "content": original,
            }
        ]
    }

    decision = RemediationEngine().propose(
        hypothesis,
        evidence,
    )

    result = PatchGenerator().generate(
        decision.proposal,
        evidence["code"],
    )

    assert result.allowed is True
    assert evidence["code"][0]["content"] == original


def test_patch_serialization():
    hypothesis = application_validation_hypothesis()

    evidence = {
        "code": [
            {
                "path": "services/payment.py",
                "content": (
                    "def process_payment(amount):\n"
                    "    charge_card(amount)\n"
                ),
            }
        ]
    }

    decision = RemediationEngine().propose(
        hypothesis,
        evidence,
    )

    result = PatchGenerator().generate(
        decision.proposal,
        evidence["code"],
    )

    payload = result.to_dict()

    assert payload["allowed"] is True
    assert len(payload["patches"]) == 1
    assert payload["patches"][0]["path"] == "services/payment.py"

def test_generates_patch_from_code_evidence_object():
    proposal = RemediationProposal(
        hypothesis="Invalid payment input",
        category="application_validation",
        summary="Validate payment input before processing.",
        rationale="Invalid payment amounts reach the application.",
        affected_files=["tests/example.py"],
        confidence=0.90,
        requires_human_approval=True,
        patch_generation_allowed=True,
        validation_requirements=[
            "Run unit tests for payment processing."
        ],
        safety_constraints=[
            "Human approval required.",
            "No production mutation.",
        ],
    )

    evidence = CodeEvidence(
        repository="Suryaaaa27/devrescue",
        path="tests/example.py",
        content=(
            "def process_payment(amount):\n"
            "    return amount\n"
        ),
    )

    result = PatchGenerator().generate(
        proposal,
        [evidence],
    )

    assert result.allowed is True
    assert len(result.patches) == 1
    assert result.patches[0].path == "tests/example.py"
