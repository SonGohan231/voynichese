#!/usr/bin/env python3
"""Verify an independently signed external-registry witness for a custodian receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from verify_acceptance_slot import verify_signature


HEX64 = re.compile(r"^[0-9a-f]{64}$")
NAMESPACE = "voynich-research-os-registry-witness-v1"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def witness_semantic_errors(
    witness: dict[str, Any],
    expected_identity: str,
    custodian_identity: str,
) -> list[str]:
    errors = []
    constants = {
        "schema_version": "1.0",
        "state": "EXTERNAL_REGISTRY_WITNESS",
        "experiment_id": "EXP-2026-001",
        "registry_identity": expected_identity,
    }
    for key, expected in constants.items():
        if witness.get(key) != expected:
            errors.append(f"invalid_{key}")
    if expected_identity == custodian_identity:
        errors.append("registry_identity_must_differ_from_custodian")
    for key in ("registry_sequence", "recorded_at_utc"):
        if not isinstance(witness.get(key), str) or not witness[key].strip():
            errors.append(f"missing_{key}")
    for key in ("receipt_sha256", "receipt_signature_sha256"):
        if not isinstance(witness.get(key), str) or not HEX64.fullmatch(witness[key]):
            errors.append(f"invalid_{key}")
    registry_uri = witness.get("registry_uri")
    parsed = urlparse(registry_uri) if isinstance(registry_uri, str) else None
    if not parsed or parsed.scheme != "https" or not parsed.netloc:
        errors.append("invalid_registry_uri")
    previous = witness.get("previous_witness_sha256")
    if previous is not None and (
        not isinstance(previous, str) or not HEX64.fullmatch(previous)
    ):
        errors.append("invalid_previous_witness_sha256")
    return sorted(set(errors))


def verify_registry_witness(
    receipt_bytes: bytes,
    receipt: dict[str, Any],
    receipt_signature_bytes: bytes,
    witness_path: Path,
    witness_signature_path: Path,
    allowed_signers_path: Path,
    registry_identity: str,
    custodian_identity: str,
) -> dict[str, Any]:
    witness_bytes = witness_path.read_bytes()
    witness = json.loads(witness_bytes.decode("utf-8"))
    signature_valid, signature_detail = verify_signature(
        witness_bytes,
        witness_signature_path,
        allowed_signers_path,
        registry_identity,
        NAMESPACE,
    )
    errors = witness_semantic_errors(
        witness, registry_identity, custodian_identity
    )
    comparisons = {
        "registry_uri": receipt.get("registry_uri"),
        "registry_sequence": receipt.get("registry_sequence"),
        "receipt_sha256": sha256_bytes(receipt_bytes),
        "receipt_signature_sha256": sha256_bytes(receipt_signature_bytes),
    }
    for key, expected in comparisons.items():
        if witness.get(key) != expected:
            errors.append(f"registry_witness_receipt_mismatch:{key}")
    if not signature_valid:
        errors.append("registry_witness_signature_invalid")
    verified = not errors
    return {
        "schema_version": "1.0",
        "status": "REGISTRY_WITNESS_VERIFIED" if verified else "REGISTRY_WITNESS_REJECTED",
        "registry_identity": registry_identity,
        "registry_uri": witness.get("registry_uri"),
        "registry_sequence": witness.get("registry_sequence"),
        "witness_sha256": sha256_bytes(witness_bytes),
        "signature_namespace": NAMESPACE,
        "signature_valid": signature_valid,
        "signature_detail": signature_detail,
        "errors": sorted(set(errors)),
        "unlocks_held_out": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("receipt_signature", type=Path)
    parser.add_argument("witness", type=Path)
    parser.add_argument("witness_signature", type=Path)
    parser.add_argument("allowed_signers", type=Path)
    parser.add_argument("--registry-identity", required=True)
    parser.add_argument("--custodian-identity", required=True)
    args = parser.parse_args()
    try:
        receipt_bytes = args.receipt.read_bytes()
        receipt = json.loads(receipt_bytes.decode("utf-8"))
        result = verify_registry_witness(
            receipt_bytes,
            receipt,
            args.receipt_signature.read_bytes(),
            args.witness,
            args.witness_signature,
            args.allowed_signers,
            args.registry_identity,
            args.custodian_identity,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        result = {
            "schema_version": "1.0",
            "status": "REGISTRY_WITNESS_REJECTED",
            "errors": [f"verification_error:{error}"],
            "unlocks_held_out": False,
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "REGISTRY_WITNESS_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
