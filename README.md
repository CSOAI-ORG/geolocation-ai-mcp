<div align="center">

# Geolocation Ai MCP

**MCP server for geolocation ai mcp operations**

[![PyPI](https://img.shields.io/pypi/v/meok-geolocation-ai-mcp)](https://pypi.org/project/meok-geolocation-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Geolocation Ai MCP provides AI-powered tools via the Model Context Protocol (MCP).

## Tools

| Tool | Description |
|------|-------------|
| `geolocate_ip` | Get approximate location from IP address. |
| `calculate_distance` | Calculate distance between two coordinates using Haversine formula. |
| `parse_coordinates` | Parse location string into lat/lon coordinates. |
| `timezone_from_coords` | Determine timezone from coordinates using brute-force offset matching. |
| `ip_to_coordinates` | Convert IP address to approximate coordinates without full geolocation. |

## Installation

```bash
pip install meok-geolocation-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "geolocation-ai-mcp": {
      "command": "python",
      "args": ["-m", "meok_geolocation_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 5 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
