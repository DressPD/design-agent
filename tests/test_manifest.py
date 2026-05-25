import json
import pytest
from pathlib import Path
from unittest.mock import patch

import src.tools.manifest as manifest_module
from src.tools.manifest import save_manifest, load_manifest, _list_projects


@pytest.fixture
def manifests_dir(tmp_path):
    d = tmp_path / "manifests"
    d.mkdir()
    return d


@pytest.fixture(autouse=True)
def patch_manifests_dir(manifests_dir):
    with patch.object(manifest_module, "MANIFESTS_DIR", manifests_dir):
        yield manifests_dir


class TestSaveManifest:
    def test_creates_manifest_file(self, manifests_dir):
        result = save_manifest("myproject")
        assert (manifests_dir / "myproject.json").exists()
        assert "myproject" in result

    def test_saves_all_fields(self, manifests_dir):
        save_manifest(
            "proj1",
            github_repo="user/proj1",
            s3_bucket="my-bucket",
            cloudfront_distribution_id="ABCDEF",
            cloudfront_domain="d123.cloudfront.net",
            stitch_project_id="stitch-123",
            local_build_path="/tmp/proj1",
        )
        data = json.loads((manifests_dir / "proj1.json").read_text())
        assert data["github_repo"] == "user/proj1"
        assert data["s3_bucket"] == "my-bucket"
        assert data["cloudfront_distribution_id"] == "ABCDEF"
        assert data["cloudfront_domain"] == "d123.cloudfront.net"
        assert data["stitch_project_id"] == "stitch-123"
        assert data["local_build_path"] == "/tmp/proj1"
        assert data["project_name"] == "proj1"

    def test_sets_created_at_on_first_save(self, manifests_dir):
        save_manifest("proj2")
        data = json.loads((manifests_dir / "proj2.json").read_text())
        assert "created_at" in data
        assert "updated_at" in data
        assert data["created_at"] == data["updated_at"]

    def test_preserves_created_at_on_update(self, manifests_dir):
        save_manifest("proj3", s3_bucket="bucket1")
        first = json.loads((manifests_dir / "proj3.json").read_text())
        save_manifest("proj3", s3_bucket="bucket2")
        second = json.loads((manifests_dir / "proj3.json").read_text())
        assert second["created_at"] == first["created_at"]
        assert second["s3_bucket"] == "bucket2"

    def test_does_not_overwrite_existing_fields_with_empty(self, manifests_dir):
        save_manifest("proj4", s3_bucket="my-bucket")
        save_manifest("proj4")
        data = json.loads((manifests_dir / "proj4.json").read_text())
        assert data["s3_bucket"] == "my-bucket"

    def test_updates_existing_field(self, manifests_dir):
        save_manifest("proj5", s3_bucket="old-bucket")
        save_manifest("proj5", s3_bucket="new-bucket")
        data = json.loads((manifests_dir / "proj5.json").read_text())
        assert data["s3_bucket"] == "new-bucket"

    def test_creates_manifests_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / "new_manifests"
        with patch.object(manifest_module, "MANIFESTS_DIR", new_dir):
            save_manifest("proj6")
        assert new_dir.exists()


class TestLoadManifest:
    def test_returns_manifest_json(self, manifests_dir):
        save_manifest("loadme", s3_bucket="test-bucket")
        result = load_manifest("loadme")
        data = json.loads(result)
        assert data["s3_bucket"] == "test-bucket"
        assert data["project_name"] == "loadme"

    def test_returns_error_when_not_found(self, manifests_dir):
        result = load_manifest("nonexistent")
        data = json.loads(result)
        assert "error" in data
        assert "nonexistent" in data["error"]

    def test_error_includes_available_projects(self, manifests_dir):
        save_manifest("existing_proj")
        result = load_manifest("nonexistent")
        data = json.loads(result)
        assert "available" in data
        assert "existing_proj" in data["available"]


class TestListProjects:
    def test_returns_empty_when_dir_missing(self, tmp_path):
        missing = tmp_path / "no_manifests"
        with patch.object(manifest_module, "MANIFESTS_DIR", missing):
            assert _list_projects() == []

    def test_returns_project_names(self, manifests_dir):
        save_manifest("alpha")
        save_manifest("beta")
        projects = _list_projects()
        assert "alpha" in projects
        assert "beta" in projects

    def test_only_returns_json_stems(self, manifests_dir):
        (manifests_dir / "not_a_project.txt").write_text("ignore me")
        save_manifest("real_project")
        projects = _list_projects()
        assert "real_project" in projects
        assert "not_a_project" not in projects
