"""EXP-2026-002: independently reconstruct a fail-closed IT2a metadata audit.

Only original local byte files are accepted; no silent network fetch or raw redistribution.
The tool does NOT compute similarity, p-values, or scientific PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

IT_SHA256 = "7f27a8b0feed8f6de0a99900df6bf912dd1d295c38e5f830bac8b41c3f536fb5"
ZL_SHA256 = "bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc"
IT_PAGES = 225
ZL_PAGES = 227
FIELDS = ("quire", "bifolio_index", "lfd_hand", "currier_language", "illustration_type", "currier_hand")
PAGE = re.compile(r"^<([^.,<>\s]+)>\s*<!\s*(.*?)>")
LOCUS = re.compile(r"^<([^.,<>\s]+)\.([^,<>]+),([^<>]+)>\s*(.*)")
VAR = re.compile(r"\$([A-Z])=([^\s>]+)")
FOLIO = re.compile(r"^f(\d+)([rv])\d*$")
SECTIONS = (
    ("BOTANICAL", 1, 66),
    ("ASTRONOMICAL_ASTROLOGICAL", 67, 73),
    ("BIOLOGICAL", 75, 84),
    ("COSMOLOGICAL_MEDALLIONS", 85, 86),
    ("PHARMACEUTICAL", 87, 102),
    ("CONTINUOUS_TEXT_STAR_ENTRIES", 103, 117),
)


class DataGateError(ValueError):
    pass


def audited_bytes(path: Path, expected: str) -> str:
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise DataGateError(f"SHA256_MISMATCH:{path.name}:expected={expected}:observed={actual}")
    try:
        return raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise DataGateError(f"NOT_ASCII_IVTFF:{path.name}") from exc


def parse_ivtff(data: str) -> tuple[list[dict], dict[str, int]]:
    pages: list[dict] = []
    loci = Counter()
    current = None
    for line in data.splitlines():
        h = PAGE.match(line)
        if h:
            attrs = dict(VAR.findall(h.group(2)))
            if any(p["id"] == h.group(1) for p in pages):
                raise DataGateError("DUPLICATE_PAGE:" + h.group(1))
            current = {
                "id": h.group(1),
                "quire": attrs.get("Q"),
                "bifolio_index": attrs.get("B"),
                "lfd_hand": attrs.get("H"),
                "currier_language": attrs.get("L"),
                "illustration_type": attrs.get("I"),
                "currier_hand": attrs.get("C"),
                "paragraph_loci": 0,
                "paragraph_tokens_strict": 0,
                "uncertain_fragments": 0,
            }
            pages.append(current)
            continue
        l = LOCUS.match(line)
        if not l:
            continue
        if current is None or current["id"] != l.group(1):
            raise DataGateError("LOCUS_PAGE_MISMATCH:" + l.group(1))
        match = re.search("[PLCR]", l.group(3))
        if match is None:
            raise DataGateError("UNKNOWN_LOCUS_TYPE:" + l.group(3))
        kind = match.group()
        loci[kind] += 1
        if kind == "P":
            current["paragraph_loci"] += 1
            payload = re.sub(r"<[^>]*>", " ", l.group(4))
            payload = re.sub(r"\{[^}]*\}", " ", payload)
            fragments = [x for x in re.split(r"[.\s=/\-]+", payload) if x]
            valid = [x for x in fragments if re.fullmatch("[a-z]+", x)]
            current["paragraph_tokens_strict"] += len(valid)
            current["uncertain_fragments"] += len(fragments) - len(valid)
    return pages, dict(loci)


def group_pages(pages: list[dict]) -> dict[str, dict]:
    physical: dict[str, dict] = {}
    for position, page in enumerate(pages):
        f = FOLIO.fullmatch(page["id"])
        page["folio_leaf"] = "f" + f.group(1) if f else page["id"]
        page["section"] = next((name for name, lo, hi in SECTIONS if f and lo <= int(f.group(1)) <= hi), None)
        page["physical_id"] = (
            f"Q{page['quire']}-B{page['bifolio_index']}"
            if page["quire"] and page["bifolio_index"] else None
        )
        page["current_order_position"] = position
        if not page["physical_id"]:
            continue
        g = physical.setdefault(page["physical_id"], {
            "quire": page["quire"], "bifolio_index": page["bifolio_index"],
            "pages": [], "leaves": []
        })
        g["pages"].append(page["id"])
        if page["folio_leaf"] not in g["leaves"]:
            g["leaves"].append(page["folio_leaf"])
    return physical


def build_audit(it_text: str, zl_text: str) -> dict:
    it_pages, it_loci = parse_ivtff(it_text)
    zl_pages, zl_loci = parse_ivtff(zl_text)
    if len(it_pages) != IT_PAGES or len(zl_pages) != ZL_PAGES:
        raise DataGateError(f"PAGE_COVERAGE_CHANGED:IT={len(it_pages)}:ZL={len(zl_pages)}")
    zl_by = {p["id"]: p for p in zl_pages}
    differences = [
        {"page": p["id"], "field": f, "IT": p[f], "ZL": zl_by[p["id"]][f]}
        for p in it_pages if p["id"] in zl_by for f in FIELDS
        if p[f] != zl_by[p["id"]][f]
    ]
    missing_zl = sorted(set(zl_by) - {p["id"] for p in it_pages})
    if differences:
        raise DataGateError("METADATA_DISAGREEMENT:" + json.dumps(differences))
    if missing_zl != ["f116v", "fRos"] or any(p["id"] not in zl_by for p in it_pages):
        raise DataGateError(f"TRANSCRIPTION_COVERAGE_CHANGED:{missing_zl}")
    groups = group_pages(it_pages)
    if len(groups) != 52:
        raise DataGateError(f"BIFOLIO_COVERAGE_CHANGED:{len(groups)}")
    return {
        "schema": "exp-2026-002/independent-parser-v1",
        "status": {
            "source_integrity": "VERIFIED_BY_SHA256",
            "metadata_cross_transcription": "PASSED",
            "independent_codicology": "PENDING_EXPERT_REVIEW",
            "science": "INCONCLUSIVE_NOT_RUN"
        },
        "source_hashes": {"IT2a-n.txt": IT_SHA256, "ZL3b-n.txt": ZL_SHA256},
        "summary": {
            "it2a_pages": len(it_pages), "zl3b_pages": len(zl_pages),
            "it2a_folia": len({p["folio_leaf"] for p in it_pages}),
            "unique_physical_bifolios": len(groups),
            "missing_in_IT2a": missing_zl,
            "metadata_disagreements": len(differences),
            "missing_currier_language": sum(p["currier_language"] not in ("A", "B") for p in it_pages),
            "mixed_hand_pages": [p["id"] for p in it_pages if p["lfd_hand"] == "@"],
            "incomplete_bifolia": [
                {"id": k, "leaves": v["leaves"]}
                for k, v in groups.items() if len(v["leaves"]) != 2
            ],
            "it2a_loci": it_loci, "zl3b_loci": zl_loci,
            "strict_paragraph_tokens": sum(p["paragraph_tokens_strict"] for p in it_pages)
        },
        "physical_groups": groups, "pages": it_pages
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--it2a", type=Path, required=True)
    parser.add_argument("--zl3b", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    it_text = audited_bytes(args.it2a, IT_SHA256)
    zl_text = audited_bytes(args.zl3b, ZL_SHA256)
    report = build_audit(it_text, zl_text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
