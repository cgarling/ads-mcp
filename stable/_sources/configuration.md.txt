(configuration)=
# Configuration Reference

ads-mcp is configured entirely through environment variables.  The
recommended approach is to place them in a `.env` file next to wherever
you run the server; the server loads this file automatically via
[python-dotenv](https://pypi.org/project/python-dotenv/).

## Variables

### `ADS_API_TOKEN` *(required)*

Your ADS API bearer token.  Obtain one at
<https://ui.adsabs.harvard.edu/user/settings/token>.

```ini
ADS_API_TOKEN=your_key_here
```

:::{warning}
Keep this value secret.  Do **not** commit it to version control.
:::

### `ADS_MCP_LOG_LEVEL` *(optional)*

Python log level for the server process.

| Value | Effect |
|-------|--------|
| `DEBUG` | Very verbose output; useful for development |
| `INFO` | Informational messages |
| `WARNING` | *(default)* Warnings and errors only |
| `ERROR` | Errors only |

```ini
ADS_MCP_LOG_LEVEL=WARNING
```

## Rate limits

ADS API access is rate-limited per endpoint (typically 5,000 requests per
day for search).  The HTTP response headers `X-RateLimit-Limit`,
`X-RateLimit-Remaining`, and `X-RateLimit-Reset` report the current status.
If you exceed the limit you will receive an `ADSError` with status 429.

Contact `adshelp@cfa.harvard.edu` if you need higher limits for a
research project.
