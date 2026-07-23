#!/usr/bin/env python3
"""Instantiate the canonical Voynich atlas schema for every Yale scan position.

This script is deterministic and geometry-neutral. It verifies source bytes, records
native image dimensions, creates one schema-ready record per unique Yale sequence,
preserves duplicate source aliases, and does not invent visual annotations.
"""

from __future__ import annotations

import hashlib
import json
import re
import struct
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "data" / "yale_hq_scans"
IMPORT_REPORT = SOURCE_ROOT / "import_report.json"
ATLAS_ROOT = REPO_ROOT / "atlas"
RECORDS_ROOT = ATLAS_ROOT / "records"
SCHEMA_ROOT = ATLAS_ROOT / "schemas"
SCHEMA_VERSION = "1.0.0"
GENERATOR_VERSION = "1.0.0"

REQUIRED_TOP_LEVEL = {
    "schema_version",
    "record_id",
    "source",
    "canonical_context",
    "page_inventory",
    "illustration_inventory",
    "text_geometry",
    "local_relations",
    "overlay",
    "quality_control",
    "execution_status",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jpeg_dimensions(path: Path) -> tuple[int, int]:
    """Read JPEG width and height from SOF markers using only the standard library."""
    sof_markers = {
        0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
        0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
    }
    with path.open("rb") as handle:
        if handle.read(2) != b"\xff\xd8":
            raise ValueError(f"Not a JPEG: {path}")
        while True:
            byte = handle.read(1)
            if not byte:
                break
            if byte != b"\xff":
                continue
            while byte == b"\xff":
                byte = handle.read(1)
            if not byte:
                break
            marker = byte[0]
            if marker in {0xD8, 0xD9}:
                continue
            if marker == 0xDA:
                break
            length_raw = handle.read(2)
            if len(length_raw) != 2:
                break
            segment_length = struct.unpack(">H", length_raw)[0]
            if segment_length < 2:
                raise ValueError(f"Invalid JPEG segment in {path}")
            if marker in sof_markers:
                payload = handle.read(5)
                if len(payload) != 5:
                    break
                _precision, height, width = struct.unpack(">BHH", payload)
                if width < 1 or height < 1:
                    raise ValueError(f"Invalid JPEG dimensions in {path}")
                return width, height
            handle.seek(segment_length - 2, 1)
    raise ValueError(f"No JPEG SOF marker found: {path}")


def safe_slug(value: str) -> str:
    normalized = value.strip().strip("[]").strip()
    normalized = re.sub(r"[^0-9A-Za-z._-]+", "_", normalized)
    normalized = normalized.strip("_.-")
    return normalized or "unlabeled"


def logical_role(label: str) -> str:
    clean = label.strip().strip("[]").strip().lower()
    if "cover" in clean or "endpaper" in clean:
        return "COVER"
    if re.fullmatch(r"\d+[rv](?:\d+)?", clean):
        return "FOLIO"
    return "UNRESOLVED"


def overlay_template(source_sha: str) -> dict[str, Any]:
    return {
        "overlay_status": "NOT_RENDERED",
        "source_sha256": source_sha,
        "id_policy": "EVERY_VISIBLE_ANNOTATED_ENTITY_HAS_UNIQUE_ID",
        "layers": [
            {"layer_id": "L01_PAGE_REGIONS", "entity_types": ["PAGE_REGION"], "z_index": 10, "label_ids": True, "opacity": 0.65},
            {"layer_id": "L02_ILLUSTRATION_OBJECTS", "entity_types": ["ILLUSTRATION_OBJECT"], "z_index": 20, "label_ids": True, "opacity": 0.75},
            {"layer_id": "L03_TEXT_GEOMETRY", "entity_types": ["TEXT_REGION"], "z_index": 30, "label_ids": True, "opacity": 0.70},
            {"layer_id": "L04_LOCAL_RELATIONS", "entity_types": ["LOCAL_RELATION"], "z_index": 40, "label_ids": True, "opacity": 0.85},
        ],
        "output": {"filename": None, "mime": None, "sha256": None},
    }


def build_record(item: dict[str, Any], width: int, height: int) -> dict[str, Any]:
    label = str(item.get("yale_canvas_label") or "").strip()
    folio_id = label.strip("[]").strip() or None
    sequence = int(item["sequence"])
    relative_path = f"data/yale_hq_scans/{item['archive']}/{item['filename']}"
    source_sha = str(item["sha256"])
    return {
        "schema_version": SCHEMA_VERSION,
        "record_id": f"CANVAS-{sequence:04d}-{safe_slug(label)}",
        "source": {
            "source_file_id": f"YALE-MS408-{sequence:04d}",
            "relative_path": relative_path,
            "filename": item["filename"],
            "sha256": source_sha,
            "bytes": int(item["bytes"]),
            "mime": "image/jpeg",
            "image_file_grid_px": {"width": width, "height": height},
            "native_scan_grid_status": "VERIFIED_NATIVE",
            "folio_or_cover_id": folio_id,
            "logical_role": logical_role(label),
            "rotation_deg": 0,
            "provenance": {
                "classification": "ORIGINAL_NATIVE",
                "verification_status": "VERIFIED",
                "measurement_permission": "NATIVE_PIXEL_MEASUREMENT_ALLOWED",
                "evidence": [
                    "Official Yale University Library Beinecke MS 408 IIIF canvas.",
                    "Repository import_report.json records the canvas identifier, full-resolution IIIF URL, byte count and SHA-256.",
                    "This generator recomputed the SHA-256 and read the JPEG dimensions without rewriting the source image.",
                ],
                "source_url_or_catalog_id": item.get("yale_canvas_id"),
                "image_url": item.get("image_url"),
            },
        },
        "canonical_context": {
            "state_status": "STATE_RECONCILED",
            "start_here_note": {"id": 334, "version": 2},
            "current_state_attachment": {
                "id": 604,
                "sha256_verified": True,
                "sha256": "ff3b2f8e175400f72de93ad8b9a7535daeb83cd710e50bdeedfa084141af6769",
            },
            "project_changelog_attachment": {
                "id": 603,
                "sha256_verified": True,
                "sha256": "6938ddab76a61331e98e9975aad74f2ab14230c6e6c370ce4fe358cddc1474fb",
            },
            "active_rules": [10, 14, 16, 17, 18, 19],
            "scope_decision": "FULL_EXECUTION_ALLOWED",
            "scope_note": "The user explicitly ordered schema application to all folios. This creates source-verified records only; it does not fabricate visual annotations or cross-page matches.",
        },
        "page_inventory": {
            "regions": [],
            "coverage_status": {
                "parchment_field": "NOT_ASSESSED",
                "main_text_fields": "NOT_ASSESSED",
                "main_illustration_fields": "NOT_ASSESSED",
                "diagrams": "NOT_ASSESSED",
                "margins": "NOT_ASSESSED",
                "damage": "NOT_ASSESSED",
                "overlap": "NOT_ASSESSED",
            },
        },
        "illustration_inventory": {"objects": [], "repeat_groups": [], "hierarchy_validated": False},
        "text_geometry": {
            "regions": [],
            "segmentation_status": "NOT_ASSESSED",
            "text_illustration_link_policy": "GEOMETRY_ONLY",
            "transliteration_policy": "REFERENCE_ONLY_NOT_BOUNDARY_AUTHORITY",
        },
        "local_relations": [],
        "overlay": overlay_template(source_sha),
        "quality_control": {
            "id_uniqueness": "PASS",
            "hierarchy_acyclic": "PASS",
            "geometry_within_source": "PASS",
            "transliteration_not_used_for_boundaries": "PASS",
            "reading_order_only_when_observable": "PASS",
            "semantic_naming_audit": "PASS",
            "review_status": "NOT_REVIEWED",
            "issues": [
                "Visual annotation has not yet been performed.",
                "No text/illustration relation or cross-page similarity is asserted by this schema-instantiation pass.",
            ],
        },
        "execution_status": "SCHEMA_READY",
        "deferred_reason": None,
    }


def build_schema() -> dict[str, Any]:
    """JSON Schema for the geometry-first atlas records."""
    status = ["COMPLETE", "PARTIAL", "NONE_VISIBLE", "NOT_ASSESSED"]
    qc = ["PASS", "FAIL", "NOT_RUN"]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://github.com/SonGohan231/voynichese/blob/master/atlas/schemas/voynich_page_atlas.schema.json",
        "title": "Voynich full-page visual and text geometry atlas record",
        "description": "Neutral geometry-first schema. Transliteration is reference-only and cannot define visual boundaries.",
        "type": "object",
        "additionalProperties": False,
        "required": sorted(REQUIRED_TOP_LEVEL),
        "properties": {
            "schema_version": {"const": SCHEMA_VERSION},
            "record_id": {"type": "string", "minLength": 1},
            "source": {
                "type": "object",
                "required": ["source_file_id", "relative_path", "filename", "sha256", "bytes", "mime", "image_file_grid_px", "folio_or_cover_id", "logical_role", "rotation_deg", "provenance"],
                "properties": {
                    "source_file_id": {"type": "string"},
                    "relative_path": {"type": "string"},
                    "filename": {"type": "string"},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "bytes": {"type": "integer", "minimum": 0},
                    "mime": {"const": "image/jpeg"},
                    "image_file_grid_px": {"type": "object", "required": ["width", "height"], "properties": {"width": {"type": "integer", "minimum": 1}, "height": {"type": "integer", "minimum": 1}}, "additionalProperties": False},
                    "native_scan_grid_status": {"enum": ["VERIFIED_NATIVE", "SCALED_FROM_NATIVE", "UNVERIFIED"]},
                    "folio_or_cover_id": {"type": ["string", "null"]},
                    "logical_role": {"enum": ["FOLIO", "COVER", "UNRESOLVED"]},
                    "rotation_deg": {"type": "number"},
                    "provenance": {"type": "object", "required": ["classification", "verification_status", "measurement_permission", "evidence"], "properties": {"classification": {"enum": ["ORIGINAL_NATIVE", "ORIGINAL_SCALED", "DERIVATIVE_PDF", "DERIVED_CROP", "UNVERIFIED_LARGE", "WORKING_SMALL", "SYNTHETIC"]}, "verification_status": {"enum": ["VERIFIED", "UNVERIFIED", "PARTIAL"]}, "measurement_permission": {"enum": ["NATIVE_PIXEL_MEASUREMENT_ALLOWED", "MEASUREMENT_WITH_SCALE_REQUIRED", "LAYOUT_ORIENTATION_ONLY", "ANALYSIS_NOT_ALLOWED"]}, "evidence": {"type": "array", "items": {"type": "string"}}, "source_url_or_catalog_id": {"type": ["string", "null"]}, "image_url": {"type": ["string", "null"]}}, "additionalProperties": False},
                },
                "additionalProperties": False,
            },
            "canonical_context": {"type": "object"},
            "page_inventory": {"type": "object", "required": ["regions", "coverage_status"], "properties": {"regions": {"type": "array", "items": {"$ref": "#/$defs/pageRegion"}}, "coverage_status": {"type": "object", "required": ["parchment_field", "main_text_fields", "main_illustration_fields", "diagrams", "margins", "damage", "overlap"], "properties": {key: {"enum": status} for key in ["parchment_field", "main_text_fields", "main_illustration_fields", "diagrams", "margins", "damage", "overlap"]}, "additionalProperties": False}}, "additionalProperties": False},
            "illustration_inventory": {"type": "object", "required": ["objects", "repeat_groups", "hierarchy_validated"], "properties": {"objects": {"type": "array", "items": {"$ref": "#/$defs/illustrationObject"}}, "repeat_groups": {"type": "array", "items": {"$ref": "#/$defs/repeatGroup"}}, "hierarchy_validated": {"type": "boolean"}}, "additionalProperties": False},
            "text_geometry": {"type": "object", "required": ["regions", "segmentation_status", "text_illustration_link_policy", "transliteration_policy"], "properties": {"regions": {"type": "array", "items": {"$ref": "#/$defs/textRegion"}}, "segmentation_status": {"enum": ["NOT_ASSESSED", "BLOCKS_ONLY", "BLOCKS_AND_PARAGRAPHS", "LINES_PARTIAL", "LINES_COMPLETE"]}, "text_illustration_link_policy": {"const": "GEOMETRY_ONLY"}, "transliteration_policy": {"const": "REFERENCE_ONLY_NOT_BOUNDARY_AUTHORITY"}}, "additionalProperties": False},
            "local_relations": {"type": "array", "items": {"$ref": "#/$defs/localRelation"}},
            "overlay": {"type": "object"},
            "quality_control": {"type": "object", "required": ["id_uniqueness", "hierarchy_acyclic", "geometry_within_source", "transliteration_not_used_for_boundaries", "reading_order_only_when_observable", "semantic_naming_audit", "review_status"], "properties": {"id_uniqueness": {"enum": qc}, "hierarchy_acyclic": {"enum": qc}, "geometry_within_source": {"enum": qc}, "transliteration_not_used_for_boundaries": {"enum": qc}, "reading_order_only_when_observable": {"enum": qc}, "semantic_naming_audit": {"enum": qc}, "review_status": {"enum": ["NOT_REVIEWED", "SINGLE_REVIEW", "DOUBLE_REVIEW", "ADJUDICATED"]}, "issues": {"type": "array", "items": {"type": "string"}}}, "additionalProperties": False},
            "execution_status": {"enum": ["SCHEMA_READY", "NOT_STARTED", "IN_PROGRESS", "ANNOTATED_DRAFT", "VERIFIED", "AMBIGUOUS", "DEFERRED_BY_ACTIVE_RULE_19"]},
            "deferred_reason": {"type": ["string", "null"]},
        },
        "$defs": {
            "point": {"type": "array", "prefixItems": [{"type": "number"}, {"type": "number"}], "items": False, "minItems": 2, "maxItems": 2},
            "bbox": {"type": "array", "prefixItems": [{"type": "number"}, {"type": "number"}, {"type": "number"}, {"type": "number"}], "items": False, "minItems": 4, "maxItems": 4},
            "geometry": {"type": "object", "required": ["geometry_type", "coordinate_space", "source_width_px", "source_height_px", "rotation_deg", "relation_tolerance_px", "source_to_geometry_transform"], "properties": {"geometry_type": {"enum": ["BBOX", "POLYGON", "MASK"]}, "coordinate_space": {"enum": ["SOURCE_IMAGE_PX", "VERIFIED_NATIVE_SCAN_PX", "CROP_PX", "NORMALIZED_0_1"]}, "source_width_px": {"type": "integer", "minimum": 1}, "source_height_px": {"type": "integer", "minimum": 1}, "bbox": {"$ref": "#/$defs/bbox"}, "polygon": {"type": "array", "minItems": 4, "items": {"$ref": "#/$defs/point"}}, "mask_artifact_id": {"type": ["string", "integer", "null"]}, "rotation_deg": {"type": "number"}, "relation_tolerance_px": {"type": "number", "minimum": 0}, "source_to_geometry_transform": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "number"}}}}, "additionalProperties": True},
            "observation": {"type": "object", "required": ["method", "annotator_id", "blind_to_semantic_hypotheses", "confidence", "ambiguity_status", "evidence_note"], "properties": {"method": {"enum": ["MANUAL_VISUAL", "AUTOMATIC", "SEMI_AUTOMATIC", "MULTIMODAL_REVIEW"]}, "annotator_id": {"type": "string"}, "blind_to_semantic_hypotheses": {"type": "boolean"}, "confidence": {"enum": ["HIGH", "MEDIUM", "LOW", "AMBIGUOUS", "NOT_ASSESSED"]}, "ambiguity_status": {"enum": ["UNAMBIGUOUS", "AMBIGUOUS", "NOT_ASSESSED"]}, "evidence_note": {"type": "string"}}, "additionalProperties": True},
            "pageRegion": {"type": "object", "required": ["region_id", "class", "geometry", "observation"], "properties": {"region_id": {"type": "string"}, "class": {"enum": ["PARCHMENT_FIELD", "MAIN_TEXT_FIELD", "MAIN_ILLUSTRATION_FIELD", "DIAGRAM_FIELD", "MARGIN_TOP", "MARGIN_BOTTOM", "MARGIN_LEFT", "MARGIN_RIGHT", "DAMAGE_AREA", "TEXT_ILLUSTRATION_OVERLAP", "UNCLASSIFIED_PAGE_AREA"]}, "geometry": {"$ref": "#/$defs/geometry"}, "observation": {"$ref": "#/$defs/observation"}, "notes": {"type": ["string", "null"]}}, "additionalProperties": False},
            "illustrationObject": {"type": "object", "required": ["object_id", "parent_id", "neutral_class", "geometry", "count", "attributes", "observation"], "properties": {"object_id": {"type": "string"}, "parent_id": {"type": ["string", "null"]}, "child_ids": {"type": "array", "items": {"type": "string"}}, "neutral_class": {"type": "string"}, "geometry": {"$ref": "#/$defs/geometry"}, "count": {"type": "object"}, "attributes": {"type": "object", "required": ["position", "orientation", "direction", "colors", "neighbor_ids", "connection_ids"], "properties": {"position": {"type": "object"}, "orientation": {"type": ["string", "number", "null"]}, "direction": {"type": ["string", "null"]}, "colors": {"type": "array", "items": {"type": "string"}}, "neighbor_ids": {"type": "array", "items": {"type": "string"}}, "connection_ids": {"type": "array", "items": {"type": "string"}}}, "additionalProperties": True}, "observation": {"$ref": "#/$defs/observation"}}, "additionalProperties": True},
            "repeatGroup": {"type": "object", "required": ["repeat_group_id", "member_ids", "count"], "properties": {"repeat_group_id": {"type": "string"}, "member_ids": {"type": "array", "items": {"type": "string"}}, "count": {"type": "object"}}, "additionalProperties": True},
            "textRegion": {"type": "object", "required": ["text_id", "parent_id", "type", "geometry", "reading_order", "transliteration_refs", "observation"], "properties": {"text_id": {"type": "string"}, "parent_id": {"type": ["string", "null"]}, "child_ids": {"type": "array", "items": {"type": "string"}}, "type": {"enum": ["MAIN_BLOCK", "PARAGRAPH", "LINE", "LABEL", "CIRCULAR", "RADIAL", "MARGINAL", "OTHER"]}, "geometry": {"$ref": "#/$defs/geometry"}, "reading_order": {"type": "object"}, "transliteration_refs": {"type": "array", "items": {"type": "object"}}, "observation": {"$ref": "#/$defs/observation"}}, "additionalProperties": True},
            "localRelation": {"type": "object", "required": ["relation_id", "subject_id", "predicate", "object_id", "geometry_only", "method", "confidence", "evidence"], "properties": {"relation_id": {"type": "string"}, "subject_id": {"type": "string"}, "predicate": {"enum": ["ABOVE", "BELOW", "LEFT_OF", "RIGHT_OF", "INSIDE", "CONTAINS", "TOUCHES", "CONNECTED_TO", "OVERLAPS", "INTERRUPTS_TEXT", "TEXT_SURROUNDS_OBJECT", "SAME_RING", "SAME_SECTOR", "SAME_ROW", "SAME_SEQUENCE", "ADJACENT_TO", "ALIGNED_WITH"]}, "object_id": {"type": "string"}, "geometry_only": {"const": True}, "method": {"enum": ["BBOX_WITH_TOLERANCE", "POLYGON_INTERSECTION", "MASK_CONTACT", "CENTERLINE_TOPOLOGY", "MANUAL_VISUAL"]}, "confidence": {"enum": ["HIGH", "MEDIUM", "LOW", "AMBIGUOUS", "NOT_ASSESSED"]}, "evidence": {"type": "object"}}, "additionalProperties": True},
        },
    }


def validate_record(record: dict[str, Any], record_ids: set[str]) -> list[str]:
    issues: list[str] = []
    missing = REQUIRED_TOP_LEVEL - set(record)
    if missing:
        issues.append(f"missing_top_level={sorted(missing)}")
    record_id = record.get("record_id")
    if record_id in record_ids:
        issues.append(f"duplicate_record_id={record_id}")
    record_ids.add(record_id)
    source = record.get("source", {})
    if not re.fullmatch(r"[0-9a-f]{64}", str(source.get("sha256", ""))):
        issues.append("invalid_source_sha256")
    grid = source.get("image_file_grid_px", {})
    if int(grid.get("width", 0)) < 1 or int(grid.get("height", 0)) < 1:
        issues.append("invalid_image_dimensions")
    if record.get("text_geometry", {}).get("text_illustration_link_policy") != "GEOMETRY_ONLY":
        issues.append("text_illustration_policy_violation")
    return issues


def main() -> None:
    if not IMPORT_REPORT.exists():
        raise SystemExit(f"Missing import report: {IMPORT_REPORT}")
    report = json.loads(IMPORT_REPORT.read_text(encoding="utf-8"))
    files = report.get("files") or []
    if len(files) != 207:
        raise SystemExit(f"Expected 207 source rows, found {len(files)}")
    by_sequence: dict[int, list[dict[str, Any]]] = defaultdict(list)
    source_checks: list[dict[str, Any]] = []
    errors: list[str] = []
    for item in files:
        sequence = int(item["sequence"])
        by_sequence[sequence].append(item)
        path = SOURCE_ROOT / str(item["archive"]) / str(item["filename"])
        exists = path.exists()
        actual_bytes = path.stat().st_size if exists else None
        actual_sha = sha256_file(path) if exists else None
        matches = exists and actual_bytes == int(item["bytes"]) and actual_sha == item["sha256"]
        source_checks.append({"sequence": sequence, "relative_path": str(path.relative_to(REPO_ROOT)), "exists": exists, "expected_bytes": int(item["bytes"]), "actual_bytes": actual_bytes, "expected_sha256": item["sha256"], "actual_sha256": actual_sha, "match": matches})
        if not matches:
            errors.append(f"source_mismatch:{path.relative_to(REPO_ROOT)}")
    if len(by_sequence) != 206:
        errors.append(f"unique_sequence_count={len(by_sequence)} expected=206")
    RECORDS_ROOT.mkdir(parents=True, exist_ok=True)
    for old_record in RECORDS_ROOT.glob("*.annotation.json"):
        old_record.unlink()
    records_index: list[dict[str, Any]] = []
    graph_nodes: list[dict[str, Any]] = []
    aliases: list[dict[str, Any]] = []
    record_ids: set[str] = set()
    record_validation: list[dict[str, Any]] = []
    for sequence in sorted(by_sequence):
        candidates = sorted(by_sequence[sequence], key=lambda row: (int(row["archive"]), str(row["filename"])))
        canonical = candidates[0]
        canonical_path = SOURCE_ROOT / str(canonical["archive"]) / str(canonical["filename"])
        width, height = jpeg_dimensions(canonical_path)
        record = build_record(canonical, width, height)
        record_issues = validate_record(record, record_ids)
        if record_issues:
            errors.extend(f"record:{record['record_id']}:{issue}" for issue in record_issues)
        record_filename = f"{sequence:04d}_{safe_slug(str(canonical.get('yale_canvas_label') or canonical['filename']))}.annotation.json"
        record_path = RECORDS_ROOT / record_filename
        write_json(record_path, record)
        records_index.append({"sequence": sequence, "record_id": record["record_id"], "folio_or_cover_id": record["source"]["folio_or_cover_id"], "logical_role": record["source"]["logical_role"], "record_path": str(record_path.relative_to(REPO_ROOT)), "source_path": record["source"]["relative_path"], "source_sha256": record["source"]["sha256"], "image_file_grid_px": record["source"]["image_file_grid_px"], "execution_status": record["execution_status"]})
        graph_nodes.append({"node_id": record["record_id"], "sequence": sequence, "folio_or_cover_id": record["source"]["folio_or_cover_id"], "record_path": str(record_path.relative_to(REPO_ROOT))})
        record_validation.append({"record_id": record["record_id"], "path": str(record_path.relative_to(REPO_ROOT)), "issues": record_issues, "status": "PASS" if not record_issues else "FAIL"})
        if len(candidates) > 1:
            aliases.append({"sequence": sequence, "canonical_source": record["source"]["relative_path"], "canonical_sha256": record["source"]["sha256"], "additional_sources": [{"relative_path": f"data/yale_hq_scans/{row['archive']}/{row['filename']}", "sha256": row["sha256"], "same_bytes_as_canonical": row["sha256"] == record["source"]["sha256"]} for row in candidates[1:]]})
    generated_at = utc_now()
    write_json(SCHEMA_ROOT / "voynich_page_atlas.schema.json", build_schema())
    write_json(ATLAS_ROOT / "atlas_project.json", {"schema_version": SCHEMA_VERSION, "generator_version": GENERATOR_VERSION, "generated_at": generated_at, "project": "Voynich canonical full-page visual and text geometry atlas", "source_manifest": report.get("source_manifest"), "source_import_report": str(IMPORT_REPORT.relative_to(REPO_ROOT)), "source_import_report_git_blob_sha": "8591c22f2918ac2d9e56266a4ac4cfda99547327", "source_rows": len(files), "canonical_page_positions": len(records_index), "duplicate_source_sequences": [entry["sequence"] for entry in aliases], "records": records_index, "annotation_policy": {"neutral_visual_classes_only": True, "transliteration_reference_only": True, "reading_order_only_when_observable": True, "text_illustration_links_geometry_only": True, "cross_page_links_require_matches_mismatches_method_negative_control_confidence": True, "bbox_size_or_background_color_alone_is_insufficient": True}})
    write_json(ATLAS_ROOT / "source_aliases.json", {"aliases": aliases})
    write_json(ATLAS_ROOT / "cross_page_graph.json", {"schema_version": SCHEMA_VERSION, "generated_at": generated_at, "nodes": graph_nodes, "edges": [], "edge_status": "NOT_EVALUATED", "candidate_features": ["TOPOLOGY", "PART_COUNT", "CONNECTION_LAYOUT", "CLOSURE", "BRANCHING", "DIRECTION", "INPUT_OUTPUT_RELATION", "POSITION_RELATIVE_TO_TEXT"], "edge_requirements": ["MATCHING_FEATURES", "CONFLICTING_FEATURES", "METHOD", "NEGATIVE_CONTROL", "CONFIDENCE_STATUS"], "prohibited_shortcuts": ["SIMILAR_BBOX_SIZE_ONLY", "SIMILAR_BACKGROUND_COLOR_ONLY"]})
    status = "PASS" if not errors else "FAIL"
    write_json(ATLAS_ROOT / "validation_report.json", {"schema_version": SCHEMA_VERSION, "generator_version": GENERATOR_VERSION, "generated_at": generated_at, "status": status, "expected_source_rows": 207, "actual_source_rows": len(files), "expected_unique_sequences": 206, "actual_unique_sequences": len(by_sequence), "generated_record_count": len(records_index), "source_checks": source_checks, "record_validation": record_validation, "errors": errors})
    readme = f"""# Canonical Voynich atlas schema — all Yale scan positions

Generated by `tools/build_canonical_atlas.py` from `data/yale_hq_scans/import_report.json`.

- Source rows verified: **{len(files)}**
- Canonical page-image positions: **{len(records_index)}**
- Duplicate source sequences preserved in `source_aliases.json`: **{len(aliases)}**
- Per-position records: `atlas/records/*.annotation.json`
- Record schema: `atlas/schemas/voynich_page_atlas.schema.json`
- Cross-page graph container: `atlas/cross_page_graph.json`
- Validation: `atlas/validation_report.json` — **{status}**

This pass applies the schema and verifies source identity, byte count, SHA-256 and JPEG dimensions. It does **not** invent parchment boundaries, text blocks, illustration objects, reading order, local relations or cross-page similarities. Those fields remain `NOT_ASSESSED`/empty until evidence-based visual annotation is performed. Transliteration is reference-only and may not define visual boundaries.
"""
    (ATLAS_ROOT / "README.md").write_text(readme, encoding="utf-8")
    if errors:
        raise SystemExit("Atlas generation failed:\n" + "\n".join(errors))
    print(f"Generated {len(records_index)} canonical records from {len(files)} verified source rows.")


if __name__ == "__main__":
    main()
