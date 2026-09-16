from dataclasses import dataclass

from evidence.models import InvestigationEvidence

from hypothesis.models import (
    EvidenceReference,
    Hypothesis,
)


@dataclass(frozen=True)
class HypothesisRule:
    """
    Deterministic rule used to evaluate a hypothesis.
    """

    name: str
    category: str
    role: str

    required_signals: tuple[str, ...]
    supporting_signals: tuple[str, ...]
    contradicting_signals: tuple[str, ...]

    signal_weights: tuple[tuple[str, float], ...]

    specificity: float

    explanation: str
    severity: str


class HypothesisEngine:
    """
    Deterministic hypothesis generation and ranking engine.

    The engine intentionally separates:

    - direct evidence
    - derived signals
    - specificity
    - temporal support
    - contradictions

    This prevents multiple representations of the same
    failure from being incorrectly counted as independent
    proof.
    """

    def __init__(self):
        self.rules = self._build_rules()

    def analyze(
        self,
        evidence: InvestigationEvidence,
    ) -> list[Hypothesis]:

        hypotheses = []

        for rule in self.rules:

            hypothesis = self._evaluate_rule(
                rule,
                evidence,
            )

            if hypothesis is not None:
                hypotheses.append(
                    hypothesis
                )

        hypotheses.sort(
            key=lambda item: (
                item.score,
                item.confidence,
                self._role_priority(
                    item.role
                ),
            ),
            reverse=True,
        )

        return hypotheses

    # ==========================================================
    # RULE EVALUATION
    # ==========================================================

    def _evaluate_rule(
        self,
        rule: HypothesisRule,
        evidence: InvestigationEvidence,
    ) -> Hypothesis | None:

        signals = set(
            evidence.signals
        )

        required_matches = [
            signal
            for signal in rule.required_signals
            if signal in signals
        ]

        missing_required = [
            signal
            for signal in rule.required_signals
            if signal not in signals
        ]

        if missing_required:
            return None

        supporting_matches = [
            signal
            for signal in rule.supporting_signals
            if signal in signals
        ]

        contradicting_matches = [
            signal
            for signal in rule.contradicting_signals
            if signal in signals
        ]

        matched_signals = (
            required_matches
            + supporting_matches
        )

        # ------------------------------------------------------
        # Evidence score
        # ------------------------------------------------------

        evidence_score = (
            self._calculate_evidence_score(
                rule,
                matched_signals,
            )
        )

        # ------------------------------------------------------
        # Specificity
        # ------------------------------------------------------

        specificity_score = (
            rule.specificity
        )

        # ------------------------------------------------------
        # Temporal support
        # ------------------------------------------------------

        temporal_score = (
            self._calculate_temporal_score(
                evidence
            )
        )

        # ------------------------------------------------------
        # Contradictions
        # ------------------------------------------------------

        contradiction_penalty = (
            self._calculate_contradiction_penalty(
                rule,
                contradicting_matches,
            )
        )

        # ------------------------------------------------------
        # Final ranking score
        # ------------------------------------------------------

        score = (
            evidence_score * 0.55
            + specificity_score * 0.25
            + temporal_score * 0.10
            - contradiction_penalty * 0.10
        )

        score = max(
            0.0,
            min(
                1.0,
                score,
            ),
        )

        confidence = (
            self._confidence_from_score(
                score,
                evidence,
            )
        )

        supporting_evidence = (
            self._collect_supporting_evidence(
                matched_signals,
                evidence,
            )
        )

        contradicting_evidence = (
            self._collect_contradicting_evidence(
                contradicting_matches,
                evidence,
            )
        )

        return Hypothesis(
            name=rule.name,
            category=rule.category,
            role=rule.role,
            confidence=confidence,
            score=score,
            explanation=rule.explanation,
            supporting_evidence=(
                supporting_evidence
            ),
            contradicting_evidence=(
                contradicting_evidence
            ),
            matched_signals=matched_signals,
            missing_signals=missing_required,
            evidence_score=evidence_score,
            specificity_score=specificity_score,
            temporal_score=temporal_score,
            contradiction_penalty=contradiction_penalty,
            severity=rule.severity,
        )

    # ==========================================================
    # EVIDENCE SCORING
    # ==========================================================

    def _calculate_evidence_score(
        self,
        rule: HypothesisRule,
        matched_signals: list[str],
    ) -> float:

        weights = dict(
            rule.signal_weights
        )

        # We calculate weighted evidence using diminishing
        # returns. The first strong signal contributes fully,
        # subsequent related signals contribute less.
        contributions = []

        for signal in matched_signals:

            weight = weights.get(
                signal,
                1.0,
            )

            contributions.append(
                weight
            )

        contributions.sort(
            reverse=True
        )

        diminishing_factors = (
            1.0,
            0.60,
            0.35,
            0.20,
            0.10,
        )

        actual_score = 0.0
        maximum_score = 0.0

        all_positive_signals = (
            list(rule.required_signals)
            + list(rule.supporting_signals)
        )

        all_weights = sorted(
            [
                weights.get(
                    signal,
                    1.0,
                )
                for signal in all_positive_signals
            ],
            reverse=True,
        )

        for index, weight in enumerate(
            contributions
        ):

            factor = (
                diminishing_factors[index]
                if index
                < len(diminishing_factors)
                else 0.05
            )

            actual_score += (
                weight * factor
            )

        for index, weight in enumerate(
            all_weights
        ):

            factor = (
                diminishing_factors[index]
                if index
                < len(diminishing_factors)
                else 0.05
            )

            maximum_score += (
                weight * factor
            )

        if maximum_score == 0:
            return 0.0

        return min(
            1.0,
            actual_score / maximum_score,
        )

    # ==========================================================
    # TEMPORAL SCORING
    # ==========================================================

    @staticmethod
    def _calculate_temporal_score(
        evidence: InvestigationEvidence,
    ) -> float:

        if not evidence.temporal_correlations:
            return 0.0

        # Temporal correlation is useful supporting evidence,
        # but it is never allowed to dominate direct evidence.
        best_delta = min(
            item.delta_seconds
            for item
            in evidence.temporal_correlations
        )

        if best_delta <= 1:
            return 1.0

        if best_delta <= 2:
            return 0.8

        if best_delta <= 3:
            return 0.6

        if best_delta <= 5:
            return 0.4

        return 0.0

    # ==========================================================
    # CONTRADICTION SCORING
    # ==========================================================

    @staticmethod
    def _calculate_contradiction_penalty(
        rule: HypothesisRule,
        contradictions: list[str],
    ) -> float:

        if not contradictions:
            return 0.0

        weights = dict(
            rule.signal_weights
        )

        penalty = 0.0

        for signal in contradictions:

            penalty += (
                weights.get(
                    signal,
                    1.0,
                )
                * 0.20
            )

        return min(
            1.0,
            penalty,
        )

    # ==========================================================
    # CONFIDENCE
    # ==========================================================

    @staticmethod
    def _confidence_from_score(
        score: float,
        evidence: InvestigationEvidence,
    ) -> float:

        if score >= 0.85:
            confidence = 0.90

        elif score >= 0.70:
            confidence = 0.78

        elif score >= 0.55:
            confidence = 0.65

        elif score >= 0.40:
            confidence = 0.50

        elif score >= 0.25:
            confidence = 0.35

        else:
            confidence = 0.20

        evidence_sources = 0

        if evidence.logs:
            evidence_sources += 1

        if evidence.metrics:
            evidence_sources += 1

        if evidence.traces:
            evidence_sources += 1

        # Domain-specific tools (database, deployment, downstream, etc.)
        # are independent evidence sources.
        if evidence.summary.get("domain_evidence_count", 0) > 0:
            evidence_sources += 1

        if evidence_sources >= 3:
            confidence += 0.04

        elif evidence_sources == 2:
            confidence += 0.02

        return min(
            0.95,
            confidence,
        )

    # ==========================================================
    # RULES
    # ==========================================================

    @staticmethod
    def _build_rules():

        return [

            HypothesisRule(
                name="Invalid payment input",
                category="application_validation",
                role="root_cause",

                required_signals=(
                    "invalid_input",
                ),

                supporting_signals=(
                    "failure_metric",
                    "trace_error",
                    "trace_status_error",
                    "failed_operation",
                ),

                contradicting_signals=(),

                signal_weights=(
                    ("invalid_input", 5.0),
                    ("failure_metric", 1.0),
                    ("trace_error", 0.8),
                    ("trace_status_error", 0.6),
                    ("failed_operation", 0.6),
                ),

                specificity=1.0,

                explanation=(
                    "The payment request contains invalid "
                    "input, and multiple independent "
                    "observability sources confirm that the "
                    "request failed during application "
                    "processing. Direct invalid-input evidence "
                    "provides the strongest support for this "
                    "root-cause hypothesis."
                ),

                severity="medium",
            ),

            HypothesisRule(
                name="Application exception",
                category="application_error",
                role="mechanism",

                required_signals=(
                    "trace_error",
                ),

                supporting_signals=(
                    "trace_status_error",
                    "failure_metric",
                    "failed_operation",
                ),

                contradicting_signals=(
                    "invalid_input",
                ),

                signal_weights=(
                    ("trace_error", 2.0),
                    ("trace_status_error", 1.2),
                    ("failure_metric", 0.8),
                    ("failed_operation", 0.6),
                    ("invalid_input", 2.0),
                ),

                specificity=0.55,

                explanation=(
                    "The application generated an exception "
                    "during request processing. Trace telemetry "
                    "confirms the error mechanism, but the "
                    "presence of more specific invalid-input "
                    "evidence indicates that the exception is "
                    "a consequence rather than the underlying "
                    "root cause."
                ),

                severity="high",
            ),

            HypothesisRule(
                name="Database dependency unavailable",
                category="database_failure",
                role="root_cause",

                required_signals=(
                    "database_connection_failure",
                ),

                supporting_signals=(
                    "database_unavailable",
                    "error_log",
                ),

                contradicting_signals=(),

                signal_weights=(
                    ("database_connection_failure", 5.0),
                    ("database_unavailable", 1.5),
                    ("error_log", 0.5),
                ),

                specificity=0.95,

                explanation=(
                    "The database investigation reports that the database "
                    "dependency is unavailable because its connection was "
                    "refused. This is more specific than the service-level "
                    "failure symptom and provides a direct dependency-level "
                    "root-cause hypothesis."
                ),

                severity="high",
            ),

            HypothesisRule(
                name="Service-level failure",
                category="service_failure",
                role="symptom",

                required_signals=(
                    "failure_metric",
                ),

                supporting_signals=(
                    "trace_error",
                    "trace_status_error",
                    "failed_operation",
                ),

                contradicting_signals=(),

                signal_weights=(
                    ("failure_metric", 1.5),
                    ("trace_error", 0.7),
                    ("trace_status_error", 0.5),
                    ("failed_operation", 0.5),
                ),

                specificity=0.25,

                explanation=(
                    "The service recorded a failed operation "
                    "and corresponding error telemetry. This "
                    "confirms the observed failure but remains "
                    "a broad symptom rather than a specific "
                    "root-cause explanation."
                ),

                severity="high",
            ),
        ]

    # ==========================================================
    # EVIDENCE REFERENCES
    # ==========================================================

    def _collect_supporting_evidence(
        self,
        signals: list[str],
        evidence: InvestigationEvidence,
    ):

        references = []

        if "invalid_input" in signals:

            references.append(
                EvidenceReference(
                    evidence_type="signal",
                    identifier="invalid_input",
                    description=(
                        "Evidence contains an explicit "
                        "invalid-input signal derived from "
                        "structured request or exception data."
                    ),
                    strength="direct",
                )
            )

            # Preserve the actual exception message.
            for trace in evidence.traces:

                for span in trace.spans:

                    for trace_log in span.logs:

                        message = trace_log.fields.get(
                            "exception.message"
                        )

                        if message:

                            references.append(
                                EvidenceReference(
                                    evidence_type="exception",
                                    identifier=span.span_id,
                                    description=(
                                        f"Exception message: {message}"
                                    ),
                                    strength="direct",
                                )
                            )

        if "database_connection_failure" in signals:
            domain = evidence.summary.get("domain_evidence", [])
            database_name = "unknown_database"
            error = "database connection failure"

            if domain:
                first = domain[0]
                database_name = str(first.get("database", database_name))
                error = str(first.get("error", error))

            references.append(
                EvidenceReference(
                    evidence_type="database",
                    identifier=database_name,
                    description=(
                        f"Database dependency '{database_name}' reported "
                        f"a connection failure: {error}."
                    ),
                    strength="direct",
                )
            )

        if "database_unavailable" in signals:
            references.append(
                EvidenceReference(
                    evidence_type="database",
                    identifier="database_unavailable",
                    description=(
                        "The domain-specific database investigation "
                        "reported the dependency as unavailable."
                    ),
                    strength="supporting",
                )
            )

        if "failure_metric" in signals:

            references.append(
                EvidenceReference(
                    evidence_type="metric",
                    identifier=self._first_metric_name(
                        evidence,
                        "failure",
                    ),
                    description=(
                        "A failure-related application "
                        "metric was observed."
                    ),
                    strength="supporting",
                )
            )

        if "trace_error" in signals:

            references.append(
                EvidenceReference(
                    evidence_type="trace",
                    identifier=self._first_trace_id(
                        evidence
                    ),
                    description=(
                        "A trace span is explicitly marked "
                        "as an error."
                    ),
                    strength="supporting",
                )
            )

        if "trace_status_error" in signals:

            references.append(
                EvidenceReference(
                    evidence_type="trace",
                    identifier=self._first_trace_id(
                        evidence
                    ),
                    description=(
                        "The trace span has an ERROR status."
                    ),
                    strength="supporting",
                )
            )

        if "failed_operation" in signals:

            references.append(
                EvidenceReference(
                    evidence_type="span",
                    identifier=self._first_span_id(
                        evidence
                    ),
                    description=(
                        "A trace span records a failed "
                        "operation."
                    ),
                    strength="supporting",
                )
            )

        return references

    def _collect_contradicting_evidence(
        self,
        signals: list[str],
        evidence: InvestigationEvidence,
    ):

        references = []

        if "invalid_input" in signals:

            references.append(
                EvidenceReference(
                    evidence_type="signal",
                    identifier="invalid_input",
                    description=(
                        "The incident contains explicit "
                        "evidence of invalid input."
                    ),
                    strength="contradicting",
                )
            )

        return references

    # ==========================================================
    # HELPERS
    # ==========================================================

    @staticmethod
    def _role_priority(role: str):

        return {
            "root_cause": 3,
            "mechanism": 2,
            "symptom": 1,
        }.get(
            role,
            0,
        )

    @staticmethod
    def _first_metric_name(
        evidence,
        keyword,
    ):

        for metric in evidence.metrics:

            name = metric.metric.get(
                "__name__",
                "",
            )

            if keyword in name.lower():
                return name

        return "unknown_metric"

    @staticmethod
    def _first_trace_id(
        evidence,
    ):

        if evidence.trace_ids:
            return sorted(
                evidence.trace_ids
            )[0]

        return "unknown_trace"

    @staticmethod
    def _first_span_id(
        evidence,
    ):

        if evidence.span_ids:
            return sorted(
                evidence.span_ids
            )[0]

        return "unknown_span"