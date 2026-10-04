Failed to connect to bus: Operation not permitted
#!/usr/bin/env python3
"""Verify the external receipt for a complete blind-annotation freeze."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from verify_acceptance_slot import verify_signature
from verify_annotation_freeze import verify_freeze


HEX64 = re.compile(r"^[0-9a-f]{64}$")
NAMESPACE = "voynich-research-os-freeze-receipt-v1"


def receipt_semantic_errors(receipt: dict[str, Any], identity: str) -> list[str]:
    errors = []
    constants = {
        "schema_version": "1.0",
        "state": "FREEZE_RECEIPTED_APPEND_ONLY",
        "experiment_id": "EXP-2026-001",
        "freeze_integrity_status": "LOCAL_FREEZE_INTEGRITY_VERIFIED",
        "custodian_identity": identity,
        "metrics_disclosed_before_receipt": False,
        "held_out_access": "FORBIDDEN",
    }
    for key, expected in constants.items():
        if receipt.get(key) != expected:
            errors.append(f"invalid_{key}")
    for key in ("acceptance_slot_id", "issued_at_utc", "registry_sequence"):
        if not isinstance(receipt.get(key), str) or not receipt[key].strip():
            errors.append(f"missing_{key}")
    for key in ("manifest_sha256", "commit_sha256"):
        if not isinstance(receipt.get(key), str) or not HEX64.fullmatch(receipt[key]):
            errors.append(f"invalid_{key}")
    if receipt.get("agreement_status") not in {
        "READY_FOR_ADJUDICATION", "INCONCLUSIVE_ANNOTATION_GATE_FAILED"
    }:
        errors.append("invalid_agreement_status")
    registry_uri = receipt.get("registry_uri")
    parsed = urlparse(registry_uri) if isinstance(registry_uri, str) else None
    if not parsed or parsed.scheme != "https" or not parsed.netloc:
        errors.append("invalid_registry_uri")
    supersedes = receipt.get("supersedes_receipt_sha256")
    if supersedes is not None and (not isinstance(supersedes, str) or not HEX64.fullmatch(supersedes)):
        errors.append("invalid_supersedes_receipt_sha256")
    return sorted(set(errors))


def verify_receipt(
    freeze_directory: Path,
    receipt_path: Path,
    signature_path: Path,
    allowed_signers_path: Path,
    identity: str,
) -> dict[str, Any]:
    freeze = verify_freeze(freeze_directory)
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes.decode("utf-8"))
    signature_valid, signature_detail = verify_signature(
        receipt_bytes, signature_path, allowed_signers_path, identity, NAMESPACE
    )
    errors = receipt_semantic_errors(receipt, identity)
    if freeze["status"] != "LOCAL_FREEZE_INTEGRITY_VERIFIED":
        errors.append("local_freeze_integrity_not_verified")
    else:
        comparisons = {
            "acceptance_slot_id": freeze["slot_id"],
            "manifest_sha256": freeze["manifest_sha256"],
            "commit_sha256": freeze["commit_sha256"],
            "agreement_status": freeze["agreement_status"],
        }
        for key, expected in comparisons.items():
            if receipt.get(key) != expected:
                errors.append(f"receipt_freeze_mismatch:{key}")
    if not signature_valid:
        errors.append("custodian_receipt_signature_invalid")
    verified = not errors
    ready = verified and receipt.get("agreement_status") == "READY_FOR_ADJUDICATION"
    return {
        "schema_version": "1.0",
        "status": "FREEZE_RECEIPT_VERIFIED" if verified else "FREEZE_RECEIPT_REJECTED",
        "acceptance_slot_id": receipt.get("acceptance_slot_id"),
        "registry_uri": receipt.get("registry_uri"),
        "registry_sequence": receipt.get("registry_sequence"),
        "signature_namespace": NAMESPACE,
        "signature_valid": signature_valid,
        "signature_detail": signature_detail,
        "local_freeze_status": freeze["status"],
        "manifest_sha256": freeze.get("manifest_sha256"),
        "commit_sha256": freeze.get("commit_sha256"),
        "agreement_status": receipt.get("agreement_status"),
        "ready_for_adjudication": ready,
        "errors": sorted(set(errors)),
        "promotes_to_ground_truth": False,
        "unlocks_held_out": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freeze_directory", type=Path)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("signature", type=Path)
    parser.add_argument("allowed_signers", type=Path)
    parser.add_argument("--identity", required=True)
    args = parser.parse_args()
    try:
        result = verify_receipt(
            args.freeze_directory, args.receipt, args.signature,
            args.allowed_signers, args.identity,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        result = {
            "schema_version": "1.0", "status": "FREEZE_RECEIPT_REJECTED",
            "errors": [f"verification_error:{error}"],
            "promotes_to_ground_truth": False, "unlocks_held_out": False,
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "FREEZE_RECEIPT_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
