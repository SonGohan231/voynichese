#!/usr/bin/env python3
"""Freeze two independent submissions before exposing agreement metrics."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from annotation_gate import agreement_report, load_atlas, validate_submission
from verify_acceptance_slot import verify_slot


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def durable_write(path: Path, data: bytes) -> None:
    """Create one artifact exclusively and flush its bytes before returning."""
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def load_json_bytes(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    return raw, json.loads(raw.decode("utf-8"))


def freeze_pair(
    records_dir: Path,
    left_path: Path,
    right_path: Path,
    packet_a_path: Path,
    packet_b_path: Path,
    output_dir: Path,
    acceptance_slot: dict[str, Any] | None = None,
    acceptance_evidence: dict[str, bytes] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    atlas = load_atlas(records_dir)
    left_raw, left = load_json_bytes(left_path)
    right_raw, right = load_json_bytes(right_path)
    packet_a_raw, packet_a = load_json_bytes(packet_a_path)
    packet_b_raw, packet_b = load_json_bytes(packet_b_path)

    errors = {
        "left": validate_submission(left, atlas),
        "right": validate_submission(right, atlas),
        "pair": [],
        "packets": [],
    }
    left_records = {record.get("record_id") for record in left.get("records", [])}
    right_records = {record.get("record_id") for record in right.get("records", [])}
    if left.get("annotator_id") == right.get("annotator_id"):
        errors["pair"].append("annotator_ids_not_distinct")
    if left_records != set(atlas) or right_records != set(atlas):
        errors["pair"].append("record_universe_incomplete")
    packet_keys = ("schema_version", "record_count", "record_universe_sha256", "protocol_sha256")
    for key in packet_keys:
        if packet_a.get(key) != packet_b.get(key):
            errors["packets"].append(f"packet_mismatch:{key}")
    if packet_a.get("record_count") != len(atlas):
        errors["packets"].append("packet_atlas_count_mismatch")
    packet_records = {record.get("record_id"): record.get("source_sha256") for record in packet_a.get("records", [])}
    if packet_records != atlas:
        errors["packets"].append("packet_atlas_universe_mismatch")
    if acceptance_slot:
        expected_ids = acceptance_slot.get("annotator_id_sha256", {})
        actual_ids = {
            "A": sha256_bytes(str(left.get("annotator_id", "")).encode("utf-8")),
            "B": sha256_bytes(str(right.get("annotator_id", "")).encode("utf-8")),
        }
        if expected_ids != actual_ids:
            errors["pair"].append("annotator_ids_do_not_match_signed_slot")
        expected_packets = acceptance_slot.get("packet_sha256", {})
        actual_packets = {"A": sha256_bytes(packet_a_raw), "B": sha256_bytes(packet_b_raw)}
        if expected_packets != actual_packets:
            errors["packets"].append("packet_bytes_do_not_match_signed_slot")
        if acceptance_slot.get("protocol_sha256") != packet_a.get("protocol_sha256"):
            errors["packets"].append("protocol_does_not_match_signed_slot")
        if acceptance_slot.get("record_universe_sha256") != packet_a.get("record_universe_sha256"):
            errors["packets"].append("record_universe_does_not_match_signed_slot")
    if any(errors.values()):
        raise ValueError(json.dumps(errors, sort_keys=True))

    report = agreement_report(left, right, atlas)
    report_raw = (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    manifest = {
        "schema_version": "1.0",
        "freeze_status": (
            "LOCAL_FREEZE_BOUND_TO_SIGNED_ACCEPTANCE_SLOT"
            if acceptance_slot else "LOCAL_DIAGNOSTIC_FREEZE_NO_SLOT"
        ),
        "created_at_utc": created_at,
        "protocol_sha256": packet_a["protocol_sha256"],
        "record_universe_sha256": packet_a["record_universe_sha256"],
        "record_count": len(atlas),
        "packet_a": {"path": "packet-a.json", "packet_id": packet_a["packet_id"], "sha256": sha256_bytes(packet_a_raw)},
        "packet_b": {"path": "packet-b.json", "packet_id": packet_b["packet_id"], "sha256": sha256_bytes(packet_b_raw)},
        "annotation_a": {
            "path": "annotation-a.json",
            "annotation_id": left["annotation_id"],
            "annotator_id": left["annotator_id"],
            "sha256": sha256_bytes(left_raw),
        },
        "annotation_b": {
            "path": "annotation-b.json",
            "annotation_id": right["annotation_id"],
            "annotator_id": right["annotator_id"],
            "sha256": sha256_bytes(right_raw),
        },
        "agreement_report": {
            "path": "agreement-report.json",
            "status": report["status"],
            "sha256": sha256_bytes(report_raw),
        },
        "acceptance_scope": "SIGNED_SINGLE_SLOT_LOCAL_COMMIT" if acceptance_slot else "DIAGNOSTIC_ONLY",
        "custodian_receipt_required": True,
        "promotes_to_ground_truth": False,
        "unlocks_held_out": False,
    }
    if acceptance_slot:
        manifest["acceptance_slot"] = acceptance_slot
        manifest["acceptance_evidence"] = {
            name: {"path": name, "sha256": sha256_bytes(data)}
            for name, data in sorted((acceptance_evidence or {}).items())
        }

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        # mkdir is the no-replace publication boundary: exactly one writer can
        # reserve a run path. A crash leaves an incomplete, non-reusable audit trail.
        output_dir.mkdir()
    except FileExistsError as error:
        raise ValueError(f"refusing_to_overwrite_existing_freeze:{output_dir}") from error
    try:
        durable_write(output_dir / "annotation-a.json", left_raw)
        durable_write(output_dir / "annotation-b.json", right_raw)
        durable_write(output_dir / "packet-a.json", packet_a_raw)
        durable_write(output_dir / "packet-b.json", packet_b_raw)
        for name, data in sorted((acceptance_evidence or {}).items()):
            if Path(name).name != name:
                raise ValueError(f"unsafe_acceptance_evidence_name:{name}")
            durable_write(output_dir / name, data)
        durable_write(output_dir / "agreement-report.json", report_raw)
        manifest_raw = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        durable_write(output_dir / "freeze-manifest.json", manifest_raw)
        commit = {
            "schema_version": "1.0",
            "state": "LOCAL_FREEZE_COMMITTED",
            "manifest_sha256": sha256_bytes(manifest_raw),
            "custodian_receipt_required": True,
        }
        durable_write(
            output_dir / "COMMIT.json",
            (json.dumps(commit, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
        directory_fd = os.open(output_dir, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        for artifact in output_dir.iterdir():
            artifact.chmod(0o444)
        output_dir.chmod(0o555)
    except Exception:
        # Never remove or reuse a partial run: its existence is evidence of an attempt.
        raise
    return manifest, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("records_dir", type=Path)
    parser.add_argument("annotation_a", type=Path)
    parser.add_argument("annotation_b", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--slot", type=Path, required=True)
    parser.add_argument("--slot-signature", type=Path, required=True)
    parser.add_argument("--allowed-signers", type=Path, required=True)
    parser.add_argument("--custodian-identity", required=True)
    parser.add_argument(
        "--packet-a", type=Path,
        default=Path("research_os/annotation/packets/annotator-a.packet.json"),
    )
    parser.add_argument(
        "--packet-b", type=Path,
        default=Path("research_os/annotation/packets/annotator-b.packet.json"),
    )
    parser.add_argument("--handoff-packet-a", type=Path, required=True)
    parser.add_argument("--handoff-packet-b", type=Path, required=True)
    parser.add_argument("--custody-map-a", type=Path, required=True)
    parser.add_argument("--custody-map-b", type=Path, required=True)
    args = parser.parse_args()
    try:
        slot_result = verify_slot(
            args.slot, args.slot_signature, args.allowed_signers, args.custodian_identity
        )
        if slot_result["status"] != "ACCEPTANCE_SLOT_VERIFIED":
            raise ValueError(json.dumps(slot_result, sort_keys=True))
        slot = slot_result["slot"]
        if args.output_dir.as_posix() != slot["output_path"]:
            raise ValueError("output_path_does_not_match_signed_slot")
        packet_a_raw, packet_a = load_json_bytes(args.packet_a)
        packet_b_raw, packet_b = load_json_bytes(args.packet_b)
        for role, packet, raw in (("A", packet_a, packet_a_raw), ("B", packet_b, packet_b_raw)):
            signed_packet = slot["packets"][role]
            if packet.get("packet_id") != signed_packet["packet_id"] or sha256_bytes(raw) != signed_packet["sha256"]:
                raise ValueError(f"packet_does_not_match_signed_slot:{role}")
        if (
            packet_a.get("protocol_sha256") != slot["protocol_sha256"]
            or packet_a.get("record_universe_sha256") != slot["record_universe_sha256"]
        ):
            raise ValueError("protocol_or_universe_does_not_match_signed_slot")

        handoff_evidence = {}
        for role, handoff_path, custody_path, canonical_raw in (
            ("A", args.handoff_packet_a, args.custody_map_a, packet_a_raw),
            ("B", args.handoff_packet_b, args.custody_map_b, packet_b_raw),
        ):
            handoff_raw, handoff = load_json_bytes(handoff_path)
            custody_raw, custody = load_json_bytes(custody_path)
            signed = slot["handoff_bindings"][role]
            if handoff.get("packet_id") != signed["packet_id"]:
                raise ValueError(f"handoff_packet_id_does_not_match_signed_slot:{role}")
            if sha256_bytes(handoff_raw) != signed["packet_sha256"]:
                raise ValueError(f"handoff_packet_bytes_do_not_match_signed_slot:{role}")
            if sha256_bytes(custody_raw) != signed["custody_map_sha256"]:
                raise ValueError(f"custody_map_bytes_do_not_match_signed_slot:{role}")
            if custody.get("seed_commitment_sha256") != signed["seed_commitment_sha256"]:
                raise ValueError(f"seed_commitment_does_not_match_signed_slot:{role}")
            if custody.get("handoff_packet_sha256") != sha256_bytes(handoff_raw):
                raise ValueError(f"custody_map_handoff_binding_invalid:{role}")
            if custody.get("canonical_packet_sha256") != sha256_bytes(canonical_raw):
                raise ValueError(f"custody_map_canonical_packet_binding_invalid:{role}")
            if handoff.get("canonical_packet_sha256") != sha256_bytes(canonical_raw):
                raise ValueError(f"handoff_canonical_packet_binding_invalid:{role}")
            handoff_evidence[f"handoff-packet-{role.lower()}.json"] = handoff_raw
        slot_binding = {
            "slot_id": slot["acceptance_slot_id"],
            "slot_sha256": sha256_bytes(args.slot.read_bytes()),
            "custodian_identity": args.custodian_identity,
            "signature_namespace": slot_result["signature_namespace"],
            "signature_valid": True,
            "annotator_id_sha256": {
                item["role"]: item["annotator_id_sha256"]
                for item in slot["annotator_bindings"]
            },
            "packet_sha256": {
                role: slot["packets"][role]["sha256"] for role in ("A", "B")
            },
            "protocol_sha256": slot["protocol_sha256"],
            "record_universe_sha256": slot["record_universe_sha256"],
            "handoff_bindings": slot["handoff_bindings"],
        }
        acceptance_evidence = {
            "acceptance-slot.json": args.slot.read_bytes(),
            "acceptance-slot.json.sig": args.slot_signature.read_bytes(),
            "allowed_signers": args.allowed_signers.read_bytes(),
            **handoff_evidence,
        }
        manifest, report = freeze_pair(
            args.records_dir, args.annotation_a, args.annotation_b,
            args.packet_a, args.packet_b, args.output_dir, slot_binding, acceptance_evidence,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "FREEZE_REFUSED", "error": str(error)}, indent=2))
        return 2
    print(json.dumps({"manifest": manifest, "gate_status": report["status"]}, indent=2))
    return 0 if report["status"] == "READY_FOR_ADJUDICATION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
