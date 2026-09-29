from evidence.models import (
    CodeEvidence,
    CommitEvidence,
    DiffEvidence,
    InvestigationEvidence,
)


def test_code_evidence_model():
    evidence = CodeEvidence(
        repository="Suryaaaa27/devrescue",
        path="services/payment_service/main.py",
        content="connection = create_connection()",
        start_line=10,
        end_line=10,
        symbol="create_payment",
    )

    assert evidence.repository == "Suryaaaa27/devrescue"
    assert evidence.path == "services/payment_service/main.py"
    assert evidence.content == "connection = create_connection()"
    assert evidence.start_line == 10
    assert evidence.end_line == 10
    assert evidence.symbol == "create_payment"


def test_commit_evidence_model():
    evidence = CommitEvidence(
        repository="Suryaaaa27/devrescue",
        commit_sha="abc123",
        message="fix: database connection handling",
        author="Surya Kumar Srivastava",
        timestamp="2026-09-16T16:28:40Z",
    )

    assert evidence.repository == "Suryaaaa27/devrescue"
    assert evidence.commit_sha == "abc123"
    assert evidence.message == "fix: database connection handling"
    assert evidence.author == "Surya Kumar Srivastava"
    assert evidence.timestamp == "2026-09-16T16:28:40Z"


def test_diff_evidence_model():
    evidence = DiffEvidence(
        repository="Suryaaaa27/devrescue",
        commit_sha="abc123",
        path="services/payment_service/main.py",
        patch="- old_connection()\n+ new_connection()",
    )

    assert evidence.repository == "Suryaaaa27/devrescue"
    assert evidence.commit_sha == "abc123"
    assert evidence.path == "services/payment_service/main.py"
    assert evidence.patch == "- old_connection()\n+ new_connection()"


def test_investigation_evidence_supports_github_evidence():
    code = CodeEvidence(
        repository="Suryaaaa27/devrescue",
        path="services/payment_service/main.py",
        content="connection = create_connection()",
    )

    commit = CommitEvidence(
        repository="Suryaaaa27/devrescue",
        commit_sha="abc123",
        message="fix: database connection handling",
    )

    diff = DiffEvidence(
        repository="Suryaaaa27/devrescue",
        commit_sha="abc123",
        path="services/payment_service/main.py",
        patch="- old_connection()\n+ new_connection()",
    )

    evidence = InvestigationEvidence(
        service="payment-service",
        code=[code],
        commits=[commit],
        diffs=[diff],
    )

    assert len(evidence.code) == 1
    assert len(evidence.commits) == 1
    assert len(evidence.diffs) == 1

    assert evidence.code[0].path == "services/payment_service/main.py"
    assert evidence.commits[0].commit_sha == "abc123"
    assert evidence.diffs[0].commit_sha == "abc123"