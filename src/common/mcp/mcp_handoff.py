from mcp.server.fastmcp import FastMCP

import logging

mcp = FastMCP("FireTools", host="0.0.0.0", port=3000, auth=None)


@mcp.tool("call_cops")
def call_cops(reason: str):
    logging.info("call cops")
    return "Handed off to operator, u can close the conversation"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
