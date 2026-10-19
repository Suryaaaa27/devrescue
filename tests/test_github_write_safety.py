from mcp_servers.github.server import (
    create_branch,
    create_or_update_file,
    create_pull_request,
)


def test_create_branch_rejects_empty_name():
    result = create_branch("")

    assert result["status"] == "error"


def test_create_branch_rejects_main():
    result = create_branch("main")

    assert result["status"] == "error"


def test_create_file_rejects_main():
    result = create_or_update_file(
        path="test.py",
        content="print('hello')",
        branch="main",
        message="test",
    )

    assert result["status"] == "error"


def test_create_file_requires_path():
    result = create_or_update_file(
        path="",
        content="print('hello')",
        branch="devrescue/fix-test",
        message="test",
    )

    assert result["status"] == "error"


def test_create_file_requires_commit_message():
    result = create_or_update_file(
        path="test.py",
        content="print('hello')",
        branch="devrescue/fix-test",
        message="",
    )

    assert result["status"] == "error"


def test_pull_request_requires_title():
    result = create_pull_request(
        title="",
        body="test",
        head="devrescue/fix-test",
    )

    assert result["status"] == "error"


def test_pull_request_rejects_main_head():
    result = create_pull_request(
        title="Test",
        body="test",
        head="main",
    )

    assert result["status"] == "error"


def test_pull_request_requires_head():
    result = create_pull_request(
        title="Test",
        body="test",
        head="",
    )

    assert result["status"] == "error"
