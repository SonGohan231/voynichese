"""Conservative provenance checks for EXP-2026-003 image-review triage.

These tests verify coordinates and queue provenance only; they never declare
semantic, botanical, codicological or 3D conclusions.
"""
import json
from pathlib import Path
import re
import unittest

BASE = Path(__file__).resolve().parents[1] / "experiments" / "EXP-2026-003"
QUEUE = BASE / "high_resolution_review_triage_2026-10-09.json"

class HighResolutionTriageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(QUEUE.read_text(encoding="utf-8"))

    def test_original_full_size_archive_inventory_and_source_hashes(self):
        d = self.data
        items = d["whole_manuscript_highres_review_inventory"]
        self.assertEqual(len(items), 206)
        self.assertEqual(len({x["canvas_oid"] for x in items}), 206)
        for item in items:
            self.assertRegex(item["source_archival_sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(item["source_archive_path"].startswith("data/yale_hq_scans/"))
            self.assertTrue(item["native_original_jpeg_url"].endswith("/full/full/0/default.jpg"))
            self.assertGreater(item["native_width"], 100)
            self.assertGreater(item["native_height"], 100)
            self.assertEqual(item["botanical_semantic_status"], "NOT_REVIEWED")
            self.assertEqual(item["architecture_semantic_status"], "NOT_REVIEWED")
        self.assertEqual(d["scientific_result"], "INCONCLUSIVE_NOT_RUN")

    def test_six_provenance_linked_triage_pairs_are_unverified(self):
        d = self.data
        pairs = d["priority_match_pairs"]
        self.assertEqual(len(pairs), 6)
        self.assertEqual(d["counts"]["manual_verified_rois"], 0)
        self.assertTrue(all(p["human_verified"] is False and p["semantic_match"] == "UNKNOWN"
                            for p in pairs))
        for pair in pairs:
            self.assertLessEqual(pair["hash_distance"], 5)
            self.assertNotEqual(pair["first"]["canvas_oid"], pair["second"]["canvas_oid"])
            for slot in ("first", "second"):
                x = pair[slot]
                self.assertRegex(x["source_sha256"], r"^[0-9a-f]{64}$")
                self.assertRegex(x["crop_url_unverified_http"], r"^https://collections\.library\.yale\.edu/iiif/2/[0-9]+/pct:")
                bx = x["box_xywh"]
                self.assertEqual(len(bx), 4)
                self.assertTrue(all(0 <= p <= 1 for p in bx))
                self.assertLessEqual(bx[0] + bx[2], 1.00001)
                self.assertLessEqual(bx[1] + bx[3], 1.00001)
        self.assertEqual(set(d["triage_thresholds"]["exclude_background_like_classes"]),
                         {"barwa_żółto-ochrowy", "barwa_ciemne_linie"})

    def test_34_grid_zones_are_not_false_rosette_claims(self):
        d = self.data
        sectors = d["foldout_highres_review_tiles"]
        self.assertEqual(len(sectors), 34)
        self.assertEqual(len({x["tile_id"] for x in sectors}), 34)
        self.assertEqual(len([x for x in sectors if x["canvas_oid"] == "1006231"]), 9)
        expected_oids = {"1006194", "1006195", "1006196", "1006197",
                         "1006228", "1006229", "1006230", "1006231"}
        self.assertEqual({x["canvas_oid"] for x in sectors}, expected_oids)
        for x in sectors:
            self.assertFalse(x["tile_is_exact_semantic_object"])
            self.assertFalse(x["reviewed"])
            self.assertIsNone(x["confidence"])
            self.assertTrue(x["iiif_crop_url_unverified_http"].startswith(
                "https://collections.library.yale.edu/iiif/2/"))
            self.assertRegex(x["original_jpeg_sha256"], r"^[0-9a-f]{64}$")

if __name__ == "__main__":
    unittest.main()
