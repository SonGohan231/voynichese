#!/usr/bin/env python3
"""Validate two independent annotations and compute a fail-closed agreement gate."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any


IOU_MATCH = 0.50
THRESHOLDS = {
    "object_f1": 0.80,
    "median_iou": 0.75,
    "port_count_agreement": 0.80,
    "occlusion_agreement": 0.80,
}
BLINDNESS_KEYS = (
    "other_annotation_unseen",
    "automated_candidates_unseen",
    "model_predictions_unseen",
    "hypothesis_labels_unseen",
    "split_assignment_unseen",
)
CLASSES = {"ILLUSTRATION_OBJECT", "ILLUSTRATION_FIELD", "TEXT_FIELD", "DIAGRAM"}
PORTS = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"}
RELATIONS = {"IN_FRONT_OF", "BEHIND", "AMBIGUOUS"}


def load_atlas(records_dir: Path) -> dict[str, str]:
    result = {}
    for path in sorted(records_dir.glob("*.annotation.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record["source"].get("logical_role") == "FOLIO":
            result[record["record_id"]] = record["source"]["sha256"]
    return result


def bbox_iou(left: list[float], right: list[float]) -> float:
    intersection = max(0.0, min(left[2], right[2]) - max(left[0], right[0])) * max(
        0.0, min(left[3], right[3]) - max(left[1], right[1])
    )
    left_area = (left[2] - left[0]) * (left[3] - left[1])
    right_area = (right[2] - right[0]) * (right[3] - right[1])
    union = left_area + right_area - intersection
    return intersection / union if union > 0 else 0.0


def validate_submission(submission: dict[str, Any], atlas: dict[str, str]) -> list[str]:
    errors = []
    if submission.get("schema_version") != "1.0":
        errors.append("unsupported_schema_version")
    if not submission.get("annotation_id") or not submission.get("annotator_id"):
        errors.append("missing_annotation_or_annotator_id")
    blindness = submission.get("blindness", {})
    if any(blindness.get(key) is not True for key in BLINDNESS_KEYS):
        errors.append("blindness_attestation_failed")
    records = submission.get("records")
    if not isinstance(records, list) or not records:
        return errors + ["records_missing_or_empty"]
    seen_records = set()
    for record in records:
        record_id = record.get("record_id")
        if record_id in seen_records:
            errors.append(f"duplicate_record:{record_id}")
        seen_records.add(record_id)
        if record_id not in atlas:
            errors.append(f"unknown_record:{record_id}")
        elif record.get("source_sha256") != atlas[record_id]:
            errors.append(f"source_sha_mismatch:{record_id}")
        seen_objects = set()
        for obj in record.get("objects", []):
            local_id = obj.get("local_id")
            if not local_id or local_id in seen_objects:
                errors.append(f"invalid_or_duplicate_object:{record_id}:{local_id}")
            seen_objects.add(local_id)
            bbox = obj.get("bbox")
            if (
                not isinstance(bbox, list)
                or len(bbox) != 4
                or any(not isinstance(value, (int, float)) or value < 0 or value > 1 for value in bbox)
                or bbox[0] >= bbox[2]
                or bbox[1] >= bbox[3]
            ):
                errors.append(f"invalid_bbox:{record_id}:{local_id}")
            if obj.get("class") not in CLASSES:
                errors.append(f"invalid_class:{record_id}:{local_id}")
            ports = obj.get("ports")
            if not isinstance(ports, list) or len(ports) != len(set(ports)) or set(ports) - PORTS:
                errors.append(f"invalid_ports:{record_id}:{local_id}")
        for relation in record.get("occlusions", []):
            if relation.get("source_id") not in seen_objects or relation.get("target_id") not in seen_objects:
                errors.append(f"orphan_occlusion:{record_id}")
            if relation.get("source_id") == relation.get("target_id"):
                errors.append(f"self_occlusion:{record_id}")
            if relation.get("relation") not in RELATIONS:
                errors.append(f"invalid_occlusion:{record_id}")
    return sorted(set(errors))


def match_objects(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> list[tuple[int, int, float]]:
    candidates = []
    for left_index, left_object in enumerate(left):
        for right_index, right_object in enumerate(right):
            if left_object["class"] == right_object["class"]:
                score = bbox_iou(left_object["bbox"], right_object["bbox"])
                if score >= IOU_MATCH:
                    candidates.append((score, left_index, right_index))
    matches, used_left, used_right = [], set(), set()
    for score, left_index, right_index in sorted(candidates, reverse=True):
        if left_index not in used_left and right_index not in used_right:
            matches.append((left_index, right_index, score))
            used_left.add(left_index)
            used_right.add(right_index)
    return matches


def comparable_occlusions(record: dict[str, Any], mapping: dict[str, str]) -> dict[tuple[str, str], str]:
    result = {}
    for item in record.get("occlusions", []):
        if item["source_id"] in mapping and item["target_id"] in mapping:
            source = mapping[item["source_id"]]
            target = mapping[item["target_id"]]
            relation = item["relation"]
            if relation == "BEHIND":
                source, target, relation = target, source, "IN_FRONT_OF"
            result[(source, target)] = relation
    return result


def agreement_report(left: dict[str, Any], right: dict[str, Any], atlas: dict[str, str]) -> dict[str, Any]:
    left_errors = validate_submission(left, atlas)
    right_errors = validate_submission(right, atlas)
    pair_errors = []
    if left.get("annotator_id") == right.get("annotator_id"):
        pair_errors.append("annotator_ids_not_distinct")
    left_records = {record["record_id"]: record for record in left.get("records", [])}
    right_records = {record["record_id"]: record for record in right.get("records", [])}
    if set(left_records) != set(right_records):
        pair_errors.append("record_universe_mismatch")
    common = sorted(set(left_records) & set(right_records))
    total_left = total_right = total_matches = port_matches = 0
    ious: list[float] = []
    left_relations: dict[tuple[str, str, str], str] = {}
    right_relations: dict[tuple[str, str, str], str] = {}
    for record_id in common:
        left_objects = left_records[record_id].get("objects", [])
        right_objects = right_records[record_id].get("objects", [])
        matches = match_objects(left_objects, right_objects)
        total_left += len(left_objects)
        total_right += len(right_objects)
        total_matches += len(matches)
        ious.extend(match[2] for match in matches)
        left_to_canonical = {}
        right_to_canonical = {}
        for index, (left_index, right_index, _) in enumerate(matches):
            canonical = f"M{index:05d}"
            left_to_canonical[left_objects[left_index]["local_id"]] = canonical
            right_to_canonical[right_objects[right_index]["local_id"]] = canonical
            if len(left_objects[left_index]["ports"]) == len(right_objects[right_index]["ports"]):
                port_matches += 1
        for key, value in comparable_occlusions(left_records[record_id], left_to_canonical).items():
            left_relations[(record_id, *key)] = value
        for key, value in comparable_occlusions(right_records[record_id], right_to_canonical).items():
            right_relations[(record_id, *key)] = value
    object_f1 = 2 * total_matches / (total_left + total_right) if total_left + total_right else None
    median_iou = statistics.median(ious) if ious else None
    port_agreement = port_matches / total_matches if total_matches else None
    comparable = set(left_relations) & set(right_relations)
    occlusion_agreement = (
        sum(left_relations[key] == right_relations[key] for key in comparable) / len(comparable)
        if comparable
        else None
    )
    metrics = {
        "object_f1": object_f1,
        "median_iou": median_iou,
        "port_count_agreement": port_agreement,
        "occlusion_agreement": occlusion_agreement,
    }
    gates = {
        "submissions_valid": not left_errors and not right_errors and not pair_errors,
        "record_and_source_universe_complete": bool(atlas)
        and set(left_records) == set(right_records) == set(atlas),
        **{
            name: value is not None and value >= THRESHOLDS[name]
            for name, value in metrics.items()
        },
    }
    return {
        "schema_version": "1.0",
        "status": "READY_FOR_ADJUDICATION" if all(gates.values()) else "INCONCLUSIVE_ANNOTATION_GATE_FAILED",
        "promotes_to_ground_truth": False,
        "unlocks_held_out": False,
        "thresholds": {"iou_match": IOU_MATCH, **THRESHOLDS},
        "errors": {"left": left_errors, "right": right_errors, "pair": pair_errors},
        "counts": {
            "common_records": len(common),
            "left_objects": total_left,
            "right_objects": total_right,
            "matched_objects": total_matches,
            "comparable_occlusions": len(comparable),
        },
        "metrics": metrics,
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("records_dir", type=Path)
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    atlas = load_atlas(args.records_dir)
    left = json.loads(args.left.read_text(encoding="utf-8"))
    right = json.loads(args.right.read_text(encoding="utf-8"))
    report = agreement_report(left, right, atlas)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.report:
        args.report.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"] == "READY_FOR_ADJUDICATION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
