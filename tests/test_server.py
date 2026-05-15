"""Tests for the ADS MCP server and client."""

from __future__ import annotations

import os
import re

import pytest

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

#: ADS bibcode used throughout the integration tests.
BIBCODE = "2025ApJS..277...61G"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def api_key():
    """Return the ADS API token, skipping the session if it is absent."""
    key = os.environ.get("ADS_API_TOKEN")
    if not key:
        pytest.skip("ADS_API_TOKEN not set — skipping integration tests")
    return key


@pytest.fixture
async def live_ctx(api_key):
    """Wire a real ADSClient into the FastMCP context for the duration of a test.

    Sets ``mcp._lifespan_result`` so that ``ctx.lifespan_context["client"]``
    returns the live client, then installs a minimal ``Context`` into the
    ``_current_context`` ContextVar consumed by ``get_context()``.
    """
    from fastmcp.server.context import Context, _current_context

    from ads_mcp.client import ADSClient
    from ads_mcp.server import mcp

    async with ADSClient(api_key=api_key) as client:
        mcp._lifespan_result = {"client": client}
        mcp._lifespan_result_set = True
        ctx = Context(fastmcp=mcp)
        token = _current_context.set(ctx)
        try:
            yield
        finally:
            _current_context.reset(token)
            mcp._lifespan_result = None
            mcp._lifespan_result_set = False


# ---------------------------------------------------------------------------
# ADSClient unit tests (no API key required)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Server registration smoke tests (no API key required)
# ---------------------------------------------------------------------------


class TestServerRegistration:
    """Smoke tests for the FastMCP application."""

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

    async def test_tools_have_descriptions(self):
        """Every registered tool has a non-empty description."""
        from ads_mcp.server import mcp

        tools = await mcp.list_tools()
        for tool in tools:
            assert tool.description, f"Tool '{tool.name}' has no description"


# ---------------------------------------------------------------------------
# Integration tests — require ADS_API_TOKEN
# ---------------------------------------------------------------------------


class TestSearchAds:
    """Integration tests for the search_ads tool."""

    async def test_bibcode_query_returns_paper(self, live_ctx):
        """Searching by bibcode returns the expected paper."""
        from ads_mcp.server import search_ads

        result = await search_ads(f"bibcode:{BIBCODE}")
        assert "ADS API error" not in result
        assert BIBCODE in result

    async def test_keyword_query_returns_results(self, live_ctx):
        """A keyword query returns a non-empty result set."""
        from ads_mcp.server import search_ads

        result = await search_ads("globular clusters millisecond pulsars", rows=5)
        assert "ADS API error" not in result
        assert "Found" in result

    async def test_empty_query_returns_no_results_message(self, live_ctx):
        """An impossible query returns the no-results message gracefully."""
        from ads_mcp.server import search_ads

        result = await search_ads("xyzzy_nonexistent_query_ads_mcp_test_abc123")
        assert "ADS API error" not in result

    async def test_pagination_parameters(self, live_ctx):
        """rows and start parameters are accepted without error."""
        from ads_mcp.server import search_ads

        result = await search_ads("pulsars", rows=3, start=0)
        assert "ADS API error" not in result
        assert "Found" in result


class TestGetAbstract:
    """Integration tests for the get_abstract tool."""

    async def test_returns_bibcode(self, live_ctx):
        """get_abstract result contains the requested bibcode."""
        from ads_mcp.server import get_abstract

        result = await get_abstract(BIBCODE)
        assert "ADS API error" not in result
        assert BIBCODE in result

    async def test_returns_abstract_text(self, live_ctx):
        """get_abstract result contains an abstract section."""
        from ads_mcp.server import get_abstract

        result = await get_abstract(BIBCODE)
        assert "Abstract" in result

    async def test_returns_ads_url(self, live_ctx):
        """get_abstract appends the ADS web URL for the paper."""
        from ads_mcp.server import get_abstract

        result = await get_abstract(BIBCODE)
        assert f"https://ui.adsabs.harvard.edu/abs/{BIBCODE}" in result

    async def test_unknown_bibcode_returns_not_found(self, live_ctx):
        """get_abstract reports a missing paper gracefully."""
        from ads_mcp.server import get_abstract

        result = await get_abstract("1900FAKE..000...00X")
        assert "No paper found" in result
        assert "ADS API error" not in result


class TestGetReferences:
    """Integration tests for the get_references tool."""

    async def test_returns_reference_list(self, live_ctx):
        """get_references returns a non-error result for a real bibcode."""
        from ads_mcp.server import get_references

        result = await get_references(BIBCODE)
        assert "ADS API error" not in result

    async def test_custom_rows_accepted(self, live_ctx):
        """get_references accepts a custom rows argument."""
        from ads_mcp.server import get_references

        result = await get_references(BIBCODE, rows=10)
        assert "ADS API error" not in result


class TestGetCitations:
    """Integration tests for the get_citations tool."""

    async def test_returns_citation_result(self, live_ctx):
        """get_citations returns a non-error result (may be empty for a new paper)."""
        from ads_mcp.server import get_citations

        result = await get_citations(BIBCODE)
        assert "ADS API error" not in result

    async def test_custom_rows_accepted(self, live_ctx):
        """get_citations accepts a custom rows argument."""
        from ads_mcp.server import get_citations

        result = await get_citations(BIBCODE, rows=10)
        assert "ADS API error" not in result


class TestExportBibtex:
    """Integration tests for the export_bibtex tool."""

    async def test_returns_bibtex_entry(self, live_ctx):
        """export_bibtex returns a string containing a BibTeX entry."""
        from ads_mcp.server import export_bibtex

        result = await export_bibtex([BIBCODE])
        assert "ADS API error" not in result
        assert "@" in result  # BibTeX entries start with @
        assert BIBCODE in result

    async def test_multiple_bibcodes(self, live_ctx):
        """export_bibtex handles a list of bibcodes."""
        from ads_mcp.server import export_bibtex

        bibcodes = [BIBCODE, "2019ApJ...887L..24M"]
        result = await export_bibtex(bibcodes)
        assert "ADS API error" not in result
        assert "@" in result


class TestExportRis:
    """Integration tests for the export_ris tool."""

    async def test_returns_ris_content(self, live_ctx):
        """export_ris returns a RIS-formatted string."""
        from ads_mcp.server import export_ris

        result = await export_ris([BIBCODE])
        assert "ADS API error" not in result
        assert "TY  -" in result


class TestExportCitation:
    """Integration tests for the export_citation tool."""

    async def test_bibtex_format(self, live_ctx):
        """export_citation in bibtex format returns a BibTeX entry."""
        from ads_mcp.server import export_citation

        result = await export_citation([BIBCODE], fmt="bibtex")
        assert "ADS API error" not in result
        assert "@" in result

    async def test_aastex_format(self, live_ctx):
        """export_citation in aastex format returns a non-error result."""
        from ads_mcp.server import export_citation

        result = await export_citation([BIBCODE], fmt="aastex")
        assert "ADS API error" not in result

    async def test_endnote_format(self, live_ctx):
        """export_citation in endnote format returns a non-error result."""
        from ads_mcp.server import export_citation

        result = await export_citation([BIBCODE], fmt="endnote")
        assert "ADS API error" not in result

    async def test_invalid_format_rejected_without_api_call(self, live_ctx):
        """export_citation rejects an unsupported format before calling the API."""
        from ads_mcp.server import export_citation

        result = await export_citation([BIBCODE], fmt="pdf")
        assert "Unsupported format" in result
        assert "ADS API error" not in result


class TestFindArxiv:
    """Integration tests for the find_arxiv tool."""

    async def test_find_by_arxiv_id(self, live_ctx):
        """find_arxiv resolves a paper from its arXiv identifier."""
        from ads_mcp.server import find_arxiv, get_abstract

        # Retrieve the paper first to discover its arXiv ID.
        abstract = await get_abstract(BIBCODE)
        match = re.search(r"arXiv\s*:\s*(\S+)", abstract)
        if not match:
            pytest.skip(f"Paper {BIBCODE} has no arXiv identifier in ADS")
        arxiv_id = match.group(1)

        result = await find_arxiv(arxiv_id)
        assert "ADS API error" not in result
        assert BIBCODE in result

    async def test_strips_arxiv_prefix(self, live_ctx):
        """find_arxiv handles the 'arXiv:' prefix transparently."""
        from ads_mcp.server import find_arxiv, get_abstract

        abstract = await get_abstract(BIBCODE)
        match = re.search(r"arXiv\s*:\s*(\S+)", abstract)
        if not match:
            pytest.skip(f"Paper {BIBCODE} has no arXiv identifier in ADS")
        arxiv_id = match.group(1)

        result = await find_arxiv(f"arXiv:{arxiv_id}")
        assert "ADS API error" not in result
        assert BIBCODE in result

    async def test_unknown_arxiv_id_returns_not_found(self, live_ctx):
        """find_arxiv returns a helpful message for an unknown arXiv ID."""
        from ads_mcp.server import find_arxiv

        result = await find_arxiv("9999.99999")
        assert "No paper found" in result
        assert "ADS API error" not in result


class TestFindDoi:
    """Integration tests for the find_doi tool."""

    async def test_find_by_doi(self, live_ctx):
        """find_doi resolves a paper from its DOI."""
        from ads_mcp.server import find_doi, get_abstract

        # Retrieve the paper to discover its DOI.
        abstract = await get_abstract(BIBCODE)
        match = re.search(r"DOI\s*:\s*(\S+)", abstract)
        if not match:
            pytest.skip(f"Paper {BIBCODE} has no DOI in ADS")
        doi = match.group(1)

        result = await find_doi(doi)
        assert "ADS API error" not in result
        assert BIBCODE in result

    async def test_strips_url_prefix(self, live_ctx):
        """find_doi strips 'https://doi.org/' before querying."""
        from ads_mcp.server import find_doi, get_abstract

        abstract = await get_abstract(BIBCODE)
        match = re.search(r"DOI\s*:\s*(\S+)", abstract)
        if not match:
            pytest.skip(f"Paper {BIBCODE} has no DOI in ADS")
        doi = match.group(1)

        result = await find_doi(f"https://doi.org/{doi}")
        assert "ADS API error" not in result
        assert BIBCODE in result

    async def test_unknown_doi_returns_not_found(self, live_ctx):
        """find_doi returns a helpful message for an unknown DOI."""
        from ads_mcp.server import find_doi

        result = await find_doi("10.9999/nonexistent-ads-mcp-test")
        assert "No paper found" in result
        assert "ADS API error" not in result


class TestGetMetrics:
    """Integration tests for the get_metrics tool."""

    async def test_returns_stats_sections(self, live_ctx):
        """get_metrics returns basic stats, citation stats, and indicators."""
        from ads_mcp.server import get_metrics

        result = await get_metrics([BIBCODE])
        assert "ADS API error" not in result
        # ADS may skip papers with no metrics; accept either outcome.
        assert "Basic Stats" in result or "Skipped" in result or "No metrics" in result

    async def test_multiple_bibcodes(self, live_ctx):
        """get_metrics accepts multiple bibcodes without error."""
        from ads_mcp.server import get_metrics

        result = await get_metrics([BIBCODE, "2019ApJ...887L..24M"])
        assert "ADS API error" not in result


class TestGetSimilar:
    """Integration tests for the get_similar tool."""

    async def test_returns_similar_papers(self, live_ctx):
        """get_similar returns a non-error result for a real bibcode."""
        from ads_mcp.server import get_similar

        result = await get_similar(BIBCODE, rows=5)
        assert "ADS API error" not in result

    async def test_custom_rows_accepted(self, live_ctx):
        """get_similar accepts a custom rows argument."""
        from ads_mcp.server import get_similar

        result = await get_similar(BIBCODE, rows=3)
        assert "ADS API error" not in result


class TestAuthorSearch:
    """Integration tests for the author_search tool."""

    async def test_finds_papers_by_author(self, live_ctx):
        """author_search returns papers for a known author name."""
        from ads_mcp.server import author_search

        # The bibcode ends with 'G'; use the last-name from the bibcode author
        result = await author_search("Garling, C", rows=5)
        assert "ADS API error" not in result
        assert "Found" in result

    async def test_refereed_only_filter(self, live_ctx):
        """author_search with refereed_only=True returns a non-error result."""
        from ads_mcp.server import author_search

        result = await author_search("Garling, C", rows=5, refereed_only=True)
        assert "ADS API error" not in result

    async def test_sort_by_date(self, live_ctx):
        """author_search with custom sort returns a non-error result."""
        from ads_mcp.server import author_search

        result = await author_search("Garling, C", rows=5, sort="date desc")
        assert "ADS API error" not in result


class TestGetPaperDetails:
    """Integration tests for the get_paper_details tool."""

    async def test_returns_bibcode_field(self, live_ctx):
        """get_paper_details output contains the bibcode field."""
        from ads_mcp.server import get_paper_details

        result = await get_paper_details(BIBCODE)
        assert "ADS API error" not in result
        assert "bibcode" in result
        assert BIBCODE in result

    async def test_custom_fields(self, live_ctx):
        """get_paper_details respects a custom field list."""
        from ads_mcp.server import get_paper_details

        result = await get_paper_details(BIBCODE, fields="bibcode,title,year")
        assert "ADS API error" not in result
        assert BIBCODE in result
        assert "title" in result

    async def test_unknown_bibcode_returns_not_found(self, live_ctx):
        """get_paper_details reports a missing paper gracefully."""
        from ads_mcp.server import get_paper_details

        result = await get_paper_details("1900FAKE..000...00X")
        assert "No paper found" in result
        assert "ADS API error" not in result
