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

- [Available Tools](#available-tools)
- [Installation](#installation)
- [Documentation](#documentation)
- [Development](#development)
- [License](#license)

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

## Installation

Install with `uv tool install git+https://github.com/cgarling/ads-mcp` and register with a client application (see below). Requires [`uv`](https://docs.astral.sh/uv/), `git`, and an ADS API token for proper authentication. Get a token by creating an account at <https://ui.adsabs.harvard.edu> and navigating to <https://ui.adsabs.harvard.edu/user/settings/token>.

---

### GitHub Copilot (Cloud Agent)

To use ads-mcp with GitHub Copilot Cloud Agent, you must make your ADS token available via a repository secret. It's possible to do this on an org-wide basis (so the same key is used across all repos), but here we focus on per-repo configuration. On your repository, go to `Settings` (cog symbol), scroll down and select `Secrets and variables` and select `Agents` from the submenu. Add a new secret with name `COPILOT_MCP_ADS_API_TOKEN` and put your ADS API Token in as the value. **The COPILOT_MCP_ prefix is necessary** as only Agents secrets and variables with names prefixed with `COPILOT_MCP_` will be available to your MCP configuration (see [here](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/configure-secrets-and-variables)). Since cloud agents are ephemeral, we will use `uvx` for a one-step setup.

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

Here we use the `inputs` feature to avoid hard-coding our API token. Upon first starting the server, VS Code will ask you for your API key and store it securely. Start the server with `>MCP: List Servers`, select `ads`, and start server -- this will require the server to be installed *where the server is running* (i.e., be careful of remotes). Note from [VS Code docs](https://code.visualstudio.com/docs/copilot/customization/mcp-servers): MCP servers run wherever they are configured. Servers in your user profile run locally. If you're connected to a remote and want a server to run on the remote machine, define it in the workspace settings or remote user settings (MCP: Open Remote User Configuration).

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
	  "command": "uv",
      "args": [
        "tool",
        "run",
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

### Claude Code
To install at the user level (Claude Code allows both user- and project-scoped MCP configurations), run `claude mcp add --transport stdio -e ADS_API_TOKEN=YOUR_TOKEN_HERE --scope user ads-mcp -- uv tool run ads-mcp`. Verify the installation with `claude mcp list`.

### Claude Desktop

The most reliable way to find the config file is through Claude Desktop itself by selecting `Top Left Dropdown > File > Settings > Developer > Edit Config` and a new Explorer window should open pointed to the appropriate file (a `claude_desktop_config.json`). Right now I recommend **hard coding your API token into the json file**, see notes below. Since this is plain text, make sure the file has appropriate permissions. Restart Claude Desktop after saving.

```json
{
  "mcpServers": {
    "ads": {
      "command": "uv",
      "args": [
        "tool",
        "run",
        "ads-mcp"
      ],
      "env": {
        "ADS_API_TOKEN": "<your token here>"
      }
    }
  }
}
```

**NOTES:** In principle Claude Desktop should be able to inherit the API token from environment variables in the system configuration. However, Claude Desktop does not launch MCP servers in a shell, so the environment variables in the context of the MCP servers are not the same as in standard shells. If anyone knows how to get Claude Desktop to read environment variables, please let me know.

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
