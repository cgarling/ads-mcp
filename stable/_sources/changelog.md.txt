# Changelog

All notable changes to ads-mcp are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] — unreleased

### Added

- Initial release of the ADS MCP server.
- 13 MCP tools: `search_ads`, `get_abstract`, `get_references`,
  `get_citations`, `export_bibtex`, `export_ris`, `export_citation`,
  `find_arxiv`, `find_doi`, `get_metrics`, `get_similar`,
  `author_search`, `get_paper_details`.
- Async HTTP client (`ADSClient`) wrapping the ADS v1 REST API.
- Integration guides for GitHub Copilot, VS Code, Claude Desktop,
  Cursor, Zed, and generic MCP clients.
- Sphinx documentation with Furo theme and MyST Markdown.
- GitHub Actions workflow for automated documentation deployment on
  release.
