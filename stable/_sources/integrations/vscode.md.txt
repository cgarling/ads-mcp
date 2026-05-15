# VS Code (GitHub Copilot)

## GitHub Copilot in VS Code

### Prerequisites

- VS Code ≥ 1.95
- [GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) extension
- `uv` installed where MCP server will run

### Configuration

VS Code can support MCP definitions at different levels (`>` = Ctrl+Shift+P on Windows, Cmd+Shift+P on Mac).

 - workspace: `>MCP: Open Workspace Folder MCP Configuration
 - remote: `>MCP: Open Remote User Configuration
 - global: `>MCP: Open User Configuration

Here we use the `inputs` feature to avoid hard-coding our API token. Upon first starting the server, VS Code will ask you for your API key and store it securely. Start the server with `>MCP: List Servers`, select `ads`, and start server -- this will require `uv` to be installed where the server is running. Note from [VS Code docs](https://code.visualstudio.com/docs/copilot/customization/mcp-servers): MCP servers run wherever they are configured. Servers in your user profile run locally. If you're connected to a remote and want a server to run on the remote machine, define it in the workspace settings or remote user settings (MCP: Open Remote User Configuration).

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "ADS_API_TOKEN",
      "description": "ADS API Token",
      "password": true
    }
],
  "servers": {
    "ads": {
      "type": "stdio",
	  "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/cgarling/ads-mcp",
        "ads-mcp"
      ],
      "env": {
        "ADS_API_TOKEN": "${input:ADS_API_TOKEN}"
      },
      "tools": ["*"]
    }
  }
}
```
