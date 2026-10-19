from unittest.mock import patch

import pytest

import mcp_servers.github.server as github


def test_request_normalizes_no_content_response():
    with patch.object(github.urllib.request, "urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value.status = 204

        result = github._request(
            "/repos/Suryaaaa27/devrescue/git/refs/heads/test-cleanup",
            method="DELETE",
        )

    assert result == {
        "status": "success",
        "status_code": 204,
    }


def test_close_pull_request_calls_patch():
    with patch.object(github, "_request") as request:
        request.return_value = {
            "status": "success",
            "pull_request": {"number": 1, "state": "closed"},
        }

        result = github.close_pull_request(
            pull_number=1,
            owner="Suryaaaa27",
            repository="devrescue",
        )

        request.assert_called_once_with(
            "/repos/Suryaaaa27/devrescue/pulls/1",
            method="PATCH",
            body={"state": "closed"},
        )

        assert result["status"] == "success"


def test_close_pull_request_rejects_invalid_number():
    with pytest.raises(ValueError):
        github.close_pull_request(
            pull_number=0,
            owner="Suryaaaa27",
            repository="devrescue",
        )


def test_delete_branch_calls_delete():
    with patch.object(github, "_request") as request:
        request.return_value = {
            "status": "success",
        }

        result = github.delete_branch(
            branch="devrescue/test-cleanup",
            owner="Suryaaaa27",
            repository="devrescue",
        )

        request.assert_called_once_with(
            "/repos/Suryaaaa27/devrescue/git/refs/heads/devrescue/test-cleanup",
            method="DELETE",
        )

        assert result["status"] == "success"


@pytest.mark.parametrize("branch", ["main", "master", "MAIN", "Master"])
def test_delete_branch_rejects_protected_branch(branch):
    with pytest.raises(ValueError):
        github.delete_branch(
            branch=branch,
            owner="Suryaaaa27",
            repository="devrescue",
        )


def test_delete_branch_rejects_empty_branch():
    with pytest.raises(ValueError):
        github.delete_branch(
            branch="",
            owner="Suryaaaa27",
            repository="devrescue",
        )
