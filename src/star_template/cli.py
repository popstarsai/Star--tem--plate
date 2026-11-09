"""Explicit metadata sync and search; no implicit network calls by MCP clients."""
import argparse
import json
import sys
from star_template.catalog import Catalog
from star_template.n8n import N8nProvider, sync

def main() -> int:
    parser = argparse.ArgumentParser(prog="star-plate")
    sub = parser.add_subparsers(dest="action", required=True)
    fetch = sub.add_parser("sync")
    pages = fetch.add_mutually_exclusive_group()
    pages.add_argument("--pages", type=int, default=3)
    pages.add_argument("--all", action="store_true")
    fetch.add_argument("--rows", type=int, default=100)
    fetch.add_argument("--delay", type=float, default=0.4)
    search = sub.add_parser("search")
    search.add_argument("query", nargs="?", default="")
    search.add_argument("--source")
    search.add_argument("--integration", action="append", default=[])
    search.add_argument("--exclude-integration", action="append", default=[])
    search.add_argument("--category")
    search.add_argument("--limit", type=int, default=10)
    get = sub.add_parser("get")
    get.add_argument("source")
    get.add_argument("id")
    sub.add_parser("status")
    sub.add_parser("serve")
    args = parser.parse_args()
    if args.action == "serve":
        from star_template.server import main as serve
        serve()
        return 0
    try:
        with Catalog() as catalog:
            if args.action == "sync":
                output = sync(catalog, N8nProvider(), pages=0 if args.all else args.pages,
                              rows=args.rows, delay=args.delay)
            elif args.action == "search":
                output = catalog.search(
                    args.query, source=args.source, integrations=args.integration,
                    exclude_integrations=args.exclude_integration, category=args.category,
                    limit=args.limit)
            elif args.action == "get":
                output = catalog.get(args.source, args.id)
            else:
                output = catalog.status()
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print("star-plate: " + str(error), file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
