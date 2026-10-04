Failed to connect to bus: Operation not permitted
import json
import unittest

from build_adjudication_packet import build_packet


def submission(annotation_id, annotator_id, bbox, ports):
    return {
        "schema_version": "1.0",
        "annotation_id": annotation_id,
        "annotator_id": annotator_id,
        "records": [{
            "record_id": "R1",
            "source_sha256": "a" * 64,
            "objects": [{
                "local_id": f"{annotation_id}-O1", "class": "DIAGRAM",
                "bbox": bbox, "ports": ports,
            }],
            "occlusions": [],
        }],
    }


class BuildAdjudicationPacketTests(unittest.TestCase):
    def setUp(self):
        self.left = submission("LEFT", "secret-annotator-a", [0.1, 0.1, 0.4, 0.4], ["N"])
        self.right = submission("RIGHT", "secret-annotator-b", [0.12, 0.1, 0.42, 0.4], ["S"])
        self.sources = [{
            "record_id": "R1", "source_path": "data/yale_hq_scans/1/test.jpg",
            "source_sha256": "a" * 64,
        }]

    def test_packet_anonymizes_submitter_identity_and_preserves_disagreement(self):
        packet, custody = build_packet(self.left, self.right, self.sources, "00" * 32, "b" * 64)
        rendered = json.dumps(packet)
        self.assertEqual(packet["status"], "READY_FOR_INDEPENDENT_ADJUDICATION")
        self.assertNotIn("secret-annotator-a", rendered)
        self.assertNotIn("secret-annotator-b", rendered)
        self.assertNotIn("AUTO_CANDIDATE", rendered)
        self.assertNotIn("annotation_id", rendered)
        self.assertNotIn("LEFT-O1", rendered)
        self.assertNotIn("RIGHT-O1", rendered)
        record = packet["records"][0]
        self.assertTrue(record["requires_review"])
        self.assertFalse(record["geometric_alignment"][0]["ports_exact"])
        self.assertEqual(custody["side_mapping"], {"SIDE_1": "A", "SIDE_2": "B"})
        self.assertEqual(custody["object_id_mapping"]["R1"]["SIDE_1"]["LEFT-O1"], "S1-O0001")
        self.assertFalse(packet["unlocks_held_out"])

    def test_receipt_hash_deterministically_blinds_side_order(self):
        packet, custody = build_packet(self.left, self.right, self.sources, "01" * 32, "b" * 64)
        self.assertEqual(custody["side_mapping"], {"SIDE_1": "B", "SIDE_2": "A"})
        self.assertEqual(packet["records"][0]["side_1"]["objects"][0]["local_id"], "S1-O0001")
        self.assertEqual(custody["object_id_mapping"]["R1"]["SIDE_1"]["RIGHT-O1"], "S1-O0001")


if __name__ == "__main__":
    unittest.main()
