Failed to connect to bus: Operation not permitted
#!/usr/bin/env python3
"""Fail-closed readiness audit and grouped split planner for EXP-2026-001."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from validate_adjudication import validate_adjudication
from verify_custodian_receipt import verify_receipt


SPLITS = (("TRAIN", 0.60), ("VALIDATION", 0.20), ("HELD_OUT", 0.20))
MINIMUM_ELIGIBLE_GROUPS = 15


def load_records(records_dir: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(records_dir.glob("*.annotation.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        record["_path"] = str(path)
        records.append(record)
    return records


def folio_numbers(folio_id: str) -> tuple[int, ...]:
    return tuple(sorted({int(value) for value in re.findall(r"\d+", folio_id)}))


def group_keys(records: Iterable[dict[str, Any]]) -> dict[str, str]:
    """Join records sharing any manuscript leaf, including compound foldouts."""
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

    record_numbers: dict[str, tuple[int, ...]] = {}
    for record in records:
        source = record.get("source", {})
        numbers = folio_numbers(str(source.get("folio_or_cover_id", "")))
        record_numbers[record["record_id"]] = numbers
        for number in numbers[1:]:
            union(numbers[0], number)

    result = {}
    for record_id, numbers in record_numbers.items():
        result[record_id] = (
            f"LEAF-{find(numbers[0]):04d}" if numbers else f"NONFOLIO-{record_id}"
        )
    return result


def audit_record(record: dict[str, Any], adjudicated: dict[str, Any] | None = None) -> dict[str, Any]:
    source = record.get("source", {})
    provenance = source.get("provenance", {})
    page_regions = record.get("page_inventory", {}).get("regions", [])
    objects = record.get("illustration_inventory", {}).get("objects", [])
    text_regions = record.get("text_geometry", {}).get("regions", [])
    relations = record.get("local_relations", [])
    review_status = record.get("quality_control", {}).get("review_status")
    checks = {
        "folio_role": source.get("logical_role") == "FOLIO",
        "native_source_verified": source.get("native_scan_grid_status") == "VERIFIED_NATIVE",
        "provenance_verified": provenance.get("verification_status") == "VERIFIED",
        "sha256_present": bool(re.fullmatch(r"[0-9a-f]{64}", str(source.get("sha256", "")))),
        "visual_units_present": bool(adjudicated.get("objects")) if adjudicated else bool(page_regions or objects or text_regions),
        "local_relations_present": isinstance(adjudicated.get("occlusions"), list) if adjudicated else bool(relations),
        "independent_review_complete": bool(adjudicated) if adjudicated else review_status not in (None, "NOT_REVIEWED"),
        "adjudicated_source_matches": (
            adjudicated.get("source_sha256") == source.get("sha256") if adjudicated else True
        ),
    }
    return {
        "record_id": record.get("record_id"),
        "source_file_id": source.get("source_file_id"),
        "folio_id": source.get("folio_or_cover_id"),
        "checks": checks,
        "eligible": all(checks.values()),
        "counts": {
            "page_regions": len(page_regions),
            "illustration_objects": len(objects),
            "text_regions": len(text_regions),
            "local_relations": len(relations),
        },
    }


def build_readiness_report(
    records: list[dict[str, Any]],
    adjudication: dict[str, Any] | None = None,
    adjudication_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    adjudicated_records = {
        item["record_id"]: item for item in (adjudication or {}).get("records", [])
    }
    audited = [audit_record(record, adjudicated_records.get(record["record_id"])) for record in records]
    failures = Counter(
        name for item in audited for name, passed in item["checks"].items() if not passed
    )
    eligible = [item for item in audited if item["eligible"]]
    groups = group_keys(records)
    eligible_groups = {groups[item["record_id"]] for item in eligible}
    gates = {
        "records_present": bool(audited),
        "all_sources_verified": all(
            item["checks"]["native_source_verified"]
            and item["checks"]["provenance_verified"]
            and item["checks"]["sha256_present"]
            for item in audited
        ),
        "minimum_eligible_groups": len(eligible_groups) >= MINIMUM_ELIGIBLE_GROUPS,
        "all_eligible_units_reviewed": bool(eligible)
        and all(item["checks"]["independent_review_complete"] for item in eligible),
    }
    if adjudication is not None:
        gates["adjudication_revalidated"] = bool(adjudication_validation) and (
            adjudication_validation.get("status") == "ADJUDICATION_VALIDATED"
            and adjudication_validation.get("structurally_valid_for_readiness_chain") is True
        )
        gates["adjudication_covers_all_folios"] = {
            record["record_id"]
            for record in records
            if record.get("source", {}).get("logical_role") == "FOLIO"
        } == set(adjudicated_records)
    ready = all(gates.values())
    return {
        "schema_version": "1.0",
        "experiment_id": "EXP-2026-001",
        "status": "READY_FOR_SPLIT" if ready else "INCONCLUSIVE_NOT_RUN",
        "held_out_exposed": False,
        "adjudication_packet_sha256": (
            adjudication_validation.get("packet_sha256") if adjudication_validation else None
        ),
        "summary": {
            "record_count": len(audited),
            "eligible_record_count": len(eligible),
            "eligible_group_count": len(eligible_groups),
            "minimum_eligible_groups": MINIMUM_ELIGIBLE_GROUPS,
        },
        "gates": gates,
        "failure_counts": dict(sorted(failures.items())),
        "eligible_record_ids": [item["record_id"] for item in eligible],
        "ineligible_records": {
            item["record_id"]: [name for name, passed in item["checks"].items() if not passed]
            for item in audited
            if not item["eligible"]
        },
    }


def bind_adjudication_evidence_chain(
    validation: dict[str, Any],
    receipt_verification: dict[str, Any],
    receipt_bytes: bytes,
    packet: dict[str, Any],
) -> dict[str, Any]:
    receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()
    if (
        receipt_verification.get("status") == "FREEZE_RECEIPT_VERIFIED"
        and receipt_verification.get("ready_for_adjudication") is True
        and packet.get("receipt_sha256") == receipt_sha256
        and packet.get("freeze_manifest_sha256") == receipt_verification.get("manifest_sha256")
    ):
        return validation
    return {
        **validation,
        "status": "ADJUDICATION_REJECTED",
        "structurally_valid_for_readiness_chain": False,
        "errors": sorted(set(validation.get("errors", [])) | {"adjudication_evidence_chain_invalid"}),
    }


def deterministic_group_split(
    records: list[dict[str, Any]], report: dict[str, Any], seed: str
) -> dict[str, Any]:
    if report["status"] != "READY_FOR_SPLIT":
        failed = [name for name, passed in report["gates"].items() if not passed]
        raise ValueError("split refused; readiness gates failed: " + ", ".join(failed))
    keys = group_keys(records)
    by_group: dict[str, list[str]] = defaultdict(list)
    eligible = set(report["eligible_record_ids"])
    for record in records:
        if record["record_id"] in eligible:
            by_group[keys[record["record_id"]]].append(record["record_id"])
    groups = sorted(by_group)
    random.Random(seed).shuffle(groups)
    total = len(groups)
    train_end = round(total * SPLITS[0][1])
    validation_end = train_end + round(total * SPLITS[1][1])
    assigned = {
        "TRAIN": groups[:train_end],
        "VALIDATION": groups[train_end:validation_end],
        "HELD_OUT": groups[validation_end:],
    }
    assignments = {
        split: sorted(record_id for group in split_groups for record_id in by_group[group])
        for split, split_groups in assigned.items()
    }
    digest_input = json.dumps(assignments, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": "1.0",
        "experiment_id": "EXP-2026-001",
        "seed": seed,
        "grouping_policy": "connected manuscript leaf numbers; compound/foldout records union groups",
        "assignments_sha256": hashlib.sha256(digest_input.encode()).hexdigest(),
        "group_counts": {name: len(values) for name, values in assigned.items()},
        "assignments": assignments,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("records_dir", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--split", type=Path)
    parser.add_argument("--seed")
    parser.add_argument("--adjudication-packet", type=Path)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--freeze-directory", type=Path)
    parser.add_argument("--custodian-receipt", type=Path)
    parser.add_argument("--receipt-signature", type=Path)
    parser.add_argument("--allowed-signers", type=Path)
    parser.add_argument("--custodian-identity")
    args = parser.parse_args()
    if args.split:
        parser.error(
            "cleartext --split materialization is disabled because it exposes HELD_OUT; "
            "use the sealed custodian split workflow"
        )
    records = load_records(args.records_dir)
    if bool(args.adjudication_packet) != bool(args.adjudication):
        parser.error("--adjudication-packet and --adjudication must be provided together")
    adjudication = validation = None
    if args.adjudication_packet:
        chain_args = (
            args.freeze_directory, args.custodian_receipt, args.receipt_signature,
            args.allowed_signers, args.custodian_identity,
        )
        if any(value is None for value in chain_args):
            parser.error(
                "adjudication readiness also requires --freeze-directory, --custodian-receipt, "
                "--receipt-signature, --allowed-signers, and --custodian-identity"
            )
        receipt_verification = verify_receipt(
            args.freeze_directory, args.custodian_receipt, args.receipt_signature,
            args.allowed_signers, args.custodian_identity,
        )
        packet_bytes = args.adjudication_packet.read_bytes()
        packet = json.loads(packet_bytes.decode("utf-8"))
        adjudication = json.loads(args.adjudication.read_text(encoding="utf-8"))
        validation = validate_adjudication(packet_bytes, packet, adjudication)
        validation = bind_adjudication_evidence_chain(
            validation, receipt_verification, args.custodian_receipt.read_bytes(), packet
        )
    report = build_readiness_report(records, adjudication, validation)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"] == "READY_FOR_SPLIT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
