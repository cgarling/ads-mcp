# Claude Desktop

[Claude Desktop](https://claude.ai/download) supports MCP servers through
its configuration file.

## Configuration

Locate your Claude Desktop configuration file:

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

Add (or merge) the following JSON:

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

If `ads-mcp` is not on your `PATH`, use the absolute path to the script,
e.g. `/usr/local/bin/ads-mcp` or the path reported by `which ads-mcp`.

## Restart

Restart Claude Desktop to pick up the configuration change.  You should
see `ads` listed under *Connected MCP Servers* in the settings panel.

## Usage

In a Claude conversation, simply ask about papers:

> "What are the most influential papers on dark energy in the last five years?"

> "Give me the BibTeX for DOI 10.3847/2041-8213/ab5c56."

> "How many times has arXiv:2301.07688 been cited?"
