import json
import pytest
from unittest.mock import patch, MagicMock, call

from src.tools.deploy import deploy_to_aws


def make_run_result(returncode=0, stdout="", stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


@pytest.fixture
def mock_cf_client():
    client = MagicMock()
    client.create_invalidation.return_value = {"Invalidation": {"Id": "INV123"}}
    client.get_distribution.return_value = {
        "Distribution": {"DomainName": "d123abc.cloudfront.net"}
    }
    return client


@pytest.fixture
def mock_boto3(mock_cf_client):
    with patch("src.tools.deploy.boto3.client", return_value=mock_cf_client) as m:
        yield m, mock_cf_client


VALID_DIST = "/tmp/design-agent-builds/test-app/dist"


class TestDeployToAws:
    def test_success_returns_live_url_with_prefix(self, mock_boto3):
        _, cf_client = mock_boto3
        sync_ok = make_run_result(returncode=0)
        cp_ok = make_run_result(returncode=0)
        with patch("src.tools.deploy.subprocess.run", side_effect=[sync_ok, cp_ok]):
            result = deploy_to_aws("test-app", VALID_DIST, "my-bucket", "DIST123")
        data = json.loads(result)
        assert data["live_url"] == "https://d123abc.cloudfront.net/test-app/"
        assert data["cloudfront_domain"] == "https://d123abc.cloudfront.net"
        assert data["deploy_status"] == "success"

    def test_success_returns_s3_bucket_and_prefix(self, mock_boto3):
        _, cf_client = mock_boto3
        sync_ok = make_run_result(returncode=0)
        cp_ok = make_run_result(returncode=0)
        with patch("src.tools.deploy.subprocess.run", side_effect=[sync_ok, cp_ok]):
            result = deploy_to_aws("test-app", VALID_DIST, "my-bucket", "DIST123")
        data = json.loads(result)
        assert data["s3_bucket"] == "my-bucket"
        assert data["s3_prefix"] == "test-app"
        assert data["cloudfront_distribution_id"] == "DIST123"

    def test_s3_sync_failure_returns_error(self, mock_boto3):
        sync_fail = make_run_result(returncode=1, stderr="Access Denied")
        with patch("src.tools.deploy.subprocess.run", return_value=sync_fail):
            result = deploy_to_aws("test-app", VALID_DIST, "my-bucket", "DIST123")
        data = json.loads(result)
        assert "error" in data
        assert data["error"] == "s3 sync failed"

    def test_calls_aws_s3_sync_with_delete_flag(self, mock_boto3):
        sync_ok = make_run_result(returncode=0)
        cp_ok = make_run_result(returncode=0)
        with patch("src.tools.deploy.subprocess.run", side_effect=[sync_ok, cp_ok]) as mock_run:
            deploy_to_aws("test-app", VALID_DIST, "my-bucket", "DIST123")
        sync_call_args = mock_run.call_args_list[0][0][0]
        assert "aws" in sync_call_args
        assert "s3" in sync_call_args
        assert "sync" in sync_call_args
        assert "--delete" in sync_call_args

    def test_calls_aws_s3_sync_with_prefixed_bucket(self, mock_boto3):
        sync_ok = make_run_result(returncode=0)
        cp_ok = make_run_result(returncode=0)
        with patch("src.tools.deploy.subprocess.run", side_effect=[sync_ok, cp_ok]) as mock_run:
            deploy_to_aws("test-app", VALID_DIST, "my-bucket", "DIST123")
        sync_call_args = mock_run.call_args_list[0][0][0]
        assert "s3://my-bucket/test-app/" in sync_call_args

    def test_creates_cf_invalidation_with_prefix(self, mock_boto3):
        _, cf_client = mock_boto3
        sync_ok = make_run_result(returncode=0)
        cp_ok = make_run_result(returncode=0)
        with patch("src.tools.deploy.subprocess.run", side_effect=[sync_ok, cp_ok]):
            deploy_to_aws("test-app", VALID_DIST, "my-bucket", "DIST123")
        cf_client.create_invalidation.assert_called_once()
        call_kwargs = cf_client.create_invalidation.call_args[1]
        assert call_kwargs["DistributionId"] == "DIST123"
        assert call_kwargs["InvalidationBatch"]["Paths"]["Items"] == ["/test-app/*"]

    def test_cf_invalidation_caller_reference_includes_project_name(self, mock_boto3):
        _, cf_client = mock_boto3
        sync_ok = make_run_result(returncode=0)
        cp_ok = make_run_result(returncode=0)
        with patch("src.tools.deploy.subprocess.run", side_effect=[sync_ok, cp_ok]):
            deploy_to_aws("test-app", VALID_DIST, "my-bucket", "DIST123")
        call_kwargs = cf_client.create_invalidation.call_args[1]
        caller_ref = call_kwargs["InvalidationBatch"]["CallerReference"]
        assert "test-app" in caller_ref
        assert "design-agent" in caller_ref

    def test_copies_index_html_with_no_cache_to_prefix(self, mock_boto3):
        sync_ok = make_run_result(returncode=0)
        cp_ok = make_run_result(returncode=0)
        with patch("src.tools.deploy.subprocess.run", side_effect=[sync_ok, cp_ok]) as mock_run:
            deploy_to_aws("test-app", VALID_DIST, "my-bucket", "DIST123")
        cp_call_args = mock_run.call_args_list[1][0][0]
        assert "cp" in cp_call_args
        assert "no-cache" in " ".join(cp_call_args)
        assert "s3://my-bucket/test-app/index.html" in cp_call_args

    def test_rejects_path_traversal_in_dist_path(self, mock_boto3):
        result = deploy_to_aws("test-app", "/tmp/../etc/passwd", "my-bucket", "DIST123")
        data = json.loads(result)
        assert "error" in data

    def test_rejects_invalid_project_name(self, mock_boto3):
        result = deploy_to_aws("../evil", VALID_DIST, "my-bucket", "DIST123")
        data = json.loads(result)
        assert "error" in data
