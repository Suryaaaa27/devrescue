from __future__ import annotations
import sys
from pathlib import Path

from agent.investigator import InvestigationAgent
from agent.mcp.registry import build_mcp_tools


from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.models import (
    InvestigationCreate,
    InvestigationStartResponse,
    InvestigationSummary,
)

from api.store import (
    get_all_investigations,
    get_investigation,
    save_investigation,
)


app = FastAPI(
    title="DevRescue API",
    version="1.0.0",
    description="HTTP API for the DevRescue reliability platform.",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "devrescue-api",
    }


@app.get(
    "/api/investigations",
    response_model=list[InvestigationSummary],
)
def list_investigations() -> list[InvestigationSummary]:
    return [
        InvestigationSummary(**item)
        for item in get_all_investigations()
    ]


@app.get(
    "/api/investigations/{investigation_id}",
)
def get_investigation_endpoint(
    investigation_id: str,
):
    investigation = get_investigation(
        investigation_id
    )

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    return investigation


@app.post(
    "/api/investigations",
    response_model=InvestigationSummary,
)
def create_investigation(
    payload: InvestigationCreate,
) -> InvestigationSummary:
    investigation_id = (
        f"INV-{uuid4().hex[:8].upper()}"
    )

    timestamp = now()

    investigation = {
        "id": investigation_id,
        "service": payload.service,
        "environment": payload.environment,
        "status": "created",
        "confidence": 0.0,
        "currentStage": "Created",
        "createdAt": timestamp,
        "updatedAt": timestamp,

        "input": payload.model_dump(),

        "evidence": [],
        "hypotheses": [],
        "timeline": [],
        "activity": [],
        "rootCause": None,
        "remediation": None,
    }

    save_investigation(
        investigation_id,
        investigation,
    )

    return InvestigationSummary(
        id=investigation_id,
        service=payload.service,
        environment=payload.environment,
        status="created",
        confidence=0.0,
        currentStage="Created",
        createdAt=timestamp,
        updatedAt=timestamp,
    )



@app.post(
    "/api/investigations/{investigation_id}/start",
    response_model=InvestigationStartResponse,
)
def start_investigation(investigation_id: str):
    investigation = get_investigation(investigation_id)

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found.",
        )

    if investigation.get("status") == "investigating":
        raise HTTPException(
            status_code=409,
            detail="This investigation is already running.",
        )

    investigation["status"] = "investigating"
    investigation["currentStage"] = "Collecting evidence"
    investigation["updatedAt"] = now()
    investigation["activity"] = [
        {
            "id": "activity-start",
            "tool": "InvestigationAgent",
            "action": "Started adaptive investigation using the configured MCP tools.",
            "status": "running",
            "timestamp": now(),
        }
    ]
    save_investigation(investigation_id, investigation)

    try:
        project_root = str(Path(__file__).resolve().parents[1])

        tools = build_mcp_tools(
           python_executable=sys.executable,
           project_root=project_root,
        )

        agent = InvestigationAgent(
            tools=tools,
            max_iterations=4,
        )

        input_data = investigation.get("input", {})

        description = str(
            input_data.get("description", "")
        ).strip()

        error_message = str(
            input_data.get("error", "") or ""
        ).strip()

        incident = description

        if error_message:
            incident = (
                f"{description}\nObserved error: {error_message}"
            ).strip()

        if not incident:
            incident = (
                f"Investigate the failure affecting "
                f"{investigation['service']} in "
                f"{investigation['environment']}."
            )

        result = agent.investigate(
            incident=incident,
            service=investigation["service"],
        )

        evidence_summary = result.evidence_summary or {}
        hypotheses = result.hypotheses or []
        tools_called = result.tools_called or []

        # Convert actual tool executions into workspace activity.
        activity = [
            {
                "id": f"activity-{index}",
                "tool": tool_name,
                "action": (
                    f"Executed {tool_name} as part of the investigation."
                ),
                "status": "completed",
                "timestamp": now(),
            }
            for index, tool_name in enumerate(tools_called, start=1)
        ]

        # Convert observed domain evidence into workspace cards.
        evidence = []

        domain_evidence = evidence_summary.get(
            "domain_evidence", []
        )

        for index, item in enumerate(domain_evidence, start=1):
            evidence.append(
                {
                    "id": f"evidence-{index}",
                    "title": str(
                        item.get("tool", "MCP observation")
                    ),
                    "source": str(
                        item.get("service", investigation["service"])
                    ),
                    "description": "; ".join(
                        f"{key}: {value}"
                        for key, value in item.items()
                        if key not in {"tool", "service"}
                        and value is not None
                    ) or "MCP tool returned an observation.",
                    "status": str(item.get("status", "observed")),
                }
            )

        for signal_index, signal in enumerate(
            evidence_summary.get("signals", []),
            start=1,
        ):
            evidence.append(
                {
                    "id": f"signal-{signal_index}",
                    "title": str(signal).replace("_", " ").title(),
                    "source": "Evidence engine",
                    "description": (
                        f"Detected investigation signal: {signal}"
                    ),
                    "status": "observed",
                }
            )

        root_cause = getattr(result, "root_cause", None)
        confidence = float(
            getattr(result, "confidence", 0.0) or 0.0
        )

        investigation["confidence"] = confidence
        investigation["evidence"] = evidence
        investigation["hypotheses"] = hypotheses
        investigation["activity"] = activity
        investigation["timeline"] = activity
        investigation["rootCause"] = (
            {
                "title": root_cause,
                "explanation": getattr(
                    result, "explanation", None
                ),
                "confidence": confidence,
            }
            if root_cause
            else None
        )
        investigation["investigationResult"] = {
            "status": result.status,
            "iterations": result.iterations,
            "toolsCalled": tools_called,
            "evidenceSummary": evidence_summary,
            "rootCause": root_cause,
            "explanation": getattr(result, "explanation", None),
        }

        if root_cause:
            investigation["status"] = "completed"
            investigation["currentStage"] = "Root cause"
        else:
            investigation["status"] = "incomplete"
            investigation["currentStage"] = (
                "Collecting evidence"
            )

        investigation["updatedAt"] = now()
        save_investigation(investigation_id, investigation)

        return InvestigationStartResponse(
            id=investigation_id,
            status=investigation["status"],
            currentStage=investigation["currentStage"],
        )

    except Exception as exc:
        investigation["status"] = "failed"
        investigation["currentStage"] = "Investigation failed"
        investigation["updatedAt"] = now()
        investigation["error"] = str(exc)

        investigation.setdefault("activity", []).append(
            {
                "id": "activity-failure",
                "tool": "InvestigationAgent",
                "action": f"Investigation failed: {exc}",
                "status": "failed",
                "timestamp": now(),
            }
        )

        save_investigation(investigation_id, investigation)

        raise HTTPException(
            status_code=500,
            detail=f"Investigation execution failed: {exc}",
        ) from exc
