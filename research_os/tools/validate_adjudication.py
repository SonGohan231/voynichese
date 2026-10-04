Failed to connect to bus: Operation not permitted
#!/usr/bin/env python3
"""Validate a completed adjudication against its exact blinded packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


CLASSES = {"ILLUSTRATION_OBJECT", "ILLUSTRATION_FIELD", "TEXT_FIELD", "DIAGRAM"}
PORTS = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"}
RELATIONS = {"IN_FRONT_OF", "BEHIND", "AMBIGUOUS"}
OBJECT_RATIONALES = {"AGREE", "SELECT_SIDE_1", "SELECT_SIDE_2", "MERGED", "INDEPENDENT_REDRAW"}
RELATION_RATIONALES = {"AGREE", "SELECT_SIDE_1", "SELECT_SIDE_2", "INDEPENDENT_DECISION"}
BLINDNESS_KEYS = {
    "annotator_identities_unseen", "automated_candidates_unseen",
    "model_predictions_unseen", "hypothesis_labels_unseen", "split_assignment_unseen",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_adjudication(
    packet_bytes: bytes, packet: dict[str, Any], submission: dict[str, Any]
) -> dict[str, Any]:
    errors = []
    if packet.get("status") != "READY_FOR_INDEPENDENT_ADJUDICATION":
        errors.append("packet_not_ready_for_adjudication")
    if packet.get("unlocks_held_out") is not False:
        errors.append("packet_scientific_firewall_invalid")
    if submission.get("schema_version") != "1.0":
        errors.append("unsupported_schema_version")
    if submission.get("packet_sha256") != sha256_bytes(packet_bytes):
        errors.append("packet_sha256_mismatch")
    if not submission.get("adjudication_id") or not submission.get("adjudicator_id"):
        errors.append("missing_adjudication_or_adjudicator_id")
    blindness = submission.get("blindness", {})
    if set(blindness) != BLINDNESS_KEYS or any(blindness.get(key) is not True for key in BLINDNESS_KEYS):
        errors.append("blindness_attestation_failed")

    packet_records = {item["record_id"]: item for item in packet.get("records", [])}
    records = submission.get("records")
    if not isinstance(records, list):
        records = []
        errors.append("records_missing")
    submitted = {}
    for record in records:
        record_id = record.get("record_id")
        if record_id in submitted:
            errors.append(f"duplicate_record:{record_id}")
            continue
        submitted[record_id] = record
        source = packet_records.get(record_id)
        if not source:
            errors.append(f"unknown_record:{record_id}")
            continue
        if record.get("source_sha256") != source.get("source_sha256"):
            errors.append(f"source_sha_mismatch:{record_id}")
        valid_refs = {
            f"SIDE_1:{item['local_id']}" for item in source["side_1"]["objects"]
        } | {
            f"SIDE_2:{item['local_id']}" for item in source["side_2"]["objects"]
        }
        ids = set()
        for obj in record.get("objects", []):
            object_id = obj.get("adjudicated_id")
            if not object_id or object_id in ids:
                errors.append(f"invalid_or_duplicate_object:{record_id}:{object_id}")
            ids.add(object_id)
            bbox = obj.get("bbox")
            if (
                not isinstance(bbox, list) or len(bbox) != 4
                or any(not isinstance(value, (int, float)) or value < 0 or value > 1 for value in bbox)
                or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]
            ):
                errors.append(f"invalid_bbox:{record_id}:{object_id}")
            if obj.get("class") not in CLASSES:
                errors.append(f"invalid_class:{record_id}:{object_id}")
            ports = obj.get("ports")
            if not isinstance(ports, list) or len(ports) != len(set(ports)) or set(ports) - PORTS:
                errors.append(f"invalid_ports:{record_id}:{object_id}")
            refs = obj.get("source_refs")
            if not isinstance(refs, list) or not refs or len(refs) != len(set(refs)) or set(refs) - valid_refs:
                errors.append(f"invalid_source_refs:{record_id}:{object_id}")
                refs = []
            rationale = obj.get("rationale_code")
            if rationale not in OBJECT_RATIONALES:
                errors.append(f"invalid_object_rationale:{record_id}:{object_id}")
            ref_sides = {ref.split(":", 1)[0] for ref in refs}
            if rationale == "AGREE" and ref_sides != {"SIDE_1", "SIDE_2"}:
                errors.append(f"agree_requires_both_sides:{record_id}:{object_id}")
            if rationale == "SELECT_SIDE_1" and "SIDE_1" not in ref_sides:
                errors.append(f"side_1_selection_missing_ref:{record_id}:{object_id}")
            if rationale == "SELECT_SIDE_2" and "SIDE_2" not in ref_sides:
                errors.append(f"side_2_selection_missing_ref:{record_id}:{object_id}")
        seen_relations = set()
        for relation in record.get("occlusions", []):
            key = (relation.get("source_id"), relation.get("target_id"), relation.get("relation"))
            if key in seen_relations:
                errors.append(f"duplicate_occlusion:{record_id}")
            seen_relations.add(key)
            if relation.get("source_id") not in ids or relation.get("target_id") not in ids:
                errors.append(f"orphan_occlusion:{record_id}")
            if relation.get("source_id") == relation.get("target_id"):
                errors.append(f"self_occlusion:{record_id}")
            if relation.get("relation") not in RELATIONS:
                errors.append(f"invalid_occlusion:{record_id}")
            if relation.get("rationale_code") not in RELATION_RATIONALES:
                errors.append(f"invalid_relation_rationale:{record_id}")
    if set(submitted) != set(packet_records):
        errors.append("record_universe_incomplete")
    valid = not errors
    return {
        "schema_version": "1.0",
        "status": "ADJUDICATION_VALIDATED" if valid else "ADJUDICATION_REJECTED",
        "packet_sha256": sha256_bytes(packet_bytes),
        "record_count": len(submitted),
        "errors": sorted(set(errors)),
        "structurally_valid_for_readiness_chain": valid,
        "promotes_to_ground_truth": False,
        "unlocks_held_out": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("submission", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        packet_bytes = args.packet.read_bytes()
        result = validate_adjudication(
            packet_bytes, json.loads(packet_bytes.decode("utf-8")),
            json.loads(args.submission.read_text(encoding="utf-8")),
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        result = {
            "schema_version": "1.0", "status": "ADJUDICATION_REJECTED",
            "errors": [f"validation_error:{error}"],
            "structurally_valid_for_readiness_chain": False,
            "promotes_to_ground_truth": False, "unlocks_held_out": False,
        }
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["status"] == "ADJUDICATION_VALIDATED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
