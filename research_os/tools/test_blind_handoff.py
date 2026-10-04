import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from build_blind_handoff import build_handoff
from unblind_annotation import unblind


class BlindHandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.ui = self.repo / "research_os/annotation/ui"
        self.ui.mkdir(parents=True)
        (self.ui / "index.html").write_text("<html></html>", encoding="utf-8")
        (self.ui / "app.js").write_text('"use strict";', encoding="utf-8")
        (self.ui / "styles.css").write_text("body{}", encoding="utf-8")
        self.protocol = self.repo / "research_os/annotation/README.md"
        self.protocol.parent.mkdir(parents=True, exist_ok=True)
        self.protocol.write_text("neutral frozen protocol\n", encoding="utf-8")

        image = self.repo / "data/yale/0003_1r.jpg"
        image.parent.mkdir(parents=True)
        image.write_bytes(b"not-a-real-jpeg-but-stable-test-bytes")
        self.image_sha = hashlib.sha256(image.read_bytes()).hexdigest()
        protocol_sha = hashlib.sha256(self.protocol.read_bytes()).hexdigest()
        universe = json.dumps(
            [["CANVAS-0003-1r", self.image_sha]],
            separators=(",", ":"),
        ).encode()
        self.packet = self.root / "canonical.packet.json"
        self.packet.write_text(json.dumps({
            "schema_version": "1.0",
            "packet_id": "PACKET-A",
            "purpose": "INDEPENDENT_BLIND_ANNOTATION_EXP_2026_001",
            "protocol_path": "research_os/annotation/README.md",
            "protocol_sha256": protocol_sha,
            "record_universe_sha256": hashlib.sha256(universe).hexdigest(),
            "record_count": 1,
            "forbidden_inputs": ["model predictions"],
            "records": [{
                "record_id": "CANVAS-0003-1r",
                "source_path": "data/yale/0003_1r.jpg",
                "source_sha256": self.image_sha,
                "width": 100,
                "height": 200,
            }],
        }), encoding="utf-8")
        self.seed = self.root / "seed.bin"
        self.seed.write_bytes(b"x" * 32)
        self.seed.chmod(0o600)
        self.bundle = self.root / "handoff"
        self.custody = self.root / "custody.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_handoff_hides_linkable_metadata_and_unblinds_exactly(self):
        packet, custody = build_handoff(
            self.repo, self.packet, self.ui, self.seed, self.bundle, self.custody
        )
        rendered = json.dumps(packet)
        self.assertNotIn("CANVAS-0003-1r", rendered)
        self.assertNotIn("0003_1r.jpg", rendered)
        self.assertNotIn(self.image_sha, rendered)
        record = packet["records"][0]
        self.assertTrue(record["record_id"].startswith("BLI-"))
        self.assertTrue(record["source_path"].startswith("blind_images/BLI-"))
        self.assertIn("source_commitment_sha256", record)
        self.assertNotIn("source_sha256", record)

        self.assertTrue(self.custody.is_file())
        self.assertEqual(self.custody.stat().st_mode & 0o777, 0o600)
        self.assertEqual(custody["records"][0]["original_record_id"], "CANVAS-0003-1r")

        handoff_packet_path = self.bundle / "research_os/annotation/packets/handoff.packet.json"
        submission = self.root / "blinded-submission.json"
        submission.write_text(json.dumps({
            "schema_version": "1.0",
            "annotation_id": "A-001",
            "annotator_id": "anon-A",
            "blindness": {
                "other_annotation_unseen": True,
                "automated_candidates_unseen": True,
                "model_predictions_unseen": True,
                "hypothesis_labels_unseen": True,
                "split_assignment_unseen": True,
            },
            "records": [{
                "record_id": record["record_id"],
                "source_commitment_sha256": record["source_commitment_sha256"],
                "objects": [],
                "occlusions": [],
            }],
        }), encoding="utf-8")
        canonical = unblind(handoff_packet_path, self.custody, submission)
        self.assertEqual(canonical["records"][0]["record_id"], "CANVAS-0003-1r")
        self.assertEqual(canonical["records"][0]["source_sha256"], self.image_sha)
        self.assertNotIn("source_commitment_sha256", canonical["records"][0])

    def test_custody_map_cannot_be_written_inside_handoff(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            build_handoff(
                self.repo, self.packet, self.ui, self.seed,
                self.bundle, self.bundle / "custody.json",
            )

    def test_world_readable_seed_is_rejected(self):
        self.seed.chmod(0o644)
        with self.assertRaisesRegex(ValueError, "permissions"):
            build_handoff(
                self.repo, self.packet, self.ui, self.seed, self.bundle, self.custody
            )

    def test_unblind_rejects_modified_source_commitment(self):
        packet, _ = build_handoff(
            self.repo, self.packet, self.ui, self.seed, self.bundle, self.custody
        )
        record = packet["records"][0]
        submission = self.root / "bad.json"
        submission.write_text(json.dumps({
            "schema_version": "1.0",
            "annotation_id": "A-001",
            "annotator_id": "anon-A",
            "blindness": {},
            "records": [{
                "record_id": record["record_id"],
                "source_commitment_sha256": "0" * 64,
                "objects": [],
                "occlusions": [],
            }],
        }))
        with self.assertRaisesRegex(ValueError, "commitment"):
            unblind(
                self.bundle / "research_os/annotation/packets/handoff.packet.json",
                self.custody,
                submission,
            )


if __name__ == "__main__":
    unittest.main()
