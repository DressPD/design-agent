import sys
import os
import types
from unittest.mock import MagicMock
import pytest


def _make_strands_stub():
    strands = types.ModuleType("strands")

    def tool(fn):
        return fn

    strands.tool = tool
    sys.modules["strands"] = strands
    sys.modules["strands.tools"] = types.ModuleType("strands.tools")
    sys.modules["strands.tools.mcp"] = types.ModuleType("strands.tools.mcp")
    mcp_mod = sys.modules["strands.tools.mcp"]
    mcp_mod.MCPClient = MagicMock()
    return strands


def _make_mcp_stub():
    mcp = types.ModuleType("mcp")
    mcp.StdioServerParameters = MagicMock()
    mcp.stdio_client = MagicMock()
    sys.modules["mcp"] = mcp

    client_mod = types.ModuleType("mcp.client")
    sys.modules["mcp.client"] = client_mod

    streamable_mod = types.ModuleType("mcp.client.streamable_http")
    streamable_mod.streamablehttp_client = MagicMock()
    sys.modules["mcp.client.streamable_http"] = streamable_mod

    return mcp


def _make_playwright_stub():
    playwright = types.ModuleType("playwright")
    sync_api = types.ModuleType("playwright.sync_api")
    sync_api.sync_playwright = MagicMock()
    sys.modules["playwright"] = playwright
    sys.modules["playwright.sync_api"] = sync_api
    return playwright


if "strands" not in sys.modules:
    _make_strands_stub()
if "mcp" not in sys.modules:
    _make_mcp_stub()
if "playwright" not in sys.modules:
    _make_playwright_stub()


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("TWENTYFIRST_API_KEY", raising=False)
    return monkeypatch


@pytest.fixture
def env_with_google_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    return monkeypatch


@pytest.fixture
def env_with_twentyfirst_key(monkeypatch):
    monkeypatch.setenv("TWENTYFIRST_API_KEY", "test-21st-key")
    return monkeypatch
