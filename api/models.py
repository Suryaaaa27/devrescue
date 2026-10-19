from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class InvestigationCreate(BaseModel):
    service: str
    environment: str
    severity: str
    failureType: str
    description: str
    error: Optional[str] = None


class InvestigationSummary(BaseModel):
    id: str
    service: str
    environment: str
    status: str
    confidence: float = 0.0
    currentStage: str
    createdAt: str
    updatedAt: str


class InvestigationStartResponse(BaseModel):
    id: str
    status: str
    currentStage: str
