from typing import Any

from .models import (
    EvaluationCase,
    EvaluationCheck,
    EvaluationReport,
    EvaluationResult,
    EvaluationStatus,
)


class EvaluationRunner:
    """
    Evaluates a DevRescue remediation result against an
    expected EvaluationCase.

    This layer intentionally does not execute the agent.
    """

    def evaluate(
        self,
        case: EvaluationCase,
        result: Any,
    ) -> EvaluationResult:
        checks: list[EvaluationCheck] = []
        errors: list[str] = []

        self._check_root_cause(case, result, checks)
        self._check_confidence(case, result, checks)
        self._check_remediation(case, result, checks)
        self._check_patch(case, result, checks)
        self._check_validation(case, result, checks)
        self._check_approval(case, result, checks)
        self._check_github(case, result, checks)

        status = (
            EvaluationStatus.PASS
            if all(check.passed for check in checks)
            else EvaluationStatus.FAIL
        )

        return EvaluationResult(
            case_id=case.case_id,
            case_name=case.name,
            status=status,
            checks=checks,
            errors=errors,
        )

    def evaluate_many(
        self,
        cases: list[EvaluationCase],
        results: dict[str, Any],
    ) -> EvaluationReport:
        report = EvaluationReport()

        for case in cases:
            if case.case_id not in results:
                report.results.append(
                    EvaluationResult(
                        case_id=case.case_id,
                        case_name=case.name,
                        status=EvaluationStatus.FAIL,
                        errors=[
                            f"No result supplied for {case.case_id}"
                        ],
                    )
                )
                continue

            report.results.append(
                self.evaluate(
                    case,
                    results[case.case_id],
                )
            )

        return report

    @staticmethod
    def _get(obj: Any, name: str, default: Any = None) -> Any:
        if obj is None:
            return default

        if isinstance(obj, dict):
            return obj.get(name, default)

        return getattr(obj, name, default)

    def _check_root_cause(
        self,
        case: EvaluationCase,
        result: Any,
        checks: list[EvaluationCheck],
    ) -> None:
        if case.expected_root_cause_category is None:
            return

        remediation = self._get(result, "remediation")
        actual = self._get(remediation, "category")

        if actual is None:
            investigation = self._get(result, "investigation")
            actual = self._get(
                investigation,
                "root_cause",
            )

        checks.append(
            EvaluationCheck(
                name="root_cause_category",
                passed=actual == case.expected_root_cause_category,
                expected=case.expected_root_cause_category,
                actual=actual,
                details="Root cause category comparison.",
            )
        )

    def _check_confidence(
        self,
        case: EvaluationCase,
        result: Any,
        checks: list[EvaluationCheck],
    ) -> None:
        if case.minimum_confidence is None:
            return

        investigation = self._get(result, "investigation")
        actual = float(
            self._get(
                investigation,
                "confidence",
                0.0,
            )
        )

        # EV-05 verifies that low confidence remains below the
        # remediation threshold; other cases require the threshold.
        if case.case_id == "EV-05":
            passed = actual < case.minimum_confidence
            expected = f"< {case.minimum_confidence}"
        else:
            passed = actual >= case.minimum_confidence
            expected = f">= {case.minimum_confidence}"

        checks.append(
            EvaluationCheck(
                name="minimum_confidence",
                passed=passed,
                expected=expected,
                actual=actual,
                details="Confidence threshold comparison.",
            )
        )

    def _check_remediation(
        self,
        case: EvaluationCase,
        result: Any,
        checks: list[EvaluationCheck],
    ) -> None:
        if case.expected_remediation_allowed is None:
            return

        remediation = self._get(result, "remediation")
        # Absence of a remediation proposal means remediation
        # was not allowed / was not reached.
        if remediation is None:
            actual = False
        else:
            actual = bool(
                self._get(
                    remediation,
                    "allowed",
                    False,
                )
            )

        checks.append(
            EvaluationCheck(
                name="remediation_allowed",
                passed=actual == case.expected_remediation_allowed,
                expected=case.expected_remediation_allowed,
                actual=actual,
                details="Remediation safety decision.",
            )
        )

    def _check_patch(
        self,
        case: EvaluationCase,
        result: Any,
        checks: list[EvaluationCheck],
    ) -> None:
        if case.expected_patch_generated is None:
            return

        patch = self._get(result, "patch")

        actual = bool(
            patch is not None
            and self._get(patch, "allowed", False)
            and self._get(patch, "patches", [])
        )

        checks.append(
            EvaluationCheck(
                name="patch_generated",
                passed=actual == case.expected_patch_generated,
                expected=case.expected_patch_generated,
                actual=actual,
                details="Patch generation outcome.",
            )
        )

    def _check_validation(
        self,
        case: EvaluationCase,
        result: Any,
        checks: list[EvaluationCheck],
    ) -> None:
        if case.expected_validation_passed is None:
            return

        validation = self._get(result, "validation")
        actual = self._get(validation, "passed")

        checks.append(
            EvaluationCheck(
                name="validation_passed",
                passed=actual == case.expected_validation_passed,
                expected=case.expected_validation_passed,
                actual=actual,
                details="Patch validation outcome.",
            )
        )

    def _check_approval(
        self,
        case: EvaluationCase,
        result: Any,
        checks: list[EvaluationCheck],
    ) -> None:
        if case.expected_human_approval_required is None:
            return

        approval_request = self._get(
            result,
            "approval_request",
        )

        actual = self._get(
            approval_request,
            "requires_human_approval",
        )

        checks.append(
            EvaluationCheck(
                name="human_approval_required",
                passed=actual == case.expected_human_approval_required,
                expected=case.expected_human_approval_required,
                actual=actual,
                details="Human approval requirement.",
            )
        )

    def _check_github(
        self,
        case: EvaluationCase,
        result: Any,
        checks: list[EvaluationCheck],
    ) -> None:
        if case.expected_github_pr is None:
            return

        github = self._get(result, "github")

        actual = bool(
            github is not None
            and self._get(github, "pull_request") is not None
            and self._get(
                github,
                "status",
            )
            == "completed"
        )

        checks.append(
            EvaluationCheck(
                name="github_pr_created",
                passed=actual == case.expected_github_pr,
                expected=case.expected_github_pr,
                actual=actual,
                details="GitHub PR creation outcome.",
            )
        )
