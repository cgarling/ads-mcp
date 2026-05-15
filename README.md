# ads-mcp

[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://cgarling.github.io/ads-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

**ads-mcp** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that gives AI assistants direct access to the [SAO/NASA Astrophysics Data System (ADS)](https://ui.adsabs.harvard.edu/) bibliographic database.

With ads-mcp your AI assistant can:

- 🔍 **Search** millions of astronomy, astrophysics, and physics papers
- 📄 **Retrieve** abstracts, full metadata, and keywords
- 🔗 **Fetch** reference lists and citing papers
- 📊 **Compute** h-index, citation counts, and other bibliometric indicators
- 📚 **Export** formatted citations in BibTeX, RIS, AASTeX, MNRAS, and more
- 🆔 **Resolve** arXiv IDs and DOIs to full ADS records

---

## Table of Contents

- [Quick Start](#quick-start)
- [Available Tools](#available-tools)
- [Configuration](#configuration)
- [Integration Guides](#integration-guides)
- [Documentation](#documentation)
- [Development](#development)
- [License](#license)

---

## Running the Server

### 1. Get an ADS API token

Create an account at <https://ui.adsabs.harvard.edu> and generate an API
token at <https://ui.adsabs.harvard.edu/user/settings/token>.

### 2. Install

From source:

```bash
git clone https://github.com/cgarling/ads-mcp.git
cd ads-mcp
pip install -e .
```

### 3. Configure

Either make your token available via an environment variable `ADS_API_TOKEN` or create and edit `.env` to contain it.

```bash
cp .env.example .env
# Edit .env and add your key:
#   ADS_API_TOKEN=your_token_here
```

### 4. Run

```bash
ads-mcp
```

The server listens on **stdin/stdout** (MCP stdio transport) and is ready
to be used by any MCP-compatible client.

---

## Available Tools

| Tool | Description |
|------|-------------|
| `search_ads` | Full-text / keyword / author search using ADS/Solr query syntax |
| `get_abstract` | Full metadata + abstract for a bibcode |
| `get_references` | Reference list of a paper |
| `get_citations` | Papers that cite a given paper |
| `export_bibtex` | BibTeX export for one or more bibcodes |
| `export_ris` | RIS export (Zotero, Mendeley, EndNote) |
| `export_citation` | Export in any ADS-supported format |
| `find_arxiv` | Look up a paper by arXiv ID |
| `find_doi` | Look up a paper by DOI |
| `get_metrics` | Citation & usage metrics (h-index, g-index, i10, ...) |
| `get_similar` | Papers similar to a given bibcode |
| `author_search` | Search papers by author name |
| `get_paper_details` | Comprehensive metadata for a paper |

See the [Tools documentation](https://cgarling.github.io/ads-mcp/stable/tools.html) for full parameter references.

### Example queries you can ask your AI assistant

> "Find the 10 most-cited papers on gravitational wave detection."

> "What are the references of 2019ApJ...887L..24M?"

> "Give me the BibTeX for DOI 10.3847/2041-8213/ab5c56."

> "How many times has arXiv:2301.07688 been cited?"

> "Search for refereed papers by author Einstein published before 1950."

> "What papers are similar to 2017ApJ...848L..12A?"

---

## Configuration

Set these environment variables (or put them in a `.env` file):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ADS_API_TOKEN` | yes | — | Your ADS API bearer token |
| `ADS_MCP_LOG_LEVEL` | no | `WARNING` | Python log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

> **Never commit your API key to version control.** Add `.env` to your `.gitignore`.

---

## Integration Guides

These examples use `uv` to build the server and so require `uv` to be installed where you are running the server.

### GitHub Copilot (Cloud Agent)

To use ads-mcp with GitHub Copilot Cloud Agent, you must make your ADS token available via a repository secret. It's possible to do this on an org-wide basis (so the same key is used across all repos), but here we focus on per-repo configuration. On your repository, go to `Settings` (cog symbol), scroll down and select `Secrets and variables` and select `Agents` from the submenu. Add a new secret with name `COPILOT_MCP_ADS_API_TOKEN` and put your ADS API Token in as the value. **The COPILOT_MCP_ prefix is necessary** as only Agents secrets and variables with names prefixed with `COPILOT_MCP_` will be available to your MCP configuration (see [here](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/configure-secrets-and-variables)).

To add the MCP configuration json, go to `Settings`, then scroll down the left panel until you get to `Copilot`, open that dropdown and select `Cloud agent`. Then scroll down to the section `Model Context Protocol (MCP)` and add the following 

```json
{
  "mcpServers": {
    "ads": {
      "type": "local",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/cgarling/ads-mcp",
        "ads-mcp"
      ],
      "env": {
        "ADS_API_TOKEN": "${COPILOT_MCP_ADS_API_TOKEN}"
      },
      "tools": ["*"]
    }
  }
}
```

### VS Code

VS Code can support MCP definitions at different levels (`>` = Ctrl+Shift+P on Windows, Cmd+Shift+P on Mac).

 - workspace: `>MCP: Open Workspace Folder MCP Configuration`
 - remote: `>MCP: Open Remote User Configuration`
 - global: `>MCP: Open User Configuration`

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

### Claude Desktop

For macOS and Linux, edit your Claude Desktop configuration file (**NOT VERIFIED**):

| OS | Path |
|----|------|
| macOS | `~/.claude/mcp.json` |
| Linux | `~/.claude/mcp.json` |

```json
{
  "mcpServers": {
    "ads": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/cgarling/ads-mcp",
        "ads-mcp"
      ],
      "env": {
        "ADS_API_TOKEN": "${ADS_API_TOKEN}"
      }
    }
  }
}
```

Where the environment variable `ADS_API_TOKEN` must be available to the shell that will run the server.
Restart Claude Desktop after saving.

On Windows the path is tricky, from Claude Desktop select `Top Left Dropdown > File > Settings > Developer > Edit Config` and a new Explorer window should open pointed to the appropriate file (a `claude_desktop_config.json`). Now you must either hardcode your API token into this file or set the API token as a Windows system- or user-level environment variable -- interpolation is not supported. The environment variable can be created by running `setx ADS_API_TOKEN "your_actual_token_here"` from a terminal; if you set the environment variable, you can omit the `"env"` portion of the json blob.
- **UPDATE**: I have not actually been able to get the environment variable mechanism to work on Windows; hard-coding the token in the `claude_desktop_config.json` is the only thing I've done that works so far
- **UPDATE 2**: When installing the server for the first time, the above json would fail with MCP logs showing something about `git` not being found. I tried various things (setting `PATH` in the `env` section of the json, etc.) and never got it to work. In the end I just opened the Command Prompt and ran `uvx --from git+https://github.com/cgarling/ads-mcp ads-mcp` which installed successfully; then the next time I opened Claude desktop the MCP server was loaded and running.

### Cursor

Edit MCP configuration files (**NOT VERIFIED**)

| OS | Path |
|----|------|
| macOS | `~/.cursor/mcp.json` |
| Windows | `%USERPROFILE%\.cursor\mcp.json` |
| Linux | `~/.cursor/mcp.json` |

and add the same json as for Claude Code above.

### Generic MCP client

Other MCP clients that support stdio transport should be able to use ads-mcp with json similar to the above, but not all may support secret interpolation `"env": {"ADS_API_TOKEN": "${ADS_API_TOKEN}"}`.

---

## Documentation

Full documentation is available at **<https://cgarling.github.io/ads-mcp>**

Includes setup guide, full tool reference, configuration reference,
integration guides, and Python API docs.

---

## Development

```bash
git clone https://github.com/cgarling/ads-mcp.git
cd ads-mcp
pip install -e ".[docs,dev]"

# Run tests
pytest

# Build docs locally
python -m sphinx docs docs/_build/html -b html

# Lint
ruff check ads_mcp/
```

---

## License

MIT — see [LICENSE](LICENSE).

---

*ads-mcp is not affiliated with or endorsed by the SAO/NASA Astrophysics Data System.*
