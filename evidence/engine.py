import json
from typing import Any
from datetime import datetime, timezone
from evidence.models import (
    Correlation,
    InvestigationEvidence,
    LogEvidence,
    MetricEvidence,
    SpanEvidence,
    TemporalCorrelation,
    TraceEvidence,
    TraceLogEvidence,
)


class EvidenceEngine:
    """
    Deterministic engine for normalizing, deduplicating,
    correlating, and summarizing observability evidence.
    """

    def build(
        self,
        service: str,
        log_result: dict[str, Any] | None = None,
        metric_results: list[dict[str, Any]] | None = None,
        trace_result: dict[str, Any] | None = None,
    ) -> InvestigationEvidence:

        evidence = InvestigationEvidence(
            service=service
        )

        self._add_logs(
            evidence,
            log_result or {},
        )

        self._add_metrics(
            evidence,
            metric_results or [],
        )

        self._add_traces(
            evidence,
            trace_result or {},
        )

        self._deduplicate(
            evidence
        )

        self._correlate(
            evidence
        )

        self._classify_signals(
            evidence
        )
        
        self._correlate_temporally(
            evidence
        )

        self._build_summary(
            evidence
        )

        return evidence

    # ---------------------------------------------------------
    # Normalization
    # ---------------------------------------------------------

    def _add_logs(
        self,
        evidence: InvestigationEvidence,
        result: dict[str, Any],
    ) -> None:

        for item in result.get("results", []):

            log = LogEvidence(
                timestamp=str(
                    item.get("timestamp", "")
                ),
                service=item.get("service"),
                level=item.get("level"),
                message=item.get("message", ""),
                trace_id=item.get("trace_id"),
                span_id=item.get("span_id"),
                request_id=item.get("request_id"),
            )

            evidence.logs.append(log)

            self._register_identifiers(
                evidence,
                request_id=log.request_id,
                trace_id=log.trace_id,
                span_id=log.span_id,
            )

    def _add_metrics(
        self,
        evidence: InvestigationEvidence,
        metric_results: list[dict[str, Any]],
    ) -> None:

        for result in metric_results:

            metric = MetricEvidence(
                metric=result.get(
                    "metric",
                    {}
                ),
                value=result.get(
                    "value"
                ),
                query=result.get(
                    "query",
                    ""
                ),
            )

            evidence.metrics.append(
                metric
            )

    def _add_traces(
        self,
        evidence: InvestigationEvidence,
        result: dict[str, Any],
    ) -> None:

        for trace_data in result.get(
            "results",
            []
        ):

            trace_id = trace_data.get(
                "trace_id"
            )

            if not trace_id:
                continue

            trace = TraceEvidence(
                trace_id=trace_id
            )

            evidence.trace_ids.add(
                trace_id
            )

            for span_data in trace_data.get(
                "spans",
                []
            ):

                span = SpanEvidence(
                    trace_id=trace_id,
                    span_id=span_data.get(
                        "span_id",
                        ""
                    ),
                    operation=span_data.get(
                        "operation"
                    ),
                    start_time=span_data.get(
                        "start_time"
                    ),
                    duration=span_data.get(
                        "duration"
                    ),
                    tags=span_data.get(
                        "tags",
                        {},
                    ),
                )

                if span.span_id:
                    evidence.span_ids.add(
                        span.span_id
                    )

                # Generic identifier discovery
                request_id = self._find_identifier(
                    span.tags,
                    [
                        "request_id",
                        "http.request_id",
                        "payment.request_id",
                        "correlation_id",
                    ],
                )

                if request_id:
                    evidence.request_ids.add(
                        str(request_id)
                    )

                for log_data in span_data.get(
                    "logs",
                    []
                ):

                    span_log = TraceLogEvidence(
                        timestamp=log_data.get(
                            "timestamp"
                        ),
                        fields=log_data.get(
                            "fields",
                            {},
                        ),
                    )

                    span.logs.append(
                        span_log
                    )

                trace.spans.append(
                    span
                )

            evidence.traces.append(
                trace
            )

    # ---------------------------------------------------------
    # Deduplication
    # ---------------------------------------------------------

    def _deduplicate(self, evidence):
        # Deduplicate logs.
        evidence.logs = list(dict.fromkeys(evidence.logs))

        # Deduplicate metrics using a deterministic JSON representation
        # because MetricEvidence contains a dictionary.
        unique_metrics = {}
        for metric in evidence.metrics:
            metric_key = (
                json.dumps(
                    metric.metric,
                    sort_keys=True,
                    default=str,
                ),
                json.dumps(
                    metric.value,
                    sort_keys=True,
                    default=str,
                ),
                metric.query,
            )
            unique_metrics[metric_key] = metric

        evidence.metrics = list(unique_metrics.values())

        # Deduplicate traces by trace ID while preserving the latest
        # complete trace object for now.
        unique_traces = {}
        for trace in evidence.traces:
            unique_traces[trace.trace_id] = trace

        evidence.traces = list(unique_traces.values())

        # Deduplicate spans within each trace.
        for trace in evidence.traces:
            unique_spans = {}
            for span in trace.spans:
                unique_spans[span.span_id] = span

            trace.spans = list(unique_spans.values())
    # ---------------------------------------------------------
    # Correlation
    # ---------------------------------------------------------

    def _correlate(
        self,
        evidence: InvestigationEvidence,
    ) -> None:

        correlations = []

        for log in evidence.logs:

            if log.trace_id:
                correlations.append(
                    Correlation(
                        source="log",
                        target="trace",
                        key="trace_id",
                        value=log.trace_id,
                        description=(
                            "Log is associated with "
                            f"trace {log.trace_id}."
                        ),
                    )
                )

            if log.span_id:
                correlations.append(
                    Correlation(
                        source="log",
                        target="span",
                        key="span_id",
                        value=log.span_id,
                        description=(
                            "Log is associated with "
                            f"span {log.span_id}."
                        ),
                    )
                )

            if log.request_id:
                correlations.append(
                    Correlation(
                        source="log",
                        target="request",
                        key="request_id",
                        value=log.request_id,
                        description=(
                            "Log belongs to request "
                            f"{log.request_id}."
                        ),
                    )
                )

        for trace in evidence.traces:

            for span in trace.spans:

                identifiers = self._extract_identifiers(
                    span.tags
                )

                for key, value in identifiers.items():

                    if key == "request_id":

                        correlations.append(
                            Correlation(
                                source="trace",
                                target="request",
                                key=key,
                                value=value,
                                description=(
                                    "Trace span is associated "
                                    f"with request {value}."
                                ),
                            )
                        )

                    elif key == "trace_id":

                        correlations.append(
                            Correlation(
                                source="span",
                                target="trace",
                                key=key,
                                value=value,
                                description=(
                                    "Span belongs to trace "
                                    f"{value}."
                                ),
                            )
                        )

        # Remove duplicate correlations
        evidence.correlations = list(
            dict.fromkeys(
                correlations
            )
        )

    # ---------------------------------------------------------
    # Signal classification
    # ---------------------------------------------------------

    def _classify_signals(self, evidence):
        signals = []

        # --------------------------------------------------
        # Log signals
        # --------------------------------------------------

        for log in evidence.logs:
            message = log.message.lower()

            if (
                log.level
                and log.level.upper()
                in {"ERROR", "CRITICAL"}
            ):
                signals.append("error_log")

            if "failed" in message:
                signals.append("failure_log")

            if "invalid" in message:
                signals.append("invalid_input")

            if "exception" in message:
                signals.append("exception_log")

        # --------------------------------------------------
        # Metric signals
        # --------------------------------------------------

        for metric in evidence.metrics:
            metric_name = (
                metric.metric
                .get("__name__", "")
                .lower()
            )

            if "failure" in metric_name:
                signals.append("failure_metric")

            if "error" in metric_name:
                signals.append("error_metric")

        # --------------------------------------------------
        # Trace / span signals
        # --------------------------------------------------

        for trace in evidence.traces:
            for span in trace.spans:

                tags = span.tags

                if tags.get("error") is True:
                    signals.append(
                        "trace_error"
                    )

                if (
                    tags.get("otel.status_code")
                    == "ERROR"
                ):
                    signals.append(
                        "trace_status_error"
                    )

                if (
                    tags.get("payment.status")
                    == "failed"
                ):
                    signals.append(
                        "failed_operation"
                    )

                # Structured invalid-input detection
                amount = tags.get(
                    "payment.amount"
                )

                if (
                    isinstance(amount, (int, float))
                    and amount <= 0
                ):
                    signals.append(
                        "invalid_input"
                    )

                # Exception evidence
                for trace_log in span.logs:

                    fields = trace_log.fields

                    exception_type = str(
                        fields.get(
                            "exception.type",
                            "",
                        )
                    ).lower()

                    exception_message = str(
                        fields.get(
                            "exception.message",
                            "",
                        )
                    ).lower()

                    if exception_type:
                        signals.append(
                            "exception_log"
                        )

                    if (
                        "must be greater than zero"
                        in exception_message
                    ):
                        signals.append(
                            "invalid_input"
                        )

                    if (
                        "invalid"
                        in exception_message
                    ):
                        signals.append(
                            "invalid_input"
                        )

        evidence.signals = list(
            dict.fromkeys(signals)
        )

    def _correlate_temporally(self, evidence):
        """
        Correlate logs and trace spans that occurred within a
        short time window.

        Temporal correlation is intentionally conservative.
        It does not claim causality. It only records that two
        pieces of evidence occurred close together in time.
        """

        WINDOW_SECONDS = 5.0

        temporal_correlations = []

        log_times = []

        for log in evidence.logs:
            timestamp = self._parse_timestamp(log.timestamp)

            if timestamp is not None:
                log_times.append(
                    (
                        log,
                        timestamp,
                    )
                )

        span_times = []

        for trace in evidence.traces:
            for span in trace.spans:
                if span.start_time is None:
                    continue

                timestamp = self._parse_timestamp(
                    span.start_time
                )

                if timestamp is not None:
                    span_times.append(
                        (
                            span,
                            timestamp,
                        )
                    )

        for log, log_time in log_times:
            for span, span_time in span_times:

                delta = abs(
                    log_time - span_time
                )

                if delta > WINDOW_SECONDS:
                    continue

                # Avoid creating a weak temporal relationship
                # when the log and span are already clearly
                # unrelated by identifiers.
                if (
                    log.trace_id
                    and log.trace_id != span.trace_id
                ):
                    continue

                temporal_correlations.append(
                    TemporalCorrelation(
                        source="log",
                        target="span",
                        source_time=log_time,
                        target_time=span_time,
                        delta_seconds=round(delta, 6),
                        description=(
                            "Log and trace span occurred "
                            f"within {round(delta, 3)} seconds."
                        ),
                    )
                )

        evidence.temporal_correlations = list(
            dict.fromkeys(
                temporal_correlations
            )
        )

    @staticmethod
    def _parse_timestamp(value):
        """
        Convert supported timestamps into Unix seconds.

        Supports:
        - ISO-8601 strings
        - Unix seconds
        - Unix milliseconds
        - Unix microseconds
        - Unix nanoseconds
        """

        if value is None:
            return None

        if isinstance(value, (int, float)):

            timestamp = float(value)

            # Jaeger timestamps are normally microseconds.
            if timestamp > 1e17:
                return timestamp / 1e9

            if timestamp > 1e14:
                return timestamp / 1e6

            if timestamp > 1e11:
                return timestamp / 1e3

            return timestamp

        value = str(value).strip()

        if not value:
            return None

        try:
            numeric = float(value)
            return EvidenceEngine._parse_timestamp(
                numeric
            )
        except ValueError:
            pass

        try:
            normalized = value.replace(
                "Z",
                "+00:00",
            )

            parsed = datetime.fromisoformat(
                normalized
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed.timestamp()

        except ValueError:
            return None

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    def _build_summary(
        self,
        evidence: InvestigationEvidence,
    ) -> None:

        failed_spans = []

        for trace in evidence.traces:

            for span in trace.spans:

                if (
                    span.tags.get("error") is True
                    or span.tags.get(
                        "otel.status_code"
                    ) == "ERROR"
                ):
                    failed_spans.append(
                        span
                    )

        evidence.summary = {
            "service": evidence.service,
            "log_count": len(
                evidence.logs
            ),
            "metric_count": len(
                evidence.metrics
            ),
            "trace_count": len(
                evidence.traces
            ),
            "span_count": sum(
                len(trace.spans)
                for trace in evidence.traces
            ),
            "failed_span_count": len(
                failed_spans
            ),
            "request_count": len(
                evidence.request_ids
            ),
            "trace_id_count": len(
                evidence.trace_ids
            ),
            "signal_count": len(
                evidence.signals
            ),
            "temporal_correlation_count": len(
                evidence.temporal_correlations
            ),
            "signals": evidence.signals,
        }

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _register_identifiers(
        evidence: InvestigationEvidence,
        request_id: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
    ) -> None:

        if request_id:
            evidence.request_ids.add(
                str(request_id)
            )

        if trace_id:
            evidence.trace_ids.add(
                str(trace_id)
            )

        if span_id:
            evidence.span_ids.add(
                str(span_id)
            )

    @staticmethod
    def _find_identifier(
        data: dict[str, Any],
        candidates: list[str],
    ) -> Any:

        for candidate in candidates:

            if candidate in data:
                return data[candidate]

        return None

    @staticmethod
    def _extract_identifiers(
        data: dict[str, Any],
    ) -> dict[str, str]:

        identifiers = {}

        for key, value in data.items():

            normalized = key.lower()

            if normalized.endswith(
                "request_id"
            ):
                identifiers[
                    "request_id"
                ] = str(value)

            elif normalized == "trace_id":
                identifiers[
                    "trace_id"
                ] = str(value)

        return identifiers