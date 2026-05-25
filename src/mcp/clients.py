import os

from mcp import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

from src.config import get_google_api_key, get_twentyfirst_api_key


def create_stitch_client() -> MCPClient:
    """Create MCP client for Google Stitch — screen/design generation via HTTP transport.

    Reads GOOGLE_API_KEY from env vars or ~/.config/opencode/.env.
    """
    api_key = get_google_api_key()

    return MCPClient(
        lambda: streamablehttp_client(
            url="https://stitch.googleapis.com/mcp",
            headers={"X-Goog-Api-Key": api_key},
            timeout=60,
        )
    )


def create_twentyfirst_client() -> MCPClient:
    """Create MCP client for 21st.dev — React component generation via stdio transport.

    Reads TWENTYFIRST_API_KEY from env vars or ~/.config/opencode/.env.
    """
    api_key = get_twentyfirst_api_key()

    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(
                command="npx",
                args=["-y", "@21st-dev/magic@latest"],
                env={"API_KEY": api_key, "PATH": os.environ.get("PATH", "")},
            )
        )
    )
