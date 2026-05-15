"""FastMCP server exposing SAO/NASA Astrophysics Data System (ADS) tools.

This module defines the :data:`mcp` FastMCP application and registers every
ADS tool as an MCP tool handler.  Each tool is a thin wrapper around
:class:`~ads_mcp.client.ADSClient`.

The server is configured via environment variables (see
:ref:`configuration`).  The most important is ``ADS_API_TOKEN``, which must
be set to a valid ADS API token.

Running the server
------------------

Start the server directly::

    python -m ads_mcp.server

or via the installed script::

    ads-mcp

Both use *stdio* transport by default (suitable for MCP hosts such as
Claude Desktop, Cursor, or VS Code Copilot).

Available tools
---------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Tool name
     - Description
   * - :func:`search_ads`
     - Full-text / keyword / author search
   * - :func:`get_abstract`
     - Full metadata + abstract for a bibcode
   * - :func:`get_references`
     - Reference list of a paper
   * - :func:`get_citations`
     - Papers that cite a given paper
   * - :func:`export_bibtex`
     - BibTeX export for one or more bibcodes
   * - :func:`export_ris`
     - RIS export for one or more bibcodes
   * - :func:`export_citation`
     - Export in any supported ADS format
   * - :func:`find_arxiv`
     - Look up a paper by arXiv identifier
   * - :func:`find_doi`
     - Look up a paper by DOI
   * - :func:`get_metrics`
     - Citation & usage metrics
   * - :func:`get_similar`
     - Papers similar to a given bibcode
   * - :func:`author_search`
     - Search papers by author name
   * - :func:`get_paper_details`
     - Retrieve a specific set of fields for a paper
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP

from ads_mcp.client import ADSClient, ADSError

load_dotenv()

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lifespan: create one shared ADSClient for the lifetime of the server
# ---------------------------------------------------------------------------


@asynccontextmanager
async def _lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:  # noqa: ARG001
    async with ADSClient() as client:
        yield {"client": client}


# ---------------------------------------------------------------------------
# FastMCP application
# ---------------------------------------------------------------------------

mcp: FastMCP = FastMCP(
    name="ADS MCP Server",
    instructions=(
        "Provides access to the SAO/NASA Astrophysics Data System (ADS/ADS-abs) "
        "bibliographic database. Use these tools to search for papers, retrieve "
        "abstracts, references, citations, metrics, and export formatted citations."
    ),
    lifespan=_lifespan,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_paper(doc: dict[str, Any]) -> str:
    """Format a single ADS search document as a human-readable string.

    Args:
        doc: A single document dict from an ADS search response.

    Returns:
        Multi-line string with the key bibliographic fields.
    """
    title = "; ".join(doc.get("title", [])) or "N/A"
    authors = doc.get("author", [])
    author_str = ", ".join(authors[:5])
    if len(authors) > 5:
        author_str += f" + {len(authors) - 5} more"
    year = doc.get("year", "N/A")
    bibcode = doc.get("bibcode", "N/A")
    pub = doc.get("pub", "")
    volume = doc.get("volume", "")
    page = doc.get("page", [])
    page_str = page[0] if page else ""
    doi = "; ".join(doc.get("doi") or [])
    citations = doc.get("citation_count", "N/A")
    reads = doc.get("read_count", "N/A")

    lines = [
        f"Title   : {title}",
        f"Authors : {author_str}",
        f"Year    : {year}",
        f"Bibcode : {bibcode}",
    ]
    if pub:
        loc = pub
        if volume:
            loc += f", vol. {volume}"
        if page_str:
            loc += f", p. {page_str}"
        lines.append(f"Published: {loc}")
    if doi:
        lines.append(f"DOI     : {doi}")
    if citations != "N/A":
        lines.append(f"Citations: {citations}  |  Reads: {reads}")
    return "\n".join(lines)


def _format_results(data: dict[str, Any]) -> str:
    """Format a full ADS search response as a human-readable string.

    Args:
        data: Parsed JSON response from :meth:`~ads_mcp.client.ADSClient.search`.

    Returns:
        Formatted multi-line string listing all returned documents.
    """
    response = data.get("response", {})
    docs = response.get("docs", [])
    num_found = response.get("numFound", 0)
    if not docs:
        return "No results found."
    lines = [f"Found {num_found} results. Showing {len(docs)}:\n"]
    for i, doc in enumerate(docs, 1):
        lines.append(f"[{i}] " + _format_paper(doc))
        abstract = doc.get("abstract", "")
        if abstract:
            snippet = abstract[:300].replace("\n", " ")
            if len(abstract) > 300:
                snippet += "…"
            lines.append(f"Abstract: {snippet}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool: search_ads
# ---------------------------------------------------------------------------


@mcp.tool
async def search_ads(
    query: str,
    rows: int = 10,
    start: int = 0,
    sort: str = "date desc",
    fields: str = "",
) -> str:
    """Search the ADS bibliographic database.

    Performs a full Solr/ADS query and returns formatted results.  The
    query syntax follows the `ADS search syntax
    <https://ui.adsabs.harvard.edu/help/search/>`_, supporting field
    operators such as ``author:``, ``title:``, ``abstract:``, ``year:``,
    ``property:refereed``, etc.

    Args:
        query: ADS/Solr query string.  Examples:

            - ``"dark matter annihilation"``
            - ``"author:Einstein AND title:relativity"``
            - ``"abs:exoplanet AND year:2020-2024"``
            - ``"bibcode:2023ApJ...946...29W"``

        rows: Number of results to return (1–2000). Defaults to ``10``.
        start: Zero-based offset for pagination. Defaults to ``0``.
        sort: Sort order, e.g. ``"citation_count desc"``,
            ``"date asc"``.  Defaults to ``"date desc"``.
        fields: Comma-separated list of ADS fields to return.  If empty,
            a sensible default set is used.

    Returns:
        Human-readable summary of matching papers including title, authors,
        year, bibcode, publication venue, DOI, citation count, and an
        abstract snippet.
    """
    ctx = mcp.get_context()
    client: ADSClient = ctx.request_context.lifespan_context["client"]
    from ads_mcp.client import DEFAULT_SEARCH_FIELDS

    fl = fields or DEFAULT_SEARCH_FIELDS + ",abstract"
    try:
        data = await client.search(query, fields=fl, rows=rows, start=start, sort=sort)
        return _format_results(data)
    except ADSError as exc:
        return f"ADS API error: {exc.message}"


# ---------------------------------------------------------------------------
# Tool: get_abstract
# ---------------------------------------------------------------------------


@mcp.tool
async def get_abstract(bibcode: str) -> str:
    """Retrieve full metadata and abstract for an ADS paper.

    Args:
        bibcode: ADS bibcode of the paper, e.g.
            ``"2019ApJ...887L..24M"``.

    Returns:
        Formatted metadata block including title, authors, journal,
        DOI, arXiv ID, keywords, and the full abstract text.
    """
    ctx = mcp.get_context()
    client: ADSClient = ctx.request_context.lifespan_context["client"]
    fields = (
        "bibcode,title,author,year,abstract,doi,identifier,"
        "pub,volume,page,keyword,citation_count,read_count,arxiv_class"
    )
    try:
        data = await client.search(f"bibcode:{bibcode}", fields=fields, rows=1)
        docs = data.get("response", {}).get("docs", [])
        if not docs:
            return f"No paper found for bibcode: {bibcode}"
        doc = docs[0]
        lines = [_format_paper(doc)]

        # Keywords
        kws = doc.get("keyword", [])
        if kws:
            lines.append(f"Keywords : {', '.join(kws[:10])}")

        # arXiv ID
        ids: list[str] = doc.get("identifier", [])
        arxiv_id = next((i for i in ids if i.startswith("arXiv:")), None)
        if arxiv_id:
            lines.append(f"arXiv    : {arxiv_id.replace('arXiv:', '')}")

        # Full abstract
        abstract = doc.get("abstract", "")
        if abstract:
            lines.append(f"\nAbstract:\n{abstract}")

        ads_url = f"https://ui.adsabs.harvard.edu/abs/{bibcode}"
        lines.append(f"\nADS URL  : {ads_url}")
        return "\n".join(lines)
    except ADSError as exc:
        return f"ADS API error: {exc.message}"


# ---------------------------------------------------------------------------
# Tool: get_references
# ---------------------------------------------------------------------------


@mcp.tool
async def get_references(bibcode: str, rows: int = 50) -> str:
    """Retrieve the reference list of an ADS paper.

    Args:
        bibcode: ADS bibcode of the paper whose references to fetch,
            e.g. ``"2019ApJ...887L..24M"``.
        rows: Maximum number of references to return. Defaults to ``50``.

    Returns:
        Formatted list of papers cited by the given bibcode.
    """
    ctx = mcp.get_context()
    client: ADSClient = ctx.request_context.lifespan_context["client"]
    try:
        data = await client.get_references(bibcode, rows=rows)
        return _format_results(data)
    except ADSError as exc:
        return f"ADS API error: {exc.message}"


# ---------------------------------------------------------------------------
# Tool: get_citations
# ---------------------------------------------------------------------------


@mcp.tool
async def get_citations(bibcode: str, rows: int = 50) -> str:
    """Retrieve papers that cite a given ADS paper.

    Args:
        bibcode: ADS bibcode of the paper whose citing papers to fetch,
            e.g. ``"2019ApJ...887L..24M"``.
        rows: Maximum number of citing papers to return. Defaults to
            ``50``.

    Returns:
        Formatted list of papers that cite the given bibcode, sorted by
        date descending.
    """
    ctx = mcp.get_context()
    client: ADSClient = ctx.request_context.lifespan_context["client"]
    try:
        data = await client.get_citations(bibcode, rows=rows)
        return _format_results(data)
    except ADSError as exc:
        return f"ADS API error: {exc.message}"


# ---------------------------------------------------------------------------
# Tool: export_bibtex
# ---------------------------------------------------------------------------


@mcp.tool
async def export_bibtex(bibcodes: list[str]) -> str:
    """Export one or more ADS papers as a BibTeX bibliography.

    Args:
        bibcodes: List of ADS bibcodes to export, e.g.
            ``["2019ApJ...887L..24M", "2023A&A...670A..42S"]``.

    Returns:
        BibTeX-formatted string containing all requested entries.
    """
    ctx = mcp.get_context()
    client: ADSClient = ctx.request_context.lifespan_context["client"]
    try:
        return await client.export(bibcodes, fmt="bibtex")
    except ADSError as exc:
        return f"ADS API error: {exc.message}"


# ---------------------------------------------------------------------------
# Tool: export_ris
# ---------------------------------------------------------------------------


@mcp.tool
async def export_ris(bibcodes: list[str]) -> str:
    """Export one or more ADS papers in RIS (EndNote/Mendeley) format.

    Args:
        bibcodes: List of ADS bibcodes to export.

    Returns:
        RIS-formatted string suitable for import into reference managers
        such as Zotero, Mendeley, or EndNote.
    """
    ctx = mcp.get_context()
    client: ADSClient = ctx.request_context.lifespan_context["client"]
    try:
        return await client.export(bibcodes, fmt="ris")
    except ADSError as exc:
        return f"ADS API error: {exc.message}"


# ---------------------------------------------------------------------------
# Tool: export_citation
# ---------------------------------------------------------------------------


_SUPPORTED_FORMATS = (
    "bibtex bibtexabs ris endnote procite refworks aastex icarus mnras "
    "soph dcxml refxml refabsxml ads medlars votable"
).split()


@mcp.tool
async def export_citation(bibcodes: list[str], fmt: str) -> str:
    """Export ADS papers in a specified bibliographic format.

    Args:
        bibcodes: List of ADS bibcodes to export.
        fmt: Target format.  Supported values:

            ``bibtex``, ``bibtexabs``, ``ris``, ``endnote``,
            ``procite``, ``refworks``, ``aastex``, ``icarus``,
            ``mnras``, ``soph``, ``dcxml``, ``refxml``,
            ``refabsxml``, ``ads``, ``medlars``, ``votable``.

    Returns:
        Formatted bibliography string in the requested format.
    """
    if fmt not in _SUPPORTED_FORMATS:
        return (
            f"Unsupported format '{fmt}'. "
            f"Supported: {', '.join(_SUPPORTED_FORMATS)}"
        )
    ctx = mcp.get_context()
    client: ADSClient = ctx.request_context.lifespan_context["client"]
    try:
        return await client.export(bibcodes, fmt=fmt)
    except ADSError as exc:
        return f"ADS API error: {exc.message}"


# ---------------------------------------------------------------------------
# Tool: find_arxiv
# ---------------------------------------------------------------------------


@mcp.tool
async def find_arxiv(arxiv_id: str) -> str:
    """Look up an ADS paper by its arXiv identifier.

    Accepts both the short form (e.g. ``2301.07688``) and the full form
    with category prefix (e.g. ``astro-ph/0612138``).

    Args:
        arxiv_id: arXiv paper identifier.

    Returns:
        Formatted metadata for the matching paper, including its ADS
        bibcode, DOI, and abstract.
    """
    ctx = mcp.get_context()
    client: ADSClient = ctx.request_context.lifespan_context["client"]
    # Normalise: strip "arXiv:" prefix if present
    clean_id = arxiv_id.strip().lstrip("arXiv:").lstrip("arxiv:")
    fields = (
        "bibcode,title,author,year,abstract,doi,identifier,"
        "pub,volume,page,keyword,citation_count,arxiv_class"
    )
    try:
        data = await client.search(
            f"identifier:arXiv:{clean_id}", fields=fields, rows=1
        )
        docs = data.get("response", {}).get("docs", [])
        if not docs:
            # Try alternate identifier form
            data = await client.search(
                f"identifier:{clean_id}", fields=fields, rows=1
            )
            docs = data.get("response", {}).get("docs", [])
        if not docs:
            return f"No paper found for arXiv ID: {arxiv_id}"
        doc = docs[0]
        bibcode = doc.get("bibcode", "")
        return await get_abstract(bibcode)
    except ADSError as exc:
        return f"ADS API error: {exc.message}"


# ---------------------------------------------------------------------------
# Tool: find_doi
# ---------------------------------------------------------------------------


@mcp.tool
async def find_doi(doi: str) -> str:
    """Look up an ADS paper by its DOI.

    Args:
        doi: Digital Object Identifier, e.g.
            ``"10.3847/2041-8213/ab5c56"``.

    Returns:
        Formatted metadata for the matching paper.
    """
    ctx = mcp.get_context()
    client: ADSClient = ctx.request_context.lifespan_context["client"]
    # Strip URL prefix if present
    clean_doi = doi.strip().lstrip("https://doi.org/").lstrip("http://dx.doi.org/")
    fields = (
        "bibcode,title,author,year,abstract,doi,identifier,"
        "pub,volume,page,keyword,citation_count"
    )
    try:
        data = await client.search(f"doi:{clean_doi}", fields=fields, rows=1)
        docs = data.get("response", {}).get("docs", [])
        if not docs:
            return f"No paper found for DOI: {doi}"
        bibcode = docs[0].get("bibcode", "")
        return await get_abstract(bibcode)
    except ADSError as exc:
        return f"ADS API error: {exc.message}"


# ---------------------------------------------------------------------------
# Tool: get_metrics
# ---------------------------------------------------------------------------


@mcp.tool
async def get_metrics(bibcodes: list[str]) -> str:
    """Retrieve citation and usage metrics for one or more ADS papers.

    Returns basic publication stats, citation counts, and bibliometric
    indicators (h-index, g-index, etc.).

    Args:
        bibcodes: List of ADS bibcodes to retrieve metrics for.

    Returns:
        Human-readable summary of the metrics, including total citations,
        h-index, i10-index, and read counts.
    """
    ctx = mcp.get_context()
    client: ADSClient = ctx.request_context.lifespan_context["client"]
    try:
        data = await client.metrics(bibcodes, types=["basic", "citations", "indicators"])
        lines: list[str] = []

        basic = data.get("basic stats", {})
        if basic:
            lines.append("=== Basic Stats ===")
            lines.append(f"Number of papers    : {basic.get('number of papers', 'N/A')}")
            lines.append(f"Total reads         : {basic.get('total number of reads', 'N/A')}")
            lines.append(f"Total downloads     : {basic.get('total number of downloads', 'N/A')}")

        cite = data.get("citation stats", {})
        if cite:
            lines.append("\n=== Citation Stats ===")
            lines.append(
                f"Total citations     : {cite.get('total number of citations', 'N/A')}"
            )
            lines.append(
                f"Refereed citations  : {cite.get('total number of refereed citations', 'N/A')}"
            )
            lines.append(
                f"Citing papers       : {cite.get('number of citing papers', 'N/A')}"
            )

        ind = data.get("indicators", {})
        if ind:
            lines.append("\n=== Bibliometric Indicators ===")
            for key in ("h", "g", "m", "i10", "i100", "tori", "riq"):
                val = ind.get(key)
                if val is not None:
                    lines.append(f"{key:20s}: {val}")

        skipped = data.get("skipped bibcodes", [])
        if skipped:
            lines.append(f"\nSkipped (no data)   : {', '.join(skipped)}")

        return "\n".join(lines) if lines else "No metrics data returned."
    except ADSError as exc:
        return f"ADS API error: {exc.message}"


# ---------------------------------------------------------------------------
# Tool: get_similar
# ---------------------------------------------------------------------------


@mcp.tool
async def get_similar(bibcode: str, rows: int = 10) -> str:
    """Find papers similar to a given ADS paper.

    Uses ADS's ``similar()`` operator which performs more-like-this
    matching based on the paper's text.

    Args:
        bibcode: ADS bibcode of the reference paper.
        rows: Number of similar papers to return. Defaults to ``10``.

    Returns:
        Formatted list of papers similar to the given bibcode.
    """
    ctx = mcp.get_context()
    client: ADSClient = ctx.request_context.lifespan_context["client"]
    try:
        data = await client.search(
            f"similar(bibcode:{bibcode})",
            fields="bibcode,title,author,year,doi,citation_count,pub,abstract",
            rows=rows,
            sort="score desc",
        )
        return _format_results(data)
    except ADSError as exc:
        return f"ADS API error: {exc.message}"


# ---------------------------------------------------------------------------
# Tool: author_search
# ---------------------------------------------------------------------------


@mcp.tool
async def author_search(
    author: str,
    rows: int = 20,
    sort: str = "citation_count desc",
    refereed_only: bool = False,
) -> str:
    """Search for papers by a specific author.

    The author name is matched using ADS's ``author:`` field operator
    which handles last-name-first and initials variations.

    Args:
        author: Author name, e.g. ``"Einstein, A"`` or
            ``"van der Hulst, J.M."``.
        rows: Maximum number of results. Defaults to ``20``.
        sort: Sort order. Defaults to ``"citation_count desc"`` to show
            the author's most-cited papers first.
        refereed_only: If ``True``, restrict results to refereed
            journals. Defaults to ``False``.

    Returns:
        Formatted list of papers matching the author query.
    """
    ctx = mcp.get_context()
    client: ADSClient = ctx.request_context.lifespan_context["client"]
    q = f'author:"{author}"'
    if refereed_only:
        q += " AND property:refereed"
    fields = "bibcode,title,author,year,doi,citation_count,read_count,pub"
    try:
        data = await client.search(q, fields=fields, rows=rows, sort=sort)
        return _format_results(data)
    except ADSError as exc:
        return f"ADS API error: {exc.message}"


# ---------------------------------------------------------------------------
# Tool: get_paper_details
# ---------------------------------------------------------------------------


_ALL_FIELDS = (
    "abstract,ack,aff,alternate_bibcode,alternate_title,arxiv_class,"
    "author,author_count,bibcode,bibgroup,bibstem,body,citation,"
    "citation_count,comment,copyright,data,database,doctype,doi,"
    "editor,eid,entdate,esources,facility,grant,identifier,"
    "indexeddate,isbn,issn,issue,keyword,lang,links_data,nedid,"
    "nedtype,orcid_pub,orcid_other,orcid_user,page,page_count,"
    "page_range,property,pub,pub_raw,pubdate,pubnote,read_count,"
    "reference,simbad_object_ids,title,vizier,volume,year"
)


@mcp.tool
async def get_paper_details(bibcode: str, fields: str = "") -> str:
    """Retrieve detailed metadata fields for an ADS paper.

    Returns a JSON-like representation of all available metadata for the
    requested paper, useful when specific fields beyond the default set are
    needed.

    Args:
        bibcode: ADS bibcode of the paper.
        fields: Comma-separated list of ADS fields to return.  If empty,
            a comprehensive default set is used.  Available fields include:
            ``abstract``, ``aff``, ``author``, ``bibcode``,
            ``citation_count``, ``doi``, ``identifier``, ``keyword``,
            ``pub``, ``title``, ``year``, and many more.

    Returns:
        Human-readable key-value summary of all requested metadata fields.
    """
    ctx = mcp.get_context()
    client: ADSClient = ctx.request_context.lifespan_context["client"]
    fl = fields or _ALL_FIELDS
    try:
        data = await client.search(f"bibcode:{bibcode}", fields=fl, rows=1)
        docs = data.get("response", {}).get("docs", [])
        if not docs:
            return f"No paper found for bibcode: {bibcode}"
        doc = docs[0]
        lines = []
        for key, value in sorted(doc.items()):
            if isinstance(value, list):
                if len(value) <= 5:
                    lines.append(f"{key}: {', '.join(str(v) for v in value)}")
                else:
                    lines.append(
                        f"{key}: {', '.join(str(v) for v in value[:5])} "
                        f"... ({len(value)} total)"
                    )
            else:
                text = str(value)
                if len(text) > 500:
                    text = text[:500] + "…"
                lines.append(f"{key}: {text}")
        return "\n".join(lines)
    except ADSError as exc:
        return f"ADS API error: {exc.message}"


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """Start the ADS MCP server using stdio transport.

    This function is called when the package is run as a script
    (``python -m ads_mcp.server``) or via the ``ads-mcp`` console script.
    """
    logging.basicConfig(level=os.environ.get("ADS_MCP_LOG_LEVEL", "WARNING"))
    mcp.run()


if __name__ == "__main__":
    main()
