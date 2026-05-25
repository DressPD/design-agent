"""Input validation for all tools — prevents path traversal and injection."""

import re

_SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$")


def safe_project_name(name: str) -> str:
    """Validate and return a safe project name.

    Rejects path traversal (../, /), shell metacharacters, and empty names.
    Raises ValueError on invalid input.
    """
    if not name or not isinstance(name, str):
        raise ValueError("project_name must be a non-empty string")
    name = name.strip()
    if ".." in name or "/" in name or "\\" in name or "\x00" in name:
        raise ValueError(f"Invalid project_name (path traversal): {name!r}")
    if not _SAFE_NAME_RE.match(name):
        raise ValueError(f"Invalid project_name (must be alphanumeric/dash/dot/underscore, 1-128 chars): {name!r}")
    return name


def safe_component_name(name: str) -> str:
    """Validate a React component name — alphanumeric + underscore only."""
    if not name or not isinstance(name, str):
        raise ValueError("Component name must be a non-empty string")
    name = name.strip()
    if ".." in name or "/" in name or "\\" in name or "\x00" in name:
        raise ValueError(f"Invalid component name (path traversal): {name!r}")
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$", name):
        raise ValueError(f"Invalid component name (must be valid identifier): {name!r}")
    return name


def safe_build_path(path_str: str, allowed_prefix: str = "/tmp/design-agent-builds/") -> str:
    """Validate a build path stays within allowed prefix."""
    from pathlib import Path
    resolved = str(Path(path_str).resolve())
    if not resolved.startswith(allowed_prefix):
        raise ValueError(f"Build path escapes allowed directory: {path_str!r}")
    return resolved


def _redact_stderr(stderr: str, max_len: int = 300) -> str:
    """Truncate stderr and strip potential secrets (tokens, keys)."""
    text = stderr[:max_len] if stderr else ""
    text = re.sub(r"(ghp_|gho_|github_pat_|sk-|AKIA)[A-Za-z0-9_-]+", "[REDACTED]", text)
    text = re.sub(r"x-access-token:[^@]+@", "x-access-token:[REDACTED]@", text)
    return text
