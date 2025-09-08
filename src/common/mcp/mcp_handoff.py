import logging
import os
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OrchestratorMCP")

# Read host and port from environment variables, provide defaults
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "3000"))

logger.info(f"Starting Orchestrator MCP server on {MCP_HOST}:{MCP_PORT}")

# Initialize MCP server
mcp = FastMCP("OrchTools", host=MCP_HOST, port=MCP_PORT, auth=None)


@mcp.tool("operator_handoff")
async def operator_handoff(summary: str):
    """
    Tool callable by orchestrator agent to handoff to human operator.
    """
    logger.info(f"Operator handoff summary: {summary}")
    return {
        "agent": "orchestrator_agent",
        "response": "Operator handoff initiated",
        "next_agent": "finish",
    }


if __name__ == "__main__":
    # Use streamable-http transport
    mcp.run(transport="streamable-http")
