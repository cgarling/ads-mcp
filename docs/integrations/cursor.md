# Cursor

[Cursor](https://www.cursor.com/) supports MCP servers starting from
version 0.43.

## Configuration

Open **Cursor Settings** (`Cmd/Ctrl+Shift+J`) → **MCP** tab → **Add
new MCP server**.

Fill in:

| Field | Value |
|-------|-------|
| Name | `ads` |
| Type | `command` |
| Command | `ads-mcp` |

Then click **Save**.

Alternatively, edit `~/.cursor/mcp.json` (created automatically by
Cursor):

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

## API key

If you do not want to hard-code the key in the JSON file, set it as an
environment variable in your shell profile:

```bash
export ADS_API_KEY=your_key_here
```

Cursor inherits your shell's environment when it launches `ads-mcp`.

## Usage

In Cursor Chat, enable the `ads` MCP server by clicking the *Tools* icon.
Then ask natural-language questions:

> "Find recent papers on fast radio bursts."

> "Export the references of 2019ApJ...887L..24M as BibTeX."
