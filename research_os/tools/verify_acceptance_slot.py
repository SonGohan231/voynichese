#!/usr/bin/env python3
"""Verify a custodian-signed, single-pair blind-annotation slot."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any


HEX64 = re.compile(r"^[0-9a-f]{64}$")
NAMESPACE = "voynich-research-os-acceptance-slot-v1"


def semantic_errors(slot: dict[str, Any], expected_identity: str) -> list[str]:
    errors = []
    constants = {
        "schema_version": "1.0",
        "state": "SEALED_BEFORE_COLLECTION",
        "experiment_id": "EXP-2026-001",
        "max_accepted_pairs": 1,
        "metrics_disclosure_policy": "AFTER_LOCAL_FREEZE_COMMIT",
        "held_out_access": "FORBIDDEN",
        "custodian_identity": expected_identity,
    }
    for key, expected in constants.items():
        if slot.get(key) != expected:
            errors.append(f"invalid_{key}")
    for key in ("annotation_round", "acceptance_slot_id", "sealed_at_utc"):
        if not isinstance(slot.get(key), str) or not slot[key].strip():
            errors.append(f"missing_{key}")
    for key in ("protocol_sha256", "record_universe_sha256"):
        if not isinstance(slot.get(key), str) or not HEX64.fullmatch(slot[key]):
            errors.append(f"invalid_{key}")

    output = slot.get("output_path")
    if not isinstance(output, str):
        errors.append("invalid_output_path")
    else:
        parsed = PurePosixPath(output)
        if parsed.is_absolute() or ".." in parsed.parts or not output.startswith("research_os/runs/EXP-2026-001/"):
            errors.append("unsafe_output_path")

    packets = slot.get("packets")
    if not isinstance(packets, dict) or set(packets) != {"A", "B"}:
        errors.append("invalid_packets")
    else:
        for role in ("A", "B"):
            packet = packets[role]
            if not isinstance(packet, dict) or not packet.get("packet_id") or not HEX64.fullmatch(str(packet.get("sha256", ""))):
                errors.append(f"invalid_packet_{role}")

    bindings = slot.get("annotator_bindings")
    if not isinstance(bindings, list) or len(bindings) != 2:
        errors.append("invalid_annotator_bindings")
    else:
        roles = {item.get("role") for item in bindings if isinstance(item, dict)}
        commitments = [item.get("annotator_id_sha256") for item in bindings if isinstance(item, dict)]
        if roles != {"A", "B"}:
            errors.append("annotator_roles_not_a_b")
        if len(commitments) != 2 or any(not isinstance(value, str) or not HEX64.fullmatch(value) for value in commitments):
            errors.append("invalid_annotator_id_hash")
        elif len(set(commitments)) != 2:
            errors.append("annotator_id_hashes_not_distinct")
    return sorted(set(errors))


def verify_signature(
    slot_bytes: bytes,
    signature_path: Path,
    allowed_signers_path: Path,
    identity: str,
    namespace: str = NAMESPACE,
) -> tuple[bool, str]:
    process = subprocess.run(
        [
            "ssh-keygen", "-Y", "verify", "-f", str(allowed_signers_path),
            "-I", identity, "-n", namespace, "-s", str(signature_path),
        ],
        input=slot_bytes,
        capture_output=True,
        check=False,
    )
    detail = (process.stdout + process.stderr).decode("utf-8", errors="replace").strip()
    return process.returncode == 0, detail


def verify_slot(
    slot_path: Path,
    signature_path: Path,
    allowed_signers_path: Path,
    identity: str,
) -> dict[str, Any]:
    slot_bytes = slot_path.read_bytes()
    slot = json.loads(slot_bytes.decode("utf-8"))
    signature_valid, signature_detail = verify_signature(
        slot_bytes, signature_path, allowed_signers_path, identity
    )
    errors = semantic_errors(slot, identity)
    if not signature_valid:
        errors.append("custodian_signature_invalid")
    return {
        "schema_version": "1.0",
        "status": "ACCEPTANCE_SLOT_VERIFIED" if not errors else "ACCEPTANCE_SLOT_REJECTED",
        "slot_id": slot.get("acceptance_slot_id"),
        "custodian_identity": identity,
        "signature_namespace": NAMESPACE,
        "signature_valid": signature_valid,
        "signature_detail": signature_detail,
        "semantic_errors": sorted(set(errors)),
        "slot": slot if not errors else None,
        "unlocks_held_out": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("slot", type=Path)
    parser.add_argument("signature", type=Path)
    parser.add_argument("allowed_signers", type=Path)
    parser.add_argument("--identity", required=True)
    args = parser.parse_args()
    try:
        result = verify_slot(args.slot, args.signature, args.allowed_signers, args.identity)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        result = {
            "schema_version": "1.0",
            "status": "ACCEPTANCE_SLOT_REJECTED",
            "semantic_errors": [f"verification_error:{error}"],
            "unlocks_held_out": False,
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "ACCEPTANCE_SLOT_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
