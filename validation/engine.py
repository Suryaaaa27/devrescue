from __future__ import annotations

import ast
import subprocess
import tempfile
from pathlib import Path

from patch_generation.models import PatchProposal

from .models import ValidationCheck, ValidationResult


class ValidationEngine:
    """
    Validates generated patches inside an isolated temporary workspace.

    This engine never modifies the real repository.
    """

    def validate(
        self,
        patch_proposal: PatchProposal,
        run_tests: bool = False,
    ) -> ValidationResult:

        if not patch_proposal.allowed:
            return ValidationResult(
                passed=False,
                status="REJECTED",
                summary="Patch proposal is not allowed.",
                error=patch_proposal.reason,
            )

        if not patch_proposal.patches:
            return ValidationResult(
                passed=False,
                status="REJECTED",
                summary="No patches are available for validation.",
            )

        checks: list[ValidationCheck] = []

        with tempfile.TemporaryDirectory(prefix="devrescue-validation-") as temp_dir:
            workspace = Path(temp_dir)

            for patch in patch_proposal.patches:
                safe, check = self._validate_patch_file(
                    workspace,
                    patch.path,
                    patch.patched_content,
                )

                checks.append(check)

                if not safe:
                    return ValidationResult(
                        passed=False,
                        status="FAILED",
                        summary="Patch validation failed.",
                        checks=checks,
                    )

            if run_tests:
                test_check, output = self._run_tests(workspace)
                checks.append(test_check)

                if not test_check.passed:
                    return ValidationResult(
                        passed=False,
                        status="FAILED",
                        summary="Validation tests failed.",
                        checks=checks,
                        test_output=output,
                    )

        return ValidationResult(
            passed=True,
            status="PASSED",
            summary="Patch passed validation.",
            checks=checks,
        )

    def _validate_patch_file(
        self,
        workspace: Path,
        path: str,
        content: str,
    ) -> tuple[bool, ValidationCheck]:

        target = workspace / path

        try:
            target.resolve().relative_to(workspace.resolve())
        except ValueError:
            return False, ValidationCheck(
                name=f"path:{path}",
                passed=False,
                message="Patch escapes the validation workspace.",
            )

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

        if target.suffix == ".py":
            try:
                ast.parse(content, filename=path)
            except SyntaxError as exc:
                return False, ValidationCheck(
                    name=f"syntax:{path}",
                    passed=False,
                    message=f"Python syntax error: {exc}",
                )

            return True, ValidationCheck(
                name=f"syntax:{path}",
                passed=True,
                message="Python syntax is valid.",
            )

        return True, ValidationCheck(
            name=f"file:{path}",
            passed=True,
            message="Patched file was created successfully.",
        )

    @staticmethod
    def _run_tests(
        workspace: Path,
    ) -> tuple[ValidationCheck, str]:

        try:
            process = subprocess.run(
                ["python", "-m", "pytest", "-q"],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=30,
                shell=False,
            )

            output = (
                process.stdout
                + "\n"
                + process.stderr
            ).strip()

            if process.returncode == 0:
                return (
                    ValidationCheck(
                        name="pytest",
                        passed=True,
                        message="Validation tests passed.",
                    ),
                    output,
                )

            return (
                ValidationCheck(
                    name="pytest",
                    passed=False,
                    message="Validation tests failed.",
                ),
                output,
            )

        except subprocess.TimeoutExpired:
            return (
                ValidationCheck(
                    name="pytest",
                    passed=False,
                    message="Validation tests timed out.",
                ),
                "pytest execution timed out.",
            )

        except Exception as exc:
            return (
                ValidationCheck(
                    name="pytest",
                    passed=False,
                    message=f"Unable to execute validation tests: {exc}",
                ),
                str(exc),
            )
