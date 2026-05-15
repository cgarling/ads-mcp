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

## Quick Start

### 1. Get an ADS API key

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

```bash
cp .env.example .env
# Edit .env and add your key:
#   ADS_API_KEY=your_token_here
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
| `ADS_API_KEY` | yes | — | Your ADS API bearer token |
| `ADS_MCP_LOG_LEVEL` | no | `WARNING` | Python log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

> **Never commit your API key to version control.** Add `.env` to your `.gitignore`.

---

## Integration Guides

### GitHub Copilot (Cloud Agent)

Add `.github/copilot-setup-steps.yml` to your repository:

```yaml
steps:
  - name: Install ads-mcp
    run: pip install ads-mcp

mcp_servers:
  - name: ads
    command: ads-mcp
    env:
      ADS_API_KEY: ${{ secrets.ADS_API_KEY }}
```

Store your token as a repository secret named `ADS_API_KEY`
(**Settings → Secrets and variables → Actions**).

### VS Code

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "ads": {
      "type": "stdio",
      "command": "ads-mcp",
      "env": {
        "ADS_API_KEY": "${env:ADS_API_KEY}"
      }
    }
  }
}
```

Make sure `ADS_API_KEY` is exported in your shell before opening VS Code.

### Claude Desktop

Edit your Claude Desktop configuration file:

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

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

Restart Claude Desktop after saving.

### Cursor

Open **Cursor Settings → MCP** and add a new server, or edit
`~/.cursor/mcp.json`:

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

### Zed

Edit `~/.config/zed/settings.json`:

```json
{
  "context_servers": {
    "ads": {
      "command": { "path": "ads-mcp", "args": [] },
      "settings": {}
    }
  }
}
```

### Generic MCP client

Any MCP client that supports stdio transport can use ads-mcp:

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

## Documentation

Full documentation is available at **<https://cgarling.github.io/ads-mcp>**

Includes setup guide, full tool reference, configuration reference,
integration guides, and Python API docs.

Documentation is built with [Sphinx](https://www.sphinx-doc.org/),
[Furo](https://pradyunsg.me/furo/) theme, and
[MyST Markdown](https://myst-parser.readthedocs.io/).
It is deployed automatically to GitHub Pages on every release.

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
