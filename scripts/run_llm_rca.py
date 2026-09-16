import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from agent.llm.context import build_llm_context
from agent.llm.factory import create_llm_client
from agent.llm.reasoner import LLMReasoner
from agent.state import InvestigationState
from agent.uncertainty import UncertaintyAnalyzer
from evidence.engine import EvidenceEngine
from hypothesis.engine import HypothesisEngine


def main():
    service = "payment-service"

    incident = (
        "Payment request req-59266 failed "
        "with an HTTP 400 response."
    )

    state = InvestigationState(
        incident=incident,
        service=service,
    )

    # ------------------------------------------------------------------
    # Simulated MCP results
    #
    # These intentionally use the same high-level result structure
    # consumed by EvidenceEngine.
    # ------------------------------------------------------------------

    log_result = {
        "results": [
            {
                "timestamp": "2026-09-14T00:00:00Z",
                "service": service,
                "level": "ERROR",
                "message": (
                    "payment_request failed "
                    "request_id=req-59266 amount=-10"
                ),
                "request_id": "req-59266",
                "trace_id": (
                    "f83d1eadb5451abfe8f913cead3922d9"
                ),
            }
        ]
    }

    metric_results = [
    {
        "metric": {
            "__name__": "payment_failures_total"
        },
        "value": 1,
        "query": "payment_failures_total",
    }
]

    trace_result = {
        "results": [
            {
                "trace_id": (
                    "f83d1eadb5451abfe8f913cead3922d9"
                ),
                "spans": [
                    {
                        "trace_id": (
                            "f83d1eadb5451abfe8f913cead3922d9"
                        ),
                        "span_id": "1004bb8f5fedc21b",
                        "operation": "POST /payments",
                        "start_time": 0,
                        "duration": 100,
                        "tags": {
                            "payment.amount": -10,
                            "payment.request_id": "req-59266",
                            "payment.status": "failed",
                            "otel.status_code": "ERROR",
                            "error": True,
                            "otel.status_description": (
                                "HTTPException: 400: "
                                "Payment amount must be greater "
                                "than zero."
                            ),
                        },
                        "logs": [],
                    }
                ],
            }
        ]
    }

    # ------------------------------------------------------------------
    # Deterministic evidence construction
    # ------------------------------------------------------------------

    evidence_engine = EvidenceEngine()

    evidence = evidence_engine.build(
        service=service,
        log_result=log_result,
        metric_results=metric_results,
        trace_result=trace_result,
    )

    state.evidence = evidence
    
    print()
    print("DEBUG — DETERMINISTIC EVIDENCE")
    print("Logs:", len(evidence.logs))
    print("Metrics:", len(evidence.metrics))
    print("Traces:", len(evidence.traces))
    print("Signals:", evidence.signals)
    print("Summary:", evidence.summary)

    # ------------------------------------------------------------------
    # Deterministic hypothesis generation
    # ------------------------------------------------------------------

    hypothesis_engine = HypothesisEngine()

    state.hypotheses = hypothesis_engine.analyze(
        evidence
    )
    print()
    print("DEBUG — HYPOTHESES")

    for hypothesis in state.hypotheses:
        print(
            f"  {hypothesis.name} | "
            f"role={hypothesis.role} | "
            f"confidence={hypothesis.confidence:.2f}"
        )

    # ------------------------------------------------------------------
    # Deterministic uncertainty assessment
    # ------------------------------------------------------------------

    uncertainty = UncertaintyAnalyzer().assess(
        state
    )

    # ------------------------------------------------------------------
    # Build the controlled context supplied to the LLM
    # ------------------------------------------------------------------

    context = build_llm_context(
        state,
        uncertainty,
    )

    # ------------------------------------------------------------------
    # LLM reasoning
    # ------------------------------------------------------------------

    client = create_llm_client()

    reasoner = LLMReasoner(client)

    result = reasoner.reason(
        incident=context["incident"],
        service=context["service"],
        evidence_summary=context["evidence_summary"],
        hypotheses=context["hypotheses"],
        uncertainty=context["uncertainty"],
        investigation_history=context[
            "investigation_history"
        ],
    )

    # ------------------------------------------------------------------
    # Display result
    # ------------------------------------------------------------------

    print()
    print("=" * 60)
    print("DEVRESCUE — LLM ROOT CAUSE ANALYSIS")
    print("=" * 60)

    print()
    print("Incident:")
    print(incident)

    print()
    print("Service:")
    print(service)

    print()
    print("Deterministic leading hypothesis:")

    if state.hypotheses:
        leading = state.hypotheses[0]

        print(
            f"  {leading.name} "
            f"(confidence={leading.confidence:.2f})"
        )
    else:
        print("  None")

    print()
    print("Uncertainty:")
    print(f"  {uncertainty.uncertainty:.2f}")

    print()
    print("LLM conclusion:")
    print(f"  {result.conclusion}")

    print()
    print("LLM confidence:")
    print(f"  {result.confidence:.2f}")

    print()
    print("Reasoning:")
    print(result.reasoning)

    print()
    print("Supporting evidence:")

    if result.supporting_evidence:
        for item in result.supporting_evidence:
            print(f"  ✓ {item}")
    else:
        print("  None")

    print()
    print("Contradicting evidence:")

    if result.contradicting_evidence:
        for item in result.contradicting_evidence:
            print(f"  ! {item}")
    else:
        print("  None")

    print()
    print("Missing evidence:")

    if result.missing_evidence:
        for item in result.missing_evidence:
            print(f"  ? {item}")
    else:
        print("  None")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()