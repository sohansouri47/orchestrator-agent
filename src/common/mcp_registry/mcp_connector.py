import asyncio
import logging

# from src.common.mcp_registry.mcp_registry import MCPDiscovery
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
import json
from mcp import StdioServerParameters
import os

# ADDED: Configure logging for MCP cleanup issues to reduce noise during shutdown
logging.getLogger("mcp").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


class MCPConnector:
    """
    Discovers the MCP servers from the config.
    Config will be loaded by the MCP discovery class
    Then it lists each server's tools
    and then caches them as MCPToolsets that are compatible with
    Google's Agent Development Kit
    """

    def __init__(self, config_file: str = None):
        raw = os.getenv("MCPREGISTRY", "[]")  # always default to valid JSON string
        try:
            self.discovery = json.loads(raw)
        except json.JSONDecodeError:
            logger.error(f"Invalid MCPREGISTRY format: {raw}")
            self.discovery = []
        self.tools: list[MCPToolset] = []
        logger.info(self.discovery)
        self.tools: list[MCPToolset] = []

    async def _load_all_tools(self):
        """
        Loads all tools from the discovered MCP servers
        and caches them as MCPToolsets.
        """

        tools = []

        for server in self.discovery:
            logger.info(server)
            try:
                conn = StreamableHTTPServerParams(url=server)
                toolset = await asyncio.wait_for(
                    MCPToolset(connection_params=conn).get_tools(), timeout=10.0
                )

                if toolset:
                    # Create the actual toolset object for caching
                    mcp_toolset = MCPToolset(connection_params=conn)
                    tool_names = [tool.name for tool in toolset]
                    # print(
                    #     f"[bold green]Loaded tools from server [cyan]'{name}'[/cyan]:[/bold green] {', '.join(tool_names)}"
                    # )
                    tools.append(mcp_toolset)

            # ADDED: Specific error handling for different types of connection failures
            except asyncio.TimeoutError:
                print(f"[bold red]Timeout loading tools from server ")
            except ConnectionError as e:
                print(f"[bold red]Connection error loading tools from server ")
            except Exception as e:
                print(f"[bold red]Error loading tools from server ")

        self.tools = tools

    async def get_tools(self) -> list[MCPToolset]:
        """
        Returns the cached list of MCPToolsets.
        """

        await self._load_all_tools()
        return self.tools.copy()
