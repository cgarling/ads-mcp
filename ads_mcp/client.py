"""HTTP client for the SAO/NASA Astrophysics Data System (ADS) API.

This module provides a thin, async wrapper around the ADS REST API
(https://github.com/adsabs/adsabs-dev-api).  All network I/O is performed
with :mod:`httpx` so it plays nicely with FastMCP's async event loop.

Example:
    Basic usage with an async context manager::

        async with ADSClient(api_key="my-token") as client:
            result = await client.search("black hole accretion", rows=5)
            print(result)
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv

load_dotenv()

#: Base URL for all ADS v1 API requests.
ADS_BASE_URL = "https://api.adsabs.harvard.edu/v1"

#: Default fields returned by the search endpoint.
DEFAULT_SEARCH_FIELDS = (
    "bibcode,title,author,year,abstract,doi,arxiv_class,"
    "identifier,citation_count,read_count,pub,volume,page,keyword"
)


class ADSError(Exception):
    """Raised when the ADS API returns a non-2xx response.

    Attributes:
        status_code: HTTP status code returned by the server.
        message: Human-readable error description.
    """

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"ADS API error {status_code}: {message}")


class ADSClient:
    """Async HTTP client for the ADS API.

    Wraps the ADS REST API endpoints into straightforward async methods.
    An API key is required; obtain one at
    https://ui.adsabs.harvard.edu/user/settings/token.

    Args:
        api_key: ADS API bearer token. If *None*, the value of the
            ``ADS_API_TOKEN`` environment variable is used.
        timeout: Request timeout in seconds. Defaults to ``30``.

    Raises:
        ValueError: If no API key is provided and ``ADS_API_TOKEN`` is
            not set in the environment.

    Example:
        ::

            async with ADSClient() as client:
                papers = await client.search("exoplanet atmospheres", rows=10)
    """

    def __init__(self, api_key: str | None = None, timeout: float = 30.0) -> None:
        resolved_key = api_key or os.environ.get("ADS_API_TOKEN")
        if not resolved_key:
            raise ValueError(
                "No ADS API key provided. Set the ADS_API_TOKEN environment variable "
                "or pass api_key= to ADSClient."
            )
        self._api_key = resolved_key
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # Context-manager helpers
    # ------------------------------------------------------------------

    async def __aenter__(self) -> ADSClient:
        self._client = httpx.AsyncClient(
            base_url=ADS_BASE_URL,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=self._timeout,
        )
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("ADSClient must be used as an async context manager.")
        return self._client

    def _check(self, response: httpx.Response) -> httpx.Response:
        """Raise :class:`ADSError` for non-2xx responses.

        Args:
            response: The HTTP response to check.

        Returns:
            The same *response* object if the status is successful.

        Raises:
            ADSError: If the status code indicates an error.
        """
        if response.is_error:
            try:
                detail = response.json().get("error", response.text)
            except Exception:
                detail = response.text
            raise ADSError(response.status_code, str(detail))
        return response

    # ------------------------------------------------------------------
    # Search endpoint
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        fields: str = DEFAULT_SEARCH_FIELDS,
        rows: int = 10,
        start: int = 0,
        sort: str = "date desc",
    ) -> dict[str, Any]:
        """Search the ADS database.

        Calls ``GET /v1/search/query``.

        Args:
            query: Solr/ADS query string, e.g. ``"author:Einstein relativity"``.
            fields: Comma-separated list of fields to return.
            rows: Maximum number of results. Capped at 2000 by ADS.
            start: Offset into the result set (for pagination).
            sort: Sort order, e.g. ``"citation_count desc"``.

        Returns:
            Parsed JSON response from ADS containing ``response.docs`` and
            ``response.numFound``.

        Raises:
            ADSError: If ADS returns a non-2xx status.
        """
        params = urlencode(
            {"q": query, "fl": fields, "rows": rows, "start": start, "sort": sort}
        )
        r = await self._http.get(f"/search/query?{params}")
        return self._check(r).json()

    # ------------------------------------------------------------------
    # Export endpoint
    # ------------------------------------------------------------------

    async def export(self, bibcodes: list[str], fmt: str = "bibtex") -> str:
        """Export one or more records in a bibliographic format.

        Calls ``POST /v1/export/{fmt}``.

        Args:
            bibcodes: List of ADS bibcodes to export.
            fmt: Export format.  One of ``bibtex``, ``bibtexabs``, ``ris``,
                ``endnote``, ``procite``, ``refworks``, ``aastex``,
                ``icarus``, ``mnras``, ``soph``, ``dcxml``, ``refxml``,
                ``ads``, ``medlars``, ``votable``.

        Returns:
            The exported bibliography as a plain string.

        Raises:
            ADSError: If ADS returns a non-2xx status.
        """
        payload = json.dumps({"bibcode": bibcodes})
        r = await self._http.post(
            f"/export/{fmt}",
            content=payload,
            headers={"Content-Type": "application/json"},
        )
        data = self._check(r).json()
        return data.get("export", "")

    # ------------------------------------------------------------------
    # Metrics endpoint
    # ------------------------------------------------------------------

    async def metrics(
        self,
        bibcodes: list[str],
        types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Retrieve citation and usage metrics for a set of papers.

        Calls ``POST /v1/metrics``.

        Args:
            bibcodes: List of ADS bibcodes to retrieve metrics for.
            types: Optional list selecting which metric types to return.
                Allowed values: ``"basic"``, ``"citations"``,
                ``"indicators"``, ``"histograms"``, ``"timeseries"``.
                If *None*, all metrics are returned.

        Returns:
            Parsed JSON metrics object from ADS.

        Raises:
            ADSError: If ADS returns a non-2xx status.
        """
        body: dict[str, Any] = {"bibcodes": bibcodes}
        if types:
            body["types"] = types
        r = await self._http.post(
            "/metrics",
            content=json.dumps(body),
            headers={"Content-Type": "application/json"},
        )
        return self._check(r).json()

    # ------------------------------------------------------------------
    # Convenience searches
    # ------------------------------------------------------------------

    async def search_by_bibcode(
        self, bibcodes: list[str], fields: str = DEFAULT_SEARCH_FIELDS, rows: int = 2000
    ) -> dict[str, Any]:
        """Retrieve records for a list of bibcodes via a big-query POST.

        Calls ``POST /v1/search/bigquery``.

        Args:
            bibcodes: List of ADS bibcodes.
            fields: Comma-separated list of fields to return.
            rows: Maximum number of results.

        Returns:
            Parsed JSON response from ADS.

        Raises:
            ADSError: If ADS returns a non-2xx status.
        """
        params = urlencode({"q": "*:*", "fl": fields, "rows": rows})
        payload = "bibcode\n" + "\n".join(bibcodes)
        r = await self._http.post(
            f"/search/bigquery?{params}",
            content=payload,
            headers={"Content-Type": "big-query/csv"},
        )
        return self._check(r).json()

    async def get_references(self, bibcode: str, rows: int = 200) -> dict[str, Any]:
        """Fetch the reference list of a paper.

        Uses the ``references()`` operator in the ADS search API.

        Args:
            bibcode: ADS bibcode of the paper whose references are requested.
            rows: Maximum number of references to return.

        Returns:
            Parsed JSON search response from ADS.

        Raises:
            ADSError: If ADS returns a non-2xx status.
        """
        return await self.search(
            f"references(bibcode:{bibcode})",
            fields="bibcode,title,author,year,doi,pub",
            rows=rows,
            sort="date desc",
        )

    async def get_citations(self, bibcode: str, rows: int = 200) -> dict[str, Any]:
        """Fetch the papers that cite a given paper.

        Uses the ``citations()`` operator in the ADS search API.

        Args:
            bibcode: ADS bibcode of the paper whose citations are requested.
            rows: Maximum number of citing papers to return.

        Returns:
            Parsed JSON search response from ADS.

        Raises:
            ADSError: If ADS returns a non-2xx status.
        """
        return await self.search(
            f"citations(bibcode:{bibcode})",
            fields="bibcode,title,author,year,doi,citation_count,pub",
            rows=rows,
            sort="date desc",
        )
