import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import src.tools.destroy as destroy_module
from src.tools.destroy import destroy_resources, _destroy_s3, _disable_cloudfront, _destroy_github_repo


def make_run_result(returncode=0, stdout="", stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


@pytest.fixture
def manifests_dir(tmp_path):
    d = tmp_path / "manifests"
    d.mkdir()
    return d


@pytest.fixture(autouse=True)
def patch_manifests_dir(manifests_dir):
    with patch.object(destroy_module, "MANIFESTS_DIR", manifests_dir):
        yield manifests_dir


def write_manifest(manifests_dir, project_name, data):
    path = manifests_dir / f"{project_name}.json"
    path.write_text(json.dumps(data))
    return path


class TestDestroyResources:
    def test_returns_error_when_no_manifest(self, manifests_dir):
        result = destroy_resources("nonexistent")
        data = json.loads(result)
        assert "error" in data
        assert "nonexistent" in data["error"]

    def test_destroys_s3_bucket(self, manifests_dir):
        write_manifest(manifests_dir, "myproj", {"s3_bucket": "my-bucket"})
        ok = make_run_result(returncode=0)
        with patch("src.tools.destroy.subprocess.run", return_value=ok):
            result = destroy_resources("myproj")
        data = json.loads(result)
        assert data["destroyed"]["s3"] == "emptied"

    def test_disables_cloudfront(self, manifests_dir):
        write_manifest(manifests_dir, "myproj", {"cloudfront_distribution_id": "DIST123"})
        mock_cf = MagicMock()
        mock_cf.get_distribution_config.return_value = {
            "DistributionConfig": {"Enabled": True},
            "ETag": "etag123",
        }
        with patch("src.tools.destroy.boto3.client", return_value=mock_cf):
            result = destroy_resources("myproj")
        data = json.loads(result)
        assert "disabled" in data["destroyed"]["cloudfront"]

    def test_deletes_github_repo(self, manifests_dir):
        write_manifest(manifests_dir, "myproj", {"github_repo": "user/myproj"})
        ok = make_run_result(returncode=0)
        with patch("src.tools.destroy.subprocess.run", return_value=ok):
            result = destroy_resources("myproj")
        data = json.loads(result)
        assert data["destroyed"]["github"] == "deleted"

    def test_removes_local_build_path(self, manifests_dir, tmp_path):
        build_dir = tmp_path / "design-agent-builds" / "myproj"
        build_dir.mkdir(parents=True)
        with patch("src.tools.destroy.safe_build_path", return_value=str(build_dir)):
            write_manifest(manifests_dir, "myproj", {"local_build_path": str(build_dir)})
            result = destroy_resources("myproj")
        data = json.loads(result)
        assert data["destroyed"]["local"] == "removed"
        assert not build_dir.exists()

    def test_removes_manifest_file(self, manifests_dir):
        manifest_path = write_manifest(manifests_dir, "myproj", {})
        result = destroy_resources("myproj")
        data = json.loads(result)
        assert data["destroyed"]["manifest"] == "removed"
        assert not manifest_path.exists()

    def test_skips_missing_optional_resources(self, manifests_dir):
        write_manifest(manifests_dir, "myproj", {})
        result = destroy_resources("myproj")
        data = json.loads(result)
        assert "s3" not in data["destroyed"]
        assert "cloudfront" not in data["destroyed"]
        assert "github" not in data["destroyed"]

    def test_destroys_all_resources_in_full_manifest(self, manifests_dir, tmp_path):
        build_dir = tmp_path / "design-agent-builds" / "myproj"
        build_dir.mkdir(parents=True)
        write_manifest(manifests_dir, "myproj", {
            "s3_bucket": "my-bucket",
            "cloudfront_distribution_id": "DIST123",
            "github_repo": "user/myproj",
            "local_build_path": str(build_dir),
        })
        ok = make_run_result(returncode=0)
        mock_cf = MagicMock()
        mock_cf.get_distribution_config.return_value = {
            "DistributionConfig": {"Enabled": True},
            "ETag": "etag123",
        }
        with patch("src.tools.destroy.subprocess.run", return_value=ok):
            with patch("src.tools.destroy.boto3.client", return_value=mock_cf):
                with patch("src.tools.destroy.safe_build_path", return_value=str(build_dir)):
                    result = destroy_resources("myproj")
        data = json.loads(result)
        assert set(data["destroyed"].keys()) == {"s3", "cloudfront", "github", "local", "manifest"}


class TestDestroyS3:
    def test_returns_emptied_on_success(self):
        ok = make_run_result(returncode=0)
        with patch("src.tools.destroy.subprocess.run", return_value=ok):
            assert _destroy_s3("my-bucket", "myproj") == "emptied"

    def test_returns_failed_on_error(self):
        fail = make_run_result(returncode=1, stderr="Access Denied")
        with patch("src.tools.destroy.subprocess.run", return_value=fail):
            result = _destroy_s3("my-bucket", "myproj")
        assert "failed" in result

    def test_calls_aws_s3_rm_recursive_with_prefix(self):
        ok = make_run_result(returncode=0)
        with patch("src.tools.destroy.subprocess.run", return_value=ok) as mock_run:
            _destroy_s3("my-bucket", "myproj")
        args = mock_run.call_args[0][0]
        assert "aws" in args
        assert "s3" in args
        assert "rm" in args
        assert "--recursive" in args
        assert "s3://my-bucket/myproj/" in args


class TestDisableCloudfront:
    def test_returns_disabled_message_on_success(self):
        mock_cf = MagicMock()
        mock_cf.get_distribution_config.return_value = {
            "DistributionConfig": {"Enabled": True},
            "ETag": "etag123",
        }
        with patch("src.tools.destroy.boto3.client", return_value=mock_cf):
            result = _disable_cloudfront("DIST123")
        assert "disabled" in result

    def test_calls_update_distribution_with_enabled_false(self):
        mock_cf = MagicMock()
        mock_cf.get_distribution_config.return_value = {
            "DistributionConfig": {"Enabled": True},
            "ETag": "etag123",
        }
        with patch("src.tools.destroy.boto3.client", return_value=mock_cf):
            _disable_cloudfront("DIST123")
        call_kwargs = mock_cf.update_distribution.call_args[1]
        assert call_kwargs["DistributionConfig"]["Enabled"] is False
        assert call_kwargs["IfMatch"] == "etag123"

    def test_returns_failed_on_exception(self):
        mock_cf = MagicMock()
        mock_cf.get_distribution_config.side_effect = Exception("NoSuchDistribution")
        with patch("src.tools.destroy.boto3.client", return_value=mock_cf):
            result = _disable_cloudfront("DIST123")
        assert "failed" in result


class TestDestroyGithubRepo:
    def test_returns_deleted_on_success(self):
        ok = make_run_result(returncode=0)
        with patch("src.tools.destroy.subprocess.run", return_value=ok):
            assert _destroy_github_repo("user/myrepo") == "deleted"

    def test_returns_failed_on_error(self):
        fail = make_run_result(returncode=1, stderr="repo not found")
        with patch("src.tools.destroy.subprocess.run", return_value=fail):
            result = _destroy_github_repo("user/myrepo")
        assert "failed" in result

    def test_calls_gh_repo_delete_with_yes(self):
        ok = make_run_result(returncode=0)
        with patch("src.tools.destroy.subprocess.run", return_value=ok) as mock_run:
            _destroy_github_repo("user/myrepo")
        args = mock_run.call_args[0][0]
        assert "gh" in args
        assert "repo" in args
        assert "delete" in args
        assert "--yes" in args
        assert "user/myrepo" in args
