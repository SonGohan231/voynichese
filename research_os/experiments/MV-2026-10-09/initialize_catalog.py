#!/usr/bin/env python3
"""Stage-0 catalog for MV-2026-10-09. Never infers object identity from empty atlas records."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ALLOWED_AUTOMATIC = {"AUTO_ANNOTATED_CANDIDATE"}
UNKNOWN = "UNKNOWN"


def check_bbox(bbox, width: int, height: int):
    """Existing auto-overlay coordinates use [x1,y1,x2,y2], NOT xywh."""
    if not isinstance(bbox, list) or len(bbox) != 4:
        raise ValueError("bbox must be [x1,y1,x2,y2]")
    if not all(type(v) in (float, int) for v in bbox):
        raise ValueError("bbox coordinates must be numeric")
    x1, y1, x2, y2 = bbox
    if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
        raise ValueError("bbox outside source dimensions or degenerate")
    xywh = [x1, y1, x2 - x1, y2 - y1]
    norm = [round(x1 / width, 8), round(y1 / height, 8),
            round((x2 - x1) / width, 8), round((y2 - y1) / height, 8)]
    return xywh, norm


def normalize_pigment(raw: str | None):
    # The old overlay's INK_OR_NEUTRAL is NOT evidence of an unpainted area.
    if raw == "PIGMENT_PRESENT":
        return {"status": "PIGMENT_DETECTED_AUTOMATICALLY", "colors": UNKNOWN}
    if raw == "INK_OR_NEUTRAL":
        return {"status": UNKNOWN, "colors": UNKNOWN}
    return {"status": UNKNOWN, "colors": UNKNOWN}


def collect(records_dir: Path, *, permit_auto: bool = False):
    output = []
    counts = {"scanned_records": 0, "covers_excluded": 0, "ready_without_annotations": 0,
              "auto_records_denied": 0, "accepted_auto_records": 0, "objects": 0,
              "invalid_records": 0}
    errors = []
    for path in sorted(records_dir.glob("*.annotation.json")):
        counts["scanned_records"] += 1
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            src = record["source"]
            if src.get("logical_role") == "COVER":
                counts["covers_excluded"] += 1
                continue
            status = record.get("execution_status")
            objects = record.get("illustration_inventory", {}).get("objects", [])
            if status == "SCHEMA_READY" and not objects:
                counts["ready_without_annotations"] += 1
                continue
            if status in ALLOWED_AUTOMATIC and not permit_auto:
                counts["auto_records_denied"] += 1
                continue
            if status not in ALLOWED_AUTOMATIC and status != "MANUALLY_REVIEWED":
                raise ValueError(f"unrecognized or unreviewed record status {status}")
            dims = src["image_file_grid_px"]
            width, height = int(dims["width"]), int(dims["height"])
            if not width or not height:
                raise ValueError("image dimensions absent")
            if status in ALLOWED_AUTOMATIC:
                counts["accepted_auto_records"] += 1
            for obj in objects:
                if obj.get("neutral_class") == "COMPOSITE_ILLUSTRATION_FIELD":
                    continue
                xywh, norm = check_bbox(obj.get("bbox"), width, height)
                output.append({
                    "object_id": f"{record['record_id']}:{obj['object_id']}",
                    "record_id": record["record_id"],
                    "folio": src.get("folio_or_cover_id"),
                    "canvas_id": src.get("provenance", {}).get("source_url_or_catalog_id", UNKNOWN),
                    "source_path": src.get("relative_path"),
                    "source_sha256": src.get("sha256"),
                    "sha_reverified_this_run": False,
                    "connected_leaf_group": UNKNOWN,
                    "section": UNKNOWN,
                    "scribe_class": UNKNOWN,
                    "bbox_xywh_px": xywh,
                    "bbox_xywh_norm": norm,
                    "crop_path": None,
                    "object_class": obj.get("neutral_class", UNKNOWN),
                    "geometry": {
                        "aspect": obj.get("metrics", {}).get("aspect", UNKNOWN),
                        "contour": UNKNOWN, "rotation_deg": UNKNOWN,
                        "perimeter": UNKNOWN, "view_transform": UNKNOWN},
                    "topology": {"edges": UNKNOWN, "cycles": UNKNOWN,
                                 "ports": UNKNOWN, "adjacency": obj.get("adjacency") or UNKNOWN},
                    "counts": {"stars": UNKNOWN, "women": UNKNOWN, "towers": UNKNOWN,
                               "sectors": UNKNOWN, "links": UNKNOWN},
                    "pigment": normalize_pigment(obj.get("color")),
                    "text_context": {"labels": UNKNOWN, "tokens": UNKNOWN,
                                     "source": UNKNOWN},
                    "figure_orientation": {"face": UNKNOWN, "body": UNKNOWN,
                                           "hands": UNKNOWN},
                    "relations": [],
                    "observation_status": "AUTO_CANDIDATE" if status in ALLOWED_AUTOMATIC
                                          else "REVIEWED",
                    "manual_adjudication": False if status in ALLOWED_AUTOMATIC else UNKNOWN,
                    "evidence": {"record_path": path.as_posix(),
                                 "source_candidate_not_ground_truth": True},
                })
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
            counts["invalid_records"] += 1
            errors.append({"record": path.name, "reason": str(exc)})
    counts["objects"] = len(output)
    return output, counts, errors


def build(records_dir: Path, output_dir: Path, *, permit_auto: bool = False):
    output, counts, errors = collect(records_dir, permit_auto=permit_auto)
    if not counts["scanned_records"]:
        status = "BLOCKED_DATA"
        errors.append({"reason": "No annotation JSON files found"})
    elif errors:
        status = "BLOCKED_DATA"
    elif not output:
        status = "BLOCKED_DATA"
    else:
        status = "AUTO_CANDIDATE_ONLY"
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / "objects.jsonl"
    with dest.open("w", encoding="utf-8") as stream:
        for obj in output:
            stream.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    qc = {
        "experiment_id": "MV-2026-10-09",
        "status": status,
        "scientific_status": "INCONCLUSIVE_NOT_RUN",
        "counts": counts,
        "errors": errors,
        "objects_sha256": digest,
        "source_hashes_reverified_this_run": False,
        "allow_auto_candidates": permit_auto,
        "pair_matching_performed": False,
        "independent_manual_review": False,
        "mv2_mv3_mv4_candidates": 0,
        "held_out_used": False,
    }
    (output_dir / "catalog_qc.json").write_text(
        json.dumps(qc, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8")
    return qc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=Path("atlas/records"))
    parser.add_argument("--output", type=Path,
                        default=Path("research_os/experiments/MV-2026-10-09/output"))
    parser.add_argument("--permit-auto-candidates", action="store_true",
                        help="Accept existing generated objects as unverified candidates only")
    args = parser.parse_args()
    qc = build(args.records, args.output, permit_auto=args.permit_auto_candidates)
    print(json.dumps(qc, ensure_ascii=False, sort_keys=True))
    if qc["status"] == "BLOCKED_DATA":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
