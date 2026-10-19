from collections import Counter

from .models import EvaluationReport


def calculate_metrics(report: EvaluationReport) -> dict:
    total_checks = 0
    passed_checks = 0

    for result in report.results:
        total_checks += len(result.checks)
        passed_checks += sum(
            check.passed
            for check in result.checks
        )

    check_accuracy = (
        passed_checks / total_checks
        if total_checks
        else 0.0
    )

    return {
        "total_cases": report.total_cases,
        "passed_cases": report.passed_cases,
        "failed_cases": report.failed_cases,
        "case_pass_rate": report.pass_rate,
        "overall_check_accuracy": check_accuracy,
        "overall_score": report.overall_score,
    }


def calculate_check_metrics(
    report: EvaluationReport,
) -> dict[str, dict[str, float]]:
    counters: dict[str, Counter] = {}

    for result in report.results:
        for check in result.checks:
            if check.name not in counters:
                counters[check.name] = Counter()

            counters[check.name]["total"] += 1

            if check.passed:
                counters[check.name]["passed"] += 1

    metrics = {}

    for name, counter in counters.items():
        total = counter["total"]
        passed = counter["passed"]

        metrics[name] = {
            "total": float(total),
            "passed": float(passed),
            "accuracy": passed / total if total else 0.0,
        }

    return metrics
