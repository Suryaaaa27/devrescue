from dataclasses import dataclass

from hypothesis.models import Hypothesis
from agent.state import InvestigationState


@dataclass(frozen=True)
class UncertaintyAssessment:
    """
    Describes how much uncertainty remains between the leading
    hypotheses in an investigation.
    """

    leading_hypothesis: str | None
    leading_confidence: float
    runner_up_hypothesis: str | None
    runner_up_confidence: float
    confidence_gap: float
    uncertainty: float
    independent_evidence_count: int
    sufficient_confidence: bool
    sufficient_separation: bool
    should_continue: bool
    reason: str


class UncertaintyAnalyzer:
    """
    Deterministic uncertainty analysis.

    This deliberately does not use probabilistic or LLM reasoning.
    """

    MIN_CONFIDENCE = 0.75
    MIN_SEPARATION = 0.10
    MIN_INDEPENDENT_EVIDENCE = 2

    def assess(
        self,
        state: InvestigationState,
    ) -> UncertaintyAssessment:
        hypotheses = sorted(
            state.hypotheses,
            key=lambda hypothesis: (
                hypothesis.confidence,
                hypothesis.score,
            ),
            reverse=True,
        )

        if not hypotheses:
            return UncertaintyAssessment(
                leading_hypothesis=None,
                leading_confidence=0.0,
                runner_up_hypothesis=None,
                runner_up_confidence=0.0,
                confidence_gap=0.0,
                uncertainty=1.0,
                independent_evidence_count=0,
                sufficient_confidence=False,
                sufficient_separation=False,
                should_continue=True,
                reason=(
                    "No hypotheses have been established yet."
                ),
            )

        leading = hypotheses[0]

        if len(hypotheses) > 1:
            runner_up = hypotheses[1]
            runner_up_confidence = runner_up.confidence
            runner_up_name = runner_up.name
        else:
            runner_up = None
            runner_up_confidence = 0.0
            runner_up_name = None

        confidence_gap = round(
            max(
                0.0,
                leading.confidence - runner_up_confidence,
            ),
            6,
        )

        # -----------------------------------------------------
        # Uncertainty
        # -----------------------------------------------------
        #
        # Higher confidence + larger separation means lower
        # remaining uncertainty.
        # -----------------------------------------------------

        uncertainty = max(
            0.0,
            min(
                1.0,
                1.0
                - (
                    leading.confidence * 0.6
                    + confidence_gap * 0.4
                ),
            ),
        )

        independent_evidence_count = (
            self._count_independent_evidence(state)
        )

        sufficient_confidence = (
            leading.role == "root_cause"
            and leading.confidence
            >= self.MIN_CONFIDENCE
        )

        sufficient_separation = (
            confidence_gap
            >= self.MIN_SEPARATION
        )

        enough_evidence = (
            independent_evidence_count
            >= self.MIN_INDEPENDENT_EVIDENCE
        )

        should_continue = not (
            sufficient_confidence
            and sufficient_separation
            and enough_evidence
        )

        reason = self._build_reason(
            leading=leading,
            runner_up=runner_up,
            confidence_gap=confidence_gap,
            independent_evidence_count=(
                independent_evidence_count
            ),
            should_continue=should_continue,
        )

        return UncertaintyAssessment(
            leading_hypothesis=leading.name,
            leading_confidence=leading.confidence,
            runner_up_hypothesis=runner_up_name,
            runner_up_confidence=runner_up_confidence,
            confidence_gap=confidence_gap,
            uncertainty=uncertainty,
            independent_evidence_count=(
                independent_evidence_count
            ),
            sufficient_confidence=sufficient_confidence,
            sufficient_separation=sufficient_separation,
            should_continue=should_continue,
            reason=reason,
        )

    def _count_independent_evidence(
        self,
        state: InvestigationState,
    ) -> int:

        evidence = state.evidence

        if evidence is None:
            return 0

        count = 0

        if evidence.logs:
            count += 1

        if evidence.metrics:
            count += 1

        if evidence.traces:
            count += 1

        domain_count = evidence.summary.get(
            "domain_evidence_count",
            0,
        )

        if domain_count > 0:
            count += 1

        return count

    def _build_reason(
        self,
        leading: Hypothesis,
        runner_up: Hypothesis | None,
        confidence_gap: float,
        independent_evidence_count: int,
        should_continue: bool,
    ) -> str:

        if runner_up is None:
            comparison = (
                "No competing hypothesis currently has "
                "meaningful confidence."
            )
        else:
            comparison = (
                f"'{leading.name}' leads "
                f"'{runner_up.name}' by "
                f"{confidence_gap:.2f} confidence."
            )

        evidence_text = (
            f"The investigation has "
            f"{independent_evidence_count} independent "
            f"evidence source(s)."
        )

        if should_continue:
            decision = (
                "More investigation is required because "
                "the evidence is not yet sufficiently "
                "confident and separated."
            )
        else:
            decision = (
                "The leading root-cause hypothesis has "
                "sufficient confidence, separation, and "
                "independent evidence to stop."
            )

        return (
            f"{comparison} "
            f"{evidence_text} "
            f"{decision}"
        )