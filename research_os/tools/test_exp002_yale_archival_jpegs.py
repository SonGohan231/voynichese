"""EXP-2026-002 archival JPEG crosswalk regression tests.

These checks protect repository-side metadata and *do not* inspect scanned pixels
or recompute the historical SHA-256 values over source JPEG bytes.
"""
import json
from pathlib import Path
import unittest

EXPERIMENT = (
    Path(__file__).resolve().parents[1]
    / "experiments" / "EXP-2026-002"
)
CROSSWALK = "yale_iiif_canvas_group_crosswalk_2026-10-09.json"
ARCHIVE = "yale_archived_jpeg_provenance_crosswalk_2026-10-09.json"


class YaleArchivedJpegProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cross = json.loads((EXPERIMENT / CROSSWALK).read_text(encoding="utf-8"))
        cls.audit = json.loads((EXPERIMENT / ARCHIVE).read_text(encoding="utf-8"))

    def test_deduplicated_archive_inventory(self):
        a = self.audit
        self.assertEqual(len(a["archive_files"]), 207)
        self.assertEqual(len({x["canvas_oid"] for x in a["archive_files"]}), 206)
        self.assertEqual(a["counts"]["duplicates_preserved"], 1)
        self.assertEqual({x["path"] for x in a["archive_files"]}.__len__(), 207)
        self.assertEqual({x["sequence_number_1based"] for x in a["archive_files"]},
                         set(range(1, 207)))
        self.assertEqual(a["counts"]["referenced_bytes_size_matching_github"], 207)
        self.assertTrue(all(x["bytes_from_import_report"] ==
                            x["bytes_from_current_github_directory"] for x in a["archive_files"]))

    def test_image_sha256_values_are_historic_not_newly_verified(self):
        a = self.audit
        self.assertEqual(a["source_inventory"]["report_sha256_status"],
                         "HISTORIC_IMPORT_RECORDED; NOT_RECOMPUTED_FROM_JPEG_BYTES_THIS_PASS")
        self.assertEqual(a["counts"]["images_independently_rehashed_this_pass"], 0)
        self.assertEqual(a["counts"]["images_directly_examined_this_pass"], 0)
        self.assertTrue(all(len(x["imported_reported_sha256"]) == 64 and
                            x["reported_sha256_recomputed_in_this_audit"] is False
                            for x in a["archive_files"]))

    def test_links_are_consistent_with_existing_iiif_map(self):
        archived = self.audit
        source = {x["oid"]: x for x in self.cross["image_canvases"]}
        self.assertEqual(len(archived["yale_canvases"]), 213)
        for file in archived["archive_files"]:
            entry = source[file["canvas_oid"]]
            self.assertEqual(file["canvas_id"], entry["canvas_id"])
            self.assertEqual(file["yale_label"], entry["label"])
            self.assertEqual(file["physical_group_ids"], entry["physical_group_ids_by_leaf_label"])
            self.assertIn(file["path"], archived["physical_group_crosswalk"]
                          [file["physical_group_ids"][0]]["archived_image_paths"]
                          if file["physical_group_ids"] else [file["path"]])

    def test_covers_all_present_groups_and_preserves_missing_material(self):
        groups = self.audit["physical_group_crosswalk"]
        present = [g for g in groups.values() if g["present_leaves"]]
        lost = [g for g in groups.values() if not g["present_leaves"]]
        self.assertEqual(len(present), 52)
        self.assertEqual(len(lost), 6)
        self.assertTrue(all(g["archived_image_paths"] for g in present))
        self.assertTrue(all(not g["archived_image_paths"] for g in lost))
        self.assertTrue(all(g["pixel_review"] == "NOT_DONE" for g in groups.values()))

    def test_special_folios_remain_intact(self):
        e = self.audit["exceptions"]
        self.assertEqual([x["path"].split("/")[-1] for x in e["q9_archive_paths"]],
                         ["0121_67r.jpg", "0122_67v.jpg", "0123_68r.jpg", "0124_68v.jpg"])
        self.assertEqual(len(e["q14_archive_paths"]), 4)
        self.assertTrue(all(x["path"].startswith("data/yale_hq_scans/")
                            for x in e["q14_archive_paths"]))
        self.assertEqual(e["deliberate_duplicate_image"]["oid"], "1006096")
        self.assertEqual(len(e["deliberate_duplicate_image"]["source_paths"]), 2)

    def test_missing_7_canvases_are_not_lost_folios(self):
        unavailable = self.audit["exceptions"]["not_archived_yale_images"]
        self.assertEqual(len(unavailable), 7)
        self.assertEqual({x["oid"] for x in unavailable},
                         {"1037113", "1006278", "11868207", "11868208",
                          "11868209", "11868210", "1006279"})
        self.assertTrue(all(not x["group_ids"] for x in unavailable))
        self.assertEqual(self.audit["historical_original_order_status"], "UNKNOWN")
        self.assertEqual(self.audit["science_status"], "INCONCLUSIVE_NOT_RUN")


if __name__ == "__main__":
    unittest.main()
