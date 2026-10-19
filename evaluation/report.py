from .metrics import calculate_check_metrics, calculate_metrics
from .models import EvaluationReport


def render_report(report: EvaluationReport) -> str:
    metrics = calculate_metrics(report)
    check_metrics = calculate_check_metrics(report)

    lines = [
        "",
        "========================================",
        "       DEVRESCUE EVALUATION REPORT",
        "========================================",
        "",
        f"Cases evaluated : {metrics['total_cases']}",
        f"Cases passed    : {metrics['passed_cases']}",
        f"Cases failed    : {metrics['failed_cases']}",
        f"Case pass rate : {metrics['case_pass_rate']:.2%}",
        f"Check accuracy  : {metrics['overall_check_accuracy']:.2%}",
        f"Overall score   : {metrics['overall_score']:.2%}",
        "",
        "----------------------------------------",
        "CASE RESULTS",
        "----------------------------------------",
    ]

    for result in report.results:
        lines.append(
            f"{result.case_id:<8} "
            f"{result.status.value:<6} "
            f"{result.case_name}"
        )

    lines.extend(
        [
            "",
            "----------------------------------------",
            "CHECK METRICS",
            "----------------------------------------",
        ]
    )

    for name, metric in check_metrics.items():
        lines.append(
            f"{name:<28} "
            f"{metric['accuracy']:.2%}"
        )

    lines.extend(
        [
            "",
            "========================================",
            (
                "RESULT: PASS"
                if report.passed
                else "RESULT: FAIL"
            ),
            "========================================",
        ]
    )

    return "\n".join(lines)
