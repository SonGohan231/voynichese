import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from verify_registry_witness import NAMESPACE, verify_registry_witness


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class VerifyRegistryWitnessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.registry_key = self.root / "registry-key"
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(self.registry_key)],
            check=True,
        )
        public = self.registry_key.with_suffix(".pub").read_text(encoding="utf-8").split()
        self.allowed = self.root / "registry-allowed-signers"
        self.allowed.write_text(
            f"registry@example {public[0]} {public[1]}\n", encoding="utf-8"
        )
        self.receipt = {
            "registry_uri": "https://registry.example/EXP-2026-001/1",
            "registry_sequence": "1",
        }
        self.receipt_bytes = b"{\"receipt\":\"exact-bytes\"}\n"
        self.receipt_signature_bytes = b"custodian-signature-bytes\n"

    def tearDown(self):
        self.temporary.cleanup()

    def build_witness(self, overrides=None):
        witness = {
            "schema_version": "1.0",
            "state": "EXTERNAL_REGISTRY_WITNESS",
            "experiment_id": "EXP-2026-001",
            "receipt_sha256": hashlib.sha256(self.receipt_bytes).hexdigest(),
            "receipt_signature_sha256": hashlib.sha256(
                self.receipt_signature_bytes
            ).hexdigest(),
            "registry_uri": self.receipt["registry_uri"],
            "registry_sequence": self.receipt["registry_sequence"],
            "registry_identity": "registry@example",
            "recorded_at_utc": "2026-10-04T20:00:00+00:00",
            "previous_witness_sha256": None,
        }
        witness.update(overrides or {})
        path = self.root / "witness.json"
        write_json(path, witness)
        subprocess.run(
            [
                "ssh-keygen", "-Y", "sign", "-q",
                "-f", str(self.registry_key), "-n", NAMESPACE, str(path),
            ],
            check=True,
        )
        return path, Path(f"{path}.sig")

    def verify(self, witness, signature, registry_identity="registry@example", custodian_identity="custodian@example"):
        return verify_registry_witness(
            self.receipt_bytes,
            self.receipt,
            self.receipt_signature_bytes,
            witness,
            signature,
            self.allowed,
            registry_identity,
            custodian_identity,
        )

    def test_valid_independent_registry_witness_verifies(self):
        witness, signature = self.build_witness()
        result = self.verify(witness, signature)
        self.assertEqual(result["status"], "REGISTRY_WITNESS_VERIFIED")
        self.assertFalse(result["unlocks_held_out"])

    def test_receipt_hash_mismatch_is_rejected(self):
        witness, signature = self.build_witness({"receipt_sha256": "0" * 64})
        result = self.verify(witness, signature)
        self.assertEqual(result["status"], "REGISTRY_WITNESS_REJECTED")
        self.assertIn(
            "registry_witness_receipt_mismatch:receipt_sha256", result["errors"]
        )

    def test_receipt_signature_hash_mismatch_is_rejected(self):
        witness, signature = self.build_witness(
            {"receipt_signature_sha256": "0" * 64}
        )
        result = self.verify(witness, signature)
        self.assertEqual(result["status"], "REGISTRY_WITNESS_REJECTED")
        self.assertIn(
            "registry_witness_receipt_mismatch:receipt_signature_sha256",
            result["errors"],
        )

    def test_registry_sequence_mismatch_is_rejected(self):
        witness, signature = self.build_witness({"registry_sequence": "2"})
        result = self.verify(witness, signature)
        self.assertEqual(result["status"], "REGISTRY_WITNESS_REJECTED")
        self.assertIn(
            "registry_witness_receipt_mismatch:registry_sequence", result["errors"]
        )

    def test_registry_identity_must_differ_from_custodian(self):
        witness, signature = self.build_witness(
            {"registry_identity": "custodian@example"}
        )
        result = self.verify(
            witness,
            signature,
            registry_identity="custodian@example",
            custodian_identity="custodian@example",
        )
        self.assertEqual(result["status"], "REGISTRY_WITNESS_REJECTED")
        self.assertIn("registry_identity_must_differ_from_custodian", result["errors"])


if __name__ == "__main__":
    unittest.main()
