from mcp.server.fastmcp import FastMCP

import logging

mcp = FastMCP("OrchTools", host="0.0.0.0", port=3000, auth=None)


@mcp.tool("operator_handoff")
def call_cops(summary: str):
    logging.info(f"operator_handoff summary:{summary}")
    return {
        "agent": "orchestrator_agent",
        "response": f"Operator handoff",
        "next_agent": "finish",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
