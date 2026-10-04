import unittest

from annotation_gate import agreement_report, bbox_iou


SHA = "a" * 64


def submission(annotation_id, annotator_id, bbox=(0.1, 0.1, 0.5, 0.5), relation="IN_FRONT_OF"):
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
        "records": [
            {
                "record_id": "R1",
                "source_sha256": SHA,
                "objects": [
                    {"local_id": "A", "class": "ILLUSTRATION_OBJECT", "bbox": list(bbox), "ports": ["N", "S"]},
                    {"local_id": "B", "class": "ILLUSTRATION_OBJECT", "bbox": [0.5, 0.5, 0.9, 0.9], "ports": []},
                ],
                "occlusions": [{"source_id": "A", "target_id": "B", "relation": relation}],
            }
        ],
    }


class AnnotationGateTests(unittest.TestCase):
    def test_iou(self):
        self.assertEqual(bbox_iou([0, 0, 1, 1], [0, 0, 1, 1]), 1.0)
        self.assertEqual(bbox_iou([0, 0, 0.2, 0.2], [0.8, 0.8, 1, 1]), 0.0)

    def test_complete_independent_pair_passes_to_adjudication_only(self):
        report = agreement_report(submission("S1", "P1"), submission("S2", "P2"), {"R1": SHA})
        self.assertEqual(report["status"], "READY_FOR_ADJUDICATION")
        self.assertFalse(report["promotes_to_ground_truth"])
        self.assertFalse(report["unlocks_held_out"])

    def test_equivalent_inverse_occlusion_is_normalized(self):
        right = submission("S2", "P2")
        right["records"][0]["occlusions"] = [
            {"source_id": "B", "target_id": "A", "relation": "BEHIND"}
        ]
        report = agreement_report(submission("S1", "P1"), right, {"R1": SHA})
        self.assertEqual(report["metrics"]["occlusion_agreement"], 1.0)

    def test_failed_blinding_fails_closed(self):
        left = submission("S1", "P1")
        left["blindness"]["automated_candidates_unseen"] = False
        report = agreement_report(left, submission("S2", "P2"), {"R1": SHA})
        self.assertEqual(report["status"], "INCONCLUSIVE_ANNOTATION_GATE_FAILED")
        self.assertIn("blindness_attestation_failed", report["errors"]["left"])

    def test_no_comparable_occlusion_fails_closed(self):
        right = submission("S2", "P2")
        right["records"][0]["occlusions"] = []
        report = agreement_report(submission("S1", "P1"), right, {"R1": SHA})
        self.assertFalse(report["gates"]["occlusion_agreement"])

    def test_source_mismatch_fails_closed(self):
        right = submission("S2", "P2")
        right["records"][0]["source_sha256"] = "b" * 64
        report = agreement_report(submission("S1", "P1"), right, {"R1": SHA})
        self.assertIn("source_sha_mismatch:R1", report["errors"]["right"])


if __name__ == "__main__":
    unittest.main()
