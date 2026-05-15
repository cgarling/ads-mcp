# ADS MCP Server Documentation

Welcome to the documentation for **ads-mcp** — a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that connects AI assistants to the [SAO/NASA Astrophysics Data System (ADS)](https://ui.adsabs.harvard.edu/) bibliographic database.

With ads-mcp, any MCP-compatible AI assistant can search for astronomical papers, retrieve abstracts and full metadata, fetch reference and citation lists, compute bibliometric indicators, and export formatted citations — all without leaving the conversation.

::::{grid} 1 2 2 3
:gutter: 3

:::{grid-item-card} 🚀 Quick Start
:link: setup
:link-type: doc

Get the server running in minutes.
:::

:::{grid-item-card} 🔧 Available Tools
:link: tools
:link-type: doc

Browse all 13 MCP tools.
:::

:::{grid-item-card} 📖 API Reference
:link: api/index
:link-type: doc

Python module documentation.
:::

::::

## Contents

```{toctree}
:maxdepth: 2
:caption: User Guide

setup
tools
configuration
```

```{toctree}
:maxdepth: 2
:caption: Integration Guides

integrations/github-copilot
integrations/vscode
integrations/claude-desktop
integrations/cursor
integrations/other
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/index
api/server
api/client
```

```{toctree}
:maxdepth: 1
:caption: Project

changelog
```
