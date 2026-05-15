"""Tests for the ADS MCP server and client."""

from __future__ import annotations

import pytest


class TestADSClient:
    """Tests for :class:`ads_mcp.client.ADSClient`."""

    def test_requires_api_key(self, monkeypatch):
        """ADSClient raises ValueError when no API key is available."""
        monkeypatch.delenv("ADS_API_TOKEN", raising=False)
        from ads_mcp.client import ADSClient

        with pytest.raises(ValueError, match="ADS_API_TOKEN"):
            ADSClient()

    def test_accepts_explicit_key(self):
        """ADSClient accepts an explicit api_key argument."""
        from ads_mcp.client import ADSClient

        client = ADSClient(api_key="test-key-123")
        assert client._api_key == "test-key-123"

    def test_accepts_env_key(self, monkeypatch):
        """ADSClient reads the key from the ADS_API_TOKEN environment variable."""
        monkeypatch.setenv("ADS_API_TOKEN", "env-key-456")
        from ads_mcp.client import ADSClient

        client = ADSClient()
        assert client._api_key == "env-key-456"


class TestServerTools:
    """Smoke tests for the FastMCP application."""

    @pytest.mark.asyncio
    async def test_all_tools_registered(self):
        """All expected tools are registered with the MCP server."""
        from ads_mcp.server import mcp

        tools = await mcp.list_tools()
        names = {t.name for t in tools}
        expected = {
            "search_ads",
            "get_abstract",
            "get_references",
            "get_citations",
            "export_bibtex",
            "export_ris",
            "export_citation",
            "find_arxiv",
            "find_doi",
            "get_metrics",
            "get_similar",
            "author_search",
            "get_paper_details",
        }
        assert expected <= names, f"Missing tools: {expected - names}"

    @pytest.mark.asyncio
    async def test_tools_have_descriptions(self):
        """Every registered tool has a non-empty description."""
        from ads_mcp.server import mcp

        tools = await mcp.list_tools()
        for tool in tools:
            assert tool.description, f"Tool '{tool.name}' has no description"
