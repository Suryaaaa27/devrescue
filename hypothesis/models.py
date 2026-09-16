from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidenceReference:
    """
    Reference to a concrete piece of investigation evidence.
    """

    evidence_type: str
    identifier: str
    description: str
    strength: str = "supporting"


@dataclass
class Hypothesis:
    """
    Candidate explanation for an incident.
    """

    name: str
    category: str
    role: str

    confidence: float
    score: float

    explanation: str

    supporting_evidence: list[EvidenceReference] = field(
        default_factory=list
    )

    contradicting_evidence: list[EvidenceReference] = field(
        default_factory=list
    )

    matched_signals: list[str] = field(
        default_factory=list
    )

    missing_signals: list[str] = field(
        default_factory=list
    )

    evidence_score: float = 0.0
    specificity_score: float = 0.0
    temporal_score: float = 0.0
    contradiction_penalty: float = 0.0

    severity: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "role": self.role,
            "confidence": round(
                self.confidence,
                3,
            ),
            "score": round(
                self.score,
                3,
            ),
            "severity": self.severity,
            "explanation": self.explanation,
            "matched_signals": self.matched_signals,
            "missing_signals": self.missing_signals,
            "evidence_score": round(
                self.evidence_score,
                3,
            ),
            "specificity_score": round(
                self.specificity_score,
                3,
            ),
            "temporal_score": round(
                self.temporal_score,
                3,
            ),
            "contradiction_penalty": round(
                self.contradiction_penalty,
                3,
            ),
            "supporting_evidence": [
                {
                    "evidence_type": item.evidence_type,
                    "identifier": item.identifier,
                    "description": item.description,
                    "strength": item.strength,
                }
                for item in self.supporting_evidence
            ],
            "contradicting_evidence": [
                {
                    "evidence_type": item.evidence_type,
                    "identifier": item.identifier,
                    "description": item.description,
                    "strength": item.strength,
                }
                for item in self.contradicting_evidence
            ],
        }