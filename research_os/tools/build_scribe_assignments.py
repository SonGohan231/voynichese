#!/usr/bin/env python3
"""Build folio-to-scribe DATA assignments from frozen ZL3b IVTFF metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from record_scope import is_manuscript_content


HEADER_RE = re.compile(r"^<([^>]+)>\s+<![^>]*\$H=([1-5@])(?:\s|>)")
SIDE_RE = re.compile(r"\d+[rv]")
NUMBER_RE = re.compile(r"\d+")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def group_keys(records: list[dict[str, Any]]) -> dict[str, str]:
    parent: dict[int, int] = {}

    def find(value: int) -> int:
        parent.setdefault(value, value)
        if parent[value] != value:
            parent[value] = find(parent[value])
        return parent[value]

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[max(left_root, right_root)] = min(left_root, right_root)

    numbers_by_record: dict[str, tuple[int, ...]] = {}
    for record in records:
        folio_id = str(record.get("source", {}).get("folio_or_cover_id", ""))
        numbers = tuple(sorted({int(value) for value in NUMBER_RE.findall(folio_id)}))
        numbers_by_record[record["record_id"]] = numbers
        for number in numbers[1:]:
            union(numbers[0], number)

    return {
        record_id: (
            f"LEAF-{find(numbers[0]):04d}" if numbers else f"NONFOLIO-{record_id}"
        )
        for record_id, numbers in numbers_by_record.items()
    }


def parse_headers(text: str, mixed_pages: dict[str, Any]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for line in text.splitlines():
        match = HEADER_RE.match(line)
        if not match:
            continue
        page, hand = match.groups()
        if hand == "@":
            configured = mixed_pages.get(page, {}).get("hand_set")
            if not configured:
                raise ValueError(f"mixed IVTFF page {page} lacks frozen hand_set")
            result[page] = {str(value) for value in configured}
        else:
            result[page] = {hand}
    if not result:
        raise ValueError("no IVTFF page headers with $H metadata found")
    return result


def source_pages_for_folio(
    folio_id: str, headers: dict[str, set[str]], aliases: list[dict[str, Any]]
) -> list[str]:
    folio_tokens = set(SIDE_RE.findall(folio_id))
    for alias in aliases:
        required = set(alias.get("atlas_folio_tokens", []))
        source_page = alias.get("source_page")
        if required and required <= folio_tokens and source_page in headers:
            return [source_page]
    pages = []
    for token in sorted(folio_tokens):
        pattern = re.compile(rf"^f{re.escape(token)}(?:\d+)?$")
        pages.extend(page for page in headers if pattern.fullmatch(page))
    return sorted(set(pages))


def build(records_dir: Path, source_register: Path, ivtff_path: Path) -> dict[str, Any]:
    register = json.loads(source_register.read_text(encoding="utf-8"))
    if register.get("claim_class") != "DATA":
        raise ValueError("scribe source register must be DATA")
    expected_hash = register.get("source_sha256")
    actual_hash = sha256(ivtff_path)
    if not isinstance(expected_hash, str) or actual_hash != expected_hash:
        raise ValueError("IVTFF source SHA-256 does not match frozen scribe register")
    headers = parse_headers(
        ivtff_path.read_text(encoding="utf-8"),
        register.get("mixed_pages", {}),
    )

    records = []
    for path in sorted(records_dir.glob("*.annotation.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if is_manuscript_content(record):
            records.append(record)
    if not records:
        raise ValueError("no manuscript-content records found")

    groups = group_keys(records)
    per_record: dict[str, dict[str, Any]] = {}
    group_hands: dict[str, set[str]] = {}
    for record in records:
        folio_id = str(record.get("source", {}).get("folio_or_cover_id", ""))
        pages = source_pages_for_folio(folio_id, headers, register.get("aliases", []))
        hands = {hand for page in pages for hand in headers.get(page, set())}
        if not pages or not hands:
            raise ValueError(f"record {record['record_id']} has no complete IVTFF scribe mapping")
        group = groups[record["record_id"]]
        group_hands.setdefault(group, set()).update(hands)
        per_record[record["record_id"]] = {
            "record_id": record["record_id"],
            "folio_id": folio_id,
            "group_id": group,
            "record_hand_set": sorted(hands),
            "source_pages": pages,
        }

    label_counts: dict[str, int] = {}
    for hands in group_hands.values():
        label = (
            f"HAND_{next(iter(hands))}"
            if len(hands) == 1
            else "MIXED_" + "_".join(sorted(hands))
        )
        label_counts[label] = label_counts.get(label, 0) + 1

    assignments = []
    for record_id in sorted(per_record):
        item = per_record[record_id]
        hands = sorted(group_hands[item["group_id"]])
        item["group_hand_set"] = hands
        item["scribe_label"] = (
            f"HAND_{hands[0]}" if len(hands) == 1 else "MIXED_" + "_".join(hands)
        )
        assignments.append(item)

    digest_input = json.dumps(assignments, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": "1.0",
        "experiment_id": "EXP-2026-001",
        "claim_class": "DATA",
        "source": {
            "source_id": register["source_id"],
            "source_url": register["source_url"],
            "source_version": register["source_version"],
            "source_sha256": expected_hash,
            "register_path": str(source_register),
            "register_sha256": sha256(source_register),
        },
        "policy": {
            "unit": "connected manuscript leaf group",
            "aggregation": "union of source hand sets across every record in the leaf group",
            "mixed_is_not_new_hand": True,
        },
        "record_count": len(assignments),
        "group_count": len(group_hands),
        "group_label_counts": dict(sorted(label_counts.items())),
        "assignments_sha256": hashlib.sha256(digest_input.encode()).hexdigest(),
        "records": assignments,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("records_dir", type=Path)
    parser.add_argument("source_register", type=Path)
    parser.add_argument("ivtff_source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build(args.records_dir, args.source_register, args.ivtff_source)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
