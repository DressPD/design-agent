import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_mcp_client():
    with patch("src.mcp.clients.MCPClient") as mock_cls:
        yield mock_cls


@pytest.fixture
def mock_streamablehttp():
    with patch("src.mcp.clients.streamablehttp_client") as m:
        yield m


class TestCreateStitchClient:
    def test_returns_mcp_client_instance(self, mock_mcp_client, mock_streamablehttp, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
        from src.mcp.clients import create_stitch_client
        result = create_stitch_client()
        mock_mcp_client.assert_called_once()
        assert result is mock_mcp_client.return_value

    def test_uses_google_api_key(self, mock_mcp_client, mock_streamablehttp, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "my-google-key-xyz")
        from src.mcp.clients import create_stitch_client
        create_stitch_client()
        factory_fn = mock_mcp_client.call_args[0][0]
        factory_fn()
        mock_streamablehttp.assert_called_once()
        call_kwargs = mock_streamablehttp.call_args[1]
        assert call_kwargs["headers"]["X-Goog-Api-Key"] == "my-google-key-xyz"

    def test_uses_stitch_url(self, mock_mcp_client, mock_streamablehttp, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        from src.mcp.clients import create_stitch_client
        create_stitch_client()
        factory_fn = mock_mcp_client.call_args[0][0]
        factory_fn()
        call_kwargs = mock_streamablehttp.call_args[1]
        assert call_kwargs["url"] == "https://stitch.googleapis.com/mcp"

    def test_raises_when_no_google_key(self, mock_mcp_client, mock_streamablehttp, monkeypatch, tmp_path):
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        import src.config as config_module
        with patch.object(config_module, "_PROJECT_ENV_FILE", tmp_path / "missing.env"):
            from src.mcp.clients import create_stitch_client
            with pytest.raises(KeyError, match="GOOGLE_API_KEY"):
                create_stitch_client()

    def test_sets_timeout_on_http_client(self, mock_mcp_client, mock_streamablehttp, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        from src.mcp.clients import create_stitch_client
        create_stitch_client()
        factory_fn = mock_mcp_client.call_args[0][0]
        factory_fn()
        call_kwargs = mock_streamablehttp.call_args[1]
        assert call_kwargs["timeout"] == 60
