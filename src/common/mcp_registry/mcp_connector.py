import asyncio
from src.common.mcp_registry.mcp_registry import MCPRegistry
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams
from src.common.logger.logger import get_logger

logger = get_logger("mcp")


class MCPConnector:
    """Discovers MCP servers, loads and caches their tools as MCPToolsets."""

    def __init__(self, config_file: str = None):
        self.discovery = MCPRegistry(config_file)
        self.tools: list[MCPToolset] = []

    async def _load_all_tools(self):
        tools = []
        for name, server in self.discovery.list_servers().items():
            logger.info(name, server)
            try:
                conn = StreamableHTTPServerParams(url=server["args"][0])
                toolset = await asyncio.wait_for(
                    MCPToolset(connection_params=conn).get_tools(), timeout=10
                )
                if toolset:
                    tools.append(MCPToolset(connection_params=conn))
                    print(
                        f"[green]Loaded tools from '{name}':[/green] {[t.name for t in toolset]}"
                    )
            except Exception as e:
                print(f"[red]Error loading tools from '{name}': {e}[/red]")
        self.tools = tools

    async def get_tools(self) -> list[MCPToolset]:
        await self._load_all_tools()
        return self.tools.copy()
