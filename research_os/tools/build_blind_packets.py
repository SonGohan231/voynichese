#!/usr/bin/env python3
"""Build deterministic, hypothesis-free source packets for independent annotators."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from record_scope import is_manuscript_content


FORBIDDEN_INPUTS = [
    "automated candidate records and overlays",
    "other annotator submissions",
    "model predictions",
    "hypothesis labels and prior pilot outcomes",
    "TRAIN, VALIDATION or HELD_OUT assignments",
    "section or scribe labels and lookup tables",
    "folio identity lookup beyond the pseudonymized handoff",
]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build_packet(records_dir: Path, protocol_path: Path, packet_id: str) -> dict[str, Any]:
    records = []
    for path in sorted(records_dir.glob("*.annotation.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        source = record["source"]
        if not is_manuscript_content(record):
            continue
        records.append(
            {
                "record_id": record["record_id"],
                "source_path": source["relative_path"],
                "source_sha256": source["sha256"],
                "width": source["image_file_grid_px"]["width"],
                "height": source["image_file_grid_px"]["height"],
            }
        )
    protocol_bytes = protocol_path.read_bytes()
    universe = json.dumps(
        [(record["record_id"], record["source_sha256"]) for record in records],
        separators=(",", ":"),
    ).encode()
    return {
        "schema_version": "1.0",
        "packet_id": packet_id,
        "purpose": "INDEPENDENT_BLIND_ANNOTATION_EXP_2026_001",
        "protocol_path": str(protocol_path.as_posix()),
        "protocol_sha256": sha256_bytes(protocol_bytes),
        "record_universe_sha256": sha256_bytes(universe),
        "record_count": len(records),
        "forbidden_inputs": FORBIDDEN_INPUTS,
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("records_dir", type=Path)
    parser.add_argument("protocol", type=Path)
    parser.add_argument("packet_id")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    packet = build_packet(args.records_dir, args.protocol, args.packet_id)
    if not packet["records"]:
        raise SystemExit("no manuscript-content records found")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
