#!/usr/bin/env python3
"""Sync legislative records from configured internet sources.

Supports:
- RSS/Atom sources
- JSON API sources with configurable field mapping
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def fetch_url(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "bill-to-brief-sync/1.0 (+https://example.org)",
            "Accept": "application/json, application/xml, text/xml;q=0.9, */*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def sha_record(record: Dict[str, Any]) -> str:
    body = json.dumps(record, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def normalize_rss_items(source_name: str, xml_bytes: bytes) -> Iterable[Dict[str, Any]]:
    root = ET.fromstring(xml_bytes)

    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    for item in items:
        title = text_or_none(item.find("title")) or text_or_none(
            item.find("{http://www.w3.org/2005/Atom}title")
        )
        summary = text_or_none(item.find("description")) or text_or_none(
            item.find("{http://www.w3.org/2005/Atom}summary")
        )
        link = text_or_none(item.find("link"))
        if not link:
            atom_link = item.find("{http://www.w3.org/2005/Atom}link")
            if atom_link is not None:
                link = atom_link.attrib.get("href")
        published = text_or_none(item.find("pubDate")) or text_or_none(
            item.find("{http://www.w3.org/2005/Atom}updated")
        )
        guid = text_or_none(item.find("guid"))

        record_id = guid or link or title
        if not record_id:
            continue

        yield {
            "id": str(record_id),
            "title": title,
            "summary": summary,
            "url": link,
            "published_at": published,
            "source": source_name,
        }


def text_or_none(node: Any) -> str | None:
    if node is None:
        return None
    text = getattr(node, "text", None)
    if text is None:
        return None
    text = text.strip()
    return text or None


def get_nested(d: Dict[str, Any], dot_path: str) -> Any:
    if not dot_path:
        return d
    cur: Any = d
    for part in dot_path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def normalize_json_items(source: Dict[str, Any], json_bytes: bytes) -> Iterable[Dict[str, Any]]:
    payload = json.loads(json_bytes.decode("utf-8"))
    items = get_nested(payload, source.get("items_path", ""))
    if not isinstance(items, list):
        return []

    field_map = source.get("field_map", {})
    source_name = source["name"]

    normalized: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        rid = value_by_map(item, field_map, "id") or value_by_map(item, field_map, "url")
        if rid is None:
            continue

        normalized.append(
            {
                "id": str(rid),
                "title": value_by_map(item, field_map, "title"),
                "summary": value_by_map(item, field_map, "summary"),
                "url": value_by_map(item, field_map, "url"),
                "published_at": value_by_map(item, field_map, "published_at"),
                "source": source_name,
            }
        )
    return normalized


def value_by_map(item: Dict[str, Any], field_map: Dict[str, str], key: str) -> Any:
    source_field = field_map.get(key)
    if not source_field:
        return None
    return item.get(source_field)


def sync_sources(
    sources_path: Path,
    output_path: Path,
    state_path: Path,
    updates_path: Path,
) -> Dict[str, Any]:
    sources = read_json(sources_path, default=[])
    state = read_json(state_path, default={"records": {}, "last_run": None})
    records_state: Dict[str, Dict[str, Any]] = state.setdefault("records", {})

    all_records: Dict[str, Dict[str, Any]] = {}
    changed_records: List[Dict[str, Any]] = []

    for source in sources:
        source_name = source["name"]
        source_type = source["type"]
        content = fetch_url(source["url"])

        if source_type == "rss":
            records = list(normalize_rss_items(source_name, content))
        elif source_type == "json":
            records = list(normalize_json_items(source, content))
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

        for record in records:
            compound_id = f"{record['source']}::{record['id']}"
            fingerprint = sha_record(record)
            prior = records_state.get(compound_id)

            if prior is None or prior.get("fingerprint") != fingerprint:
                changed_records.append(record)

            records_state[compound_id] = {
                "fingerprint": fingerprint,
                "last_seen": utc_now_iso(),
            }
            all_records[compound_id] = record

    output_payload = {
        "generated_at": utc_now_iso(),
        "count": len(all_records),
        "records": sorted(all_records.values(), key=lambda r: (r["source"], str(r["id"]))),
    }
    updates_payload = {
        "generated_at": utc_now_iso(),
        "count": len(changed_records),
        "records": changed_records,
    }

    state["last_run"] = utc_now_iso()

    write_json(output_path, output_payload)
    write_json(state_path, state)
    write_json(updates_path, updates_payload)

    return {
        "total_records": len(all_records),
        "changed_records": len(changed_records),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync legislative sources")
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--updates", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = sync_sources(args.sources, args.output, args.state, args.updates)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
