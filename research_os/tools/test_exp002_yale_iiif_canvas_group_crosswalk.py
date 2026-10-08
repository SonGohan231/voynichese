"""Fail-closed QA for EXP-2026-002 Yale IIIF canvas/physical-leaf label crosswalk.

Crosswalk is metadata provenance ONLY, not an inspection of scanned pixels.
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXP = ROOT / "research_os" / "experiments" / "EXP-2026-002"
CROSSWALK = EXP / "yale_iiif_canvas_group_crosswalk_2026-10-09.json"
GRAPH = EXP / "physical_order_constraint_graph_v1.json"


class TestExp002YaleCanvasCrosswalk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping = json.loads(CROSSWALK.read_text(encoding="utf-8"))
        cls.graph = json.loads(GRAPH.read_text(encoding="utf-8"))
        cls.canvases = cls.mapping["image_canvases"]
        cls.groups = cls.mapping["physical_groups"]

    def test_manifest_metadata_linkage_only(self):
        self.assertEqual(self.mapping["provenance"]["official_yale_iiif_manifest_url"],
                         "https://collections.library.yale.edu/manifests/2002046")
        self.assertEqual(self.mapping["status"], "METADATA_MAPPING_ONLY_NOT_PHYSICAL_OBSERVATION")
        self.assertIsNone(self.mapping["provenance"]["source_bytes_sha256"])
        self.assertIs(self.mapping["provenance"]["independent_original_image_inspection"], False)
        self.assertEqual(self.mapping["science_status"], "INCONCLUSIVE_NOT_RUN")

    def test_exact_group_and_canvas_counts(self):
        self.assertEqual(len(self.canvases), 213)
        self.assertEqual(len(self.groups), 58)
        physical = self.graph["groups"]
        self.assertEqual(set(self.groups), set(physical))
        present = [name for name, g in physical.items() if g.get("present_leaves")]
        missing = [name for name, g in physical.items() if not g.get("present_leaves")]
        self.assertEqual(len(present), 52)
        self.assertEqual(len(missing), 6)
        self.assertEqual(self.mapping["statistics"]["present_groups_with_canvas_label_links"], 52)
        self.assertTrue(all(self.groups[name]["yale_canvas_oids_by_folio_label"] for name in present))
        self.assertTrue(all(not self.groups[name]["yale_canvas_oids_by_folio_label"] for name in missing))

    def test_no_fabricated_or_duplicate_canvas_identifiers(self):
        oids = [item["oid"] for item in self.canvases]
        self.assertEqual(len(oids), len(set(oids)))
        for item in self.canvases:
            self.assertTrue(item["canvas_id"].endswith("/" + item["oid"]))
            self.assertEqual(item["sequence_index"], self.canvases.index(item))
            self.assertIn(item["oid"], item["image_resource_url"])
            self.assertFalse(item["pixel_inspected"])
            self.assertFalse(item["exact_it2a_panel_mapping_validated"])

    def test_mapping_is_invertible_on_folio_label_only(self):
        for item in self.canvases:
            actual = set(item["physical_group_ids_by_leaf_label"])
            side_leaves = {side[:-1] for side in item["folio_sides_from_label"]}
            expected = {name for name, g in self.graph["groups"].items()
                        if side_leaves.intersection(g.get("present_leaves") or [])}
            self.assertEqual(actual, expected, item["label"])
        for name, group in self.groups.items():
            actual = {item["oid"] for item in self.canvases
                      if name in item["physical_group_ids_by_leaf_label"]}
            self.assertEqual(set(group["yale_canvas_oids_by_folio_label"]), actual)

    def test_foldout_and_composite_not_false_panel_alignment(self):
        q09 = self.mapping["special_cases"]["q09"]
        q14 = self.mapping["special_cases"]["q14"]
        self.assertEqual({x["oid"] for x in q09},
                         {"1006194", "1006195", "1006196", "1006197"})
        self.assertEqual({x["oid"] for x in q14},
                         {"1006228", "1006229", "1006230", "1006231"})
        self.assertTrue(all(x["groups"] == ["QI-B1"] for x in q09))
        self.assertTrue(all(x["groups"] == ["QN-B1"] for x in q14))
        self.assertEqual(sum(x["mapping_kind"] == "COMPOSITE_OR_FOLDOUT_LABEL"
                             for x in self.canvases), 21)
        self.assertEqual(sum(len(x["physical_group_ids_by_leaf_label"]) > 1
                             for x in self.canvases), 2)
        self.assertEqual(self.mapping["statistics"]["groups_with_independent_pixel_review"], 0)
        self.assertTrue(all(group["panel_geometry_verified"] is False
                            for group in self.groups.values()))


if __name__ == "__main__":
    unittest.main()
