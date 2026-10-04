Failed to connect to bus: Operation not permitted
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from freeze_annotation_pair import freeze_pair
from verify_acceptance_slot import NAMESPACE
from verify_annotation_freeze import verify_freeze
from verify_custodian_receipt import NAMESPACE as RECEIPT_NAMESPACE, verify_receipt


SHA = "a" * 64


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class VerifyAnnotationFreezeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        records = self.root / "records"
        records.mkdir()
        write_json(records / "r1.annotation.json", {
            "record_id": "R1", "source": {"logical_role": "FOLIO", "sha256": SHA},
        })
        blindness = {
            "other_annotation_unseen": True, "automated_candidates_unseen": True,
            "model_predictions_unseen": True, "hypothesis_labels_unseen": True,
            "split_assignment_unseen": True,
        }
        def submission(annotation_id, annotator_id):
            return {
                "schema_version": "1.0", "annotation_id": annotation_id,
                "annotator_id": annotator_id, "blindness": blindness,
                "records": [{
                    "record_id": "R1", "source_sha256": SHA,
                    "objects": [
                        {"local_id": "O1", "class": "DIAGRAM", "bbox": [0.1, 0.1, 0.3, 0.3], "ports": ["N"]},
                        {"local_id": "O2", "class": "TEXT_FIELD", "bbox": [0.5, 0.5, 0.8, 0.8], "ports": ["S"]},
                    ],
                    "occlusions": [{"source_id": "O1", "target_id": "O2", "relation": "IN_FRONT_OF"}],
                }],
            }
        left = self.root / "left.json"; write_json(left, submission("A", "annotator-a"))
        right = self.root / "right.json"; write_json(right, submission("B", "annotator-b"))
        packet = {
            "schema_version": "1.0", "packet_id": "PACKET-A", "record_count": 1,
            "record_universe_sha256": "b" * 64, "protocol_sha256": "c" * 64,
            "records": [{"record_id": "R1", "source_sha256": SHA}],
        }
        packet_a = self.root / "packet-a.json"; write_json(packet_a, packet)
        packet["packet_id"] = "PACKET-B"
        packet_b = self.root / "packet-b.json"; write_json(packet_b, packet)

        self.key = self.root / "key"
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(self.key)], check=True)
        public = self.key.with_suffix(".pub").read_text(encoding="utf-8").split()
        self.allowed = self.root / "allowed_signers"
        self.allowed.write_text(f"custodian@example {public[0]} {public[1]}\n", encoding="utf-8")
        slot_value = {
            "schema_version": "1.0", "state": "SEALED_BEFORE_COLLECTION",
            "experiment_id": "EXP-2026-001", "annotation_round": "ROUND-001",
            "acceptance_slot_id": "SLOT-001", "max_accepted_pairs": 1,
            "output_path": "research_os/runs/EXP-2026-001/annotation-freeze-001",
            "protocol_sha256": "c" * 64, "record_universe_sha256": "b" * 64,
            "packets": {
                "A": {"packet_id": "PACKET-A", "sha256": hashlib.sha256(packet_a.read_bytes()).hexdigest()},
                "B": {"packet_id": "PACKET-B", "sha256": hashlib.sha256(packet_b.read_bytes()).hexdigest()},
            },
            "annotator_bindings": [
                {"role": "A", "annotator_id_sha256": hashlib.sha256(b"annotator-a").hexdigest()},
                {"role": "B", "annotator_id_sha256": hashlib.sha256(b"annotator-b").hexdigest()},
            ],
            "custodian_identity": "custodian@example", "sealed_at_utc": "2026-10-04T15:00:00+00:00",
            "metrics_disclosure_policy": "AFTER_LOCAL_FREEZE_COMMIT", "held_out_access": "FORBIDDEN",
        }
        slot = self.root / "slot.json"; write_json(slot, slot_value)
        subprocess.run(["ssh-keygen", "-Y", "sign", "-q", "-f", str(self.key), "-n", NAMESPACE, str(slot)], check=True)
        signature = Path(f"{slot}.sig")
        binding = {
            "slot_id": "SLOT-001", "slot_sha256": hashlib.sha256(slot.read_bytes()).hexdigest(),
            "custodian_identity": "custodian@example", "signature_namespace": NAMESPACE,
            "signature_valid": True,
            "annotator_id_sha256": {item["role"]: item["annotator_id_sha256"] for item in slot_value["annotator_bindings"]},
            "packet_sha256": {role: slot_value["packets"][role]["sha256"] for role in ("A", "B")},
            "protocol_sha256": "c" * 64, "record_universe_sha256": "b" * 64,
        }
        evidence = {
            "acceptance-slot.json": slot.read_bytes(),
            "acceptance-slot.json.sig": signature.read_bytes(),
            "allowed_signers": self.allowed.read_bytes(),
        }
        self.freeze = self.root / "freeze"
        freeze_pair(records, left, right, packet_a, packet_b, self.freeze, binding, evidence)

    def tearDown(self):
        for path in self.root.rglob("*"):
            path.chmod(0o755 if path.is_dir() else 0o644)
        self.temporary.cleanup()

    def test_complete_signed_freeze_verifies(self):
        result = verify_freeze(self.freeze)
        self.assertEqual(result["status"], "LOCAL_FREEZE_INTEGRITY_VERIFIED")
        self.assertEqual(result["acceptance_slot_status"], "ACCEPTANCE_SLOT_VERIFIED")
        self.assertTrue(result["custodian_final_receipt_required"])
        self.assertFalse(result["unlocks_held_out"])

    def test_post_freeze_mutation_is_detected(self):
        target = self.freeze / "annotation-a.json"
        target.chmod(0o644)
        target.write_text("{}\n", encoding="utf-8")
        result = verify_freeze(self.freeze)
        self.assertEqual(result["status"], "FREEZE_INTEGRITY_REJECTED")
        self.assertIn("artifact_digest_mismatch:annotation-a.json", result["errors"])

    def write_and_sign_receipt(self, overrides=None):
        freeze = verify_freeze(self.freeze)
        receipt = {
            "schema_version": "1.0", "state": "FREEZE_RECEIPTED_APPEND_ONLY",
            "experiment_id": "EXP-2026-001", "acceptance_slot_id": freeze["slot_id"],
            "manifest_sha256": freeze["manifest_sha256"], "commit_sha256": freeze["commit_sha256"],
            "freeze_integrity_status": "LOCAL_FREEZE_INTEGRITY_VERIFIED",
            "agreement_status": freeze["agreement_status"],
            "custodian_identity": "custodian@example", "issued_at_utc": "2026-10-04T16:00:00+00:00",
            "registry_uri": "https://example.invalid/append-only/EXP-2026-001/1",
            "registry_sequence": "1", "metrics_disclosed_before_receipt": False,
            "held_out_access": "FORBIDDEN", "supersedes_receipt_sha256": None,
        }
        receipt.update(overrides or {})
        path = self.root / "receipt.json"; write_json(path, receipt)
        signature = Path(f"{path}.sig")
        subprocess.run(
            ["ssh-keygen", "-Y", "sign", "-q", "-f", str(self.key),
             "-n", RECEIPT_NAMESPACE, str(path)], check=True,
        )
        return path, signature

    def test_matching_external_receipt_verifies_without_unlocking_heldout(self):
        receipt, signature = self.write_and_sign_receipt()
        result = verify_receipt(
            self.freeze, receipt, signature, self.allowed, "custodian@example"
        )
        self.assertEqual(result["status"], "FREEZE_RECEIPT_VERIFIED")
        self.assertTrue(result["ready_for_adjudication"])
        self.assertFalse(result["unlocks_held_out"])

    def test_receipt_for_different_manifest_is_rejected(self):
        receipt, signature = self.write_and_sign_receipt({"manifest_sha256": "0" * 64})
        result = verify_receipt(
            self.freeze, receipt, signature, self.allowed, "custodian@example"
        )
        self.assertEqual(result["status"], "FREEZE_RECEIPT_REJECTED")
        self.assertIn("receipt_freeze_mismatch:manifest_sha256", result["errors"])


if __name__ == "__main__":
    unittest.main()
