from __future__ import annotations

import re
from pathlib import PurePosixPath


class PatchSafetyPolicy:
    FORBIDDEN_PATHS = {
        ".env",
        ".git",
        ".git/config",
        "id_rsa",
        "id_ed25519",
    }

    FORBIDDEN_PATTERNS = [
        r"-----BEGIN .*PRIVATE KEY-----",
        r"(?i)aws_access_key_id\s*=",
        r"(?i)aws_secret_access_key\s*=",
        r"(?i)api[_-]?key\s*=",
        r"(?i)secret[_-]?key\s*=",
        r"(?i)password\s*=",
        r"(?i)token\s*=",
    ]

    FORBIDDEN_COMMAND_PATTERNS = [
        r"\bos\.system\s*\(",
        r"\bsubprocess\.",
        r"\bshutil\.rmtree\s*\(",
        r"\brm\s+-rf\b",
        r"\bdel\s+/[sfq]\b",
    ]

    @classmethod
    def validate_path(cls, path: str) -> tuple[bool, str]:
        if not path:
            return False, "Patch target path is empty."

        normalized = path.replace("\\", "/")
        pure_path = PurePosixPath(normalized)

        if pure_path.is_absolute():
            return False, "Absolute file paths are not allowed."

        if ".." in pure_path.parts:
            return False, "Path traversal is not allowed."

        if normalized in cls.FORBIDDEN_PATHS:
            return False, f"Patch target '{path}' is forbidden."

        if normalized.startswith(".git/"):
            return False, "Modifying .git files is forbidden."

        return True, "Path is safe."

    @classmethod
    def scan_content(cls, content: str) -> tuple[bool, str]:
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, content):
                return False, "Potential secret or credential detected."

        for pattern in cls.FORBIDDEN_COMMAND_PATTERNS:
            if re.search(pattern, content):
                return False, "Potential destructive or arbitrary command detected."

        return True, "Content passed safety scanning."

    @classmethod
    def validate_patch(
        cls,
        path: str,
        original_content: str,
        patched_content: str,
    ) -> tuple[bool, str]:
        path_ok, path_reason = cls.validate_path(path)

        if not path_ok:
            return False, path_reason

        content_ok, content_reason = cls.scan_content(patched_content)

        if not content_ok:
            return False, content_reason

        if original_content == patched_content:
            return False, "Patch does not change the file."

        return True, "Patch passed safety checks."
