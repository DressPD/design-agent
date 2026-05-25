"""Resource manifest — tracks all provisioned resources per project for teardown."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strands import tool

MANIFESTS_DIR = Path(__file__).resolve().parent.parent.parent / "manifests"


def _manifest_path(project_name: str) -> Path:
    return MANIFESTS_DIR / f"{project_name}.json"


@tool
def save_manifest(
    project_name: str,
    github_repo: str = "",
    s3_bucket: str = "",
    cloudfront_distribution_id: str = "",
    cloudfront_domain: str = "",
    stitch_project_id: str = "",
    local_build_path: str = "",
) -> str:
    """Save or update a resource manifest for a design project.

    Tracks all provisioned AWS and GitHub resources so they can be torn down later.
    Call this after each provisioning step to keep the manifest current.

    Args:
        project_name: Unique project identifier (used as manifest filename).
        github_repo: GitHub repo in 'owner/name' format (e.g. 'user/my-app').
        s3_bucket: S3 bucket name where the app is deployed.
        cloudfront_distribution_id: CloudFront distribution ID.
        cloudfront_domain: CloudFront domain (e.g. 'd123abc.cloudfront.net').
        stitch_project_id: Stitch project ID used for design generation.
        local_build_path: Local path to the built project.

    Returns:
        Confirmation message with manifest path.
    """
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    path = _manifest_path(project_name)

    manifest: dict[str, Any] = {}
    if path.exists():
        manifest = json.loads(path.read_text())

    updates = {
        "github_repo": github_repo,
        "s3_bucket": s3_bucket,
        "cloudfront_distribution_id": cloudfront_distribution_id,
        "cloudfront_domain": cloudfront_domain,
        "stitch_project_id": stitch_project_id,
        "local_build_path": local_build_path,
    }
    for key, value in updates.items():
        if value:
            manifest[key] = value

    manifest["project_name"] = project_name
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    if "created_at" not in manifest:
        manifest["created_at"] = manifest["updated_at"]

    path.write_text(json.dumps(manifest, indent=2))
    return f"Manifest saved: {path}"


@tool
def load_manifest(project_name: str) -> str:
    """Load a resource manifest for a design project.

    Returns all tracked resources (GitHub repo, S3 bucket, CloudFront distribution, etc.)
    for the given project. Use this before destroy or status checks.

    Args:
        project_name: The project identifier to look up.

    Returns:
        JSON string of the manifest, or error if not found.
    """
    path = _manifest_path(project_name)
    if not path.exists():
        return json.dumps({"error": f"No manifest found for project '{project_name}'", "available": _list_projects()})
    return path.read_text()


def _list_projects() -> list[str]:
    """List all project names with manifests."""
    if not MANIFESTS_DIR.exists():
        return []
    return [p.stem for p in MANIFESTS_DIR.glob("*.json")]
