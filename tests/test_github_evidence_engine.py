from evidence.engine import EvidenceEngine


def test_build_code_evidence():
    engine = EvidenceEngine()

    evidence = engine.build(
        service="payment-service",
        code_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "file": {
                    "path": "services/payment_service/main.py",
                    "content": "connection = create_connection()",
                },
            }
        ],
    )

    assert len(evidence.code) == 1

    code = evidence.code[0]

    assert code.repository == "Suryaaaa27/devrescue"
    assert code.path == "services/payment_service/main.py"
    assert code.content == "connection = create_connection()"

    assert evidence.summary["code_count"] == 1


def test_build_commit_evidence():
    engine = EvidenceEngine()

    evidence = engine.build(
        service="payment-service",
        commit_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "results": [
                    {
                        "sha": "abc123",
                        "message": "fix: database connection handling",
                        "author": "Surya Kumar Srivastava",
                        "timestamp": "2026-09-16T16:28:40Z",
                    }
                ],
            }
        ],
    )

    assert len(evidence.commits) == 1

    commit = evidence.commits[0]

    assert commit.repository == "Suryaaaa27/devrescue"
    assert commit.commit_sha == "abc123"
    assert commit.message == "fix: database connection handling"

    assert evidence.summary["commit_count"] == 1


def test_build_diff_evidence():
    engine = EvidenceEngine()

    evidence = engine.build(
        service="payment-service",
        diff_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "commit_sha": "abc123",
                "files": [
                    {
                        "path": "services/payment_service/main.py",
                        "patch": (
                            "- old_connection()\n"
                            "+ new_connection()"
                        ),
                    }
                ],
            }
        ],
    )

    assert len(evidence.diffs) == 1

    diff = evidence.diffs[0]

    assert diff.repository == "Suryaaaa27/devrescue"
    assert diff.commit_sha == "abc123"
    assert diff.path == "services/payment_service/main.py"
    assert "- old_connection()" in diff.patch

    assert evidence.summary["diff_count"] == 1


def test_build_combines_github_evidence():
    engine = EvidenceEngine()

    evidence = engine.build(
        service="payment-service",
        code_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "file": {
                    "path": "services/payment_service/main.py",
                    "content": "connection = create_connection()",
                },
            }
        ],
        commit_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "results": [
                    {
                        "sha": "abc123",
                        "message": "fix: database connection handling",
                    }
                ],
            }
        ],
        diff_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "commit_sha": "abc123",
                "files": [
                    {
                        "path": "services/payment_service/main.py",
                        "patch": "+ new_connection()",
                    }
                ],
            }
        ],
    )

    assert len(evidence.code) == 1
    assert len(evidence.commits) == 1
    assert len(evidence.diffs) == 1

    assert evidence.summary["code_count"] == 1
    assert evidence.summary["commit_count"] == 1
    assert evidence.summary["diff_count"] == 1
    
def test_build_real_github_diff_shape():

    engine = EvidenceEngine()

    result = engine.build(
        service="payment-service",
        diff_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "commit": {
                    "sha": "abc123",
                    "message": "change payment validation",
                },
                "files": [
                    {
                        "filename": "services/payment_service/main.py",
                        "status": "modified",
                        "patch": "@@ -1 +1 @@",
                    }
                ],
            }
        ],
    )

    assert len(result.diffs) == 1

    diff = result.diffs[0]

    assert diff.repository == "Suryaaaa27/devrescue"
    assert diff.commit_sha == "abc123"
    assert diff.path == "services/payment_service/main.py"


def test_build_real_get_commit_shape():

    engine = EvidenceEngine()

    result = engine.build(
        service="payment-service",
        commit_results=[
            {
                "status": "success",
                "commit": {
                    "sha": "abc123",
                    "message": "change payment validation",
                    "author": {
                        "name": "Developer",
                        "email": "developer@example.com",
                        "date": "2026-09-17T10:00:00Z",
                    },
                },
            }
        ],
    )

    assert len(result.commits) == 1

    commit = result.commits[0]

    assert commit.commit_sha == "abc123"
    assert commit.message == "change payment validation"
    assert commit.author == "Developer"
    assert commit.timestamp == "2026-09-17T10:00:00Z"
    
def test_code_and_diff_are_correlated():
    engine = EvidenceEngine()

    evidence = engine.build(
        service="payment-service",
        code_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "file": {
                    "path": "services/payment_service/main.py",
                    "content": "raise HTTPException(...)",
                },
            }
        ],
        diff_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "commit": {
                    "sha": "abc123",
                    "message": "fix payment validation",
                },
                "files": [
                    {
                        "filename": "services/payment_service/main.py",
                        "patch": (
                            "@@ -10,2 +10,3 @@\n"
                            "+raise HTTPException(...)"
                        ),
                    }
                ],
            }
        ],
    )

    matches = [
        correlation
        for correlation in evidence.correlations
        if (
            correlation.source == "code"
            and correlation.target == "diff"
        )
    ]

    assert len(matches) == 1
    assert matches[0].key == "repository_path"
    assert "main.py" in matches[0].value
    
def test_commit_and_diff_are_correlated():
    engine = EvidenceEngine()

    evidence = engine.build(
        service="payment-service",
        commit_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "results": [
                    {
                        "sha": "abc123",
                        "message": "fix payment validation",
                        "author": "Surya",
                        "timestamp": "2026-09-17T10:00:00Z",
                    }
                ],
            }
        ],
        diff_results=[
            {
                "status": "success",
                "repository": "Suryaaaa27/devrescue",
                "commit": {
                    "sha": "abc123",
                    "message": "fix payment validation",
                },
                "files": [
                    {
                        "filename": "services/payment_service/main.py",
                        "patch": "+validation fix",
                    }
                ],
            }
        ],
    )

    matches = [
        correlation
        for correlation in evidence.correlations
        if (
            correlation.source == "commit"
            and correlation.target == "diff"
        )
    ]

    assert len(matches) == 1
    assert matches[0].key == "commit_sha"
    assert matches[0].value == "abc123"