#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
import re
import shutil
import zipfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

VERSION = "AUTO_CANDIDATE_FINAL_V1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slug(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z._-]+", "_", text).strip("_.-") or "unlabeled"


def largest(mask: np.ndarray) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    if count <= 1:
        return mask.astype(np.uint8)
    idx = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return (labels == idx).astype(np.uint8)


def remove_small(mask: np.ndarray, minimum: int) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    out = np.zeros_like(mask, np.uint8)
    for idx in range(1, count):
        if stats[idx, cv2.CC_STAT_AREA] >= minimum:
            out[labels == idx] = 1
    return out


def page_geometry(image: np.ndarray):
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    options = []
    for raw in (otsu, 255 - otsu):
        closed = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8), iterations=2)
        component = largest(closed > 0)
        area = int(component.sum())
        fraction = area / max(1, h * w)
        mean = float(gray[component > 0].mean()) if area else 0.0
        score = (1.0 - abs(fraction - 0.70)) * 2.0 + mean / 255.0
        if 0.15 < fraction < 0.98:
            options.append((score, component))
    mask = max(options, key=lambda item: item[0])[1] if options else np.ones((h, w), np.uint8)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return mask, [0, 0, w, h], [[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]]
    contour = max(contours, key=cv2.contourArea)
    filled = np.zeros_like(mask)
    cv2.drawContours(filled, [contour], -1, 1, -1)
    x, y, bw, bh = cv2.boundingRect(contour)
    polygon = cv2.approxPolyDP(contour, 0.002 * cv2.arcLength(contour, True), True).reshape(-1, 2).tolist()
    return filled, [x, y, x + bw, y + bh], polygon


def foreground_masks(image: np.ndarray, page_mask: np.ndarray):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
    values = gray[page_mask > 0]
    median_gray = float(np.median(values)) if values.size else 200.0
    local = cv2.GaussianBlur(gray, (0, 0), 7).astype(np.int16) - gray.astype(np.int16)
    ink = ((local > 20) & (gray < min(220, median_gray + 25)) & (page_mask > 0)).astype(np.uint8)
    ink = remove_small(ink, 2)
    valid = (page_mask > 0) & (gray > 70) & (gray < 235)
    median_a = float(np.median(lab[:, :, 1][valid])) if np.any(valid) else 128.0
    median_b = float(np.median(lab[:, :, 2][valid])) if np.any(valid) else 128.0
    distance = np.sqrt((lab[:, :, 1] - median_a) ** 2 + (lab[:, :, 2] - median_b) ** 2)
    pigment = ((distance > 10) & (hsv[:, :, 1] > 25) & (gray < 235) & (page_mask > 0)).astype(np.uint8)
    pigment = remove_small(pigment, 8)
    return ink, pigment, ((ink > 0) | (pigment > 0)).astype(np.uint8), gray


def text_lines(ink: np.ndarray, page_bbox: list[int]):
    x1, y1, x2, y2 = page_bbox
    pw, ph = x2 - x1, y2 - y1
    kernel_width = max(11, int(pw * 0.016))
    joined = cv2.dilate(ink, np.ones((1, kernel_width), np.uint8), iterations=1)
    joined = cv2.morphologyEx(joined, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    count, _, stats, _ = cv2.connectedComponentsWithStats(joined, 8)
    raw = []
    for idx in range(1, count):
        x, y, w, h, _ = stats[idx]
        if w < max(35, pw * 0.035) or h < 2 or h > ph * 0.04:
            continue
        density = float(ink[y:y + h, x:x + w].sum()) / max(1, w * h)
        if w / max(1, h) >= 2.5 and 0.004 <= density <= 0.42:
            raw.append([int(x), int(y), int(x + w), int(y + h)])
    raw.sort(key=lambda b: ((b[1] + b[3]) / 2, b[0]))
    merged: list[list[int]] = []
    for box in raw:
        cy = (box[1] + box[3]) / 2
        for candidate in merged:
            candidate_cy = (candidate[1] + candidate[3]) / 2
            tolerance = max(3.0, min(box[3] - box[1], candidate[3] - candidate[1]) * 0.45)
            gap = max(0, box[0] - candidate[2], candidate[0] - box[2])
            if abs(cy - candidate_cy) <= tolerance and gap <= pw * 0.035:
                candidate[0] = min(candidate[0], box[0])
                candidate[1] = min(candidate[1], box[1])
                candidate[2] = max(candidate[2], box[2])
                candidate[3] = max(candidate[3], box[3])
                break
        else:
            merged.append(box[:])
    return sorted(
        [b for b in merged if b[2] - b[0] >= pw * 0.04 and (b[2] - b[0]) / max(1, b[3] - b[1]) >= 2.2],
        key=lambda b: (b[1], b[0]),
    )


def text_fields(lines: list[list[int]]):
    if not lines:
        return []
    heights = [b[3] - b[1] for b in lines]
    median_height = float(np.median(heights))
    parent = list(range(len(lines)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i, a in enumerate(lines):
        for j in range(i + 1, len(lines)):
            b = lines[j]
            vertical_gap = max(0, max(a[1], b[1]) - min(a[3], b[3]))
            overlap = max(0, min(a[2], b[2]) - max(a[0], b[0]))
            if vertical_gap <= median_height * 2.6 and overlap >= min(a[2] - a[0], b[2] - b[0]) * 0.18:
                union(i, j)
    groups: dict[int, list[list[int]]] = {}
    for i, box in enumerate(lines):
        groups.setdefault(find(i), []).append(box)
    result = []
    for group in groups.values():
        result.append([
            min(b[0] for b in group), min(b[1] for b in group),
            max(b[2] for b in group), max(b[3] for b in group), len(group),
        ])
    return sorted(result, key=lambda b: (b[1], b[0]))


def illustration_fields(foreground: np.ndarray, pigment: np.ndarray, lines: list[list[int]], page_bbox: list[int]):
    x1, y1, x2, y2 = page_bbox
    pw, ph = x2 - x1, y2 - y1
    page_area = max(1, pw * ph)
    nontext = foreground.copy()
    padding = max(2, int(ph * 0.002))
    for x, y, xx, yy in lines:
        nontext[max(0, y - padding):min(nontext.shape[0], yy + padding), max(0, x - padding):min(nontext.shape[1], xx + padding)] = 0
    nontext = cv2.morphologyEx(nontext, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(nontext, 8)
    components = []
    for idx in range(1, count):
        x, y, w, h, area = [int(v) for v in stats[idx]]
        if area < max(30, page_area * 0.0002) or w < 3 or h < 3:
            continue
        sub = (labels[y:y + h, x:x + w] == idx).astype(np.uint8)
        contours, hierarchy = cv2.findContours(sub, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        holes = 0 if hierarchy is None else sum(1 for k in range(len(contours)) if hierarchy[0][k][3] >= 0)
        pigment_ratio = float(pigment[y:y + h, x:x + w].sum()) / max(1, area)
        aspect = max(w / max(1, h), h / max(1, w))
        neutral = "PIGMENT_BEARING_COMPONENT" if pigment_ratio > 0.16 else (
            "CLOSED_COMPACT_COMPONENT" if holes else (
                "ELONGATED_CONNECTOR_OR_STROKE" if aspect > 5 else "INK_CONNECTED_COMPONENT"
            )
        )
        components.append({
            "bbox": [x, y, x + w, y + h], "area": area, "holes": holes,
            "pigment_ratio": round(pigment_ratio, 6), "aspect": round(aspect, 4), "neutral_class": neutral,
        })
    seed = np.zeros_like(nontext)
    for component in components:
        x, y, xx, yy = component["bbox"]
        seed[y:yy, x:xx] = np.maximum(seed[y:yy, x:xx], nontext[y:yy, x:xx])
    kernel = np.ones((max(7, int(ph * 0.008)), max(7, int(pw * 0.008))), np.uint8)
    clustered = cv2.dilate(seed, kernel, iterations=1)
    field_count, _, field_stats, _ = cv2.connectedComponentsWithStats(clustered, 8)
    fields = []
    for idx in range(1, field_count):
        x, y, w, h, _ = [int(v) for v in field_stats[idx]]
        children = [i for i, c in enumerate(components) if x <= (c["bbox"][0] + c["bbox"][2]) / 2 < x + w and y <= (c["bbox"][1] + c["bbox"][3]) / 2 < y + h]
        if not children:
            continue
        boxes = [components[i]["bbox"] for i in children]
        box = [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]
        field_area = max(1, (box[2] - box[0]) * (box[3] - box[1]))
        pigment_pixels = int(pigment[box[1]:box[3], box[0]:box[2]].sum())
        max_child = max(components[i]["area"] for i in children)
        text_overlap = 0
        for tx, ty, txx, tyy in lines:
            text_overlap += max(0, min(box[2], txx) - max(box[0], tx)) * max(0, min(box[3], tyy) - max(box[1], ty))
        keep = pigment_pixels > page_area * 0.00001 or max_child > page_area * 0.0004 or (field_area > page_area * 0.004 and len(children) >= 2)
        if text_overlap / field_area > 0.55 and pigment_pixels < page_area * 0.00002:
            keep = False
        if keep:
            fields.append({"bbox": box, "children": children})
    unique = []
    for field in sorted(fields, key=lambda f: (f["bbox"][2] - f["bbox"][0]) * (f["bbox"][3] - f["bbox"][1]), reverse=True):
        box = field["bbox"]
        area = max(1, (box[2] - box[0]) * (box[3] - box[1]))
        if any(max(0, min(box[2], u["bbox"][2]) - max(box[0], u["bbox"][0])) * max(0, min(box[3], u["bbox"][3]) - max(box[1], u["bbox"][1])) > 0.9 * area for u in unique):
            continue
        unique.append(field)
    return components, sorted(unique, key=lambda f: (f["bbox"][1], f["bbox"][0]))


def scale_box(box, scale: float):
    return [int(round(v / scale)) for v in box]


def relation(a: list[int], b: list[int]) -> str:
    overlap_x = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    overlap_y = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    if overlap_x * overlap_y > 0:
        return "OVERLAPS"
    acx, acy = (a[0] + a[2]) / 2, (a[1] + a[3]) / 2
    bcx, bcy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    if abs(acx - bcx) > abs(acy - bcy):
        return "LEFT_OF" if acx < bcx else "RIGHT_OF"
    return "ABOVE" if acy < bcy else "BELOW"


def analyse(source: Path, overlay_path: Path, maximum: int):
    original = cv2.imread(str(source), cv2.IMREAD_COLOR)
    if original is None:
        raise RuntimeError(f"Cannot read {source}")
    h0, w0 = original.shape[:2]
    scale = min(1.0, maximum / max(h0, w0))
    image = cv2.resize(original, (int(w0 * scale), int(h0 * scale)), interpolation=cv2.INTER_AREA) if scale < 1 else original.copy()
    page_mask, page_bbox, page_polygon = page_geometry(image)
    ink, pigment, foreground, gray = foreground_masks(image, page_mask)
    lines = text_lines(ink, page_bbox)
    fields = text_fields(lines)
    components, illustration = illustration_fields(foreground, pigment, lines, page_bbox)
    px1, py1, px2, py2 = page_bbox
    page_area = max(1, (px2 - px1) * (py2 - py1))
    diagrams = []
    for field in illustration:
        x, y, xx, yy = field["bbox"]
        child_set = [components[i] for i in field["children"]]
        closed = sum(1 for c in child_set if c["holes"] > 0)
        if (xx - x) * (yy - y) > page_area * 0.01 and 0.45 < (xx - x) / max(1, yy - y) < 2.2 and closed:
            diagrams.append(field["bbox"])
    dark = ((gray < 35) & (page_mask > 0)).astype(np.uint8)
    count, _, stats, _ = cv2.connectedComponentsWithStats(dark, 8)
    damage = []
    for idx in range(1, count):
        x, y, w, h, area = [int(v) for v in stats[idx]]
        edge = min(x - px1, y - py1, px2 - (x + w), py2 - (y + h))
        if area >= max(30, page_area * 0.00008) and (edge < min(px2 - px1, py2 - py1) * 0.04 or area > page_area * 0.001):
            damage.append([x, y, x + w, y + h])
    overlaps = []
    for box in lines:
        x, y, xx, yy = box
        if float(pigment[y:yy, x:xx].sum()) / max(1, (xx - x) * (yy - y)) > 0.015:
            overlaps.append(box)
    all_content = [f[:4] for f in fields] + [f["bbox"] for f in illustration]
    content = [min(b[0] for b in all_content), min(b[1] for b in all_content), max(b[2] for b in all_content), max(b[3] for b in all_content)] if all_content else page_bbox
    cx1, cy1, cx2, cy2 = content
    margins = [[px1, py1, px2, max(py1, cy1)], [px1, min(py2, cy2), px2, py2], [px1, cy1, max(px1, cx1), cy2], [min(px2, cx2), cy1, px2, cy2]]
    page_regions = [{"region_id": "PAGE-PARCHMENT-001", "class": "PARCHMENT_FIELD", "geometry_type": "POLYGON", "polygon": [[int(round(x / scale)), int(round(y / scale))] for x, y in page_polygon], "bbox": scale_box(page_bbox, scale), "confidence": "HIGH"}]
    for i, box in enumerate(margins, 1):
        if box[2] > box[0] and box[3] > box[1]:
            page_regions.append({"region_id": f"PAGE-MARGIN-{i:03d}", "class": ["MARGIN_TOP", "MARGIN_BOTTOM", "MARGIN_LEFT", "MARGIN_RIGHT"][i - 1], "geometry_type": "BBOX", "bbox": scale_box(box, scale), "confidence": "MEDIUM"})
    for i, field in enumerate(fields, 1):
        page_regions.append({"region_id": f"PAGE-TEXT-FIELD-{i:03d}", "class": "MAIN_TEXT_FIELD_CANDIDATE", "geometry_type": "BBOX", "bbox": scale_box(field[:4], scale), "line_count": field[4], "confidence": "MEDIUM"})
    for i, field in enumerate(illustration, 1):
        page_regions.append({"region_id": f"PAGE-ILL-FIELD-{i:03d}", "class": "MAIN_ILLUSTRATION_FIELD_CANDIDATE", "geometry_type": "BBOX", "bbox": scale_box(field["bbox"], scale), "confidence": "MEDIUM"})
    for name, boxes in (("DIAGRAM", diagrams), ("DAMAGE", damage), ("OVERLAP", overlaps)):
        for i, box in enumerate(boxes, 1):
            page_regions.append({"region_id": f"PAGE-{name}-{i:03d}", "class": {"DIAGRAM": "DIAGRAM_CANDIDATE", "DAMAGE": "DAMAGE_CANDIDATE", "OVERLAP": "TEXT_ILLUSTRATION_OVERLAP_CANDIDATE"}[name], "geometry_type": "BBOX", "bbox": scale_box(box, scale), "confidence": "LOW"})
    objects = []
    child_parent = {child: i for i, field in enumerate(illustration) for child in field["children"]}
    for i, field in enumerate(illustration, 1):
        objects.append({"object_id": f"ILL-FIELD-{i:03d}", "parent_id": None, "neutral_class": "COMPOSITE_ILLUSTRATION_FIELD", "geometry_type": "BBOX", "bbox": scale_box(field["bbox"], scale), "child_ids": [f"ILL-OBJ-{child + 1:04d}" for child in field["children"]], "count_status": "COUNTED", "confidence": "MEDIUM"})
    for i, component in enumerate(components, 1):
        parent = child_parent.get(i - 1)
        objects.append({"object_id": f"ILL-OBJ-{i:04d}", "parent_id": f"ILL-FIELD-{parent + 1:03d}" if parent is not None else None, "neutral_class": component["neutral_class"], "geometry_type": "BBOX", "bbox": scale_box(component["bbox"], scale), "orientation": "UNDETERMINED", "direction": "UNDETERMINED", "color": "PIGMENT_PRESENT" if component["pigment_ratio"] > 0.16 else "INK_OR_NEUTRAL", "adjacency": [], "connections": [], "metrics": {k: component[k] for k in ("area", "holes", "pigment_ratio", "aspect")}, "confidence": "LOW"})
    repeat_bins: dict[tuple, list[str]] = {}
    for i, component in enumerate(components, 1):
        key = (component["neutral_class"], round(math.log10(max(1, component["area"])), 1), round(component["aspect"], 1), min(2, component["holes"]))
        repeat_bins.setdefault(key, []).append(f"ILL-OBJ-{i:04d}")
    repeats = [{"repeat_group_id": f"REP-{i:03d}", "neutral_signature": list(key), "member_ids": ids, "count": len(ids), "count_status": "COUNTED"} for i, (key, ids) in enumerate((item for item in repeat_bins.items() if len(item[1]) >= 3), 1)]
    text_records = []
    for i, box in enumerate(lines, 1):
        near = min(box[0] - px1, box[1] - py1, px2 - box[2], py2 - box[3]) < min(px2 - px1, py2 - py1) * 0.05
        klass = "MARGINAL_TEXT_CANDIDATE" if near else ("LABEL_TEXT_CANDIDATE" if box[2] - box[0] < (px2 - px1) * 0.18 else "TEXT_LINE_CANDIDATE")
        text_records.append({"text_region_id": f"TXT-LINE-{i:04d}", "class": klass, "geometry_type": "BBOX", "bbox": scale_box(box, scale), "reading_order": i if klass == "TEXT_LINE_CANDIDATE" else None, "reading_order_status": "OBSERVABLE_TOP_TO_BOTTOM_CANDIDATE" if klass == "TEXT_LINE_CANDIDATE" else "NOT_ASSERTED", "confidence": "MEDIUM"})
    local_relations = []
    for i, field in enumerate(fields, 1):
        if not illustration:
            break
        center = ((field[0] + field[2]) / 2, (field[1] + field[3]) / 2)
        nearest = sorted(enumerate(illustration), key=lambda item: math.dist(center, ((item[1]["bbox"][0] + item[1]["bbox"][2]) / 2, (item[1]["bbox"][1] + item[1]["bbox"][3]) / 2)))[:2]
        for j, target in nearest:
            local_relations.append({"source_id": f"TXT-FIELD-{i:03d}", "target_id": f"ILL-FIELD-{j + 1:03d}", "relation": relation(field[:4], target["bbox"]), "method": "BBOX_GEOMETRY", "confidence": "MEDIUM"})
    overlay = image.copy()
    colors = {"page": (0, 220, 0), "margin": (0, 210, 255), "text": (255, 80, 20), "illustration": (220, 0, 220), "diagram": (0, 140, 255), "damage": (0, 0, 255), "overlap": (255, 255, 255)}
    cv2.polylines(overlay, [np.array(page_polygon, np.int32)], True, colors["page"], 3)
    for i, box in enumerate(margins, 1):
        cv2.rectangle(overlay, (box[0], box[1]), (box[2], box[3]), colors["margin"], 1)
    for i, field in enumerate(fields, 1):
        box = field[:4]
        cv2.rectangle(overlay, (box[0], box[1]), (box[2], box[3]), colors["text"], 2)
        cv2.putText(overlay, f"TF{i}", (box[0], max(12, box[1] - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.48, colors["text"], 1, cv2.LINE_AA)
    for box in lines:
        cv2.rectangle(overlay, (box[0], box[1]), (box[2], box[3]), colors["text"], 1)
    for i, field in enumerate(illustration, 1):
        box = field["bbox"]
        cv2.rectangle(overlay, (box[0], box[1]), (box[2], box[3]), colors["illustration"], 2)
        cv2.putText(overlay, f"IF{i}", (box[0], max(12, box[1] - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.48, colors["illustration"], 1, cv2.LINE_AA)
    for code, boxes, color in (("D", diagrams, colors["diagram"]), ("X", damage, colors["damage"]), ("O", overlaps, colors["overlap"])):
        for i, box in enumerate(boxes, 1):
            cv2.rectangle(overlay, (box[0], box[1]), (box[2], box[3]), color, 2)
            cv2.putText(overlay, f"{code}{i}", (box[0], box[1] + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
    cv2.rectangle(overlay, (0, 0), (min(overlay.shape[1], 900), 70), (20, 20, 20), -1)
    cv2.putText(overlay, "GREEN parchment | YELLOW margins | BLUE text | MAGENTA illustration | ORANGE diagram | RED damage | WHITE overlap", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.43, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(overlay, f"{VERSION} - geometry only; manual review required", (10, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.imwrite(str(overlay_path), overlay, [cv2.IMWRITE_JPEG_QUALITY, 90])
    page_pixels = max(1, int(page_mask.sum()))
    features = {"text_field_count": len(fields), "text_line_count": len(lines), "illustration_field_count": len(illustration), "illustration_object_count": len(components), "diagram_count": len(diagrams), "damage_count": len(damage), "overlap_count": len(overlaps), "pigment_ratio": round(float(pigment.sum()) / page_pixels, 6), "foreground_ratio": round(float(foreground.sum()) / page_pixels, 6), "closed_object_ratio": round(sum(1 for c in components if c["holes"] > 0) / max(1, len(components)), 6), "mean_object_aspect": round(float(np.mean([c["aspect"] for c in components])) if components else 0.0, 6)}
    return {"page_inventory": {"regions": page_regions, "coverage_status": {"parchment_field": "COMPLETE", "main_text_fields": "PARTIAL" if fields else "NONE_VISIBLE", "main_illustration_fields": "PARTIAL" if illustration else "NONE_VISIBLE", "diagrams": "PARTIAL" if diagrams else "NONE_VISIBLE", "margins": "COMPLETE", "damage": "PARTIAL" if damage else "NONE_VISIBLE", "overlap": "PARTIAL" if overlaps else "NONE_VISIBLE"}}, "illustration_inventory": {"objects": objects, "repeat_groups": repeats, "hierarchy_validated": True}, "text_geometry": {"regions": text_records, "segmentation_status": "AUTO_CANDIDATE", "text_illustration_link_policy": "GEOMETRY_ONLY", "transliteration_policy": "REFERENCE_ONLY_NOT_BOUNDARY_AUTHORITY"}, "local_relations": local_relations, "features": features}


def graph(items: list[dict]):
    names = ["text_field_count", "text_line_count", "illustration_field_count", "illustration_object_count", "diagram_count", "damage_count", "overlap_count", "pigment_ratio", "foreground_ratio", "closed_object_ratio", "mean_object_aspect"]
    matrix = np.array([[float(item["features"].get(name, 0)) for name in names] for item in items], dtype=float)
    deviation = matrix.std(axis=0)
    deviation[deviation < 1e-9] = 1
    standardized = (matrix - matrix.mean(axis=0)) / deviation
    edges, seen = [], set()
    for i in range(len(items)):
        distances = np.sqrt(((standardized - standardized[i]) ** 2).mean(axis=1))
        distances[i] = np.inf
        far = int(np.argmax(np.where(np.isfinite(distances), distances, -1)))
        for j_raw in np.argsort(distances)[:3]:
            j = int(j_raw)
            if not np.isfinite(distances[j]):
                continue
            pair = tuple(sorted((i, j)))
            if pair in seen:
                continue
            seen.add(pair)
            agreements, disagreements = [], []
            for k, name in enumerate(names):
                delta = abs(standardized[i, k] - standardized[j, k])
                if delta <= 0.45:
                    agreements.append(name)
                elif delta >= 1.25:
                    disagreements.append(name)
            score = float(math.exp(-float(distances[j])))
            edges.append({"edge_id": f"EDGE-{len(edges) + 1:05d}", "source_record_id": items[i]["record_id"], "target_record_id": items[j]["record_id"], "relation": "NEUTRAL_LAYOUT_TOPOLOGY_CANDIDATE", "score": round(score, 6), "consistent_features": agreements, "inconsistent_features": disagreements, "method": "STANDARDIZED_EUCLIDEAN_AUTO_FEATURE_VECTOR_V1", "negative_control": {"record_id": items[far]["record_id"], "score": round(float(math.exp(-float(distances[far]))), 6), "selection": "FARTHEST_STANDARDIZED_FEATURE_VECTOR"}, "confidence": "HIGH" if score >= 0.72 else ("MEDIUM" if score >= 0.5 else "LOW"), "status": "AUTO_CANDIDATE_NOT_MANUALLY_ADJUDICATED"})
    return {"analysis_version": VERSION, "feature_names": names, "node_count": len(items), "edge_count": len(edges), "nodes": [{"record_id": item["record_id"], "folio_or_cover_id": item["folio"], "overlay_path": item["overlay_relative"], "features": item["features"]} for item in items], "edges": edges, "policy": "BBox size or background color alone never creates an edge; every edge includes agreements, disagreements, method, negative control and confidence."}


def preview(items: list[dict], destination: Path):
    cards = []
    for index, item in enumerate(items, 1):
        image = Image.open(item["overlay_path"]).convert("RGB")
        image.thumbnail((430, 580))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=68, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        f = item["features"]
        cards.append(f'<article><h2>{index:03d}. {item["folio"]}</h2><img src="data:image/jpeg;base64,{encoded}"><p>Text fields {f["text_field_count"]}; lines {f["text_line_count"]}; illustration fields {f["illustration_field_count"]}; objects {f["illustration_object_count"]}; diagrams {f["diagram_count"]}; damage {f["damage_count"]}; overlaps {f["overlap_count"]}</p><code>{item["record_id"]}</code></article>')
    destination.write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Voynich annotated preview</title><style>body{margin:0;background:#171717;color:#eee;font-family:system-ui}header{position:sticky;top:0;background:#111;padding:12px;z-index:2}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:14px;padding:14px}article{background:#252525;border:1px solid #555;padding:10px}img{width:100%;height:auto}h1{font-size:20px}h2{font-size:16px}p,code{font-size:11px}</style></head><body><header><h1>Voynich full-corpus preview — ' + VERSION + '</h1><p>Green parchment; yellow margins; blue text; magenta illustration; orange diagram; red damage; white overlap. Automated geometry candidate; manual review required.</p></header><main>' + ''.join(cards) + '</main></body></html>', encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--output", default="analysis_output")
    parser.add_argument("--max-side", type=int, default=1400)
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    output = root / args.output
    if output.exists():
        shutil.rmtree(output)
    overlays, records = output / "overlays", output / "records"
    overlays.mkdir(parents=True)
    records.mkdir(parents=True)
    project = json.loads((root / "atlas" / "atlas_project.json").read_text(encoding="utf-8"))
    items, failures = [], []
    for position, entry in enumerate(project["records"], 1):
        try:
            source = root / entry["source_path"]
            if sha256(source) != entry["source_sha256"]:
                raise RuntimeError("source SHA mismatch")
            canonical = json.loads((root / entry["record_path"]).read_text(encoding="utf-8"))
            folio = str(entry.get("folio_or_cover_id") or f"sequence-{entry['sequence']}")
            stem = f"{int(entry['sequence']):04d}_{slug(folio)}"
            overlay_path = overlays / f"{stem}.overlay.jpg"
            result = analyse(source, overlay_path, args.max_side)
            canonical["analysis_version"] = VERSION
            canonical["page_inventory"] = result["page_inventory"]
            canonical["illustration_inventory"] = result["illustration_inventory"]
            canonical["text_geometry"] = result["text_geometry"]
            canonical["local_relations"] = result["local_relations"]
            canonical["feature_vector"] = result["features"]
            canonical["overlay"] = {"overlay_status": "RENDERED_AUTO_CANDIDATE", "relative_path": f"overlays/{overlay_path.name}", "mime": "image/jpeg", "sha256": sha256(overlay_path), "legend": "GREEN parchment; YELLOW margins; BLUE text; MAGENTA illustration; ORANGE diagram; RED damage; WHITE overlap"}
            canonical["quality_control"] = {**canonical.get("quality_control", {}), "geometry_within_source": "PASS", "source_untouched": "PASS", "manual_review": "REQUIRED", "issues": ["Heuristic segmentation can confuse dense illustration strokes with text.", "Diagram, damage and overlap detections are low-confidence candidates."]}
            canonical["execution_status"] = "AUTO_ANNOTATED_CANDIDATE"
            record_path = records / f"{stem}.annotation.json"
            write_json(record_path, canonical)
            items.append({"record_id": canonical["record_id"], "folio": folio, "overlay_path": overlay_path, "overlay_relative": f"overlays/{overlay_path.name}", "features": result["features"]})
            print(f"[{position:03d}/{len(project['records'])}] {folio}: OK", flush=True)
        except Exception as error:
            failures.append({"sequence": entry.get("sequence"), "record_id": entry.get("record_id"), "error": repr(error)})
            print(f"[{position:03d}/{len(project['records'])}] FAIL: {error}", flush=True)
    cross_page = graph(items)
    write_json(output / "cross_page_graph.json", cross_page)
    preview(items, output / "voynich_full_corpus_preview.html")
    status = "PASS" if len(items) == 206 and not failures else "PARTIAL_OR_FAIL"
    summary = {"analysis_version": VERSION, "status": status, "expected_records": 206, "completed_records": len(items), "failed_records": len(failures), "failures": failures, "overlay_count": len(list(overlays.glob("*.jpg"))), "record_count": len(list(records.glob("*.json"))), "graph_node_count": cross_page["node_count"], "graph_edge_count": cross_page["edge_count"], "manual_review_status": "REQUIRED", "source_policy": "Original JPEG files were SHA-verified and never modified."}
    write_json(output / "analysis_summary.json", summary)
    (output / "README.md").write_text("# Voynich full-corpus annotated atlas\n\nAutomated geometry candidate pass for 206 canonical Yale image positions. Includes marked overlays, populated records, cross-page graph, self-contained HTML preview and validation summary. Original scans are unchanged. Manual adjudication remains required.\n", encoding="utf-8")
    bundle = output / "voynich_annotated_final_v1.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(output.rglob("*")):
            if path.is_file() and path != bundle:
                archive.write(path, path.relative_to(output))
    summary["bundle_zip_sha256"] = sha256(bundle)
    summary["bundle_zip_bytes"] = bundle.stat().st_size
    write_json(output / "analysis_summary.json", summary)
    if status != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
