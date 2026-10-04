#!/usr/bin/env python3
"""Merge frozen section and scribe DATA assignments into the split strata manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build(section_path: Path, scribe_path: Path) -> dict[str, Any]:
    sections = json.loads(section_path.read_text(encoding="utf-8"))
    scribes = json.loads(scribe_path.read_text(encoding="utf-8"))
    if sections.get("claim_class") != "DATA" or scribes.get("claim_class") != "DATA":
        raise ValueError("section and scribe assignments must both be DATA")
    section_by_id = {item["record_id"]: item for item in sections.get("records", [])}
    scribe_by_id = {item["record_id"]: item for item in scribes.get("records", [])}
    if not section_by_id or set(section_by_id) != set(scribe_by_id):
        raise ValueError("section and scribe assignments must cover exactly the same records")

    section_source = sections.get("source", {})
    scribe_source = scribes.get("source", {})
    records = []
    for record_id in sorted(section_by_id):
        section = section_by_id[record_id]
        scribe = scribe_by_id[record_id]
        records.append({
            "record_id": record_id,
            "section_label": section["section_label"],
            "section_claim_class": "DATA",
            "section_provenance": {
                "source_reference": section_source["register_path"],
                "source_sha256": section_source["register_sha256"],
            },
            "scribe_label": scribe["scribe_label"],
            "scribe_claim_class": "DATA",
            "scribe_provenance": {
                "source_reference": scribe_source["source_url"] + "#IVTFF-$H",
                "source_sha256": scribe_source["source_sha256"],
            },
        })
    return {
        "schema_version": "1.0",
        "experiment_id": "EXP-2026-001",
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("section_assignments", type=Path)
    parser.add_argument("scribe_assignments", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.section_assignments, args.scribe_assignments)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
