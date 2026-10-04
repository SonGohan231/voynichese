#!/usr/bin/env python3
"""Build an isolated pseudonymized annotation handoff without folio-identifying metadata."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import shutil
import stat
from pathlib import Path
from typing import Any


MIN_SEED_BYTES = 32


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def require_private_seed(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError("seed must be a regular non-symlink file")
    if path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise ValueError("seed permissions must not grant group or other access")
    value = path.read_bytes()
    if len(value) < MIN_SEED_BYTES:
        raise ValueError("seed must contain at least 32 bytes")
    return value


def keyed_hex(seed: bytes, domain: str, value: str) -> str:
    return hmac.new(seed, f"{domain}:{value}".encode("utf-8"), hashlib.sha256).hexdigest()


def ensure_outside_bundle(bundle_dir: Path, custody_map_path: Path) -> None:
    bundle = bundle_dir.resolve()
    custody = custody_map_path.resolve()
    if custody == bundle or bundle in custody.parents:
        raise ValueError("custody map must be outside the annotator bundle")


def resolve_repo_relative_file(repo_root: Path, value: str, label: str) -> tuple[Path, str]:
    relative = Path(value)
    if relative.is_absolute():
        raise ValueError(f"{label} must be repository-relative")
    root = repo_root.resolve()
    candidate = (root / relative).resolve()
    try:
        normalized = candidate.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{label} escapes repository root") from error
    if not candidate.is_file():
        raise ValueError(f"{label} file is missing")
    return candidate, normalized.as_posix()


def build_handoff(
    repo_root: Path,
    canonical_packet_path: Path,
    ui_dir: Path,
    seed_path: Path,
    bundle_dir: Path,
    custody_map_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ensure_outside_bundle(bundle_dir, custody_map_path)
    if bundle_dir.exists():
        raise ValueError(f"refusing_to_overwrite_existing_bundle:{bundle_dir}")
    if custody_map_path.exists():
        raise ValueError(f"refusing_to_overwrite_existing_custody_map:{custody_map_path}")

    seed = require_private_seed(seed_path)
    packet_raw = canonical_packet_path.read_bytes()
    canonical_packet = json.loads(packet_raw.decode("utf-8"))
    records = canonical_packet.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("canonical packet records missing or empty")

    protocol_rel = canonical_packet.get("protocol_path")
    if not isinstance(protocol_rel, str) or not protocol_rel:
        raise ValueError("canonical packet protocol_path missing")
    protocol_source, protocol_rel = resolve_repo_relative_file(
        repo_root, protocol_rel, "canonical protocol"
    )
    if sha256_bytes(protocol_source.read_bytes()) != canonical_packet.get("protocol_sha256"):
        raise ValueError("protocol bytes do not match canonical packet")

    handoff_records = []
    custody_records = []
    copy_sources: dict[str, Path] = {}
    seen_opaque = set()
    for record in records:
        original_id = record.get("record_id")
        original_path = record.get("source_path")
        source_sha = record.get("source_sha256")
        if not all(isinstance(value, str) and value for value in (original_id, original_path, source_sha)):
            raise ValueError("canonical packet record is incomplete")
        source_file, original_path = resolve_repo_relative_file(
            repo_root, original_path, f"source image:{original_id}"
        )
        source_bytes = source_file.read_bytes()
        if sha256_bytes(source_bytes) != source_sha:
            raise ValueError(f"source image SHA-256 mismatch:{original_id}")

        opaque = "BLI-" + keyed_hex(seed, "record-id", f"{original_id}|{source_sha}")[:24]
        if opaque in seen_opaque:
            raise ValueError("opaque identifier collision")
        seen_opaque.add(opaque)
        copy_sources[opaque] = source_file
        source_commitment = keyed_hex(seed, "source-commitment", source_sha)
        extension = source_file.suffix.lower() or ".img"
        blinded_path = f"blind_images/{opaque}{extension}"

        handoff_records.append({
            "record_id": opaque,
            "source_path": blinded_path,
            "source_commitment_sha256": source_commitment,
            "width": record.get("width"),
            "height": record.get("height"),
        })
        custody_records.append({
            "opaque_record_id": opaque,
            "original_record_id": original_id,
            "original_source_path": original_path,
            "source_sha256": source_sha,
            "source_commitment_sha256": source_commitment,
            "bundled_source_path": blinded_path,
        })

    handoff_records.sort(
        key=lambda item: keyed_hex(seed, "record-order", item["record_id"])
    )
    universe = canonical_json([
        [item["record_id"], item["source_commitment_sha256"]]
        for item in handoff_records
    ])
    handoff_packet = {
        "schema_version": "1.0",
        "packet_id": canonical_packet["packet_id"] + "-BLINDED-HANDOFF",
        "purpose": canonical_packet.get("purpose", "INDEPENDENT_BLIND_ANNOTATION_EXP_2026_001"),
        "protocol_path": protocol_rel,
        "protocol_sha256": canonical_packet["protocol_sha256"],
        "record_universe_sha256": sha256_bytes(universe),
        "canonical_record_universe_sha256": canonical_packet["record_universe_sha256"],
        "canonical_packet_sha256": sha256_bytes(packet_raw),
        "record_count": len(handoff_records),
        "identity_exposure": "PSEUDONYMIZED_FOLIO_AND_SOURCE_METADATA",
        "forbidden_inputs": sorted(set(canonical_packet.get("forbidden_inputs", [])) | {
            "folio identity lookup",
            "section labels",
            "scribe labels",
        }),
        "records": handoff_records,
    }
    handoff_raw = (json.dumps(handoff_packet, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    custody_map = {
        "schema_version": "1.0",
        "experiment_id": "EXP-2026-001",
        "packet_id": canonical_packet["packet_id"],
        "canonical_packet_sha256": sha256_bytes(packet_raw),
        "handoff_packet_sha256": sha256_bytes(handoff_raw),
        "seed_commitment_sha256": sha256_bytes(seed),
        "record_count": len(custody_records),
        "sensitive": True,
        "records": sorted(custody_records, key=lambda item: item["opaque_record_id"]),
    }

    bundle_dir.mkdir(parents=True)
    try:
        target_ui = bundle_dir / "research_os/annotation/ui"
        shutil.copytree(ui_dir, target_ui)
        target_protocol = bundle_dir / protocol_rel
        target_protocol.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(protocol_source, target_protocol)
        packet_dir = bundle_dir / "research_os/annotation/packets"
        packet_dir.mkdir(parents=True, exist_ok=True)
        handoff_packet_path = packet_dir / "handoff.packet.json"
        handoff_packet_path.write_bytes(handoff_raw)

        for item in custody_records:
            source_file = copy_sources[item["opaque_record_id"]]
            target = bundle_dir / item["bundled_source_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target)
            if sha256_bytes(target.read_bytes()) != item["source_sha256"]:
                raise ValueError(f"copied source mismatch:{item['opaque_record_id']}")

        start = bundle_dir / "START_HERE.txt"
        start.write_text(
            "Serve this directory locally and open:\n"
            "research_os/annotation/ui/?packet=../packets/handoff.packet.json\n"
            "Do not provide the annotator with the custody map, repository, history, "
            "section/scribe tables, model outputs, predictions, or split information.\n",
            encoding="utf-8",
        )
        custody_map_path.parent.mkdir(parents=True, exist_ok=True)
        custody_map_path.write_text(
            json.dumps(custody_map, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        custody_map_path.chmod(0o600)
    except Exception:
        # Do not silently reuse a partial bundle after a failed build.
        raise

    return handoff_packet, custody_map


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", type=Path)
    parser.add_argument("canonical_packet", type=Path)
    parser.add_argument("ui_dir", type=Path)
    parser.add_argument("seed_file", type=Path)
    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument("custody_map", type=Path)
    args = parser.parse_args()
    try:
        packet, custody = build_handoff(
            args.repo_root, args.canonical_packet, args.ui_dir,
            args.seed_file, args.bundle_dir, args.custody_map,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "HANDOFF_BUILD_REFUSED", "error": str(error)}, indent=2))
        return 2
    print(json.dumps({
        "status": "BLINDED_HANDOFF_READY",
        "packet_id": packet["packet_id"],
        "record_count": packet["record_count"],
        "handoff_packet_sha256": custody["handoff_packet_sha256"],
        "custody_map": str(args.custody_map),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
