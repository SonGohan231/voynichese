Failed to connect to bus: Operation not permitted
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from sealed_split import seal_split


def adjudicated_record(record_id):
    return {
        "record_id": record_id,
        "source_sha256": "a" * 64,
        "objects": [{
            "adjudicated_id": f"{record_id}-OBJECT",
            "class": "DIAGRAM",
            "bbox": [0.1, 0.1, 0.4, 0.4],
            "ports": ["N"],
            "source_refs": ["SIDE_1:S1-O0001", "SIDE_2:S2-O0001"],
            "rationale_code": "AGREE",
        }],
        "occlusions": [],
    }


class SealedSplitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.key = self.root / "custodian-key.pem"
        self.cert = self.root / "custodian-cert.pem"
        subprocess.run(
            [
                "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                "-keyout", str(self.key), "-out", str(self.cert),
                "-subj", "/CN=voynich-test-custodian", "-days", "1",
            ],
            capture_output=True,
            check=True,
        )
        self.split = {
            "schema_version": "1.0", "experiment_id": "EXP-2026-001",
            "seed": "not-public", "grouping_policy": "test",
            "assignments_sha256": "b" * 64,
            "group_counts": {"TRAIN": 2, "VALIDATION": 1, "HELD_OUT": 1},
            "assignments": {
                "TRAIN": ["R1", "R2"], "VALIDATION": ["R3"], "HELD_OUT": ["R4"],
            },
        }
        self.adjudication = {"records": [adjudicated_record(f"R{i}") for i in range(1, 5)]}

    def tearDown(self):
        for path in self.root.rglob("*"):
            path.chmod(0o755 if path.is_dir() else 0o644)
        self.temporary.cleanup()

    def test_developer_package_hides_universe_and_heldout_while_ciphertext_recovers(self):
        output = self.root / "sealed"
        manifest = seal_split(self.split, self.adjudication, b"s" * 32, self.cert, output)
        developer_bytes = (output / "model-development.json").read_bytes()
        developer = json.loads(developer_bytes)
        self.assertEqual(len(developer["records"]), 3)
        self.assertFalse(developer["contains_full_record_universe"])
        self.assertFalse(developer["contains_held_out_identifiers"])
        rendered = developer_bytes.decode("utf-8")
        for secret in ("R1", "R2", "R3", "R4", "source_sha256", "source_refs", "folio"):
            self.assertNotIn(secret, rendered)
        self.assertNotIn("HELD_OUT", {item["split"] for item in developer["records"]})
        decrypted = subprocess.run(
            [
                "openssl", "cms", "-decrypt", "-inform", "DER",
                "-in", str(output / "custodian-split.p7m"),
                "-recip", str(self.cert), "-inkey", str(self.key),
            ],
            capture_output=True,
            check=True,
        ).stdout
        secret = json.loads(decrypted)
        self.assertEqual(secret["split"]["assignments"]["HELD_OUT"], ["R4"])
        self.assertEqual(secret["seed_hex"], (b"s" * 32).hex())
        self.assertFalse(manifest["held_out_identifiers_public"])
        self.assertFalse(manifest["unlocks_held_out"])

    def test_short_seed_is_rejected_before_output(self):
        with self.assertRaisesRegex(ValueError, "at_least_32_bytes"):
            seal_split(self.split, self.adjudication, b"short", self.cert, self.root / "sealed")

    def test_authenticated_ciphertext_rejects_tampering(self):
        output = self.root / "sealed"
        seal_split(self.split, self.adjudication, b"s" * 32, self.cert, output)
        ciphertext = output / "custodian-split.p7m"
        ciphertext.chmod(0o644)
        value = bytearray(ciphertext.read_bytes())
        value[-1] ^= 1
        ciphertext.write_bytes(value)
        process = subprocess.run(
            [
                "openssl", "cms", "-decrypt", "-inform", "DER",
                "-in", str(ciphertext), "-recip", str(self.cert), "-inkey", str(self.key),
            ],
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(process.returncode, 0)


if __name__ == "__main__":
    unittest.main()
