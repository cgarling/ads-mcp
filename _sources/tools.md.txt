(tools)=
# Available Tools

ads-mcp registers **13 tools** with the MCP host.  Each tool accepts
structured arguments and returns plain-text output that is easy for an
AI assistant to interpret and relay to the user.

---

## `search_ads`

Search the ADS database using the full [ADS/Solr query syntax](https://ui.adsabs.harvard.edu/help/search/).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | *(required)* | ADS query string |
| `rows` | `int` | `10` | Number of results to return (1–2000) |
| `start` | `int` | `0` | Pagination offset |
| `sort` | `str` | `"date desc"` | Sort order |
| `fields` | `str` | *sensible defaults* | Comma-separated ADS fields |

**Example queries:**

- `"dark matter annihilation"` — keyword search
- `"author:Einstein AND title:relativity"` — field-specific search
- `"abs:exoplanet AND year:2020-2024"` — abstract + year filter
- `"property:refereed AND keyword:black hole"` — refereed papers only

---

## `get_abstract`

Retrieve full metadata and the abstract of a paper by its ADS bibcode.

| Parameter | Type | Description |
|-----------|------|-------------|
| `bibcode` | `str` | ADS bibcode, e.g. `"2019ApJ...887L..24M"` |

Returns: title, authors, journal, DOI, arXiv ID, keywords, full abstract, and ADS URL.

---

## `get_references`

Retrieve the reference list of a paper.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bibcode` | `str` | *(required)* | ADS bibcode |
| `rows` | `int` | `50` | Maximum references to return |

---

## `get_citations`

Retrieve papers that cite a given paper.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bibcode` | `str` | *(required)* | ADS bibcode |
| `rows` | `int` | `50` | Maximum citing papers to return |

---

## `export_bibtex`

Export one or more papers as a BibTeX bibliography.

| Parameter | Type | Description |
|-----------|------|-------------|
| `bibcodes` | `list[str]` | List of ADS bibcodes |

**Example:** `export_bibtex(["2019ApJ...887L..24M", "2023A&A...670A..42S"])`

---

## `export_ris`

Export one or more papers in RIS format (compatible with Zotero, Mendeley, EndNote).

| Parameter | Type | Description |
|-----------|------|-------------|
| `bibcodes` | `list[str]` | List of ADS bibcodes |

---

## `export_citation`

Export papers in any format supported by ADS.

| Parameter | Type | Description |
|-----------|------|-------------|
| `bibcodes` | `list[str]` | List of ADS bibcodes |
| `fmt` | `str` | Target format (see below) |

**Supported formats:** `bibtex`, `bibtexabs`, `ris`, `endnote`, `procite`,
`refworks`, `aastex`, `icarus`, `mnras`, `soph`, `dcxml`, `refxml`,
`refabsxml`, `ads`, `medlars`, `votable`.

---

## `find_arxiv`

Look up a paper by its arXiv identifier.

| Parameter | Type | Description |
|-----------|------|-------------|
| `arxiv_id` | `str` | arXiv ID, e.g. `"2301.07688"` or `"astro-ph/0612138"` |

---

## `find_doi`

Look up a paper by its DOI.

| Parameter | Type | Description |
|-----------|------|-------------|
| `doi` | `str` | DOI, e.g. `"10.3847/2041-8213/ab5c56"` |

Accepts both bare DOIs and `https://doi.org/...` URL forms.

---

## `get_metrics`

Retrieve citation and usage metrics for one or more papers.

| Parameter | Type | Description |
|-----------|------|-------------|
| `bibcodes` | `list[str]` | List of ADS bibcodes |

Returns: number of papers, total reads, total downloads, citation counts,
and bibliometric indicators (h-index, g-index, i10-index, etc.).

---

## `get_similar`

Find papers similar to a given paper using ADS's more-like-this operator.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bibcode` | `str` | *(required)* | ADS bibcode |
| `rows` | `int` | `10` | Number of similar papers |

---

## `author_search`

Search for papers by a specific author.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `author` | `str` | *(required)* | Author name, e.g. `"Einstein, A"` |
| `rows` | `int` | `20` | Maximum results |
| `sort` | `str` | `"citation_count desc"` | Sort order |
| `refereed_only` | `bool` | `False` | Restrict to refereed journals |

---

## `get_paper_details`

Retrieve a comprehensive set of metadata fields for a paper.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bibcode` | `str` | *(required)* | ADS bibcode |
| `fields` | `str` | *all available fields* | Comma-separated field names |

Returns a verbose key-value dump of all available ADS metadata for the paper.
