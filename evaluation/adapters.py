from typing import Any


def _get(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def adapt_workflow_result(result: Any) -> Any:
    """
    Normalize a real RemediationWorkflowResult into the
    structure expected by EvaluationRunner.

    No mutation is performed.
    """

    investigation = _get(result, "investigation")
    remediation = _get(result, "remediation")
    patch = _get(result, "patch")
    validation = _get(result, "validation")
    approval_request = _get(result, "approval_request")
    github = _get(result, "github")
    proposal = _get(remediation, "proposal")
    approval_required = _get(
        approval_request,
        "requires_human_approval",
        _get(proposal, "requires_human_approval"),
    )

    return {
        "investigation": {
            "root_cause": _get(
                investigation,
                "root_cause",
            ),
            "confidence": _get(
                investigation,
                "confidence",
            ),
        },
        "remediation": {
            "allowed": _get(
                remediation,
                "allowed",
            ),
            "category": _get(
                remediation,
                "category",
            ),
        },
        "patch": (
            {
                "allowed": _get(
                    patch,
                    "allowed",
                    False,
                ),
                "patches": _get(
                    patch,
                    "patches",
                    [],
                ),
            }
            if patch is not None
            else None
        ),
        "validation": (
            {
                "passed": _get(
                    validation,
                    "passed",
                ),
            }
            if validation is not None
            else None
        ),
        "approval_request": (
            {
                "requires_human_approval": approval_required,
            }
            if approval_required is not None
            else None
        ),
        "github": (
            {
                "status": _get(
                    github,
                    "status",
                ),
                "pull_request": _get(
                    github,
                    "pull_request",
                ),
            }
            if github is not None
            else None
        ),
    }
