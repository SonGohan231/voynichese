import unittest

from annotation_gate import agreement_report, bbox_iou, match_objects


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
        self.assertEqual(report["diagnostics"]["macro_object_f1"], 1.0)
        self.assertIn("R1", report["diagnostics"]["per_record"])

    def test_equivalent_inverse_occlusion_is_normalized(self):
        right = submission("S2", "P2")
        right["records"][0]["occlusions"] = [
            {"source_id": "B", "target_id": "A", "relation": "BEHIND"}
        ]
        report = agreement_report(submission("S1", "P1"), right, {"R1": SHA})
        self.assertEqual(report["metrics"]["occlusion_f1"], 1.0)

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
        self.assertFalse(report["gates"]["occlusion_f1"])

    def test_missing_relation_is_penalized_not_ignored(self):
        right = submission("S2", "P2")
        right["records"][0]["occlusions"] = [
            {"source_id": "A", "target_id": "B", "relation": "IN_FRONT_OF"},
            {"source_id": "B", "target_id": "A", "relation": "AMBIGUOUS"},
        ]
        report = agreement_report(submission("S1", "P1"), right, {"R1": SHA})
        self.assertLess(report["metrics"]["occlusion_f1"], 0.8)

    def test_port_sector_mismatch_is_not_count_agreement(self):
        right = submission("S2", "P2")
        right["records"][0]["objects"][0]["ports"] = ["E", "W"]
        report = agreement_report(submission("S1", "P1"), right, {"R1": SHA})
        self.assertEqual(report["metrics"]["port_set_agreement"], 0.5)

    def test_matching_and_metrics_are_symmetric(self):
        left = submission("S1", "P1")
        right = submission("S2", "P2", bbox=(0.11, 0.1, 0.51, 0.5))
        forward = agreement_report(left, right, {"R1": SHA})
        reverse = agreement_report(right, left, {"R1": SHA})
        self.assertEqual(forward["metrics"], reverse["metrics"])

    def test_optimal_matching_beats_greedy_cardinality_trap(self):
        left = [
            {"class": "DIAGRAM", "bbox": [0.0, 0.0, 0.6, 1.0]},
            {"class": "DIAGRAM", "bbox": [0.4, 0.0, 1.0, 1.0]},
        ]
        right = [
            {"class": "DIAGRAM", "bbox": [0.0, 0.0, 1.0, 1.0]},
            {"class": "DIAGRAM", "bbox": [0.0, 0.0, 0.5, 1.0]},
        ]
        self.assertEqual(len(match_objects(left, right)), 2)

    def test_source_mismatch_fails_closed(self):
        right = submission("S2", "P2")
        right["records"][0]["source_sha256"] = "b" * 64
        report = agreement_report(submission("S1", "P1"), right, {"R1": SHA})
        self.assertIn("source_sha_mismatch:R1", report["errors"]["right"])


if __name__ == "__main__":
    unittest.main()
