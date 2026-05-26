"""Destroy all provisioned resources for a design project."""

import json
import subprocess
from pathlib import Path

from strands import tool

from src.tools._validate import _redact_stderr, safe_build_path, safe_project_name

MANIFESTS_DIR = Path(__file__).resolve().parent.parent.parent / "manifests"


@tool
def destroy_resources(project_name: str) -> str:
    """Tear down all AWS and GitHub resources for a design project.

    Reads the project manifest and destroys: S3 project prefix,
    and GitHub repository. Also removes the local manifest file.

    Args:
        project_name: The project identifier whose resources should be destroyed.

    Returns:
        JSON summary of what was destroyed and any errors.
    """
    try:
        project_name = safe_project_name(project_name)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    manifest_path = MANIFESTS_DIR / f"{project_name}.json"
    if not manifest_path.exists():
        return json.dumps({"error": f"No manifest for project '{project_name}'"})

    manifest = json.loads(manifest_path.read_text())
    results: dict[str, str] = {}

    if bucket := manifest.get("s3_bucket"):
        prefix = manifest.get("s3_prefix", project_name)
        results["s3"] = _destroy_s3(bucket, prefix)

    # CloudFront is shared infra — never disable it per-project.
    # Removing the S3 prefix is sufficient to take a project offline.

    if repo := manifest.get("github_repo"):
        results["github"] = _destroy_github_repo(repo)

    if build_path := manifest.get("local_build_path"):
        try:
            validated = safe_build_path(build_path)
            local = Path(validated)
            if local.exists():
                import shutil
                shutil.rmtree(local)
                results["local"] = "removed"
        except ValueError:
            results["local"] = "skipped (path outside allowed directory)"

    manifest_path.unlink()
    results["manifest"] = "removed"

    return json.dumps({"project": project_name, "destroyed": results})


def _destroy_s3(bucket: str, prefix: str) -> str:
    result = subprocess.run(
        ["aws", "s3", "rm", f"s3://{bucket}/{prefix}/", "--recursive"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        return f"failed: {_redact_stderr(result.stderr, 200)}"
    return "emptied"



def _destroy_github_repo(repo: str) -> str:
    result = subprocess.run(
        ["gh", "repo", "delete", repo, "--yes"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        return f"failed: {_redact_stderr(result.stderr, 200)}"
    return "deleted"
