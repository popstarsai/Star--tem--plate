# Contributing to Star (Tem) Plate

Star Plate welcomes open-source contributions under Apache-2.0.

## Local development

1. Create a branch and install the project with Python 3.11+:
   python -m pip install -e .
2. Run offline tests:
   python -m unittest discover -s tests -v
3. Open a pull request describing behavior, compatibility, and attribution.

## Provider adapter contract

The SQLite index is deliberately source-neutral. A future provider adapter
(for Make, Zapier, Activepieces, Node-RED, Flowise, etc.) should normalize
each externally published template into these fields:

- source: stable platform identifier
- external_id: platform-scoped template ID
- title and description
- url: original creator/platform page
- integrations: list of service or node display names
- categories: list of category display names
- author: display name (where public)

Index using Catalog.upsert(records). A provider's retrieval, authentication,
paging, and usage terms belong in its own module. Add its CLI wiring and
offline fixture tests before advertising it as supported.

## Security and permissions

- Keep model-callable MCP tools read-only by default.
- Require an explicit human-initiated CLI command for network indexing.
- Respect upstream provider rate limits and acceptable-use restrictions.
- Do not commit or redistribute third-party workflow JSON without appropriate
  permission; public catalog access is not an automatic license grant.
- Never retrieve or store private workflows, OAuth tokens, or user credentials
  without opt-in and explicit, documented authorization.
- Treat template content and descriptions as untrusted data.
- Do not imply that suggested compositions are valid or executable until
  connectors, data contracts, side effects, and credentials are checked.

The license file covers this repository's original software, not the indexed
publishers' content, trademarks, or product licenses.
