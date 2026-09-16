from dataclasses import dataclass
from typing import Any

from hypothesis.models import Hypothesis
from agent.state import InvestigationState


@dataclass(frozen=True)
class EvidenceValueScore:
    """
    Deterministic estimate of how valuable an investigation action is.
    """

    tool: str
    score: float

    relevance: float
    discrimination: float
    specificity: float
    novelty: float
    cost: float

    reason: str


class EvidenceValueScorer:
    """
    Scores candidate investigation actions according to their expected
    information value.

    This is intentionally deterministic. No LLM is involved.
    """

    TOOL_COSTS = {
        "get_service_health": 0.1,
        "search_logs": 0.2,
        "find_traces": 0.3,
        "query_metrics": 0.2,
        "investigate_database": 0.4,
    }

    def score(
        self,
        tool: str,
        hypothesis: Hypothesis,
        state: InvestigationState,
    ) -> EvidenceValueScore:

        relevance = self._relevance(
            tool=tool,
            hypothesis=hypothesis,
        )

        discrimination = self._discrimination(
            tool=tool,
            hypotheses=state.hypotheses,
        )

        specificity = self._specificity(
            tool=tool,
            hypothesis=hypothesis,
        )

        novelty = self._novelty(
            tool=tool,
            state=state,
        )

        cost = self.TOOL_COSTS.get(
            tool,
            0.5,
        )

        # -----------------------------------------------------
        # Information value
        # -----------------------------------------------------
        #
        # Positive factors:
        #   relevance
        #   discrimination
        #   specificity
        #   novelty
        #
        # Cost is a penalty.
        # -----------------------------------------------------

        raw_score = (
            relevance * 0.30
            + discrimination * 0.35
            + specificity * 0.20
            + novelty * 0.15
            - cost * 0.10
        )

        score = max(
            0.0,
            min(1.0, raw_score),
        )

        reason = self._build_reason(
            tool=tool,
            relevance=relevance,
            discrimination=discrimination,
            specificity=specificity,
            novelty=novelty,
            cost=cost,
        )

        return EvidenceValueScore(
            tool=tool,
            score=score,
            relevance=relevance,
            discrimination=discrimination,
            specificity=specificity,
            novelty=novelty,
            cost=cost,
            reason=reason,
        )

    def _relevance(
        self,
        tool: str,
        hypothesis: Hypothesis,
    ) -> float:

        if hypothesis.category == "database_failure":
            if tool == "investigate_database":
                return 1.0

            if tool in {
                "search_logs",
                "find_traces",
            }:
                return 0.7

            if tool == "query_metrics":
                return 0.5

        if hypothesis.category == "application_validation":
            if tool == "find_traces":
                return 1.0

            if tool == "search_logs":
                return 0.8

            if tool == "query_metrics":
                return 0.5

        if hypothesis.category == "application_error":
            if tool == "search_logs":
                return 1.0

            if tool == "find_traces":
                return 0.9

            if tool == "query_metrics":
                return 0.5

        return 0.5

    def _discrimination(
        self,
        tool: str,
        hypotheses: list[Hypothesis],
    ) -> float:

        if len(hypotheses) < 2:
            return 0.3

        categories = {
            hypothesis.category
            for hypothesis in hypotheses[:3]
        }

        # Database investigation is particularly useful when
        # database failure competes with application failure.
        if tool == "investigate_database":
            if {
                "database_failure",
                "application_error",
            }.issubset(categories):
                return 1.0

            if "database_failure" in categories:
                return 0.8

        if tool == "find_traces":
            if "application_error" in categories:
                return 0.8

        if tool == "search_logs":
            if "application_error" in categories:
                return 0.8

        if tool == "query_metrics":
            return 0.5

        return 0.4

    def _specificity(
        self,
        tool: str,
        hypothesis: Hypothesis,
    ) -> float:

        if tool == "investigate_database":
            return 1.0 if hypothesis.category == "database_failure" else 0.6

        if tool == "find_traces":
            return 0.9

        if tool == "search_logs":
            return 0.7

        if tool == "query_metrics":
            return 0.5

        return 0.5

    def _novelty(
        self,
        tool: str,
        state: InvestigationState,
    ) -> float:

        if tool not in state.tool_history:
            return 1.0

        return 0.0

    def _build_reason(
        self,
        tool: str,
        relevance: float,
        discrimination: float,
        specificity: float,
        novelty: float,
        cost: float,
    ) -> str:

        factors: list[str] = []

        if relevance >= 0.8:
            factors.append("high relevance")

        if discrimination >= 0.8:
            factors.append(
                "strong ability to distinguish competing hypotheses"
            )

        if specificity >= 0.8:
            factors.append("high specificity")

        if novelty >= 0.8:
            factors.append("new evidence source")

        if not factors:
            factors.append("moderate expected information value")

        return (
            f"{tool} is valuable because it provides "
            + ", ".join(factors)
            + "."
        )