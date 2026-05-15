# Other MCP Clients

## Zed Editor

[Zed](https://zed.dev/) supports MCP servers.  Add the following to your
Zed settings (`~/.config/zed/settings.json`):

```json
{
  "context_servers": {
    "ads": {
      "command": {
        "path": "ads-mcp",
        "args": []
      },
      "settings": {}
    }
  }
}
```

Set `ADS_API_KEY` in your environment before launching Zed.

---

## Any MCP-compatible client

ads-mcp uses the standard **stdio** transport defined by the MCP
specification.  Any client that can launch a subprocess and communicate
with it over stdin/stdout can use ads-mcp.

Generic configuration pattern:

```json
{
  "mcpServers": {
    "ads": {
      "command": "ads-mcp",
      "env": {
        "ADS_API_KEY": "your_key_here"
      }
    }
  }
}
```

---

## Running as a standalone HTTP server

FastMCP also supports HTTP/SSE transport.  To start ads-mcp as an HTTP
server (for example, to serve multiple clients):

```python
import os
from ads_mcp.server import mcp

os.environ["ADS_API_KEY"] = "your_key_here"
mcp.run(transport="streamable-http", host="127.0.0.1", port=8080)
```

Then configure your MCP client to connect to `http://127.0.0.1:8080/mcp`.

---

## Python SDK / programmatic access

You can also call the server programmatically using the
[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk):

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="ads-mcp",
    env={"ADS_API_KEY": "your_key_here"},
)

async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "search_ads",
                {"query": "exoplanet atmospheres", "rows": 5},
            )
            print(result.content[0].text)

asyncio.run(main())
```
