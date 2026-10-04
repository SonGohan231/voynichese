#!/usr/bin/env python3
"""Custodian-only conversion from blinded handoff IDs to canonical atlas IDs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def unblind(
    handoff_packet_path: Path,
    custody_map_path: Path,
    submission_path: Path,
) -> dict[str, Any]:
    packet_raw = handoff_packet_path.read_bytes()
    packet = json.loads(packet_raw.decode("utf-8"))
    custody = json.loads(custody_map_path.read_text(encoding="utf-8"))
    submission = json.loads(submission_path.read_text(encoding="utf-8"))

    if custody.get("handoff_packet_sha256") != sha256_bytes(packet_raw):
        raise ValueError("handoff packet does not match custody map")
    if packet.get("record_count") != custody.get("record_count"):
        raise ValueError("handoff/custody record count mismatch")

    mapping = {}
    for item in custody.get("records", []):
        opaque = item.get("opaque_record_id")
        if not isinstance(opaque, str) or not opaque or opaque in mapping:
            raise ValueError("invalid or duplicate opaque ID in custody map")
        mapping[opaque] = item

    packet_records = {item.get("record_id"): item for item in packet.get("records", [])}
    if set(packet_records) != set(mapping):
        raise ValueError("handoff packet and custody map universes differ")
    for opaque, item in mapping.items():
        packet_item = packet_records[opaque]
        if packet_item.get("source_commitment_sha256") != item.get("source_commitment_sha256"):
            raise ValueError(f"source commitment mismatch in handoff packet:{opaque}")

    submission_records = submission.get("records")
    if not isinstance(submission_records, list) or len(submission_records) != len(mapping):
        raise ValueError("submission does not cover complete blinded universe")
    submitted = {}
    for record in submission_records:
        opaque = record.get("record_id")
        if not isinstance(opaque, str) or not opaque or opaque in submitted:
            raise ValueError("invalid or duplicate record ID in blinded submission")
        submitted[opaque] = record
    if set(submitted) != set(mapping):
        raise ValueError("submission blinded universe mismatch")

    canonical_records = []
    seen_original = set()
    for opaque in sorted(mapping):
        source = mapping[opaque]
        record = submitted[opaque]
        if record.get("source_commitment_sha256") != source.get("source_commitment_sha256"):
            raise ValueError(f"submission source commitment mismatch:{opaque}")
        original_id = source.get("original_record_id")
        source_sha = source.get("source_sha256")
        if not isinstance(original_id, str) or original_id in seen_original:
            raise ValueError("invalid or duplicate original record ID in custody map")
        if not isinstance(source_sha, str) or len(source_sha) != 64:
            raise ValueError("invalid source SHA-256 in custody map")
        seen_original.add(original_id)
        canonical_records.append({
            "record_id": original_id,
            "source_sha256": source_sha,
            "objects": record.get("objects", []),
            "occlusions": record.get("occlusions", []),
        })

    return {
        "schema_version": "1.0",
        "annotation_id": submission.get("annotation_id"),
        "annotator_id": submission.get("annotator_id"),
        "blindness": submission.get("blindness"),
        "records": sorted(canonical_records, key=lambda item: item["record_id"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("handoff_packet", type=Path)
    parser.add_argument("custody_map", type=Path)
    parser.add_argument("submission", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        result = unblind(args.handoff_packet, args.custody_map, args.submission)
        if args.output.exists():
            raise ValueError("refusing to overwrite existing canonical submission")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "UNBLIND_REFUSED", "error": str(error)}, indent=2))
        return 2
    print(json.dumps({
        "status": "CANONICAL_SUBMISSION_READY",
        "annotation_id": result["annotation_id"],
        "record_count": len(result["records"]),
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
