"""Public template-catalog adapter. Not the authenticated n8n instance API."""
from __future__ import annotations
import json
import os
import time
import urllib.parse
import urllib.request
from star_template.catalog import Catalog, normalize_n8n

class N8nProvider:
    name = "n8n"

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.getenv("STAR_PLATE_N8N_URL", "https://api.n8n.io")).rstrip("/")
        if not (self.base_url.startswith("https://") or
                self.base_url.startswith("http://localhost:") or
                self.base_url.startswith("http://127.0.0.1:")):
            raise ValueError("Use HTTPS except for localhost fixtures")

    def fetch_page(self, page: int, rows: int):
        params = urllib.parse.urlencode({"page": page, "rows": rows})
        request = urllib.request.Request(
            self.base_url + "/templates/search?" + params,
            headers={"Accept": "application/json", "User-Agent": "Star-Tem-Plate/0.1"})
        with urllib.request.urlopen(request, timeout=25) as result:
            response = json.load(result)
        root = response.get("data", response) if isinstance(response, dict) else response
        if isinstance(root, list):
            workflows, total = root, None
        elif isinstance(root, dict):
            workflows = root.get("workflows", root.get("results"))
            total = next((root[k] for k in ("totalWorkflows", "total", "totalCount")
                          if isinstance(root.get(k), int)), None)
        else:
            raise ValueError("Unrecognized template API response")
        if not isinstance(workflows, list):
            raise ValueError("Template API schema changed: missing workflow list")
        return [normalize_n8n(w) for w in workflows if isinstance(w, dict)], total

def sync(catalog: Catalog, provider: N8nProvider, *, pages: int = 3,
         rows: int = 100, delay: float = 0.4) -> dict:
    if pages < 0 or not 1 <= rows <= 100 or delay < 0:
        raise ValueError("Invalid sync options")
    page, count, seen, total, complete = 1, 0, set(), None, False
    while pages == 0 or page <= pages:
        records, reported = provider.fetch_page(page, rows)
        total = reported if reported is not None else total
        new = [record for record in records
               if (record["source"], record["external_id"]) not in seen]
        if not new:
            complete = True
            break
        seen.update((r["source"], r["external_id"]) for r in new)
        count += catalog.upsert(new)
        if len(records) < rows or (total is not None and page * rows >= total):
            complete = True
            break
        page += 1
        if delay:
            time.sleep(delay)
    return {"indexed_this_run": count, "reported_total": total,
            "complete": complete, "catalog": catalog.status()}
