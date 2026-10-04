import json
import unittest

from validate_adjudication import sha256_bytes, validate_adjudication


def packet():
    return {
        "schema_version": "1.0",
        "status": "READY_FOR_INDEPENDENT_ADJUDICATION",
        "unlocks_held_out": False,
        "records": [{
            "record_id": "R1", "source_sha256": "a" * 64,
            "side_1": {
                "objects": [{"local_id": "S1-O0001", "class": "DIAGRAM", "bbox": [0.1, 0.1, 0.4, 0.4], "ports": ["N"]}],
                "occlusions": [],
            },
            "side_2": {
                "objects": [{"local_id": "S2-O0001", "class": "DIAGRAM", "bbox": [0.1, 0.1, 0.4, 0.4], "ports": ["N"]}],
                "occlusions": [],
            },
        }],
    }


def submission(packet_sha):
    return {
        "schema_version": "1.0", "packet_sha256": packet_sha,
        "adjudication_id": "ADJ-001", "adjudicator_id": "adjudicator-1",
        "blindness": {
            "annotator_identities_unseen": True, "automated_candidates_unseen": True,
            "model_predictions_unseen": True, "hypothesis_labels_unseen": True,
            "split_assignment_unseen": True,
        },
        "records": [{
            "record_id": "R1", "source_sha256": "a" * 64,
            "objects": [{
                "adjudicated_id": "ADJ-O0001", "class": "DIAGRAM",
                "bbox": [0.1, 0.1, 0.4, 0.4], "ports": ["N"],
                "source_refs": ["SIDE_1:S1-O0001", "SIDE_2:S2-O0001"],
                "rationale_code": "AGREE",
            }],
            "occlusions": [],
        }],
    }


class ValidateAdjudicationTests(unittest.TestCase):
    def setUp(self):
        self.packet = packet()
        self.packet_bytes = (json.dumps(self.packet, sort_keys=True) + "\n").encode()
        self.submission = submission(sha256_bytes(self.packet_bytes))

    def test_complete_blind_adjudication_validates_without_unlocking(self):
        result = validate_adjudication(self.packet_bytes, self.packet, self.submission)
        self.assertEqual(result["status"], "ADJUDICATION_VALIDATED")
        self.assertTrue(result["structurally_valid_for_readiness_chain"])
        self.assertFalse(result["promotes_to_ground_truth"])
        self.assertFalse(result["unlocks_held_out"])

    def test_unknown_source_reference_is_rejected(self):
        self.submission["records"][0]["objects"][0]["source_refs"] = ["SIDE_1:S1-O9999"]
        result = validate_adjudication(self.packet_bytes, self.packet, self.submission)
        self.assertEqual(result["status"], "ADJUDICATION_REJECTED")
        self.assertTrue(any(error.startswith("invalid_source_refs") for error in result["errors"]))

    def test_agree_requires_both_sides(self):
        self.submission["records"][0]["objects"][0]["source_refs"] = ["SIDE_1:S1-O0001"]
        result = validate_adjudication(self.packet_bytes, self.packet, self.submission)
        self.assertIn("agree_requires_both_sides:R1:ADJ-O0001", result["errors"])

    def test_packet_byte_change_is_rejected(self):
        changed = self.packet_bytes + b" "
        result = validate_adjudication(changed, self.packet, self.submission)
        self.assertIn("packet_sha256_mismatch", result["errors"])


if __name__ == "__main__":
    unittest.main()
