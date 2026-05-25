from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

from src.config import get_google_api_key


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
        )
    )
