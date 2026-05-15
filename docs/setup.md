(setup)=
# Setup & Installation

## Prerequisites

- Python 3.10 or later
- An [ADS API key](https://ui.adsabs.harvard.edu/user/settings/token)

## Install

### From PyPI (once published)

```bash
pip install ads-mcp
```

### From source

```bash
git clone https://github.com/cgarling/ads-mcp.git
cd ads-mcp
pip install -e .
```

## Configure your API key

The server reads your ADS API key from the `ADS_API_KEY` environment variable.

### Using a `.env` file (recommended)

Copy the template and fill in your key:

```bash
cp .env.example .env
# edit .env and replace the placeholder with your real key
```

Your `.env` should look like:

```ini
ADS_API_KEY=your_real_ads_key_here
```

:::{warning}
Never commit your `.env` file or your API key to version control.
`.env` is listed in `.gitignore` by default.
:::

### Using environment variables directly

```bash
export ADS_API_KEY=your_real_ads_key_here
ads-mcp
```

## Verify the installation

Run the server once to confirm it starts without errors:

```bash
ads-mcp
```

The server waits for MCP protocol messages on *stdin/stdout*.  Press
`Ctrl-C` to stop it.  You should see no error output if the key is valid.
