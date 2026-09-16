import json

from agent.llm.models import LLMReasoningResult
from agent.llm.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)


class LLMReasoner:
    def __init__(self, client):
        self.client = client

    def reason(
        self,
        *,
        incident: str,
        service: str,
        evidence_summary: dict,
        hypotheses: list[dict],
        uncertainty: dict,
        investigation_history: list[dict],
    ) -> LLMReasoningResult:

        user_prompt = USER_PROMPT_TEMPLATE.format(
            incident=incident,
            service=service,
            evidence_summary=json.dumps(
                evidence_summary,
                indent=2,
                default=str,
            ),
            hypotheses=json.dumps(
                hypotheses,
                indent=2,
                default=str,
            ),
            uncertainty=json.dumps(
                uncertainty,
                indent=2,
                default=str,
            ),
            investigation_history=json.dumps(
                investigation_history,
                indent=2,
                default=str,
            ),
        )

        result = self.client.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        return self._parse_result(result)

    def _parse_result(
        self,
        result: dict,
    ) -> LLMReasoningResult:

        required_fields = {
            "conclusion",
            "reasoning",
            "supporting_evidence",
            "contradicting_evidence",
            "missing_evidence",
            "confidence",
        }

        missing_fields = required_fields - result.keys()

        if missing_fields:
            raise ValueError(
                "LLM response missing required fields: "
                + ", ".join(sorted(missing_fields))
            )

        confidence = float(result["confidence"])

        confidence = max(
            0.0,
            min(1.0, confidence),
        )

        return LLMReasoningResult(
            conclusion=str(result["conclusion"]),
            reasoning=str(result["reasoning"]),
            supporting_evidence=list(
                result["supporting_evidence"]
            ),
            contradicting_evidence=list(
                result["contradicting_evidence"]
            ),
            missing_evidence=list(
                result["missing_evidence"]
            ),
            confidence=confidence,
        )