#!/usr/bin/env python3
"""Verify archived Yale JPEG *bytes*, not the manuscript's physical structure.

Downloads the existing immutable-ish GitHub scan branch by exact image paths,
computes SHA-256 over downloaded bytes, compares the July 2026 archival ledger,
and checks JPEG dimensions/header without changing source files. A match is
provenance/integrity evidence, NEVER a visual sewing/fold/collation assessment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
AUDIT_FILE = ROOT / "experiments" / "EXP-2026-002" / "yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"
CANVAS_FILE = ROOT / "experiments" / "EXP-2026-002" / "yale_iiif_canvas_group_crosswalk_2026-10-09.json"
REPO = "SonGohan231/voynichese"
BRANCH = "import-voynich-yale-scans-2026-07-23"
PRIORITY_OIDS = {"1006194", "1006195", "1006196", "1006197", "1006228", "1006229", "1006230", "1006231"}
MAX_IMAGE_BYTES = 64 * 1024 * 1024


def image_url(path: str) -> str:
    if not path.startswith("data/yale_hq_scans/") or ".." in path.split("/"):
        raise ValueError("Image path escapes archive")
    return "https://raw.githubusercontent.com/{}/{}/{}".format(
        REPO, BRANCH, urllib.parse.quote(path, safe="/")
    )


def dimensions_from_jpeg(payload: bytes) -> tuple[int, int]:
    if not payload.startswith(b"\xff\xd8"):
        raise ValueError("Missing JPEG start-of-image marker")
    pointer = 2
    while pointer < len(payload):
        if payload[pointer] != 0xFF:
            raise ValueError("Invalid JPEG marker at {}".format(pointer))
        while pointer < len(payload) and payload[pointer] == 0xFF:
            pointer += 1
        if pointer >= len(payload):
            break
        marker = payload[pointer]
        pointer += 1
        if marker in (0xD8, 0xD9, 0x01) or 0xD0 <= marker <= 0xD7:
            continue
        if pointer + 2 > len(payload):
            break
        seglen = struct.unpack_from(">H", payload, pointer)[0]
        if seglen < 2 or pointer + seglen > len(payload):
            raise ValueError("Invalid JPEG segment")
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            if seglen < 7:
                raise ValueError("Incomplete JPEG SOF")
            height, width = struct.unpack_from(">HH", payload, pointer + 3)
            return width, height
        if marker == 0xDA:
            break
        pointer += seglen
    raise ValueError("Missing readable JPEG frame header")


def fetch_bytes(url: str, attempts: int = 3) -> bytes:
    last = None
    for i in range(attempts):
        try:
            request = urllib.request.Request(url, headers={
                "User-Agent": "VoynichResearchOS-EXP002/2026 (+https://github.com/SonGohan231/voynichese)",
                "Accept": "image/jpeg",
            })
            with urllib.request.urlopen(request, timeout=105) as response:
                reported_type = response.headers.get("Content-Type", "")
                payload = response.read(MAX_IMAGE_BYTES + 1)
            if len(payload) > MAX_IMAGE_BYTES:
                raise ValueError("Source JPEG exceeds permitted size")
            if not payload.startswith(b"\xff\xd8"):
                raise ValueError("Not JPEG bytes (Content-Type {})".format(reported_type))
            return payload
        except Exception as exc:
            last = exc
            if i + 1 < attempts:
                time.sleep(2 + 4 * i)
    raise RuntimeError("Download failed after {} attempts: {}".format(attempts, last))


def run(mode: str, output: Path) -> dict:
    archive = json.loads(AUDIT_FILE.read_text(encoding="utf-8"))
    canvas = json.loads(CANVAS_FILE.read_text(encoding="utf-8"))
    if archive["science_status"] != "INCONCLUSIVE_NOT_RUN":
        raise ValueError("Scientific readiness contract changed")
    by_oid = {row["oid"]: row for row in canvas["image_canvases"]}
    files = archive["archive_files"]
    selected = ([row for row in files if row["canvas_oid"] in PRIORITY_OIDS]
                if mode == "priority" else files)
    if mode == "priority" and (len(selected) != 8 or
                                {row["canvas_oid"] for row in selected} != PRIORITY_OIDS):
        raise ValueError("Eight high-priority scan candidates not found")
    results = []
    for pos, item in enumerate(selected, 1):
        url = image_url(item["path"])
        entry = {"file": item["path"], "canvas_oid": item["canvas_oid"],
                 "folio_label": item["yale_label"], "url": url,
                 "source_expected_sha256": item["imported_reported_sha256"]}
        try:
            payload = fetch_bytes(url)
            digest = hashlib.sha256(payload).hexdigest()
            width, height = dimensions_from_jpeg(payload)
            source_canvas = by_oid[item["canvas_oid"]]
            expected_dims = [source_canvas["width"], source_canvas["height"]]
            observed_dims = [width, height]
            entry.update(downloaded_byte_count=len(payload),
                         recomputed_sha256=digest,
                         reported_bytes_match=len(payload) == item["bytes_from_import_report"],
                         sha256_match=digest == item["imported_reported_sha256"],
                         image_size=observed_dims,
                         yale_manifest_dimensions=expected_dims,
                         dimensions_match=(expected_dims == observed_dims) if
                         all(v is not None for v in expected_dims) else None)
            entry["valid"] = bool(entry["reported_bytes_match"] and
                                  entry["sha256_match"] and
                                  entry["dimensions_match"] is not False)
        except Exception as exc:
            entry.update(valid=False, error=type(exc).__name__ + ": " + str(exc))
        results.append(entry)
        print("[{}/{}] {} {}".format(pos, len(selected), entry["folio_label"],
                                      "PASS" if entry["valid"] else "FAIL"), flush=True)

    result = {
        "schema": "exp-2026-002/archived-yale-jpeg-binary-integrity-v1",
        "status": ("VERIFIED_ARCHIVAL_BYTES_ONLY" if all(x["valid"] for x in results)
                   else "INTEGRITY_CHECK_FAILED"),
        "mode": mode, "source_branch": BRANCH,
        "source_archival_ledger": str(AUDIT_FILE.relative_to(ROOT)),
        "count_checked": len(results),
        "passed": sum(1 for x in results if x["valid"]),
        "failed": sum(1 for x in results if not x["valid"]),
        "pixel_semantics_or_codicology_review": "NOT_PERFORMED",
        "historical_original_order": "UNKNOWN",
        "science_status": "INCONCLUSIVE_NOT_RUN",
        "files": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "checked": result["count_checked"],
                      "passed": result["passed"], "failed": result["failed"]},
                     ensure_ascii=False))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("priority", "all"), default="priority")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        r = run(args.mode, args.output)
        sys.exit(0 if r["failed"] == 0 else 2)
    except Exception as e:
        print("ARCHIVE_INTEGRITY_FATAL: {}".format(e), file=sys.stderr)
        sys.exit(2)
