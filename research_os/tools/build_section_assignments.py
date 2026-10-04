#!/usr/bin/env python3
"""Build a complete folio-to-section DATA register from a frozen range source."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from record_scope import is_manuscript_content


def canonical_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(records_dir: Path, source_path: Path) -> dict[str, Any]:
    source = json.loads(source_path.read_text(encoding="utf-8"))
    ranges = source.get("ranges", [])
    if source.get("claim_class") != "DATA" or not ranges:
        raise ValueError("section source must be a non-empty DATA register")
    previous_end = 0
    for item in ranges:
        if (
            not isinstance(item.get("first_folio"), int)
            or not isinstance(item.get("last_folio"), int)
            or item["first_folio"] > item["last_folio"]
            or item["first_folio"] <= previous_end
            or not item.get("section_label")
        ):
            raise ValueError("section ranges must be ordered, disjoint, and labelled")
        previous_end = item["last_folio"]
    assignments = []
    for path in sorted(records_dir.glob("*.annotation.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        source_record = record.get("source", {})
        if not is_manuscript_content(record):
            continue
        folio_id = str(source_record.get("folio_or_cover_id", ""))
        numbers = {int(value) for value in re.findall(r"\d+", folio_id)}
        labels = {
            item["section_label"]
            for number in numbers
            for item in ranges
            if item["first_folio"] <= number <= item["last_folio"]
        }
        if not numbers or len(labels) != 1:
            raise ValueError(f"record {record.get('record_id')} has no unique catalog section")
        assignments.append({
            "record_id": record["record_id"],
            "folio_id": folio_id,
            "section_label": next(iter(labels)),
        })
    if not assignments:
        raise ValueError("no manuscript-content records found")
    digest_input = json.dumps(assignments, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": "1.0",
        "experiment_id": "EXP-2026-001",
        "claim_class": "DATA",
        "source": {
            "source_id": source["source_id"],
            "source_url": source["source_url"],
            "register_path": str(source_path),
            "register_sha256": canonical_sha256(source_path),
        },
        "record_count": len(assignments),
        "assignments_sha256": hashlib.sha256(digest_input.encode()).hexdigest(),
        "records": assignments,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("records_dir", type=Path)
    parser.add_argument("source_register", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.records_dir, args.source_register)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
