#!/usr/bin/env python3
"""Exploratory Voynich section-locality diagnostic.

Non-confirmatory, separate from EXP-2026-001 and the sealed HELD-OUT workflow.
Input ZL3b IVTFF from the original transcription maintainer or a byte-identical copy.
Uses only the Python standard library; never reads or writes sealed split records.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

PAGE = re.compile(r"^<(f\d+[rv]\d*)>\s*<!\s*(.*?)>")
LOCUS = re.compile(r"^<(f(\d+)[rv]\d*)\.([^>]+)>\s+(.+)")
FOLIO_RECORD = re.compile(r"-(\d+)[rv]")
LANG = re.compile(r"\$L=([A-Z@])")
PROSE = re.compile(r",[@+*=]P[0t]")
TAG = re.compile(r"<[^>]*>")
WORD = re.compile(r"^[a-z]{2,25}$")


def parse(transcription: str, manifest: dict) -> tuple[list[dict], dict]:
    folios: dict[int, dict] = {}
    for record in manifest["records"]:
        match = FOLIO_RECORD.search(record["record_id"])
        if not match:
            continue
        num = int(match.group(1))
        if num not in folios:
            folios[num] = {
                "num": num, "section": record["section_label"],
                "hands": set(), "tokens": [], "languages": set(),
                "features": Counter(),
            }
        folios[num]["hands"].add(record["scribe_label"])
        if folios[num]["section"] != record["section_label"]:
            raise ValueError(f"section conflict for numbered folio {num}")

    lang_by_side: dict[str, str] = {}
    line_count = prose_count = raw_tokens = clean_tokens = 0
    for line in transcription.splitlines():
        header = PAGE.match(line)
        if header:
            lang_match = LANG.search(header.group(2))
            if lang_match:
                lang_by_side[header.group(1)] = lang_match.group(1)
            continue
        locus = LOCUS.match(line)
        if not locus:
            continue
        line_count += 1
        side, folio_num, code, line_text = locus.groups()
        folio = folios.get(int(folio_num))
        if not folio or not PROSE.search(code):
            continue
        prose_count += 1
        if side in lang_by_side:
            folio["languages"].add(lang_by_side[side])
        pieces = [word for word in re.split(r"[.\s]+", TAG.sub(" ", line_text)) if word]
        raw_tokens += len(pieces)
        for word in pieces:
            if not WORD.fullmatch(word):
                continue
            clean_tokens += 1
            folio["tokens"].append(word)
            folio["features"]["p:" + word[:2]] += 1
            folio["features"]["s:" + word[-2:]] += 1

    for f in folios.values():
        f["hand"] = next(iter(f["hands"])) if len(f["hands"]) == 1 else "MIXED"
        f["language"] = next(iter(f["languages"])) if len(f["languages"]) == 1 else "MIXED"
        del f["hands"], f["languages"]
        norm = math.sqrt(sum(n * n for n in f["features"].values())) or 1.0
        f["features"] = {k: n / norm for k, n in f["features"].items()}

    eligible = [
        folios[k] for k in sorted(folios)
        if len(folios[k]["tokens"]) >= 40
        and folios[k]["language"] in {"A", "B"}
        and not folios[k]["hand"].startswith("MIXED")
    ]
    audit = {
        "atlasRecords": len(manifest["records"]),
        "folioGroups": len(folios),
        "ivttfTextLoci": line_count,
        "proseLineCount": prose_count,
        "proseTokensBeforeFiltering": raw_tokens,
        "cleanTokens": clean_tokens,
        "foliosUsable": len(eligible),
        "foliosExcluded": len(folios) - len(eligible),
    }
    return eligible, audit


def cosine(a: dict, b: dict) -> float:
    x, y = (a, b) if len(a) <= len(b) else (b, a)
    return sum(v * y.get(k, 0.0) for k, v in x.items())


def pair_data(eligible: list[dict]) -> list[tuple[int, int, float]]:
    pairs = []
    for i, a in enumerate(eligible):
        for j in range(i + 1, len(eligible)):
            b = eligible[j]
            if a["hand"] != b["hand"] or a["language"] != b["language"]:
                continue
            if abs(a["num"] - b["num"]) < 5:
                continue
            pairs.append((i, j, cosine(a["features"], b["features"])))
    return pairs


def effect(labels: list[str], pairs: list[tuple[int, int, float]]) -> dict:
    same_sum = cross_sum = 0.0
    same_n = cross_n = 0
    for i, j, similarity in pairs:
        if labels[i] == labels[j]:
            same_sum += similarity
            same_n += 1
        else:
            cross_sum += similarity
            cross_n += 1
    mean_same = same_sum / same_n if same_n else None
    mean_cross = cross_sum / cross_n if cross_n else None
    delta = mean_same - mean_cross if same_n and cross_n else None
    return {
        "meanSame": mean_same, "meanDifferent": mean_cross,
        "withinPairs": same_n, "crossPairs": cross_n, "delta": delta
    }


def run(transcription: str, manifest: dict, count: int = 999, seed: int = 1729) -> dict:
    eligible, audit = parse(transcription, manifest)
    pairs = pair_data(eligible)
    labels = [folio["section"] for folio in eligible]
    strata: dict[str, list[int]] = {}
    for i, f in enumerate(eligible):
        strata.setdefault(f["hand"] + "|" + f["language"], []).append(i)
    observed = effect(labels, pairs)
    if observed["delta"] is None:
        raise ValueError("No same- and cross-section pairs remain after controls")

    state = seed & 0xFFFFFFFF

    def random() -> float:
        nonlocal state
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        return state / 4294967296.0

    exceed = valid = 0
    for _ in range(count):
        perm = labels[:]
        for indices in strata.values():
            values = [labels[i] for i in indices]
            for k in range(len(values) - 1, 0, -1):
                j = math.floor(random() * (k + 1))
                values[k], values[j] = values[j], values[k]
            for i, v in zip(indices, values):
                perm[i] = v
        null_delta = effect(perm, pairs)["delta"]
        if null_delta is not None:
            valid += 1
            if null_delta >= observed["delta"] - 1e-12:
                exceed += 1

    audit["totalPairs"] = len(pairs)
    audit["strata"] = [
        {
            "stratum": name, "folios": len(indices),
            "sections": dict(Counter(labels[i] for i in indices)),
        } for name, indices in strata.items()
    ]
    return {
        "analysis": "EXPLORATORY / NOT EXP-2026-001",
        "method": {
            "unit": "numbered folio",
            "features": "2-glyph token prefixes and suffixes, l2-normalized",
            "inclusion": "P0/Pt text, strict a-z 2-25 tokens, >=40 per folio",
            "pairRestriction": "same hand and Currier language, folio-number gap>=5",
            "permutations": count,
            "randomSeed": seed,
            "test": "stratified folio-label permutation",
            "notPreregistered": True,
        },
        "audit": audit, "observed": observed,
        "permutationsValid": valid, "pExploratory": (1 + exceed) / (1 + valid),
        "warnings": [
            "Exploratory p is not confirmatory evidence.",
            "A numbered folio is not necessarily a physical bifolio or independent leaf group.",
            "Hand/section and language/section confounding may remain.",
            "Confirm source hashes, parser fidelity and holdout independence before replication."
        ]
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--transcription", type=Path, required=True)
    p.add_argument("--strata", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--permutations", type=int, default=999)
    p.add_argument("--seed", type=int, default=1729)
    args = p.parse_args()
    if args.permutations < 1:
        p.error("--permutations must be >=1")
    source = args.transcription.read_bytes()
    meta = args.strata.read_bytes()
    result = run(source.decode("utf-8"), json.loads(meta), args.permutations, args.seed)
    result["source"] = {
        "transcriptionSha256": hashlib.sha256(source).hexdigest(),
        "strataSha256": hashlib.sha256(meta).hexdigest(),
        "transcriptionPath": str(args.transcription),
        "strataPath": str(args.strata),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"observed": result["observed"], "pExploratory": result["pExploratory"], "audit": result["audit"]}, indent=2))


if __name__ == "__main__":
    main()
