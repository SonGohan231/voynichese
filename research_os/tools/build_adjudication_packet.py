Failed to connect to bus: Operation not permitted
#!/usr/bin/env python3
"""Build an anonymized adjudication packet only after a verified receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from annotation_gate import match_objects
from verify_custodian_receipt import verify_receipt


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def anonymize_record(record: dict[str, Any], prefix: str) -> tuple[dict[str, Any], dict[str, str]]:
    mapping = {
        item["local_id"]: f"{prefix}-O{index:04d}"
        for index, item in enumerate(record["objects"], 1)
    }
    objects = [
        {**item, "local_id": mapping[item["local_id"]]}
        for item in record["objects"]
    ]
    occlusions = [
        {
            **item,
            "source_id": mapping[item["source_id"]],
            "target_id": mapping[item["target_id"]],
        }
        for item in record["occlusions"]
    ]
    return {**record, "objects": objects, "occlusions": occlusions}, mapping


def build_packet(
    left: dict[str, Any],
    right: dict[str, Any],
    packet_records: list[dict[str, Any]],
    receipt_sha256: str,
    manifest_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    swap = int(receipt_sha256[:2], 16) % 2 == 1
    side_1, side_2 = (right, left) if swap else (left, right)
    side_1_role, side_2_role = ("B", "A") if swap else ("A", "B")
    records_1 = {item["record_id"]: item for item in side_1["records"]}
    records_2 = {item["record_id"]: item for item in side_2["records"]}
    sources = {item["record_id"]: item for item in packet_records}
    output_records = []
    custody_object_maps = {}
    for record_id in sorted(records_1):
        first, map_1 = anonymize_record(records_1[record_id], "S1")
        second, map_2 = anonymize_record(records_2[record_id], "S2")
        custody_object_maps[record_id] = {"SIDE_1": map_1, "SIDE_2": map_2}
        matches = match_objects(first["objects"], second["objects"])
        matched_1 = {i for i, _, _ in matches}
        matched_2 = {j for _, j, _ in matches}
        aligned = []
        for left_index, right_index, iou in matches:
            object_1 = first["objects"][left_index]
            object_2 = second["objects"][right_index]
            aligned.append({
                "side_1_id": object_1["local_id"],
                "side_2_id": object_2["local_id"],
                "class": object_1["class"],
                "iou": round(iou, 8),
                "bbox_exact": object_1["bbox"] == object_2["bbox"],
                "ports_exact": set(object_1["ports"]) == set(object_2["ports"]),
            })
        unmatched_1 = [item["local_id"] for index, item in enumerate(first["objects"]) if index not in matched_1]
        unmatched_2 = [item["local_id"] for index, item in enumerate(second["objects"]) if index not in matched_2]
        output_records.append({
            "record_id": record_id,
            "source_path": sources[record_id]["source_path"],
            "source_sha256": sources[record_id]["source_sha256"],
            "side_1": {"objects": first["objects"], "occlusions": first["occlusions"]},
            "side_2": {"objects": second["objects"], "occlusions": second["occlusions"]},
            "geometric_alignment": aligned,
            "unmatched": {"side_1": unmatched_1, "side_2": unmatched_2},
            "requires_review": bool(
                unmatched_1 or unmatched_2
                or any(not item["bbox_exact"] or not item["ports_exact"] for item in aligned)
                or first["occlusions"] != second["occlusions"]
            ),
        })
    packet = {
        "schema_version": "1.0",
        "status": "READY_FOR_INDEPENDENT_ADJUDICATION",
        "purpose": "Resolve two frozen human annotations without model or split information",
        "receipt_sha256": receipt_sha256,
        "freeze_manifest_sha256": manifest_sha256,
        "record_count": len(output_records),
        "forbidden_inputs": [
            "annotator identities", "automated candidates", "model predictions",
            "hypothesis labels", "TRAIN/VALIDATION/HELD-OUT assignments",
        ],
        "records": output_records,
        "promotes_to_ground_truth": False,
        "unlocks_held_out": False,
    }
    custody = {
        "schema_version": "1.0",
        "status": "OPERATOR_CUSTODY_DO_NOT_GIVE_TO_ADJUDICATOR",
        "receipt_sha256": receipt_sha256,
        "side_mapping": {"SIDE_1": side_1_role, "SIDE_2": side_2_role},
        "source_files": {"A": "annotation-a.json", "B": "annotation-b.json"},
        "object_id_mapping": custody_object_maps,
    }
    return packet, custody


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freeze_directory", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("receipt_signature", type=Path)
    parser.add_argument("allowed_signers", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--identity", required=True)
    args = parser.parse_args()
    try:
        verified = verify_receipt(
            args.freeze_directory, args.receipt, args.receipt_signature,
            args.allowed_signers, args.identity,
        )
        if verified["status"] != "FREEZE_RECEIPT_VERIFIED" or not verified["ready_for_adjudication"]:
            raise ValueError("verified_ready_receipt_required")
        receipt_raw = args.receipt.read_bytes()
        packet_a = load_json(args.freeze_directory / "packet-a.json")
        manifest_sha256 = sha256_bytes(
            (args.freeze_directory / "freeze-manifest.json").read_bytes()
        )
        packet, custody = build_packet(
            load_json(args.freeze_directory / "annotation-a.json"),
            load_json(args.freeze_directory / "annotation-b.json"),
            packet_a["records"], sha256_bytes(receipt_raw),
            manifest_sha256,
        )
        rendered = (json.dumps(packet, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        custody["adjudication_packet_sha256"] = sha256_bytes(rendered)
        custody["created_at_utc"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        args.output_directory.mkdir(parents=True, exist_ok=False)
        (args.output_directory / "adjudication-packet.json").write_bytes(rendered)
        (args.output_directory / "operator-custody.json").write_text(
            json.dumps(custody, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        for path in args.output_directory.iterdir():
            path.chmod(0o444)
        args.output_directory.chmod(0o555)
        directory_fd = os.open(args.output_directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "ADJUDICATION_PACKET_REFUSED", "error": str(error)}, indent=2))
        return 2
    print(json.dumps({
        "status": packet["status"], "record_count": packet["record_count"],
        "packet_sha256": custody["adjudication_packet_sha256"],
        "give_to_adjudicator": str(args.output_directory / "adjudication-packet.json"),
        "withhold_from_adjudicator": str(args.output_directory / "operator-custody.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
