from __future__ import annotations

import time

import mcp_servers.github.server as github


def test_real_github_write_path():
    owner = github.GITHUB_OWNER
    repository = github.GITHUB_REPOSITORY

    assert github.GITHUB_TOKEN
    assert owner
    assert repository

    suffix = str(int(time.time()))
    branch = f"devrescue/integration-test-{suffix}"
    path = f"devrescue-integration-test-{suffix}.txt"

    # 1. Create temporary branch
    branch_result = github.create_branch(
        branch=branch,
        from_branch="main",
        owner=owner,
        repository=repository,
    )

    assert branch_result["status"] == "success", branch_result

    # 2. Create harmless test file
    content = (
        "DevRescue GitHub write integration test.\n"
        f"Temporary branch: {branch}\n"
    )

    file_result = github.create_or_update_file(
        path=path,
        content=content,
        branch=branch,
        message="test: verify DevRescue GitHub write workflow",
        owner=owner,
        repository=repository,
    )

    assert file_result["status"] == "success", file_result

    # 3. Verify the file through the existing read API
    read_result = github.get_file(
        path=path,
        ref=branch,
        owner=owner,
        repository=repository,
    )

    assert read_result["status"] == "success", read_result
    assert read_result["file"]["content"] == content

    # 4. Create temporary PR
    pr_result = github.create_pull_request(
        title="test: DevRescue GitHub write integration",
        body=(
            "Temporary integration test PR created by DevRescue "
            "to verify the GitHub write workflow."
        ),
        head=branch,
        base="main",
        owner=owner,
        repository=repository,
    )

    assert pr_result["status"] == "success", pr_result
    assert pr_result["pull_request"]["head"] == branch
    assert pr_result["pull_request"]["base"] == "main"

    print()
    print("=== DEVRESCUE GITHUB WRITE TEST ===")
    print(f"Branch: {branch}")
    print(f"File:   {path}")
    print(
        "PR:     "
        f"{pr_result['pull_request']['html_url']}"
    )
    print("===================================")
