"""A provider-neutral, read-only-to-agents SQLite index of template metadata."""
from __future__ import annotations
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def db_path() -> Path:
    override = os.getenv("STAR_PLATE_DB")
    if override:
        return Path(override).expanduser()
    return Path(os.getenv("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "star-tem-plate" / "catalog.sqlite3"

def names(data: Any) -> list[str]:
    if not isinstance(data, list):
        return []
    output = []
    for value in data:
        item = value if isinstance(value, str) else (
            value.get("displayName") or value.get("name") or "" if isinstance(value, dict) else "")
        if isinstance(item, str) and item.strip() and item.strip() not in output:
            output.append(item.strip())
    return output

def normalize_n8n(raw: dict) -> dict:
    if raw.get("id") is None:
        raise ValueError("Template has no id")
    user = raw.get("user") or {}
    link = raw.get("url")
    if not isinstance(link, str) or not link.startswith("https://n8n.io/workflows/"):
        link = "https://n8n.io/workflows/" + str(raw["id"])
    return {
        "source": "n8n", "external_id": str(raw["id"]),
        "title": str(raw.get("name") or "Untitled"),
        "description": str(raw.get("description") or ""),
        "url": link, "integrations": names(raw.get("nodes")),
        "categories": names(raw.get("categories")),
        "author": str(user.get("username") or "") if isinstance(user, dict) else "",
    }

class Catalog:
    def __init__(self, path: str | Path | None = None):
        path = path if path is not None else db_path()
        if str(path) != ":memory:":
            Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("""CREATE TABLE IF NOT EXISTS templates(
            source TEXT NOT NULL, external_id TEXT NOT NULL,
            title TEXT NOT NULL, description TEXT NOT NULL, url TEXT NOT NULL,
            integrations TEXT NOT NULL, categories TEXT NOT NULL,
            author TEXT NOT NULL, fetched_at TEXT NOT NULL,
            PRIMARY KEY(source, external_id))""")
        self.conn.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS search_index
            USING fts5(title, description, integrations, categories)""")
        self.conn.commit()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.conn.close()

    def upsert(self, records: list[dict]) -> int:
        timestamp = datetime.now(timezone.utc).isoformat()
        with self.conn:
            for row in records:
                integrations = list(row.get("integrations", []))
                categories = list(row.get("categories", []))
                self.conn.execute("""INSERT INTO templates VALUES(?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(source,external_id) DO UPDATE SET
                    title=excluded.title, description=excluded.description,
                    url=excluded.url, integrations=excluded.integrations,
                    categories=excluded.categories, author=excluded.author,
                    fetched_at=excluded.fetched_at""", (
                    row["source"], row["external_id"], row["title"],
                    row["description"], row["url"], json.dumps(integrations),
                    json.dumps(categories), row.get("author", ""), timestamp))
                rowid = self.conn.execute(
                    "SELECT rowid FROM templates WHERE source=? AND external_id=?",
                    (row["source"], row["external_id"])).fetchone()[0]
                self.conn.execute("DELETE FROM search_index WHERE rowid=?", (rowid,))
                self.conn.execute("""INSERT INTO search_index
                    (rowid,title,description,integrations,categories)
                    VALUES(?,?,?,?,?)""", (rowid, row["title"], row["description"],
                                           " ".join(integrations), " ".join(categories)))
        return len(records)

    @staticmethod
    def to_dict(row: sqlite3.Row) -> dict:
        result = dict(row)
        result["integrations"] = json.loads(result["integrations"])
        result["categories"] = json.loads(result["categories"])
        return result

    def get(self, source: str, key: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM templates WHERE source=? AND external_id=?",
            (source, str(key))).fetchone()
        return self.to_dict(row) if row else None

    def search(self, query: str = "", *, source: str | None = None,
               integrations: list[str] | None = None,
               exclude_integrations: list[str] | None = None,
               category: str | None = None, limit: int = 10) -> list[dict]:
        words = re.findall(r"\w+", query)[:16]
        match = " AND ".join('"' + word + '"' for word in words)
        sql = "SELECT t.* FROM templates t"
        clauses, params = [], []
        if match:
            sql += " JOIN search_index ON search_index.rowid=t.rowid"
            clauses.append("search_index MATCH ?")
            params.append(match)
        if source:
            clauses.append("t.source=?")
            params.append(source)
        for value in integrations or []:
            clauses.append("LOWER(t.integrations) LIKE ?")
            params.append("%" + value.lower() + "%")
        for value in exclude_integrations or []:
            clauses.append("LOWER(t.integrations) NOT LIKE ?")
            params.append("%" + value.lower() + "%")
        if category:
            clauses.append("LOWER(t.categories) LIKE ?")
            params.append("%" + category.lower() + "%")
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY " + ("bm25(search_index)" if match else "t.title COLLATE NOCASE")
        sql += " LIMIT ?"
        params.append(max(1, min(int(limit), 50)))
        return [self.to_dict(row) for row in self.conn.execute(sql, params)]

    def status(self) -> dict:
        rows = self.conn.execute("""SELECT source,COUNT(*) count,MAX(fetched_at) last_indexed
            FROM templates GROUP BY source ORDER BY source""").fetchall()
        return {"total": sum(row["count"] for row in rows), "sources": [dict(r) for r in rows]}

def suggest_pairs(catalog: Catalog, goal: str, limit: int = 5) -> dict:
    found = catalog.search(goal, limit=40)
    pairs = []
    for index, first in enumerate(found):
        for second in found[index + 1:]:
            common = sorted(set(n.casefold() for n in first["integrations"]) &
                            set(n.casefold() for n in second["integrations"]))
            if common:
                pairs.append({
                    "first": {"id": first["external_id"], "source": first["source"],
                              "title": first["title"], "url": first["url"]},
                    "second": {"id": second["external_id"], "source": second["source"],
                               "title": second["title"], "url": second["url"]},
                    "shared_integrations": common, "compatibility_verified": False})
    pairs.sort(key=lambda p: -len(p["shared_integrations"]))
    return {"goal": goal, "suggestions": pairs[:max(1, min(int(limit), 20))],
            "warning": "Overlapping integrations do not prove workflows can be joined."}
