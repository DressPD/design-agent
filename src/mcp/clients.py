from mcp.client.streamable_http import streamablehttp_client
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters
from strands.tools.mcp import MCPClient

from src.config import get_google_api_key, get_21st_dev_api_key


def create_stitch_client() -> MCPClient:
    """Create MCP client for Google Stitch — screen/design generation via HTTP transport.

    Reads GOOGLE_API_KEY from env vars or project .env file.
    """
    api_key = get_google_api_key()

    return MCPClient(
        lambda: streamablehttp_client(
            url="https://stitch.googleapis.com/mcp",
            headers={"X-Goog-Api-Key": api_key},
            timeout=60,
        ),
        startup_timeout=60,
    )


def create_21st_dev_client() -> MCPClient:
    """Create MCP client for 21st.dev Magic — animated component generation via stdio transport.

    Reads TWENTYFIRST_API_KEY from env vars or project .env file.
    Launches `npx -y @21st-dev/magic@latest` as a subprocess.
    """
    api_key = get_21st_dev_api_key()

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@21st-dev/magic@latest"],
        env={"API_KEY": api_key},
    )

    return MCPClient(lambda: stdio_client(server_params), startup_timeout=120)
