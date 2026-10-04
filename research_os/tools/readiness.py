#!/usr/bin/env python3
"""Fail-closed readiness audit and grouped split planner for EXP-2026-001."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import stat
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from validate_adjudication import validate_adjudication
from verify_custodian_receipt import verify_receipt
from sealed_split import seal_split


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
    records: list[dict[str, Any]], report: dict[str, Any], seed: str,
    strata_manifest: dict[str, Any] | None = None,
    adjudication: dict[str, Any] | None = None,
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
    group_strata = compile_group_strata(records, by_group, strata_manifest, adjudication)
    strata: dict[str, list[str]] = defaultdict(list)
    for group, stratum in group_strata.items():
        strata[stratum].append(group)
    assigned = {name: [] for name, _ in SPLITS}
    for stratum in sorted(strata):
        groups = sorted(strata[stratum])
        random.Random(f"{seed}:{stratum}").shuffle(groups)
        counts = proportional_counts(len(groups))
        offset = 0
        for (split, _), count in zip(SPLITS, counts):
            assigned[split].extend(groups[offset:offset + count])
            offset += count
    rebalance_global_counts(assigned, group_strata)
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
        "stratification_policy": (
            "custodian-provided section with provenance; deterministic complexity tertiles from "
            "adjudicated object plus occlusion counts"
        ),
        "stratum_group_counts": dict(sorted(Counter(group_strata.values()).items())),
        "assignments_sha256": hashlib.sha256(digest_input.encode()).hexdigest(),
        "group_counts": {name: len(values) for name, values in assigned.items()},
        "assignments": assignments,
    }


def proportional_counts(total: int) -> list[int]:
    """Largest-remainder 60/20/20 allocation, deterministic on declared split order."""
    raw = [total * fraction for _, fraction in SPLITS]
    counts = [int(value) for value in raw]
    for index in sorted(range(len(raw)), key=lambda i: (-(raw[i] - counts[i]), i))[:total - sum(counts)]:
        counts[index] += 1
    return counts


def rebalance_global_counts(
    assigned: dict[str, list[str]], group_strata: dict[str, str]
) -> None:
    """Meet exact global ratios while minimizing squared within-stratum deviation."""
    names = [name for name, _ in SPLITS]
    targets = dict(zip(names, proportional_counts(len(group_strata))))
    stratum_totals = Counter(group_strata.values())
    while any(len(assigned[name]) != targets[name] for name in names):
        donor = next(name for name in names if len(assigned[name]) > targets[name])
        receiver = next(name for name in names if len(assigned[name]) < targets[name])
        before = Counter((group_strata[group], split) for split in names for group in assigned[split])

        def penalty(group: str) -> tuple[float, str]:
            stratum = group_strata[group]
            total = stratum_totals[stratum]
            expected = {name: total * fraction for name, fraction in SPLITS}
            current = {name: before[(stratum, name)] for name in names}
            old = sum((current[name] - expected[name]) ** 2 for name in names)
            current[donor] -= 1
            current[receiver] += 1
            new = sum((current[name] - expected[name]) ** 2 for name in names)
            return new - old, group

        selected = min(assigned[donor], key=penalty)
        assigned[donor].remove(selected)
        assigned[receiver].append(selected)


def compile_group_strata(
    records: list[dict[str, Any]],
    by_group: dict[str, list[str]],
    manifest: dict[str, Any] | None,
    adjudication: dict[str, Any] | None,
) -> dict[str, str]:
    """Validate external section provenance and derive non-color complexity bins."""
    if manifest is None or adjudication is None:
        raise ValueError("split refused; section strata manifest and adjudication are required")
    if manifest.get("schema_version") != "1.0" or manifest.get("experiment_id") != "EXP-2026-001":
        raise ValueError("split refused; invalid strata manifest identity")
    entries = manifest.get("records")
    if not isinstance(entries, list):
        raise ValueError("split refused; strata manifest records must be a list")
    by_record = {}
    for entry in entries:
        record_id = entry.get("record_id")
        provenance = entry.get("provenance", {})
        if (
            not record_id or record_id in by_record
            or not isinstance(entry.get("section_label"), str) or not entry["section_label"].strip()
            or entry.get("claim_class") not in {"FACT", "DATA"}
            or not isinstance(provenance.get("source_reference"), str)
            or not provenance["source_reference"].strip()
            or not re.fullmatch(r"[0-9a-f]{64}", str(provenance.get("source_sha256", "")))
        ):
            raise ValueError("split refused; invalid or duplicate section-strata entry")
        by_record[record_id] = entry
    eligible_ids = {record_id for values in by_group.values() for record_id in values}
    if set(by_record) != eligible_ids:
        raise ValueError("split refused; section strata must cover exactly all eligible records")
    adjudicated = {item.get("record_id"): item for item in adjudication.get("records", [])}
    if not eligible_ids <= set(adjudicated):
        raise ValueError("split refused; adjudication does not cover all stratified records")
    group_rows = []
    for group, record_ids in sorted(by_group.items()):
        sections = {by_record[record_id]["section_label"].strip() for record_id in record_ids}
        if len(sections) != 1:
            raise ValueError(f"split refused; connected group {group} crosses section labels")
        complexity = sum(
            len(adjudicated[record_id].get("objects", []))
            + len(adjudicated[record_id].get("occlusions", []))
            for record_id in record_ids
        )
        group_rows.append((group, next(iter(sections)), complexity))
    ranked = sorted(group_rows, key=lambda row: (row[2], row[0]))
    bins = {}
    for rank, (group, _, _) in enumerate(ranked):
        bins[group] = ("LOW", "MEDIUM", "HIGH")[min(2, (3 * rank) // len(ranked))]
    return {group: f"{section}::{bins[group]}" for group, section, _ in group_rows}


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
    parser.add_argument("--sealed-split-directory", type=Path)
    parser.add_argument("--custodian-certificate", type=Path)
    parser.add_argument("--seed-file", type=Path)
    parser.add_argument("--strata-manifest", type=Path)
    args = parser.parse_args()
    if args.split:
        parser.error(
            "cleartext --split materialization is disabled because it exposes HELD_OUT; "
            "use the sealed custodian split workflow"
        )
    if args.seed:
        parser.error("command-line --seed is disabled; use a protected --seed-file with sealed output")
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
    sealed_args = (
        args.sealed_split_directory, args.custodian_certificate, args.seed_file,
    )
    if any(value is not None for value in sealed_args):
        if any(value is None for value in sealed_args):
            parser.error(
                "sealed split requires --sealed-split-directory, --custodian-certificate, and --seed-file"
            )
        if report["status"] != "READY_FOR_SPLIT" or adjudication is None:
            parser.error("sealed split refused until the complete evidence chain is READY_FOR_SPLIT")
        if args.seed_file.is_symlink() or not args.seed_file.is_file():
            parser.error("seed file must be a regular non-symlink file")
        if args.seed_file.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            parser.error("seed file permissions must not grant group or other access")
        seed_bytes = args.seed_file.read_bytes()
        if args.strata_manifest is None:
            parser.error("sealed split requires --strata-manifest with section provenance")
        try:
            strata_manifest = json.loads(args.strata_manifest.read_text(encoding="utf-8"))
            split = deterministic_group_split(
                records, report, seed_bytes.hex(), strata_manifest, adjudication
            )
            sealed_manifest = seal_split(
                split, adjudication, seed_bytes,
                args.custodian_certificate, args.sealed_split_directory,
            )
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
            parser.error(f"sealed split failed: {error}")
        report["sealed_split"] = {
            "status": sealed_manifest["status"],
            "manifest": str(args.sealed_split_directory / "sealed-split-manifest.json"),
            "seed_commitment_sha256": sealed_manifest["seed_commitment_sha256"],
            "held_out_exposed": False,
        }
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"] == "READY_FOR_SPLIT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
