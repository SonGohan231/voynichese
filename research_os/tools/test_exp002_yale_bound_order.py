"""Recompute Yale clean-canvas order audit from frozen crosswalk and O1 headers.

This test asserts agreement of ordinary folio labels only, never historical physical order.
"""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / "research_os" / "experiments" / "EXP-2026-002"


class YaleManifestOrderTest(unittest.TestCase):
    def test_clean_image_labels_remain_monotone_against_it2a_o1(self):
        crosswalk = json.loads((EXP / "yale_iiif_canvas_group_crosswalk_2026-10-09.json").read_text())
        graph = json.loads((EXP / "physical_order_constraint_graph_v1.json").read_text())
        audit = json.loads((EXP / "yale_iiif_bound_order_compatibility_2026-10-09.json").read_text())

        o1_first = {}
        for ordinal, page in enumerate(graph["order_scenarios"]["O1_BOUND"]["order_page_headers"]):
            match = re.match(r"^(f\d+[rv])", page)
            if match:
                o1_first.setdefault(match.group(1), ordinal)
        simple = [(row["sequence_index"], row["oid"], "f" + row["label"])
                  for row in crosswalk["image_canvases"]
                  if re.fullmatch(r"\d{1,3}[rv]", row["label"])]
        compared = [(order, oid, folio, o1_first[folio])
                    for order, oid, folio in simple if folio in o1_first]
        self.assertEqual(len(simple), 183)
        self.assertEqual(len(compared), 182)
        self.assertEqual(sum(b[3] < a[3] for a, b in zip(compared, compared[1:])), 0)
        self.assertEqual(audit["counts"]["same_side_comparable_canvases"], len(compared))
        self.assertEqual(audit["counts"]["compared_order_inversions"], 0)

    def test_manifest_extra_sides_are_not_silently_lost(self):
        crosswalk = json.loads((EXP / "yale_iiif_canvas_group_crosswalk_2026-10-09.json").read_text())
        graph = json.loads((EXP / "physical_order_constraint_graph_v1.json").read_text())
        audit = json.loads((EXP / "yale_iiif_bound_order_compatibility_2026-10-09.json").read_text())
        images = {side for canvas in crosswalk["image_canvases"]
                  for side in canvas["folio_sides_from_label"]}
        it2a = {m.group(1) for p in graph["order_scenarios"]["O1_BOUND"]["order_page_headers"]
                if (m := re.match(r"^(f\d+[rv])", p))}
        self.assertEqual(images - it2a, {"f85v", "f86r", "f116v"})
        self.assertEqual(it2a - images, set())
        self.assertEqual(audit["exceptional_sides"]["yale_label_sides_absent_from_it2a"],
                         ["f85v", "f86r", "f116v"])
        self.assertEqual(audit["physical_scans_inspected"], 0)
        self.assertEqual(audit["O2_historical_original_order"], "UNKNOWN")
        self.assertEqual(audit["science_status"], "INCONCLUSIVE_NOT_RUN")
