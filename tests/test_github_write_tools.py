from __future__ import annotations

import base64

import mcp_servers.github.server as github


def test_create_branch_uses_git_ref_api(monkeypatch):
    calls = []

    def fake_request(path, params=None, method="GET", body=None):
        calls.append(
            {
                "path": path,
                "params": params,
                "method": method,
                "body": body,
            }
        )

        if path.endswith("/git/ref/heads/main"):
            return {
                "ref": "refs/heads/main",
                "object": {
                    "sha": "base-sha-123",
                },
            }

        return {
            "ref": "refs/heads/devrescue/fix-payment",
            "object": {
                "sha": "base-sha-123",
            },
        }

    monkeypatch.setattr(github, "_request", fake_request)

    result = github.create_branch(
        branch="devrescue/fix-payment",
        from_branch="main",
        owner="Suryaaaa27",
        repository="devrescue",
    )

    assert result["status"] == "success"
    assert result["branch"] == "devrescue/fix-payment"
    assert result["from_branch"] == "main"

    create_call = calls[-1]

    assert create_call["method"] == "POST"
    assert create_call["path"] == "/repos/Suryaaaa27/devrescue/git/refs"
    assert create_call["body"] == {
        "ref": "refs/heads/devrescue/fix-payment",
        "sha": "base-sha-123",
    }


def test_create_branch_propagates_source_branch_error(monkeypatch):
    def fake_request(path, params=None, method="GET", body=None):
        return {
            "status": "error",
            "http_status": 404,
            "error": "Branch not found",
        }

    monkeypatch.setattr(github, "_request", fake_request)

    result = github.create_branch(
        branch="devrescue/fix-payment",
        from_branch="main",
        owner="Suryaaaa27",
        repository="devrescue",
    )

    assert result["status"] == "error"
    assert result["http_status"] == 404


def test_create_branch_rejects_missing_source_sha(monkeypatch):
    def fake_request(path, params=None, method="GET", body=None):
        return {
            "ref": "refs/heads/main",
            "object": {},
        }

    monkeypatch.setattr(github, "_request", fake_request)

    result = github.create_branch(
        branch="devrescue/fix-payment",
        from_branch="main",
        owner="Suryaaaa27",
        repository="devrescue",
    )

    assert result["status"] == "error"
    assert "source branch commit" in result["error"]


def test_create_file_uses_put_and_base64(monkeypatch):
    calls = []

    def fake_request(path, params=None, method="GET", body=None):
        calls.append(
            {
                "path": path,
                "params": params,
                "method": method,
                "body": body,
            }
        )

        return {
            "commit": {
                "sha": "commit-sha-123",
                "message": "fix payment validation",
                "html_url": "https://github.com/example",
            }
        }

    monkeypatch.setattr(github, "_request", fake_request)

    content = (
        "def process_payment(amount):\n"
        "    if amount <= 0:\n"
        "        raise ValueError('invalid amount')\n"
    )

    result = github.create_or_update_file(
        path="services/payment.py",
        content=content,
        branch="devrescue/fix-payment",
        message="fix payment validation",
        owner="Suryaaaa27",
        repository="devrescue",
    )

    assert result["status"] == "success"

    call = calls[0]

    assert call["method"] == "PUT"
    assert (
        call["path"]
        == "/repos/Suryaaaa27/devrescue/contents/services/payment.py"
    )

    expected_encoded = base64.b64encode(
        content.encode("utf-8")
    ).decode("ascii")

    assert call["body"]["content"] == expected_encoded
    assert call["body"]["branch"] == "devrescue/fix-payment"
    assert call["body"]["message"] == "fix payment validation"


def test_create_file_includes_sha_for_update(monkeypatch):
    captured = {}

    def fake_request(path, params=None, method="GET", body=None):
        captured["body"] = body

        return {
            "commit": {
                "sha": "updated-sha",
                "message": "update file",
            }
        }

    monkeypatch.setattr(github, "_request", fake_request)

    result = github.create_or_update_file(
        path="services/payment.py",
        content="updated content",
        branch="devrescue/fix-payment",
        message="update file",
        sha="existing-file-sha",
        owner="Suryaaaa27",
        repository="devrescue",
    )

    assert result["status"] == "success"
    assert captured["body"]["sha"] == "existing-file-sha"


def test_create_file_propagates_github_error(monkeypatch):
    def fake_request(path, params=None, method="GET", body=None):
        return {
            "status": "error",
            "http_status": 409,
            "error": "Conflict",
        }

    monkeypatch.setattr(github, "_request", fake_request)

    result = github.create_or_update_file(
        path="services/payment.py",
        content="content",
        branch="devrescue/fix-payment",
        message="update",
        owner="Suryaaaa27",
        repository="devrescue",
    )

    assert result["status"] == "error"
    assert result["http_status"] == 409


def test_create_pull_request_uses_post(monkeypatch):
    captured = {}

    def fake_request(path, params=None, method="GET", body=None):
        captured["path"] = path
        captured["method"] = method
        captured["body"] = body

        return {
            "number": 42,
            "title": "Fix payment validation",
            "state": "open",
            "html_url": "https://github.com/Suryaaaa27/devrescue/pull/42",
            "head": {
                "ref": "devrescue/fix-payment",
            },
            "base": {
                "ref": "main",
            },
        }

    monkeypatch.setattr(github, "_request", fake_request)

    result = github.create_pull_request(
        title="Fix payment validation",
        body="Automated remediation proposal.",
        head="devrescue/fix-payment",
        base="main",
        owner="Suryaaaa27",
        repository="devrescue",
    )

    assert result["status"] == "success"
    assert result["pull_request"]["number"] == 42
    assert result["pull_request"]["head"] == "devrescue/fix-payment"
    assert result["pull_request"]["base"] == "main"

    assert captured["method"] == "POST"
    assert captured["path"] == "/repos/Suryaaaa27/devrescue/pulls"

    assert captured["body"] == {
        "title": "Fix payment validation",
        "body": "Automated remediation proposal.",
        "head": "devrescue/fix-payment",
        "base": "main",
    }


def test_create_pull_request_propagates_github_error(monkeypatch):
    def fake_request(path, params=None, method="GET", body=None):
        return {
            "status": "error",
            "http_status": 422,
            "error": "Validation Failed",
        }

    monkeypatch.setattr(github, "_request", fake_request)

    result = github.create_pull_request(
        title="Fix payment validation",
        body="Test",
        head="devrescue/fix-payment",
        owner="Suryaaaa27",
        repository="devrescue",
    )

    assert result["status"] == "error"
    assert result["http_status"] == 422
