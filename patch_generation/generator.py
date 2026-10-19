from __future__ import annotations

import difflib
from typing import Any

from remediation.models import RemediationProposal

from .models import PatchFile, PatchProposal
from .safety import PatchSafetyPolicy


class PatchGenerator:
    """
    Generates in-memory unified diffs from remediation proposals.

    This component does NOT:
    - modify files
    - execute commands
    - commit changes
    - push changes
    - create pull requests
    """

    def generate(
        self,
        proposal: RemediationProposal,
        code_evidence: list[Any],
    ) -> PatchProposal:

        if not proposal.patch_generation_allowed:
            return PatchProposal(
                allowed=False,
                reason="Patch generation is not allowed by the remediation proposal.",
            )

        if not code_evidence:
            return PatchProposal(
                allowed=False,
                reason="No code evidence is available for patch generation.",
            )

        patches: list[PatchFile] = []

        for evidence in code_evidence:
            if isinstance(evidence, dict):
                path = evidence.get("path")
                original_content = evidence.get("content", "")
            else:
                path = getattr(evidence, "path", None)
                original_content = getattr(evidence, "content", "")

            if not path:
                continue

            if not original_content:
                continue

            patched_content = self._generate_patch_content(
                proposal,
                path,
                original_content,
            )

            if patched_content is None:
                continue

            safe, reason = PatchSafetyPolicy.validate_patch(
                path,
                original_content,
                patched_content,
            )

            if not safe:
                return PatchProposal(
                    allowed=False,
                    reason=reason,
                )

            diff = self._build_diff(
                path,
                original_content,
                patched_content,
            )

            if not diff:
                continue

            patches.append(
                PatchFile(
                    path=path,
                    original_content=original_content,
                    patched_content=patched_content,
                    diff=diff,
                )
            )

        if not patches:
            return PatchProposal(
                allowed=False,
                reason="No safe deterministic patch could be generated from the available code evidence.",
            )

        return PatchProposal(
            allowed=True,
            reason="Patch generated successfully in memory.",
            patches=patches,
            rationale=proposal.rationale,
            validation_requirements=proposal.validation_requirements,
            safety_checks=[
                "No source files were modified.",
                "No commands were executed.",
                "No git operations were performed.",
                "Patch paths were validated.",
                "Patch content was scanned for secrets and destructive commands.",
            ],
        )

    def _generate_patch_content(
        self,
        proposal: RemediationProposal,
        path: str,
        content: str,
    ) -> str | None:

        category = proposal.category

        if category == "application_validation":
            return self._patch_application_validation(content)

        if category == "application_error":
            return self._patch_application_exception(content)

        return None

    @staticmethod
    def _patch_application_validation(content: str) -> str | None:
        """
        v1 deterministic patch:
        Add a clear validation guard for obvious payment amount handling.
        """

        target = "def process_payment(amount):"

        if target not in content:
            return None

        if "if amount <= 0:" in content:
            return None

        replacement = (
            "def process_payment(amount):\n"
            "    if amount <= 0:\n"
            '        raise ValueError("Payment amount must be greater than zero.")'
        )

        return content.replace(
            target,
            replacement,
            1,
        )

    @staticmethod
    def _patch_application_exception(content: str) -> str | None:
        """
        v1 deterministic patch for an application exception.

        We only generate this patch when an explicit validation location
        exists in the supplied code evidence.
        """

        target = "raise Exception("

        if target not in content:
            return None

        replacement = "raise ValueError("

        return content.replace(
            target,
            replacement,
            1,
        )

    @staticmethod
    def _build_diff(
        path: str,
        original_content: str,
        patched_content: str,
    ) -> str:

        original_lines = original_content.splitlines(keepends=True)
        patched_lines = patched_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            original_lines,
            patched_lines,
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )

        return "".join(diff)
