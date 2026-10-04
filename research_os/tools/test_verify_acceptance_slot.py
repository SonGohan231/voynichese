import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from verify_acceptance_slot import NAMESPACE, verify_slot


def valid_slot():
    return {
        "schema_version": "1.0",
        "state": "SEALED_BEFORE_COLLECTION",
        "experiment_id": "EXP-2026-001",
        "annotation_round": "ROUND-001",
        "acceptance_slot_id": "EXP-2026-001-ROUND-001-PAIR-001",
        "max_accepted_pairs": 1,
        "output_path": "research_os/runs/EXP-2026-001/annotation-freeze-001",
        "protocol_sha256": "a" * 64,
        "record_universe_sha256": "b" * 64,
        "packets": {
            "A": {"packet_id": "PACKET-A", "sha256": "c" * 64},
            "B": {"packet_id": "PACKET-B", "sha256": "d" * 64},
        },
        "annotator_bindings": [
            {"role": "A", "annotator_id_sha256": "e" * 64},
            {"role": "B", "annotator_id_sha256": "f" * 64},
        ],
        "custodian_identity": "custodian@example",
        "sealed_at_utc": "2026-10-04T15:00:00+00:00",
        "metrics_disclosure_policy": "AFTER_LOCAL_FREEZE_COMMIT",
        "held_out_access": "FORBIDDEN",
    }


class VerifyAcceptanceSlotTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.key = self.root / "custodian-key"
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(self.key)],
            check=True,
        )
        public = (self.key.with_suffix(".pub")).read_text(encoding="utf-8").split()
        self.allowed = self.root / "allowed_signers"
        self.allowed.write_text(
            f"custodian@example {public[0]} {public[1]}\n", encoding="utf-8"
        )

    def tearDown(self):
        self.temporary.cleanup()

    def write_and_sign(self, slot):
        path = self.root / "slot.json"
        path.write_text(json.dumps(slot, indent=2) + "\n", encoding="utf-8")
        signature = Path(f"{path}.sig")
        if signature.exists():
            signature.unlink()
        subprocess.run(
            ["ssh-keygen", "-Y", "sign", "-q", "-f", str(self.key), "-n", NAMESPACE, str(path)],
            check=True,
        )
        return path, signature

    def test_valid_signed_slot_is_verified(self):
        path, signature = self.write_and_sign(valid_slot())
        result = verify_slot(path, signature, self.allowed, "custodian@example")
        self.assertEqual(result["status"], "ACCEPTANCE_SLOT_VERIFIED")
        self.assertTrue(result["signature_valid"])
        self.assertFalse(result["unlocks_held_out"])

    def test_tampering_after_signature_is_rejected(self):
        path, signature = self.write_and_sign(valid_slot())
        value = json.loads(path.read_text(encoding="utf-8"))
        value["max_accepted_pairs"] = 2
        path.write_text(json.dumps(value), encoding="utf-8")
        result = verify_slot(path, signature, self.allowed, "custodian@example")
        self.assertEqual(result["status"], "ACCEPTANCE_SLOT_REJECTED")
        self.assertFalse(result["signature_valid"])

    def test_same_annotator_commitment_is_rejected_even_when_signed(self):
        value = valid_slot()
        value["annotator_bindings"][1]["annotator_id_sha256"] = "e" * 64
        path, signature = self.write_and_sign(value)
        result = verify_slot(path, signature, self.allowed, "custodian@example")
        self.assertTrue(result["signature_valid"])
        self.assertIn("annotator_id_hashes_not_distinct", result["semantic_errors"])

    def test_path_traversal_is_rejected_even_when_signed(self):
        value = valid_slot()
        value["output_path"] = "research_os/runs/EXP-2026-001/../../retry"
        path, signature = self.write_and_sign(value)
        result = verify_slot(path, signature, self.allowed, "custodian@example")
        self.assertTrue(result["signature_valid"])
        self.assertIn("unsafe_output_path", result["semantic_errors"])


if __name__ == "__main__":
    unittest.main()
