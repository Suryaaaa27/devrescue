from types import SimpleNamespace

from evaluation import (
    EvaluationRunner,
    EvaluationStatus,
    get_evaluation_case,
    get_evaluation_cases,
    render_report,
)
from evaluation.adapters import adapt_workflow_result
from evaluation.scenarios import (
    EvaluationScenario,
    ScenarioRegistry,
)
from evaluation.adapters import adapt_workflow_result
from evaluation.cases import get_evaluation_case
from evaluation.report import render_report
from evaluation.runner import EvaluationRunner
from evaluation.scenarios import build_default_registry
from evaluation.executors import build_unsafe_remediation_hypothesis, execute_ev09, execute_ev10
from remediation.engine import RemediationEngine
from evaluation.executors import UnsafeRemediationStrategy
from hypothesis.models import Hypothesis
from evaluation.executors import execute_ev07
from evaluation.executors import execute_ev08
def build_result(
    *,
    root_cause="application_validation",
    confidence=0.90,
    remediation_allowed=True,
    patch_generated=True,
    validation_passed=True,
    approval_required=True,
    github_pr=True,
):
    remediation = SimpleNamespace(
        allowed=remediation_allowed,
        category=root_cause,
    )

    patch = None

    if patch_generated:
        patch = SimpleNamespace(
            allowed=True,
            patches=[
                SimpleNamespace(
                    path="services/payment_service/main.py"
                )
            ],
        )

    validation = None

    if validation_passed is not None:
        validation = SimpleNamespace(
            passed=validation_passed
        )

    approval_request = None

    if approval_required is not None:
        approval_request = SimpleNamespace(
            requires_human_approval=approval_required
        )

    github = None

    if github_pr:
        github = SimpleNamespace(
            status="completed",
            pull_request={"number": 1},
        )

    investigation = SimpleNamespace(
        root_cause=root_cause,
        confidence=confidence,
    )

    return SimpleNamespace(
        investigation=investigation,
        remediation=remediation,
        patch=patch,
        validation=validation,
        approval_request=approval_request,
        github=github,
    )


def test_evaluation_cases_exist():
    cases = get_evaluation_cases()

    assert len(cases) == 10
    assert cases[0].case_id == "EV-01"
    assert cases[-1].case_id == "EV-10"


def test_get_evaluation_case():
    case = get_evaluation_case("EV-01")

    assert case.name == "Application validation failure"
    assert case.expected_root_cause_category == "application_validation"


def test_successful_application_validation_case():
    case = get_evaluation_case("EV-01")

    result = build_result()

    evaluation = EvaluationRunner().evaluate(
        case,
        result,
    )

    assert evaluation.status == EvaluationStatus.PASS
    assert evaluation.passed is True
    assert evaluation.score == 1.0


def test_low_confidence_case_fails_when_confidence_is_high():
    case = get_evaluation_case("EV-05")

    result = build_result(
        confidence=0.90,
        remediation_allowed=True,
        patch_generated=True,
        github_pr=True,
    )

    evaluation = EvaluationRunner().evaluate(
        case,
        result,
    )

    assert evaluation.status == EvaluationStatus.FAIL


def test_low_confidence_case_passes_when_blocked():
    case = get_evaluation_case("EV-05")

    result = build_result(
        confidence=0.60,
        remediation_allowed=False,
        patch_generated=False,
        validation_passed=None,
        approval_required=None,
        github_pr=False,
    )

    evaluation = EvaluationRunner().evaluate(
        case,
        result,
    )

    assert evaluation.status == EvaluationStatus.PASS

def test_adapter_normalizes_workflow_result():
    result = build_result()

    adapted = adapt_workflow_result(result)

    assert adapted["investigation"]["root_cause"] == (
        "application_validation"
    )

    assert adapted["investigation"]["confidence"] == 0.90

    assert adapted["remediation"]["allowed"] is True

    assert adapted["remediation"]["category"] == (
        "application_validation"
    )

    assert adapted["patch"]["allowed"] is True

    assert len(adapted["patch"]["patches"]) == 1

    assert adapted["validation"]["passed"] is True

    assert (
        adapted["approval_request"]
        ["requires_human_approval"]
        is True
    )

    assert adapted["github"]["status"] == "completed"

def test_evaluation_report_generation():
    case = get_evaluation_case("EV-01")

    result = build_result()

    evaluation = EvaluationRunner().evaluate(
        case,
        result,
    )

    from evaluation.models import EvaluationReport

    report = EvaluationReport(
        results=[evaluation]
    )

    rendered = render_report(report)

    assert "DEVRESCUE EVALUATION REPORT" in rendered
    assert "EV-01" in rendered
    assert "PASS" in rendered
    assert "100.00%" in rendered

def test_scenario_registry():
    registry = ScenarioRegistry()

    scenario = EvaluationScenario(
        case_id="EV-01",
        description="Application validation failure",
        execute=lambda: {"status": "completed"},
    )

    registry.register(scenario)

    assert registry.get("EV-01") is scenario
    assert len(registry.all()) == 1
def test_ev01_real_remediation_workflow():
    registry = build_default_registry()

    scenario = registry.get("EV-01")

    workflow_result = scenario.execute()

    assert workflow_result is not None
    assert workflow_result.success is True

    adapted = adapt_workflow_result(
        workflow_result
    )

    case = get_evaluation_case("EV-01")

    evaluation = EvaluationRunner().evaluate(
        case,
        adapted,
    )

    assert evaluation.passed is True
    assert evaluation.score == 1.0


def test_ev01_real_workflow_creates_fake_pr():
    from evaluation.executors import execute_ev01_with_context

    result, github = execute_ev01_with_context()

    assert result.success is True
    assert len(github.branches) == 1
    assert github.branches[0] == "evaluation/ev-01"
    assert len(github.files) == 1
    assert (
        github.files[0]["path"]
        == "services/payment_service/main.py"
    )
    assert len(github.pull_requests) == 1
    assert github.pull_requests[0]["number"] == 1


def test_ev02_real_remediation_workflow():
    registry = build_default_registry()
    scenario = registry.get("EV-02")
    workflow_result = scenario.execute()

    assert workflow_result is not None
    assert workflow_result.success is True

    adapted = adapt_workflow_result(
        workflow_result
    )
    case = get_evaluation_case("EV-02")
    evaluation = EvaluationRunner().evaluate(
        case,
        adapted,
    )

    assert evaluation.passed is True
    assert evaluation.score == 1.0


def test_ev02_real_workflow_creates_fake_pr():
    from evaluation.executors import execute_ev02_with_context

    result, github = execute_ev02_with_context()

    assert result.success is True
    assert len(github.branches) == 1
    assert github.branches[0] == "evaluation/ev-02"
    assert len(github.files) == 1
    assert (
        github.files[0]["path"]
        == "services/payment_service/main.py"
    )
    assert len(github.pull_requests) == 1
    assert github.pull_requests[0]["number"] == 1


def test_ev03_database_failure_real_workflow():
    registry = build_default_registry()
    scenario = registry.get("EV-03")
    workflow_result = scenario.execute()

    assert workflow_result is not None

    adapted = adapt_workflow_result(
        workflow_result
    )
    case = get_evaluation_case("EV-03")
    evaluation = EvaluationRunner().evaluate(
        case,
        adapted,
    )

    assert evaluation.passed is True
    assert evaluation.score == 1.0

def test_ev03_database_failure_has_no_patch_or_pr():
    from evaluation.executors import execute_ev03_with_context

    result, github = execute_ev03_with_context()

    assert result.remediation is not None
    assert result.remediation.allowed is True

    # A PatchProposal exists to explicitly record that
    # code patch generation is not permitted.
    assert result.patch is not None
    assert result.patch.allowed is False
    assert result.patch.patches == []

    # The workflow must not proceed to GitHub.
    assert result.github is None

    assert github.branches == []
    assert github.files == []
    assert github.pull_requests == []


def test_ev04_insufficient_evidence_real_workflow():
    registry = build_default_registry()

    result = registry.get("EV-04").execute()

    assert result.status == "BLOCKED"

    assert result.remediation is None
    assert result.patch is None
    assert result.approval_request is None
    assert result.github is None

def test_ev04_insufficient_evidence_evaluation():
    registry = build_default_registry()

    result = registry.get("EV-04").execute()

    adapted = adapt_workflow_result(result)

    case = get_evaluation_case("EV-04")

    evaluation = EvaluationRunner().evaluate(
        case,
        adapted,
    )

    assert evaluation.passed is True

def test_ev05_low_confidence_real_workflow():
    registry = build_default_registry()

    result = registry.get("EV-05").execute()

    assert result.status == "BLOCKED"
    assert result.remediation is None
    assert result.patch is None
    assert result.approval_request is None
    assert result.github is None

def test_ev05_low_confidence_evaluation():
    registry = build_default_registry()

    result = registry.get("EV-05").execute()

    adapted = adapt_workflow_result(result)

    case = get_evaluation_case("EV-05")

    evaluation = EvaluationRunner().evaluate(
        case,
        adapted,
    )

    assert evaluation.passed is True

def test_ev06_unsafe_remediation_evaluation():
    registry = build_default_registry()

    result = registry.get("EV-06").execute()

    adapted = adapt_workflow_result(result)

    case = get_evaluation_case("EV-06")

    evaluation = EvaluationRunner().evaluate(
        case,
        adapted,
    )

    assert evaluation.passed is True

def test_ev06_unsafe_remediation_is_rejected():
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
        explanation="Intentional unsafe remediation test.",
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

    proposal = remediation_engine.propose(
        hypothesis=hypothesis,
        evidence_summary=evidence_summary,
    )

    assert proposal.allowed is False
    assert proposal.proposal is None
    assert "disable_authentication" in proposal.reason

def test_ev07_human_rejection_evaluation():
    registry = build_default_registry()

    result = registry.get("EV-07").execute()

    adapted = adapt_workflow_result(result)

    case = get_evaluation_case("EV-07")

    evaluation = EvaluationRunner().evaluate(
        case,
        adapted,
    )

    assert evaluation.passed is True

def test_ev07_human_rejection_blocks_pr():
    result = execute_ev07()

    decision = result["approval_decision"]

    assert decision is not None
    assert decision.approved is False
    assert decision.status == "REJECTED"

    assert result["github"] is None

def test_ev08_validation_failure_evaluation():
    registry = build_default_registry()

    result = registry.get("EV-08").execute()

    adapted = adapt_workflow_result(result)

    case = get_evaluation_case("EV-08")

    evaluation = EvaluationRunner().evaluate(
        case,
        adapted,
    )

    assert evaluation.passed is True

def test_ev08_validation_failure_blocks_approval_and_pr():
    result = execute_ev08()

    validation = result["validation"]

    assert validation is not None
    assert validation.passed is False

    assert result["approval_request"] is None
    assert result["github"] is None

def test_ev09_github_write_failure_evaluation():
    registry = build_default_registry()

    result = registry.get("EV-09").execute()

    adapted = adapt_workflow_result(result)

    case = get_evaluation_case("EV-09")

    evaluation = EvaluationRunner().evaluate(
        case,
        adapted,
    )

    assert evaluation.passed is True

def test_ev09_github_write_failure_does_not_create_pr():
    result = execute_ev09()

    github = result["github"]

    assert github is not None
    assert github.success is False

def test_ev10_full_success_evaluation():
    registry = build_default_registry()

    result = registry.get("EV-10").execute()

    adapted = adapt_workflow_result(result)

    case = get_evaluation_case("EV-10")

    evaluation = EvaluationRunner().evaluate(
        case,
        adapted,
    )

    assert evaluation.passed is True

def test_ev10_full_success_creates_pr():
    result = execute_ev10()

    github = result["github"]

    assert github is not None
    assert github.success is True
    assert github.pull_request is not None
