from dataclasses import field
import re

from evidence.models import (
    CodeEvidence,
    CodeRelevance,
    DiffEvidence,
)

class CodeRelevanceEngine:
    """
    Deterministic relevance engine for connecting observed
    runtime failures with source code and GitHub diffs.

    This intentionally avoids embeddings/LLMs at this stage.
    """

    def analyze(
        self,
        code: list[CodeEvidence],
        diffs: list[DiffEvidence],
        traces: list,
        logs: list | None = None,
    ) -> list[CodeRelevance]:

        terms = self._extract_terms(
            traces=traces,
            logs=logs or [],
        )

        results: list[CodeRelevance] = []

        for item in code:
            score = 0.0
            matched_terms: list[str] = []
            reasons: list[str] = []

            content = item.content or ""
            path = item.path or ""
            symbol = item.symbol or ""

            searchable = " ".join(
                [
                    path,
                    symbol,
                    content,
                ]
            ).lower()

            # -------------------------------------------------
            # Runtime evidence → source-code matching
            # -------------------------------------------------

            for term in terms:
                if term.lower() in searchable:
                    if term not in matched_terms:
                        matched_terms.append(term)

                    score += 0.25
                    reasons.append(
                        f"Runtime evidence matches '{term}'."
                    )

            # -------------------------------------------------
            # Symbol / operation relationship
            # -------------------------------------------------

            for trace in traces:
                for span in trace.spans:
                    operation = span.operation

                    if not operation:
                        continue

                    operation_terms = self._tokenize(
                        operation
                    )

                    if any(
                        token in searchable
                        for token in operation_terms
                    ):
                        score += 0.20
                        reasons.append(
                            "Trace operation is related to "
                            "the source code."
                        )
                        break

            # -------------------------------------------------
            # GitHub diff relationship
            # -------------------------------------------------

            related_diff = any(
                diff.repository == item.repository
                and diff.path == item.path
                for diff in diffs
            )

            if related_diff:
                score += 0.25
                reasons.append(
                    "GitHub diff modifies the same source file."
                )

            score = min(score, 1.0)

            if score > 0:
                results.append(
                    CodeRelevance(
                        path=path,
                        score=score,
                        matched_terms=matched_terms,
                        reasons=reasons,
                    )
                )

        results.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return results

    def _extract_terms(
        self,
        traces: list,
        logs: list,
    ) -> list[str]:

        terms: list[str] = []

        for trace in traces:
            for span in trace.spans:

                if span.operation:
                    terms.extend(
                        self._tokenize(
                            span.operation
                        )
                    )

                for trace_log in span.logs:
                    fields = trace_log.fields

                    exception_type = fields.get(
                        "exception.type"
                    )

                    exception_message = fields.get(
                        "exception.message"
                    )

                    if exception_type:
                        terms.append(
                            str(exception_type)
                        )

                    if exception_message:
                        terms.extend(
                            self._tokenize(
                                str(exception_message)
                            )
                        )

        for log in logs:
            if log.message:
                terms.extend(
                    self._tokenize(
                        log.message
                    )
                )

        # Preserve order while removing duplicates.
        unique: list[str] = []

        for term in terms:
            normalized = term.strip()

            if (
                len(normalized) < 3
                or normalized.lower() in {
                    "the",
                    "and",
                    "for",
                    "with",
                    "from",
                    "must",
                    "greater",
                    "than",
                    "less",
                }
            ):
                continue

            if normalized not in unique:
                unique.append(normalized)

        return unique[:30]

    def _tokenize(self, value: str) -> list[str]:

        return re.findall(
            r"[A-Za-z_][A-Za-z0-9_]*",
            value,
        )