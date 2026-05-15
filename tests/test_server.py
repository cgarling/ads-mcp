"""Tests for the ADS MCP server and client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

BIBCODE = "2025ApJS..277...61G"
ARXIV_ID = "2501.12345"
DOI = "10.3847/1538-4365/adacbc"

MOCK_DOC = {
    "bibcode": BIBCODE,
    "title": ["The MAVERIC Survey: A Test Paper"],
    "author": ["Garling, C. T.", "Strader, J.", "Chomiuk, L."],
    "year": "2025",
    "abstract": (
        "We present a catalog of compact binary millisecond pulsars detected "
        "in globular clusters across the Milky Way."
    ),
    "doi": [DOI],
    "identifier": [f"arXiv:{ARXIV_ID}", f"2025arXiv250112345G"],
    "pub": "The Astrophysical Journal Supplement Series",
    "volume": "277",
    "page": ["61"],
    "keyword": ["globular clusters: general", "pulsars: general"],
    "citation_count": 3,
    "read_count": 42,
    "arxiv_class": ["astro-ph.HE"],
}

MOCK_SEARCH_ONE = {"response": {"numFound": 1, "docs": [MOCK_DOC]}}
MOCK_SEARCH_MULTI = {"response": {"numFound": 15, "docs": [MOCK_DOC] * 5}}
MOCK_EMPTY_SEARCH = {"response": {"numFound": 0, "docs": []}}

MOCK_BIBTEX = (
    "@ARTICLE{2025ApJS..277...61G,\n"
    "       author = {{Garling}, C. T.},\n"
    "        title = {The MAVERIC Survey: A Test Paper},\n"
    "      journal = {\\apjs},\n"
    "         year = 2025,\n"
    "       volume = {277},\n"
    "          eid = {61},\n"
    "}\n"
)

MOCK_RIS = (
    "TY  - JOUR\n"
    f"ID  - {BIBCODE}\n"
    "TI  - The MAVERIC Survey: A Test Paper\n"
    "AU  - Garling, C. T.\n"
    "PY  - 2025\n"
    "ER  -\n"
)

MOCK_METRICS = {
    "basic stats": {
        "number of papers": 1,
        "total number of reads": 42,
        "total number of downloads": 20,
    },
    "citation stats": {
        "total number of citations": 3,
        "total number of refereed citations": 3,
        "number of citing papers": 3,
    },
    "indicators": {
        "h": 1,
        "g": 1,
        "m": 0.5,
        "i10": 0,
        "i100": 0,
        "tori": 0.05,
        "riq": 5,
    },
}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_ads_client():
    """AsyncMock of ADSClient with canned responses for every method."""
    client = AsyncMock()
    client.search.return_value = MOCK_SEARCH_ONE
    client.get_references.return_value = MOCK_SEARCH_MULTI
    client.get_citations.return_value = MOCK_SEARCH_MULTI
    client.export.return_value = MOCK_BIBTEX
    client.metrics.return_value = MOCK_METRICS
    return client


@pytest.fixture
def mcp_ctx(mock_ads_client):
    """Patch mcp.get_context so every tool function uses mock_ads_client."""
    ctx = MagicMock()
    ctx.request_context.lifespan_context = {"client": mock_ads_client}
    with patch("ads_mcp.server.mcp.get_context", return_value=ctx):
        yield mock_ads_client


# ---------------------------------------------------------------------------
# ADSClient unit tests
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
# Server registration smoke tests
# ---------------------------------------------------------------------------


class TestServerTools:
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
# Tool functional tests
# ---------------------------------------------------------------------------


class TestSearchAds:
    """Tests for the search_ads tool."""

    async def test_returns_formatted_results(self, mcp_ctx):
        """search_ads returns a formatted result string."""
        from ads_mcp.server import search_ads

        result = await search_ads("globular clusters")
        assert "Found" in result
        assert BIBCODE in result
        mcp_ctx.search.assert_called_once()

    async def test_no_results(self, mcp_ctx):
        """search_ads reports no results when search returns an empty response."""
        from ads_mcp.server import search_ads

        mcp_ctx.search.return_value = MOCK_EMPTY_SEARCH
        result = await search_ads("xyzzy nonexistent query")
        assert "No results found" in result

    async def test_passes_query_and_pagination(self, mcp_ctx):
        """search_ads forwards query, rows, start, and sort to the client."""
        from ads_mcp.server import search_ads

        await search_ads("pulsars", rows=5, start=2, sort="citation_count desc")
        call_kwargs = mcp_ctx.search.call_args
        assert call_kwargs.kwargs["rows"] == 5
        assert call_kwargs.kwargs["start"] == 2
        assert call_kwargs.kwargs["sort"] == "citation_count desc"


class TestGetAbstract:
    """Tests for the get_abstract tool."""

    async def test_returns_abstract_block(self, mcp_ctx):
        """get_abstract returns title, authors, and full abstract."""
        from ads_mcp.server import get_abstract

        result = await get_abstract(BIBCODE)
        assert BIBCODE in result
        assert "Abstract" in result
        assert MOCK_DOC["abstract"] in result

    async def test_includes_arxiv_id(self, mcp_ctx):
        """get_abstract extracts and shows the arXiv identifier."""
        from ads_mcp.server import get_abstract

        result = await get_abstract(BIBCODE)
        assert ARXIV_ID in result

    async def test_includes_ads_url(self, mcp_ctx):
        """get_abstract appends the ADS web URL."""
        from ads_mcp.server import get_abstract

        result = await get_abstract(BIBCODE)
        assert f"https://ui.adsabs.harvard.edu/abs/{BIBCODE}" in result

    async def test_not_found(self, mcp_ctx):
        """get_abstract returns a helpful message when the bibcode is unknown."""
        from ads_mcp.server import get_abstract

        mcp_ctx.search.return_value = MOCK_EMPTY_SEARCH
        result = await get_abstract("1900FAKE..000...00X")
        assert "No paper found" in result


class TestGetReferences:
    """Tests for the get_references tool."""

    async def test_returns_reference_list(self, mcp_ctx):
        """get_references returns a formatted list of references."""
        from ads_mcp.server import get_references

        result = await get_references(BIBCODE)
        assert "Found" in result
        mcp_ctx.get_references.assert_called_once_with(BIBCODE, rows=50)

    async def test_custom_rows(self, mcp_ctx):
        """get_references passes the rows parameter to the client."""
        from ads_mcp.server import get_references

        await get_references(BIBCODE, rows=100)
        mcp_ctx.get_references.assert_called_once_with(BIBCODE, rows=100)


class TestGetCitations:
    """Tests for the get_citations tool."""

    async def test_returns_citation_list(self, mcp_ctx):
        """get_citations returns a formatted list of citing papers."""
        from ads_mcp.server import get_citations

        result = await get_citations(BIBCODE)
        assert "Found" in result
        mcp_ctx.get_citations.assert_called_once_with(BIBCODE, rows=50)

    async def test_custom_rows(self, mcp_ctx):
        """get_citations passes the rows parameter to the client."""
        from ads_mcp.server import get_citations

        await get_citations(BIBCODE, rows=25)
        mcp_ctx.get_citations.assert_called_once_with(BIBCODE, rows=25)


class TestExportBibtex:
    """Tests for the export_bibtex tool."""

    async def test_returns_bibtex_string(self, mcp_ctx):
        """export_bibtex returns a BibTeX-formatted string."""
        from ads_mcp.server import export_bibtex

        result = await export_bibtex([BIBCODE])
        assert "@ARTICLE" in result
        mcp_ctx.export.assert_called_once_with([BIBCODE], fmt="bibtex")

    async def test_multiple_bibcodes(self, mcp_ctx):
        """export_bibtex passes all bibcodes to the client."""
        from ads_mcp.server import export_bibtex

        bibcodes = [BIBCODE, "2019ApJ...887L..24M"]
        await export_bibtex(bibcodes)
        mcp_ctx.export.assert_called_once_with(bibcodes, fmt="bibtex")


class TestExportRis:
    """Tests for the export_ris tool."""

    async def test_returns_ris_string(self, mcp_ctx):
        """export_ris returns an RIS-formatted string."""
        from ads_mcp.server import export_ris

        mcp_ctx.export.return_value = MOCK_RIS
        result = await export_ris([BIBCODE])
        assert "TY  - JOUR" in result
        mcp_ctx.export.assert_called_once_with([BIBCODE], fmt="ris")


class TestExportCitation:
    """Tests for the export_citation tool."""

    async def test_valid_format(self, mcp_ctx):
        """export_citation returns formatted output for a valid format string."""
        from ads_mcp.server import export_citation

        result = await export_citation([BIBCODE], fmt="bibtex")
        assert "@ARTICLE" in result
        mcp_ctx.export.assert_called_once_with([BIBCODE], fmt="bibtex")

    async def test_aastex_format(self, mcp_ctx):
        """export_citation accepts the aastex format."""
        from ads_mcp.server import export_citation

        mcp_ctx.export.return_value = "\\bibitem{...}"
        result = await export_citation([BIBCODE], fmt="aastex")
        assert "ADS API error" not in result
        mcp_ctx.export.assert_called_once_with([BIBCODE], fmt="aastex")

    async def test_invalid_format_rejected(self, mcp_ctx):
        """export_citation rejects an unsupported format without calling the API."""
        from ads_mcp.server import export_citation

        result = await export_citation([BIBCODE], fmt="pdf")
        assert "Unsupported format" in result
        mcp_ctx.export.assert_not_called()


class TestFindArxiv:
    """Tests for the find_arxiv tool."""

    async def test_finds_paper_by_arxiv_id(self, mcp_ctx):
        """find_arxiv returns paper details for a valid arXiv identifier."""
        from ads_mcp.server import find_arxiv

        result = await find_arxiv(ARXIV_ID)
        assert BIBCODE in result
        assert "Abstract" in result

    async def test_strips_arxiv_prefix(self, mcp_ctx):
        """find_arxiv normalises the 'arXiv:' prefix before querying."""
        from ads_mcp.server import find_arxiv

        result = await find_arxiv(f"arXiv:{ARXIV_ID}")
        assert BIBCODE in result

    async def test_not_found(self, mcp_ctx):
        """find_arxiv returns a helpful message when no paper matches."""
        from ads_mcp.server import find_arxiv

        mcp_ctx.search.return_value = MOCK_EMPTY_SEARCH
        result = await find_arxiv("9999.99999")
        assert "No paper found" in result


class TestFindDoi:
    """Tests for the find_doi tool."""

    async def test_finds_paper_by_doi(self, mcp_ctx):
        """find_doi returns paper details for a valid DOI."""
        from ads_mcp.server import find_doi

        result = await find_doi(DOI)
        assert BIBCODE in result
        assert "Abstract" in result

    async def test_strips_url_prefix(self, mcp_ctx):
        """find_doi strips the 'https://doi.org/' URL prefix."""
        from ads_mcp.server import find_doi

        result = await find_doi(f"https://doi.org/{DOI}")
        assert "ADS API error" not in result

    async def test_not_found(self, mcp_ctx):
        """find_doi returns a helpful message when no paper matches."""
        from ads_mcp.server import find_doi

        mcp_ctx.search.return_value = MOCK_EMPTY_SEARCH
        result = await find_doi("10.9999/nonexistent")
        assert "No paper found" in result


class TestGetMetrics:
    """Tests for the get_metrics tool."""

    async def test_returns_metrics_summary(self, mcp_ctx):
        """get_metrics returns basic, citation, and indicator stats."""
        from ads_mcp.server import get_metrics

        result = await get_metrics([BIBCODE])
        assert "Basic Stats" in result
        assert "Citation Stats" in result
        assert "Bibliometric Indicators" in result
        mcp_ctx.metrics.assert_called_once_with(
            [BIBCODE], types=["basic", "citations", "indicators"]
        )

    async def test_citation_counts_present(self, mcp_ctx):
        """get_metrics output includes total citation count."""
        from ads_mcp.server import get_metrics

        result = await get_metrics([BIBCODE])
        assert "3" in result  # total citations from MOCK_METRICS

    async def test_skipped_bibcodes_reported(self, mcp_ctx):
        """get_metrics reports bibcodes that ADS skipped."""
        from ads_mcp.server import get_metrics

        mcp_ctx.metrics.return_value = {
            **MOCK_METRICS,
            "skipped bibcodes": ["1900FAKE..000...00X"],
        }
        result = await get_metrics([BIBCODE, "1900FAKE..000...00X"])
        assert "Skipped" in result
        assert "1900FAKE..000...00X" in result

    async def test_empty_response(self, mcp_ctx):
        """get_metrics handles an empty metrics dict gracefully."""
        from ads_mcp.server import get_metrics

        mcp_ctx.metrics.return_value = {}
        result = await get_metrics([BIBCODE])
        assert "No metrics data returned" in result


class TestGetSimilar:
    """Tests for the get_similar tool."""

    async def test_returns_similar_papers(self, mcp_ctx):
        """get_similar returns a formatted list of similar papers."""
        from ads_mcp.server import get_similar

        mcp_ctx.search.return_value = MOCK_SEARCH_MULTI
        result = await get_similar(BIBCODE)
        assert "Found" in result

    async def test_passes_bibcode_and_rows(self, mcp_ctx):
        """get_similar passes bibcode and rows to the client search call."""
        from ads_mcp.server import get_similar

        mcp_ctx.search.return_value = MOCK_SEARCH_MULTI
        await get_similar(BIBCODE, rows=5)
        call_args = mcp_ctx.search.call_args
        assert f"similar(bibcode:{BIBCODE})" in call_args.args[0]
        assert call_args.kwargs["rows"] == 5


class TestAuthorSearch:
    """Tests for the author_search tool."""

    async def test_returns_author_papers(self, mcp_ctx):
        """author_search returns formatted results for a given author."""
        from ads_mcp.server import author_search

        mcp_ctx.search.return_value = MOCK_SEARCH_ONE
        result = await author_search("Garling, C")
        assert "Found" in result

    async def test_query_contains_author_operator(self, mcp_ctx):
        """author_search wraps the name with the author: field operator."""
        from ads_mcp.server import author_search

        await author_search("Garling, C")
        call_args = mcp_ctx.search.call_args
        assert 'author:"Garling, C"' in call_args.args[0]

    async def test_refereed_only_filter(self, mcp_ctx):
        """author_search appends AND property:refereed when refereed_only=True."""
        from ads_mcp.server import author_search

        await author_search("Garling, C", refereed_only=True)
        call_args = mcp_ctx.search.call_args
        assert "property:refereed" in call_args.args[0]

    async def test_no_refereed_filter_by_default(self, mcp_ctx):
        """author_search does not add the refereed filter by default."""
        from ads_mcp.server import author_search

        await author_search("Garling, C")
        call_args = mcp_ctx.search.call_args
        assert "property:refereed" not in call_args.args[0]


class TestGetPaperDetails:
    """Tests for the get_paper_details tool."""

    async def test_returns_all_fields(self, mcp_ctx):
        """get_paper_details returns key-value pairs for every field in the doc."""
        from ads_mcp.server import get_paper_details

        result = await get_paper_details(BIBCODE)
        assert "bibcode" in result
        assert BIBCODE in result
        assert "title" in result

    async def test_not_found(self, mcp_ctx):
        """get_paper_details returns a helpful message when bibcode is unknown."""
        from ads_mcp.server import get_paper_details

        mcp_ctx.search.return_value = MOCK_EMPTY_SEARCH
        result = await get_paper_details("1900FAKE..000...00X")
        assert "No paper found" in result

    async def test_custom_fields(self, mcp_ctx):
        """get_paper_details passes a custom field list to the client."""
        from ads_mcp.server import get_paper_details

        await get_paper_details(BIBCODE, fields="bibcode,title,year")
        call_args = mcp_ctx.search.call_args
        assert call_args.kwargs["fields"] == "bibcode,title,year"
