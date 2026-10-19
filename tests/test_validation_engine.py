from patch_generation.models import PatchFile, PatchProposal
from validation.engine import ValidationEngine


def valid_patch():
    return PatchProposal(
        allowed=True,
        reason="Patch generated successfully.",
        patches=[
            PatchFile(
                path="services/payment.py",
                original_content=(
                    "def process_payment(amount):\n"
                    "    charge_card(amount)\n"
                ),
                patched_content=(
                    "def process_payment(amount):\n"
                    "    if amount <= 0:\n"
                    '        raise ValueError("Payment amount must be greater than zero.")\n'
                    "    charge_card(amount)\n"
                ),
                diff="dummy diff",
            )
        ],
    )


def test_valid_python_patch_passes_validation():
    result = ValidationEngine().validate(valid_patch())

    assert result.passed is True
    assert result.status == "PASSED"
    assert any(
        check.name == "syntax:services/payment.py"
        and check.passed
        for check in result.checks
    )


def test_invalid_python_patch_fails_validation():
    proposal = PatchProposal(
        allowed=True,
        reason="Patch generated successfully.",
        patches=[
            PatchFile(
                path="services/payment.py",
                original_content="",
                patched_content=(
                    "def broken(:\n"
                    "    return True\n"
                ),
                diff="dummy diff",
            )
        ],
    )

    result = ValidationEngine().validate(proposal)

    assert result.passed is False
    assert result.status == "FAILED"
    assert "syntax" in result.checks[0].name


def test_disallowed_patch_is_rejected():
    proposal = PatchProposal(
        allowed=False,
        reason="Patch failed safety checks.",
    )

    result = ValidationEngine().validate(proposal)

    assert result.passed is False
    assert result.status == "REJECTED"
    assert result.error == "Patch failed safety checks."


def test_empty_patch_is_rejected():
    proposal = PatchProposal(
        allowed=True,
        reason="Allowed.",
        patches=[],
    )

    result = ValidationEngine().validate(proposal)

    assert result.passed is False
    assert result.status == "REJECTED"


def test_nested_patch_path_is_supported():
    proposal = PatchProposal(
        allowed=True,
        reason="Allowed.",
        patches=[
            PatchFile(
                path="services/payment_service/main.py",
                original_content="",
                patched_content=(
                    "def process_payment(amount):\n"
                    "    return amount\n"
                ),
                diff="dummy diff",
            )
        ],
    )

    result = ValidationEngine().validate(proposal)

    assert result.passed is True


def test_path_traversal_cannot_escape_workspace():
    proposal = PatchProposal(
        allowed=True,
        reason="Allowed.",
        patches=[
            PatchFile(
                path="../../outside.py",
                original_content="",
                patched_content="print('bad')\n",
                diff="dummy diff",
            )
        ],
    )

    result = ValidationEngine().validate(proposal)

    assert result.passed is False
    assert result.status == "FAILED"


def test_non_python_file_can_be_validated():
    proposal = PatchProposal(
        allowed=True,
        reason="Allowed.",
        patches=[
            PatchFile(
                path="config/settings.txt",
                original_content="DEBUG=false\n",
                patched_content="DEBUG=true\n",
                diff="dummy diff",
            )
        ],
    )

    result = ValidationEngine().validate(proposal)

    assert result.passed is True


def test_validation_serialization():
    result = ValidationEngine().validate(valid_patch())

    payload = result.to_dict()

    assert payload["passed"] is True
    assert payload["status"] == "PASSED"
    assert isinstance(payload["checks"], list)
