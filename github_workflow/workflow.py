from __future__ import annotations

from typing import Any, Callable

from github_workflow.models import (
    GitHubWorkflowResult,
    GitHubWorkflowStatus,
)


class GitHubPRWorkflow:
    """
    Orchestrates the safe remediation -> GitHub PR workflow.

    Safety gates:

        Patch Proposal
              ↓
        Validation PASSED
              ↓
        Human Approval APPROVED
              ↓
        Create Branch
              ↓
        Write Files
              ↓
        Create Pull Request
    """

    def __init__(
        self,
        create_branch: Callable[..., dict[str, Any]],
        create_or_update_file: Callable[..., dict[str, Any]],
        create_pull_request: Callable[..., dict[str, Any]],
    ) -> None:
        self.create_branch = create_branch
        self.create_or_update_file = create_or_update_file
        self.create_pull_request = create_pull_request

    def execute(
        self,
        *,
        patch_proposal: Any,
        validation_result: Any,
        approval_decision: Any,
        branch: str,
        commit_message: str,
        pr_title: str,
        pr_body: str,
        base_branch: str = "main",
        owner: str | None = None,
        repository: str | None = None,
    ) -> GitHubWorkflowResult:
        """
        Execute the remediation PR workflow.

        No GitHub mutation occurs unless:
        1. Validation passed.
        2. Human approval was granted.
        3. Patch proposal contains files.
        """

        # ---------------------------------------------------------
        # GATE 1 — Validation
        # ---------------------------------------------------------

        validation_passed = self._validation_passed(validation_result)

        if not validation_passed:
            return GitHubWorkflowResult(
                status=GitHubWorkflowStatus.BLOCKED,
                message="Workflow blocked because validation did not pass.",
                validation_passed=False,
                approval_granted=False,
            )

        # ---------------------------------------------------------
        # GATE 2 — Human Approval
        # ---------------------------------------------------------

        approval_granted = self._approval_granted(approval_decision)

        if not approval_granted:
            return GitHubWorkflowResult(
                status=GitHubWorkflowStatus.BLOCKED,
                message="Workflow blocked because human approval was not granted.",
                validation_passed=True,
                approval_granted=False,
            )

        # ---------------------------------------------------------
        # GATE 3 — Patch
        # ---------------------------------------------------------

        files = self._extract_files(patch_proposal)

        if not files:
            return GitHubWorkflowResult(
                status=GitHubWorkflowStatus.BLOCKED,
                message="Workflow blocked because the patch contains no files.",
                validation_passed=True,
                approval_granted=True,
            )

        if not branch.strip():
            return GitHubWorkflowResult(
                status=GitHubWorkflowStatus.BLOCKED,
                message="Workflow blocked because remediation branch is empty.",
                validation_passed=True,
                approval_granted=True,
            )

        normalized_branch = branch.strip().lower()
        if normalized_branch in {"main", "master"}:
            return GitHubWorkflowResult(
                status=GitHubWorkflowStatus.BLOCKED,
                message="Workflow blocked because protected branches cannot be remediation branches.",
                validation_passed=True,
                approval_granted=True,
            )

        # ---------------------------------------------------------
        # STEP 1 — Create branch
        # ---------------------------------------------------------

        try:
            branch_result = self.create_branch(
                branch=branch,
                from_branch=base_branch,
                owner=owner,
                repository=repository,
            )

            if not self._is_success(branch_result):
                return GitHubWorkflowResult(
                    status=GitHubWorkflowStatus.FAILED,
                    message="Failed to create remediation branch.",
                    branch=branch,
                    validation_passed=True,
                    approval_granted=True,
                    errors=[self._error_message(branch_result)],
                )

        except Exception as exc:
            return GitHubWorkflowResult(
                status=GitHubWorkflowStatus.FAILED,
                message="Exception while creating remediation branch.",
                branch=branch,
                validation_passed=True,
                approval_granted=True,
                errors=[str(exc)],
            )

        # ---------------------------------------------------------
        # STEP 2 — Write patch files
        # ---------------------------------------------------------

        written_files: list[str] = []

        for patch_file in files:
            path = self._get_value(patch_file, "path")
            content = self._get_value(patch_file, "patched_content")

            if not path:
                return GitHubWorkflowResult(
                    status=GitHubWorkflowStatus.FAILED,
                    message="Patch contains a file with no path.",
                    branch=branch,
                    validation_passed=True,
                    approval_granted=True,
                    written_files=written_files,
                )

            try:
                file_result = self.create_or_update_file(
                    path=path,
                    content=content,
                    branch=branch,
                    message=commit_message,
                    owner=owner,
                    repository=repository,
                )

                if not self._is_success(file_result):
                    return GitHubWorkflowResult(
                        status=GitHubWorkflowStatus.FAILED,
                        message=f"Failed to write patch file: {path}",
                        branch=branch,
                        validation_passed=True,
                        approval_granted=True,
                        written_files=written_files,
                        errors=[self._error_message(file_result)],
                    )

                written_files.append(path)

            except Exception as exc:
                return GitHubWorkflowResult(
                    status=GitHubWorkflowStatus.FAILED,
                    message=f"Exception while writing patch file: {path}",
                    branch=branch,
                    validation_passed=True,
                    approval_granted=True,
                    written_files=written_files,
                    errors=[str(exc)],
                )

        # ---------------------------------------------------------
        # STEP 3 — Create Pull Request
        # ---------------------------------------------------------

        try:
            pr_result = self.create_pull_request(
                title=pr_title,
                body=pr_body,
                head=branch,
                base=base_branch,
                owner=owner,
                repository=repository,
            )

            if not self._is_success(pr_result):
                return GitHubWorkflowResult(
                    status=GitHubWorkflowStatus.FAILED,
                    message="Patch was written, but pull request creation failed.",
                    branch=branch,
                    validation_passed=True,
                    approval_granted=True,
                    written_files=written_files,
                    errors=[self._error_message(pr_result)],
                )

        except Exception as exc:
            return GitHubWorkflowResult(
                status=GitHubWorkflowStatus.FAILED,
                message="Exception while creating pull request.",
                branch=branch,
                validation_passed=True,
                approval_granted=True,
                written_files=written_files,
                errors=[str(exc)],
            )

        return GitHubWorkflowResult(
            status=GitHubWorkflowStatus.COMPLETED,
            message="Remediation branch, patch, and pull request created successfully.",
            branch=branch,
            pull_request=pr_result.get("pull_request"),
            written_files=written_files,
            validation_passed=True,
            approval_granted=True,
        )

    # ------------------------------------------------------------------
    # Safety helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validation_passed(result: Any) -> bool:
        if result is None:
            return False

        if isinstance(result, bool):
            return result

        status = GitHubPRWorkflow._get_value(result, "status")

        if isinstance(status, str):
            return status.lower() in {
                "passed",
                "pass",
                "success",
                "validated",
            }

        return bool(
            GitHubPRWorkflow._get_value(
                result,
                "passed",
                False,
            )
        )

    @staticmethod
    def _approval_granted(decision: Any) -> bool:
        if decision is None:
            return False

        if isinstance(decision, bool):
            return decision

        status = GitHubPRWorkflow._get_value(decision, "status")

        if isinstance(status, str):
            return status.lower() in {
                "approved",
                "approve",
            }

        decision_value = GitHubPRWorkflow._get_value(
            decision,
            "decision",
        )

        if isinstance(decision_value, str):
            return decision_value.lower() in {
                "approved",
                "approve",
            }

        return bool(
            GitHubPRWorkflow._get_value(
                decision,
                "approved",
                False,
            )
        )

    @staticmethod
    def _extract_files(patch_proposal: Any) -> list[Any]:
        if patch_proposal is None:
            return []

        if isinstance(patch_proposal, dict):
            files = patch_proposal.get("files")

            if files is None:
                files = patch_proposal.get("patches", [])
        else:
            files = getattr(patch_proposal, "files", None)

            if files is None:
                files = getattr(patch_proposal, "patches", [])

        return list(files or [])

    @staticmethod
    def _get_value(
        obj: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)

        return getattr(obj, key, default)

    @staticmethod
    def _is_success(result: Any) -> bool:
        if not isinstance(result, dict):
            return bool(result)

        return result.get("status") == "success"

    @staticmethod
    def _error_message(result: Any) -> str:
        if not isinstance(result, dict):
            return str(result)

        error = result.get("error")

        if isinstance(error, dict):
            return str(
                error.get(
                    "message",
                    error,
                )
            )

        if error:
            return str(error)

        return str(result)
