from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class LogEvidence:
    timestamp: str
    service: Optional[str]
    level: Optional[str]
    message: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    request_id: Optional[str] = None


@dataclass(frozen=True)
class MetricEvidence:
    metric: dict[str, Any]
    value: Any
    query: str


@dataclass(frozen=True)
class TraceLogEvidence:
    timestamp: Optional[int]
    fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanEvidence:
    trace_id: str
    span_id: str
    operation: Optional[str]
    start_time: Optional[int]
    duration: Optional[int]
    tags: dict[str, Any] = field(default_factory=dict)
    logs: list[TraceLogEvidence] = field(default_factory=list)


@dataclass
class TraceEvidence:
    trace_id: str
    spans: list[SpanEvidence] = field(default_factory=list)


@dataclass(frozen=True)
class Correlation:
    source: str
    target: str
    key: str
    value: str
    description: str


@dataclass(frozen=True)
class TemporalCorrelation:
    source: str
    target: str
    source_time: float
    target_time: float
    delta_seconds: float
    description: str


@dataclass
class InvestigationEvidence:
    service: str
    logs: list[LogEvidence] = field(default_factory=list)
    metrics: list[MetricEvidence] = field(default_factory=list)
    traces: list[TraceEvidence] = field(default_factory=list)
    correlations: list[Correlation] = field(default_factory=list)
    temporal_correlations: list[TemporalCorrelation] = field(default_factory=list)
    request_ids: set[str] = field(default_factory=set)
    trace_ids: set[str] = field(default_factory=set)
    span_ids: set[str] = field(default_factory=set)
    signals: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)