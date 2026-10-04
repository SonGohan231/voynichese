Failed to connect to bus: Operation not permitted
#!/usr/bin/env python3
"""Encrypt the full split and emit an opaque TRAIN/VALIDATION developer package."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import subprocess
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def opaque_id(seed: bytes, domain: str, value: str, length: int = 24) -> str:
    digest = hmac.new(seed, f"{domain}:{value}".encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:length]


def developer_record(
    record: dict[str, Any], split_name: str, seed: bytes
) -> tuple[dict[str, Any], dict[str, Any]]:
    original_record_id = record["record_id"]
    unit_id = "UNIT-" + opaque_id(seed, "record", original_record_id)
    object_map = {
        item["adjudicated_id"]: "OBJ-" + opaque_id(
            seed, f"object:{original_record_id}", item["adjudicated_id"], 20
        )
        for item in record["objects"]
    }
    objects = [{
        "object_id": object_map[item["adjudicated_id"]],
        "class": item["class"],
        "bbox": item["bbox"],
        "ports": item["ports"],
    } for item in record["objects"]]
    occlusions = [{
        "source_id": object_map[item["source_id"]],
        "target_id": object_map[item["target_id"]],
        "relation": item["relation"],
    } for item in record["occlusions"]]
    public = {
        "unit_id": unit_id,
        "split": split_name,
        "objects": objects,
        "occlusions": occlusions,
    }
    private = {
        "record_id": original_record_id,
        "unit_id": unit_id,
        "object_id_mapping": object_map,
    }
    return public, private


def cms_encrypt(plaintext: bytes, certificate: Path) -> bytes:
    process = subprocess.run(
        [
            "openssl", "cms", "-encrypt", "-binary", "-outform", "DER",
            "-aes-256-gcm", "-recip", str(certificate),
        ],
        input=plaintext,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise ValueError("custodian_encryption_failed:" + process.stderr.decode("utf-8", errors="replace"))
    return process.stdout


def seal_split(
    split: dict[str, Any],
    adjudication: dict[str, Any],
    seed: bytes,
    custodian_certificate: Path,
    output_directory: Path,
) -> dict[str, Any]:
    if len(seed) < 32:
        raise ValueError("split_seed_must_contain_at_least_32_bytes")
    if output_directory.exists():
        raise ValueError(f"refusing_to_overwrite_sealed_split:{output_directory}")
    certificate_bytes = custodian_certificate.read_bytes()
    by_id = {item["record_id"]: item for item in adjudication["records"]}
    developer_records = []
    private_mapping = {}
    for split_name in ("TRAIN", "VALIDATION"):
        for record_id in split["assignments"][split_name]:
            public, private = developer_record(by_id[record_id], split_name, seed)
            developer_records.append(public)
            private_mapping[public["unit_id"]] = private
    developer_records.sort(key=lambda item: (item["split"], item["unit_id"]))
    developer_package = {
        "schema_version": "1.0",
        "status": "ISOLATED_MODEL_DEVELOPMENT_PACKAGE",
        "experiment_id": "EXP-2026-001",
        "allowed_splits": ["TRAIN", "VALIDATION"],
        "contains_full_record_universe": False,
        "contains_source_paths": False,
        "contains_held_out_identifiers": False,
        "records": developer_records,
    }
    developer_bytes = (json.dumps(developer_package, indent=2, sort_keys=True) + "\n").encode("utf-8")
    secret_payload = {
        "schema_version": "1.0",
        "status": "CUSTODIAN_SECRET_SPLIT",
        "experiment_id": "EXP-2026-001",
        "seed_hex": seed.hex(),
        "split": split,
        "opaque_mapping": private_mapping,
        "adjudication_canonical_sha256": sha256_bytes(
            (json.dumps(adjudication, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        ),
    }
    secret_bytes = (json.dumps(secret_payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    ciphertext = cms_encrypt(secret_bytes, custodian_certificate)
    manifest = {
        "schema_version": "1.0",
        "status": "SEALED_SPLIT_READY",
        "experiment_id": "EXP-2026-001",
        "seed_commitment_sha256": sha256_bytes(seed),
        "assignments_commitment_sha256": split["assignments_sha256"],
        "group_counts": split["group_counts"],
        "developer_package": {
            "path": "model-development.json",
            "sha256": sha256_bytes(developer_bytes),
            "record_count": len(developer_records),
        },
        "custodian_ciphertext": {
            "path": "custodian-split.p7m",
            "format": "CMS-DER-AES-256-GCM",
            "sha256": sha256_bytes(ciphertext),
        },
        "custodian_certificate_sha256": sha256_bytes(certificate_bytes),
        "held_out_identifiers_public": False,
        "full_record_universe_public": False,
        "unlocks_held_out": False,
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    output_directory.mkdir(parents=True)
    try:
        for name, data in (
            ("model-development.json", developer_bytes),
            ("custodian-split.p7m", ciphertext),
            ("sealed-split-manifest.json", manifest_bytes),
        ):
            with (output_directory / name).open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        directory_fd = os.open(output_directory, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        for path in output_directory.iterdir():
            path.chmod(0o444)
        output_directory.chmod(0o555)
    except Exception:
        # Preserve partial output as evidence; never reuse the path.
        raise
    return manifest
