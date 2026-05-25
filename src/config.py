import os
from pathlib import Path

_PROJECT_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().strip("'\"")
    return result


def get_api_key(name: str) -> str:
    """Resolve key by name: env var → project .env file."""
    value = os.environ.get(name)
    if value:
        return value

    env_file_vars = _parse_env_file(_PROJECT_ENV_FILE)
    value = env_file_vars.get(name)
    if value:
        return value

    raise KeyError(
        f"'{name}' not found. Set it as env var or add to {_PROJECT_ENV_FILE}"
    )


def get_google_api_key() -> str:
    return get_api_key("GOOGLE_API_KEY")


def get_twentyfirst_api_key() -> str:
    return get_api_key("TWENTYFIRST_API_KEY")


def get_github_token() -> str:
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        try:
            return get_api_key(name)
        except KeyError:
            continue
    raise KeyError(
        f"GitHub token not found. Set GITHUB_TOKEN as env var or add to {_PROJECT_ENV_FILE}"
    )
