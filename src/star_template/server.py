"""A local read-only MCP server for searched workflow metadata."""
from mcp.server import MCPServer
from star_template.catalog import Catalog, suggest_pairs

mcp = MCPServer("Star (Tem) Plate",
                instructions="Search locally indexed public template metadata. "
                             "Do not assume suggested pairs are executable.")

@mcp.tool()
def search_templates(query: str = "", source: str | None = None,
                     integrations: list[str] | None = None,
                     exclude_integrations: list[str] | None = None,
                     category: str | None = None, limit: int = 10) -> dict:
    """Search keywords and ALL required / excluded integration labels."""
    with Catalog() as catalog:
        hits = catalog.search(query, source=source, integrations=integrations,
                              exclude_integrations=exclude_integrations,
                              category=category, limit=limit)
    return {"results": hits, "count": len(hits)}

@mcp.tool()
def get_template(source: str, template_id: str) -> dict:
    """Look up one template's source-attributed metadata and original URL."""
    with Catalog() as catalog:
        result = catalog.get(source, template_id)
    return {"found": result is not None, "template": result}

@mcp.tool()
def suggest_compositions(goal: str, limit: int = 5) -> dict:
    """Suggest related pairs; shared integrations do not verify compatibility."""
    with Catalog() as catalog:
        return suggest_pairs(catalog, goal, limit)

@mcp.tool()
def catalog_status() -> dict:
    """Show indexed providers, row counts, and freshness."""
    with Catalog() as catalog:
        return catalog.status()

def main() -> None:
    mcp.run()

if __name__ == "__main__":
    main()
