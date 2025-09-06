import json
import os
from typing import Any, Dict
from src.common.logger.logger import get_logger

logger = get_logger("refi")


class MCPRegistry:
    """Load MCP server definitions from a JSON config file."""

    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.join(
            os.path.dirname(__file__), "mcp_registry.json"
        )
        self.config = self._load_config()
        logger.info(self.config)

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_file, "r") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("Invalid config format")
            return data
        except FileNotFoundError:
            raise FileNotFoundError(f"{self.config_file} not found")
        except Exception as e:
            raise RuntimeError(f"Error reading config: {e}")

    def list_servers(self) -> Dict[str, Any]:
        if "mcpServers" not in self.config:
            raise KeyError("'mcpServers' key not found in config")
        return self.config["mcpServers"]
