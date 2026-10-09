"""EXP-2026-002 fail-closed tests for pending independent manuscript-photo review."""
import json
from pathlib import Path
import unittest

EXP = Path(__file__).resolve().parents[1] / "experiments" / "EXP-2026-002"


class IndependentPhysicalImageQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.queue = json.loads((EXP / "physical_photo_expert_review_queue_2026-10-09.json").read_text())
        cls.receipt = json.loads((EXP / "yale_207_jpeg_binary_integrity_receipt_2026-10-09.json").read_text())
        cls.tasks = cls.queue["ordered_review_tasks"]

    def test_exact_group_scope_without_fake_photo_for_lost_sheets(self):
        self.assertEqual(len(self.tasks), 58)
        self.assertEqual(len({x["group_id"] for x in self.tasks}), 58)
        present = [x for x in self.tasks if x["physical_presence"] == "SURVIVING_FULL_OR_PARTIAL"]
        missing = [x for x in self.tasks if x["physical_presence"] == "LOST_PLACEHOLDER"]
        self.assertEqual(len(present), 52)
        self.assertEqual(len(missing), 6)
        self.assertTrue(all(x["source_filenames"] for x in present))
        self.assertTrue(all(not x["source_filenames"] for x in missing))

    def test_photo_bytes_provenance_is_ci_and_not_material_review(self):
        self.assertEqual(self.receipt["aggregate"]["checked"], 207)
        self.assertEqual(self.receipt["aggregate"]["pass"], 207)
        self.assertEqual(self.receipt["aggregate"]["fail"], 0)
        verified_paths = {entry["archive_file"] for entry in self.receipt["images"]}
        for row in self.tasks:
            for f in row["source_filenames"]:
                self.assertIn(f["path"], verified_paths)
                self.assertTrue(f["image_sha256_verified_by_ci_2026_10_09"])
            review = row["independent_image_review"]
            self.assertFalse(review["pixels_examined"])
            self.assertEqual(review["status"], "NOT_STARTED" if row["folio_leaves"]
                             else "NOT_POSSIBLE_LOST_MATERIAL")
            self.assertEqual(review["independent_verdict"], "PENDING")
            self.assertEqual(review["findings"], [])
            self.assertEqual(review["crop_coordinates"], [])
        self.assertEqual(self.queue["science_status"], "INCONCLUSIVE_NOT_RUN")

    def test_disputed_foldout_review_is_priority_one(self):
        by_id = {x["group_id"]: x for x in self.tasks}
        self.assertEqual(set(self.queue["priority_buckets"]["critical"]), {"QI-B1", "QN-B1"})
        for group in ("QI-B1", "QN-B1"):
            self.assertEqual(by_id[group]["priority"], 1)
            self.assertEqual(len(by_id[group]["source_filenames"]), 4)
            self.assertTrue(by_id[group]["source_context_urls"])
        self.assertEqual(by_id["QN-B1"]["independent_image_review"]["confirmed_sheet_join"], None)
        self.assertEqual(self.queue["physical_order_freeze"], "NOT_APPROVED")


if __name__ == "__main__":
    unittest.main()
