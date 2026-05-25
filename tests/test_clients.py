import pytest
from unittest.mock import patch, MagicMock, call


@pytest.fixture
def mock_mcp_client():
    with patch("src.mcp.clients.MCPClient") as mock_cls:
        yield mock_cls


@pytest.fixture
def mock_streamablehttp():
    with patch("src.mcp.clients.streamablehttp_client") as m:
        yield m


@pytest.fixture
def mock_stdio():
    with patch("src.mcp.clients.stdio_client") as m:
        yield m


@pytest.fixture
def mock_stdio_params():
    with patch("src.mcp.clients.StdioServerParameters") as m:
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
        with patch.object(config_module, "OPENCODE_ENV_FILE", tmp_path / "missing.env"):
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


class TestCreateTwentyfirstClient:
    def test_returns_mcp_client_instance(self, mock_mcp_client, mock_stdio, mock_stdio_params, monkeypatch):
        monkeypatch.setenv("TWENTYFIRST_API_KEY", "test-21st-key")
        from src.mcp.clients import create_twentyfirst_client
        result = create_twentyfirst_client()
        mock_mcp_client.assert_called_once()
        assert result is mock_mcp_client.return_value

    def test_uses_twentyfirst_api_key(self, mock_mcp_client, mock_stdio, mock_stdio_params, monkeypatch):
        monkeypatch.setenv("TWENTYFIRST_API_KEY", "my-21st-key-abc")
        from src.mcp.clients import create_twentyfirst_client
        create_twentyfirst_client()
        factory_fn = mock_mcp_client.call_args[0][0]
        factory_fn()
        params_call_kwargs = mock_stdio_params.call_args[1]
        assert params_call_kwargs["env"]["API_KEY"] == "my-21st-key-abc"

    def test_uses_npx_command(self, mock_mcp_client, mock_stdio, mock_stdio_params, monkeypatch):
        monkeypatch.setenv("TWENTYFIRST_API_KEY", "test-key")
        from src.mcp.clients import create_twentyfirst_client
        create_twentyfirst_client()
        factory_fn = mock_mcp_client.call_args[0][0]
        factory_fn()
        params_call_kwargs = mock_stdio_params.call_args[1]
        assert params_call_kwargs["command"] == "npx"

    def test_uses_magic_package(self, mock_mcp_client, mock_stdio, mock_stdio_params, monkeypatch):
        monkeypatch.setenv("TWENTYFIRST_API_KEY", "test-key")
        from src.mcp.clients import create_twentyfirst_client
        create_twentyfirst_client()
        factory_fn = mock_mcp_client.call_args[0][0]
        factory_fn()
        params_call_kwargs = mock_stdio_params.call_args[1]
        assert "@21st-dev/magic@latest" in params_call_kwargs["args"]

    def test_raises_when_no_twentyfirst_key(self, mock_mcp_client, mock_stdio, mock_stdio_params, monkeypatch, tmp_path):
        monkeypatch.delenv("TWENTYFIRST_API_KEY", raising=False)
        import src.config as config_module
        with patch.object(config_module, "OPENCODE_ENV_FILE", tmp_path / "missing.env"):
            from src.mcp.clients import create_twentyfirst_client
            with pytest.raises(KeyError, match="TWENTYFIRST_API_KEY"):
                create_twentyfirst_client()

    def test_passes_path_env_var(self, mock_mcp_client, mock_stdio, mock_stdio_params, monkeypatch):
        monkeypatch.setenv("TWENTYFIRST_API_KEY", "test-key")
        monkeypatch.setenv("PATH", "/usr/bin:/usr/local/bin")
        from src.mcp.clients import create_twentyfirst_client
        create_twentyfirst_client()
        factory_fn = mock_mcp_client.call_args[0][0]
        factory_fn()
        params_call_kwargs = mock_stdio_params.call_args[1]
        assert "PATH" in params_call_kwargs["env"]
