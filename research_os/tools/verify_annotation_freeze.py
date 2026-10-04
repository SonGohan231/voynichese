#!/usr/bin/env python3
"""Verify the complete local blind-annotation freeze before receipt/adjudication."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
from pathlib import Path
from typing import Any

from verify_acceptance_slot import verify_slot


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_freeze(directory: Path) -> dict[str, Any]:
    errors = []
    if not directory.is_dir() or directory.is_symlink():
        return {"status": "FREEZE_INTEGRITY_REJECTED", "errors": ["invalid_freeze_directory"], "unlocks_held_out": False}

    commit_path = directory / "COMMIT.json"
    manifest_path = directory / "freeze-manifest.json"
    try:
        commit = json.loads(commit_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {"status": "FREEZE_INTEGRITY_REJECTED", "errors": [f"missing_or_invalid_control_file:{error}"], "unlocks_held_out": False}

    if commit.get("state") != "LOCAL_FREEZE_COMMITTED":
        errors.append("commit_state_invalid")
    if commit.get("manifest_sha256") != digest(manifest_path):
        errors.append("manifest_digest_mismatch")
    if manifest.get("freeze_status") != "LOCAL_FREEZE_BOUND_TO_SIGNED_ACCEPTANCE_SLOT":
        errors.append("freeze_not_bound_to_signed_slot")
    if manifest.get("promotes_to_ground_truth") is not False or manifest.get("unlocks_held_out") is not False:
        errors.append("scientific_firewall_invalid")

    tracked = {"COMMIT.json", "freeze-manifest.json"}
    entries = [
        manifest.get("annotation_a"), manifest.get("annotation_b"),
        manifest.get("packet_a"), manifest.get("packet_b"),
        manifest.get("agreement_report"),
    ] + list((manifest.get("acceptance_evidence") or {}).values())
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("path") or not entry.get("sha256"):
            errors.append("invalid_manifest_artifact_entry")
            continue
        name = entry["path"]
        if Path(name).name != name:
            errors.append(f"unsafe_artifact_path:{name}")
            continue
        tracked.add(name)
        path = directory / name
        if not path.is_file() or path.is_symlink():
            errors.append(f"missing_or_nonregular_artifact:{name}")
        elif digest(path) != entry["sha256"]:
            errors.append(f"artifact_digest_mismatch:{name}")
        elif path.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
            errors.append(f"artifact_is_writable:{name}")

    actual = {path.name for path in directory.iterdir()}
    for name in sorted(actual - tracked):
        errors.append(f"untracked_artifact:{name}")
    for name in sorted(tracked - actual):
        errors.append(f"tracked_artifact_missing:{name}")
    if directory.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
        errors.append("freeze_directory_is_writable")

    binding = manifest.get("acceptance_slot") or {}
    slot_result = None
    required_evidence = {"acceptance-slot.json", "acceptance-slot.json.sig", "allowed_signers"}
    if required_evidence <= actual and binding.get("custodian_identity"):
        slot_result = verify_slot(
            directory / "acceptance-slot.json",
            directory / "acceptance-slot.json.sig",
            directory / "allowed_signers",
            binding["custodian_identity"],
        )
        if slot_result["status"] != "ACCEPTANCE_SLOT_VERIFIED":
            errors.append("embedded_acceptance_slot_invalid")
        elif binding.get("slot_sha256") != digest(directory / "acceptance-slot.json"):
            errors.append("embedded_slot_binding_mismatch")
    else:
        errors.append("acceptance_evidence_incomplete")

    return {
        "schema_version": "1.0",
        "status": "LOCAL_FREEZE_INTEGRITY_VERIFIED" if not errors else "FREEZE_INTEGRITY_REJECTED",
        "slot_id": binding.get("slot_id"),
        "manifest_sha256": digest(manifest_path),
        "commit_sha256": digest(commit_path),
        "agreement_status": (manifest.get("agreement_report") or {}).get("status"),
        "acceptance_slot_status": slot_result.get("status") if slot_result else None,
        "errors": sorted(set(errors)),
        "promotes_to_ground_truth": False,
        "unlocks_held_out": False,
        "custodian_final_receipt_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("freeze_directory", type=Path)
    args = parser.parse_args()
    result = verify_freeze(args.freeze_directory)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "LOCAL_FREEZE_INTEGRITY_VERIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
