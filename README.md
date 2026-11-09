# ★ Star (Tem) Plate

**Composable workflow template discovery for developers, vibe coders, and AI agents.**

A local-first Python MCP server and SQLite FTS5 template index. Version 0.1
starts with the **public n8n workflow template catalog** and exposes a
provider-neutral format intended for future Make, Zapier, Activepieces,
Node-RED, and agent-workflow adapters.

[![Python CI](https://github.com/popstarsai/Star--tem--plate/actions/workflows/ci.yml/badge.svg)](https://github.com/popstarsai/Star--tem--plate/actions/workflows/ci.yml)

## What works

- Index n8n public workflow **metadata** with pagination and explicit throttling.
- Search keywords, source, category, all required integration labels, or exclude integrations.
- Resolve source-attributed templates and link to their original n8n pages.
- Suggest template pairs sharing integration names (discovery only; **not executable joins**).
- Expose four read-only MCP tools: search_templates, get_template,
  suggest_compositions, and catalog_status.

## Quick start

Python 3.11+ required. Installing the package provides the MCP Python SDK.

~~~bash
git clone https://github.com/popstarsai/Star--tem--plate.git
cd Star--tem--plate
python -m pip install -e .

# Fast initial index: first three pages
star-plate sync --pages 3

# Search the local metadata index
star-plate search "Slack" --integration "Google Sheets"
star-plate search "email" --exclude-integration "OpenAI"
star-plate status

# Run the stdio MCP server (connect through an MCP client)
star-plate-mcp
~~~

For a full scan, run **star-plate sync --all**. This can require many requests;
observe n8n's access policies and rate limits. A sync uses public catalog
endpoints and needs no private n8n account or API key. No catalog data is
bundled into this repository; run sync before searching.

The database defaults to ~/.cache/star-tem-plate/catalog.sqlite3, or
$XDG_CACHE_HOME/star-tem-plate/catalog.sqlite3. Set STAR_PLATE_DB to override.

## MCP client configuration

Example for MCP clients supporting the usual mcpServers JSON convention:

~~~json
{
  "mcpServers": {
    "star-tem-plate": {
      "command": "star-plate-mcp",
      "args": []
    }
  }
}
~~~

Use the full path to the installed executable if your host cannot find it.
Codex, Claude, and Goose may each have different configuration syntax; use
their current MCP registration commands/settings to launch this stdio server.

Agents can now ask:
- Find public n8n templates for Slack that also use Google Sheets.
- Find AI workflow templates that do not mention Gmail.
- Suggest two related workflows for lead enrichment and explain what
  data-contract checks would be needed before connecting them.

## Architecture

~~~text
Public n8n template search endpoint
               |
         n8n adapter
               |
  normalized source/ID/title/URL/integrations/categories
               |
      SQLite + FTS5 index
               |
     CLI search / MCP tools
               |
      Codex, Claude, Goose, other MCP clients

Future adapters: Make, Zapier, Activepieces, Node-RED...
Future surfaces: REST API, skills, Hermes and Goose harnesses
~~~

New providers must supply the same normalized metadata fields and use their
own source namespace. The initial provider is in src/star_template/n8n.py;
the index itself is independent of n8n. Cross-platform mapping and real
workflow composition are **not** implemented in v0.1.

## Tests

~~~bash
python -m unittest discover -s tests -v
~~~

Tests are offline with synthetic templates. GitHub Actions runs them on
Python 3.12. A live n8n sync has not been part of the offline test suite.

## License, credit, and safety

The **code in this repository** is licensed under Apache 2.0. This does
not relicense n8n, its workflow library, or third-party authors' templates.

The tool stores public **metadata** and original URLs, not template JSON.
It does not retrieve private workflows, embed credentials, or execute
third-party automation code. Review original sources, applicable platform
terms, and each template's license before downloading, adapting, or sharing
their workflow definitions. Shared integration labels are only hints, not
proof of a valid data path or technical compatibility.

n8n documents its public template search endpoint here:
https://docs.n8n.io/deploy/host-n8n/configure-n8n/basic-configuration/configuration-examples/configure-a-custom-workflow-templates-library/

## Contributing

Source adapters, tests, documentation, and integrations are welcome.
See [CONTRIBUTING.md](CONTRIBUTING.md).
