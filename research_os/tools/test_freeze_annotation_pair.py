import hashlib
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from freeze_annotation_pair import freeze_pair


SHA = "a" * 64


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def submission(annotation_id, annotator_id):
    return {
        "schema_version": "1.0",
        "annotation_id": annotation_id,
        "annotator_id": annotator_id,
        "blindness": {
            "other_annotation_unseen": True,
            "automated_candidates_unseen": True,
            "model_predictions_unseen": True,
            "hypothesis_labels_unseen": True,
            "split_assignment_unseen": True,
        },
        "records": [{
            "record_id": "R1",
            "source_sha256": SHA,
            "objects": [
                {"local_id": "O1", "class": "DIAGRAM", "bbox": [0.1, 0.1, 0.3, 0.3], "ports": ["N"]},
                {"local_id": "O2", "class": "TEXT_FIELD", "bbox": [0.5, 0.5, 0.8, 0.8], "ports": ["S"]},
            ],
            "occlusions": [{"source_id": "O1", "target_id": "O2", "relation": "IN_FRONT_OF"}],
        }],
    }


class FreezeAnnotationPairTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.records = self.root / "records"
        self.records.mkdir()
        write_json(self.records / "r1.annotation.json", {
            "record_id": "R1",
            "source": {"logical_role": "FOLIO", "sha256": SHA},
        })
        self.left = self.root / "left.json"
        self.right = self.root / "right.json"
        write_json(self.left, submission("A", "annotator-a"))
        write_json(self.right, submission("B", "annotator-b"))
        packet = {
            "schema_version": "1.0",
            "packet_id": "PACKET-A",
            "record_count": 1,
            "record_universe_sha256": "b" * 64,
            "protocol_sha256": "c" * 64,
            "records": [{"record_id": "R1", "source_sha256": SHA}],
        }
        self.packet_a = self.root / "packet-a.json"
        self.packet_b = self.root / "packet-b.json"
        write_json(self.packet_a, packet)
        packet["packet_id"] = "PACKET-B"
        write_json(self.packet_b, packet)

    def tearDown(self):
        for path in self.root.rglob("*"):
            if path.is_dir():
                path.chmod(0o755)
            else:
                path.chmod(0o644)
        self.temporary.cleanup()

    def test_freezes_exact_inputs_before_report(self):
        output = self.root / "frozen"
        manifest, report = freeze_pair(
            self.records, self.left, self.right, self.packet_a, self.packet_b, output
        )
        self.assertEqual(manifest["freeze_status"], "LOCAL_DIAGNOSTIC_FREEZE_NO_SLOT")
        self.assertEqual(report["status"], "READY_FOR_ADJUDICATION")
        self.assertFalse(manifest["unlocks_held_out"])
        self.assertEqual(
            manifest["annotation_a"]["sha256"], hashlib.sha256(self.left.read_bytes()).hexdigest()
        )
        self.assertEqual((output / "annotation-a.json").read_bytes(), self.left.read_bytes())
        self.assertTrue((output / "agreement-report.json").is_file())
        commit = json.loads((output / "COMMIT.json").read_text(encoding="utf-8"))
        self.assertEqual(commit["state"], "LOCAL_FREEZE_COMMITTED")
        self.assertTrue(commit["custodian_receipt_required"])

    def test_refuses_to_overwrite_a_frozen_run(self):
        output = self.root / "frozen"
        freeze_pair(self.records, self.left, self.right, self.packet_a, self.packet_b, output)
        with self.assertRaisesRegex(ValueError, "refusing_to_overwrite"):
            freeze_pair(self.records, self.left, self.right, self.packet_a, self.packet_b, output)

    def test_manifest_records_verified_slot_binding(self):
        binding = {
            "slot_id": "SLOT-001",
            "slot_sha256": "1" * 64,
            "custodian_identity": "custodian@example",
            "signature_namespace": "voynich-research-os-acceptance-slot-v1",
            "signature_valid": True,
            "annotator_id_sha256": {
                "A": hashlib.sha256(b"annotator-a").hexdigest(),
                "B": hashlib.sha256(b"annotator-b").hexdigest(),
            },
            "packet_sha256": {
                "A": hashlib.sha256(self.packet_a.read_bytes()).hexdigest(),
                "B": hashlib.sha256(self.packet_b.read_bytes()).hexdigest(),
            },
            "protocol_sha256": "c" * 64,
            "record_universe_sha256": "b" * 64,
        }
        evidence = {
            "acceptance-slot.json": b"slot\n",
            "acceptance-slot.json.sig": b"signature\n",
            "allowed_signers": b"custodian@example ssh-ed25519 test\n",
        }
        manifest, _ = freeze_pair(
            self.records, self.left, self.right, self.packet_a, self.packet_b,
            self.root / "frozen", binding, evidence,
        )
        self.assertEqual(
            manifest["freeze_status"], "LOCAL_FREEZE_BOUND_TO_SIGNED_ACCEPTANCE_SLOT"
        )
        self.assertEqual(manifest["acceptance_slot"], binding)
        self.assertEqual(
            (self.root / "frozen" / "acceptance-slot.json").read_bytes(), b"slot\n"
        )
        self.assertIn("acceptance-slot.json.sig", manifest["acceptance_evidence"])

    def test_signed_slot_binding_rejects_substituted_annotator_id(self):
        binding = {
            "slot_id": "SLOT-001",
            "slot_sha256": "1" * 64,
            "custodian_identity": "custodian@example",
            "signature_namespace": "voynich-research-os-acceptance-slot-v1",
            "signature_valid": True,
            "annotator_id_sha256": {"A": "0" * 64, "B": "1" * 64},
            "packet_sha256": {
                "A": hashlib.sha256(self.packet_a.read_bytes()).hexdigest(),
                "B": hashlib.sha256(self.packet_b.read_bytes()).hexdigest(),
            },
            "protocol_sha256": "c" * 64,
            "record_universe_sha256": "b" * 64,
        }
        with self.assertRaisesRegex(ValueError, "annotator_ids_do_not_match_signed_slot"):
            freeze_pair(
                self.records, self.left, self.right, self.packet_a, self.packet_b,
                self.root / "frozen", binding, {"acceptance-slot.json": b"slot\n"},
            )

    def test_refuses_same_annotator_identity(self):
        value = submission("B", "annotator-a")
        write_json(self.right, value)
        with self.assertRaisesRegex(ValueError, "annotator_ids_not_distinct"):
            freeze_pair(
                self.records, self.left, self.right, self.packet_a, self.packet_b, self.root / "frozen"
            )

    def test_exactly_one_concurrent_writer_reserves_the_run(self):
        output = self.root / "frozen"

        def attempt():
            try:
                freeze_pair(
                    self.records, self.left, self.right, self.packet_a, self.packet_b, output
                )
                return "committed"
            except ValueError as error:
                return str(error)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: attempt(), range(2)))
        self.assertEqual(results.count("committed"), 1)
        self.assertEqual(sum("refusing_to_overwrite" in result for result in results), 1)


if __name__ == "__main__":
    unittest.main()
