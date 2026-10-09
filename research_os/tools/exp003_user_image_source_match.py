#!/usr/bin/env python3
"""EXP-2026-003: candidate-only fingerprint matching against sha-verified Yale JPEG archive.

Output identifies which archived image should be inspected next. It makes NO
semantic claim, does not validate added arrows or inferred flow, and never
uses these same user-selected images as held-out scientific confirmation.
"""
import argparse
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP2 = ROOT / "experiments" / "EXP-2026-002"
EXP3 = ROOT / "experiments" / "EXP-2026-003"
ARCHIVE_BRANCH = "import-voynich-yale-scans-2026-07-23"
ARCHIVE_REPO = "SonGohan231/voynichese"
VARIANTS = ("full", "center80", "top55", "bottom55")
DEFAULT_OUT = EXP3 / "user_image_source_match_pilot_2026-10-09.json"


def phash(gray):
    """64-bit global low-frequency perceptual hash; 32x32 / 8x8 DCT."""
    normalized = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    freq = cv2.dct(normalized)[:8, :8]
    threshold = float(np.median(freq.ravel()[1:]))
    packed = 0
    for bit in (freq > threshold).ravel():
        packed = (packed << 1) | int(bit)
    return f"{packed:016x}"


def signatures(bgr):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    return {
        "full": phash(gray),
        "center80": phash(gray[int(0.1*h):int(0.9*h), int(0.1*w):int(0.9*w)]),
        "top55": phash(gray[:int(.55*h), :]),
        "bottom55": phash(gray[int(.45*h):, :]),
    }


def hamming(a, b):
    if not (isinstance(a, str) and isinstance(b, str)
            and re.fullmatch(r"[0-9a-f]{16}", a)
            and re.fullmatch(r"[0-9a-f]{16}", b)):
        raise ValueError("Expected two lowercase 64-bit hexadecimal fingerprints")
    return (int(a, 16) ^ int(b, 16)).bit_count()


def compare(query, source):
    distances = {k: hamming(query[k], source[k]) for k in query if k in source}
    if not distances:
        raise ValueError("No compatible source fingerprint variants")
    # Comparisons are heuristic candidate discovery, not calibrated probabilities.
    weights = {"full": 3, "center80": 2, "top55": 1, "bottom55": 1}
    numerator = sum(weights[k] * d for k, d in distances.items())
    denominator = sum(weights[k] for k in distances)
    return {"weighted_hamming": round(numerator/denominator, 3),
            "per_variant_hamming": distances}


def download_jpeg(entry, retries=3):
    path = entry["path"]
    if not path.startswith("data/yale_hq_scans/") or ".." in path.split("/"):
        raise ValueError("Invalid archive path")
    url = ("https://raw.githubusercontent.com/" + ARCHIVE_REPO + "/" + ARCHIVE_BRANCH
           + "/" + urllib.parse.quote(path, safe="/"))
    last_error = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "VoynichEXP003SourceMatch/1.0"})
            with urllib.request.urlopen(req, timeout=80) as res:
                data = res.read(30_000_001)
            if len(data) > 30_000_000:
                raise ValueError("Archived image too large")
            digest = hashlib.sha256(data).hexdigest()
            if digest != entry["imported_reported_sha256"]:
                raise ValueError("SHA256_MISMATCH")
            bgr = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
            if bgr is None:
                raise ValueError("JPEG_DECODE_FAILURE")
            return bgr, digest
        except Exception as ex:
            last_error = ex
            if i < retries - 1:
                time.sleep(1.5 * (i + 1))
    raise RuntimeError(str(last_error))


def run(crosswalk, targets, out, limit=None):
    archive = json.loads(Path(crosswalk).read_text(encoding="utf-8"))
    queries = json.loads(Path(targets).read_text(encoding="utf-8"))
    if queries.get("schema") != "voynich-exp003-user-phash-v1":
        raise ValueError("Unexpected user fingerprint schema")
    rows, seen = [], set()
    for entry in archive["archive_files"]:
        oid = entry["canvas_oid"]
        if oid in seen:
            continue
        seen.add(oid)
        rows.append(entry)
    if limit is not None:
        rows = rows[:limit]
    scored = {q["id"]: [] for q in queries["images"]}
    for q in queries["images"]:
        for part in q.get("regions", []):
            scored[q["id"] + "/" + part["id"]] = []
    audited, failed = [], []
    for i, entry in enumerate(rows):
        try:
            bgr, digest = download_jpeg(entry)
            h, w = bgr.shape[:2]
            shrink = min(1., 1150. / max(h, w))
            if shrink < 1:
                bgr = cv2.resize(bgr, (max(1, int(w*shrink)), max(1, int(h*shrink))),
                                 interpolation=cv2.INTER_AREA)
            sig = signatures(bgr)
            audited.append({"canvas_oid":entry["canvas_oid"],"folio_label":entry["yale_label"],
                            "sha256":digest,"source_file":entry["path"],
                            "native_dimensions_px":[w,h]})
            for q in queries["images"]:
                for key, part in [(q["id"], q)] + [
                    (q["id"] + "/" + reg["id"], reg) for reg in q.get("regions", [])
                ]:
                    candidate = compare(part["variants"], sig)
                    scored[key].append({**candidate, "canvas_oid":entry["canvas_oid"],
                                        "folio_label":entry["yale_label"],
                                        "source_image_sha256":digest,
                                        "source_image_path":entry["path"]})
        except Exception as ex:
            failed.append({"path":entry["path"],"error":str(ex)[:160]})
        if (i + 1) % 25 == 0:
            print("ARCHIVE_PROGRESS", i + 1, "/", len(rows), "processed", len(audited),
                  "failures",len(failed), flush=True)
    rankings = {}
    for key, hits in scored.items():
        hits.sort(key=lambda v: (v["weighted_hamming"], v["folio_label"],v["canvas_oid"]))
        rankings[key] = {
            "scored_candidates":len(hits),
            "top10":hits[:10],
            "rank_gap_first_second":round(hits[1]["weighted_hamming"] -
                hits[0]["weighted_hamming"],3) if len(hits)>1 else None,
            "source_identification": "CANDIDATE_ONLY_NOT_HUMAN_CONFIRMED",
        }
    result = {
        "schema":"voynich-exp003-image-source-phash-ranking-v1",
        "scientific_verdict":"INCONCLUSIVE_NOT_RUN",
        "technical_status":"COMPLETE" if not failed and len(audited)==len(rows) else "SOURCE_INCOMPLETE",
        "input_phash_manifest_sha256":hashlib.sha256(Path(targets).read_bytes()).hexdigest(),
        "archive_crosswalk_sha256":hashlib.sha256(Path(crosswalk).read_bytes()).hexdigest(),
        "archive_images_scheduled":len(rows),"archive_images_hash_verified":len(audited),
        "failed_archive_entries":failed,
        "archived_provenance_digest_policy":"verified each JPEG against archived import SHA256",
        "hypothesis_blinding":"NONE: exploratory uploaded images were previously inspected by user",
        "limitations":["pHash is a lossy image-likeness candidate rank, not an authenticated source match",
                       "user modern arrows/notes remain in fingerprint; no inpainting",
                       "high-res pixels were decoded but matching signatures were derived from 1150px max-side working copies",
                       "multiple dependent views of one foldout are not independent observations",
                       "no directed edges, depth or semantic meanings tested here"],
        "rankings":rankings,
    }
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)+"\n",
                   encoding="utf-8")
    print("MATCH_REPORT",out,"STATUS",result["technical_status"],
          "VERIFIED",len(audited),"FAILED",len(failed),flush=True)
    for key,v in rankings.items():
        top=v["top10"][:3]
        print("QUERY",key,[(c["folio_label"], c["weighted_hamming"]) for c in top],flush=True)
    return 0 if result["technical_status"]=="COMPLETE" else 2


def selftest():
    img = np.zeros((120, 80, 3), dtype=np.uint8)
    cv2.circle(img, (40, 55), 15, (255, 255, 255), -1)
    expected = signatures(img)
    assert all(re.fullmatch(r"[0-9a-f]{16}", s) for s in expected.values())
    assert expected == signatures(img.copy())
    assert hamming("0000000000000000", "ffffffffffffffff")==64
    assert compare(expected,expected)["weighted_hamming"]==0
    print("SELFTEST PASS: deterministic signature, hex, hamming, exact ranking")


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--crosswalk", default=str(EXP2 / "yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"))
    parser.add_argument("--targets", default=str(EXP3 / "user_six_image_phash_2026-10-09.json"))
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    parser.add_argument("--limit",type=int,default=None)
    parser.add_argument("--selftest",action="store_true")
    args=parser.parse_args()
    if args.selftest:
        selftest()
    else:
        raise SystemExit(run(args.crosswalk,args.targets,args.output,args.limit))
