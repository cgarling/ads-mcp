# GitHub Copilot Cloud Agent

ads-mcp can be used as a tool server for [GitHub Copilot coding agent](https://docs.github.com/en/copilot/using-github-copilot/using-github-copilot-coding-agent-in-your-ide)
sessions so that Copilot can search ADS while helping you write research
software or papers.

## `copilot-setup-steps.yml`

Create or edit `.github/copilot-setup-steps.yml` in your repository:

```yaml
steps:
  - name: Install ads-mcp
    run: pip install ads-mcp

  - name: Configure ADS API key
    env:
      ADS_API_TOKEN: ${{ secrets.ADS_API_TOKEN }}
    run: echo "ADS_API_TOKEN=$ADS_API_TOKEN" >> $GITHUB_ENV
```

## Add the secret

1. Go to **Settings → Secrets and variables → Actions**.
2. Click **New repository secret**.
3. Name: `ADS_API_TOKEN`, Value: your ADS token.

## MCP server block

In your Copilot settings (or `.github/copilot-setup-steps.yml`), add
the MCP server:

```json
{
  "mcpServers": {
    "ads": {
      "type": "local",
      "command": "uvx",
      "args": ["ads-mcp"],
      "env": {
        "ADS_API_TOKEN": "$ADS_API_TOKEN"
      },
      "tools": ["*"]
    }
  }
}
```

## Usage

Once configured, start a Copilot chat and ask questions like:

> "Find the 5 most-cited papers on gravitational waves from 2017."

> "Get the BibTeX for arXiv:2301.07688."
