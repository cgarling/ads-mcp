# VS Code (GitHub Copilot / Continue)

## GitHub Copilot in VS Code

### Prerequisites

- VS Code ≥ 1.95
- [GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) extension

### Configuration

Open (or create) `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "ads": {
      "type": "stdio",
      "command": "ads-mcp",
      "env": {
        "ADS_API_TOKEN": "${env:ADS_API_TOKEN}"
      }
    }
  }
}
```

Set `ADS_API_TOKEN` in your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
export ADS_API_TOKEN=your_key_here
```

Then restart VS Code (or reload the window with `Ctrl+Shift+P` →
*Developer: Reload Window*).

In Copilot Chat, switch to **Agent** mode and select the `ads` server.

## Continue extension

If you use the [Continue](https://marketplace.visualstudio.com/items?itemName=Continue.continue)
extension, add the following to `~/.continue/config.json`:

```json
{
  "mcpServers": {
    "ads": {
      "command": "ads-mcp",
      "env": {
        "ADS_API_TOKEN": "your_key_here"
      }
    }
  }
}
```
