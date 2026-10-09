#!/usr/bin/env python3
"""Fail-closed tests for the MV catalog gate. Run: python3 -m unittest discover -s research_os/experiments/MV-2026-10-09 -p 'test_*.py'"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("initialize_catalog.py")
SPEC = importlib.util.spec_from_file_location("mv_initialize_catalog", MODULE_PATH)
mv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mv)


def record(*, status="SCHEMA_READY", objects=None, role="FOLIO"):
    return {
        "record_id": "CANVAS-0003-1r",
        "execution_status": status,
        "source": {
            "logical_role": role, "folio_or_cover_id": "1r",
            "relative_path": "data/yale_hq_scans/1/0003_1r.jpg",
            "sha256": "a" * 64,
            "image_file_grid_px": {"width": 200, "height": 100},
            "provenance": {"source_url_or_catalog_id": "canvas:123"}},
        "illustration_inventory": {"objects": objects if objects is not None else []}
    }


class MVContractTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.records = self.root / "records"
        self.records.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def write_record(self, item, name="0003.annotation.json"):
        (self.records / name).write_text(json.dumps(item), encoding="utf-8")

    def test_empty_atlas_blocks_and_no_objects(self):
        self.write_record(record())
        qc = mv.build(self.records, self.root / "out")
        self.assertEqual(qc["status"], "BLOCKED_DATA")
        self.assertEqual(qc["counts"]["ready_without_annotations"], 1)
        self.assertEqual(qc["counts"]["objects"], 0)
        self.assertEqual(qc["mv2_mv3_mv4_candidates"], 0)
        self.assertEqual((self.root / "out" / "objects.jsonl").read_text(), "")

    def test_untrusted_auto_without_optin_blocks(self):
        self.write_record(record(status="AUTO_ANNOTATED_CANDIDATE",
                                 objects=[{"object_id":"O1","bbox":[10,10,40,30]}]))
        qc = mv.build(self.records, self.root / "out")
        self.assertEqual(qc["status"], "BLOCKED_DATA")
        self.assertEqual(qc["counts"]["auto_records_denied"], 1)

    def test_candidate_optin_does_not_make_ground_truth(self):
        self.write_record(record(status="AUTO_ANNOTATED_CANDIDATE",
                                 objects=[{"object_id":"O1","neutral_class":"GENERIC",
                                           "bbox":[10,10,40,30],
                                           "color":"INK_OR_NEUTRAL",
                                           "metrics":{"aspect":1.5}}]))
        qc = mv.build(self.records, self.root / "out", permit_auto=True)
        self.assertEqual(qc["status"], "AUTO_CANDIDATE_ONLY")
        candidate = json.loads((self.root / "out" / "objects.jsonl").read_text().strip())
        self.assertEqual(candidate["bbox_xywh_px"], [10,10,30,20])
        self.assertEqual(candidate["bbox_xywh_norm"], [0.05,0.1,0.15,0.2])
        self.assertEqual(candidate["pigment"]["status"], "UNKNOWN")
        self.assertEqual(candidate["counts"]["stars"], "UNKNOWN")
        self.assertEqual(candidate["manual_adjudication"], False)
        self.assertFalse(qc["pair_matching_performed"])

    def test_invalid_bbox_fails_closed(self):
        self.write_record(record(status="AUTO_ANNOTATED_CANDIDATE",
                                 objects=[{"object_id":"O1","bbox":[10,10,300,30]}]))
        qc = mv.build(self.records, self.root / "out", permit_auto=True)
        self.assertEqual(qc["status"], "BLOCKED_DATA")
        self.assertEqual(qc["counts"]["invalid_records"], 1)

    def test_confirmed_unpainted_cannot_be_inferred(self):
        self.assertEqual(mv.normalize_pigment("INK_OR_NEUTRAL")["status"], "UNKNOWN")
        self.assertEqual(mv.normalize_pigment(None)["status"], "UNKNOWN")
        self.assertNotEqual(mv.normalize_pigment("PIGMENT_PRESENT")["status"], "UNPAINTED")

    def test_cover_does_not_count_as_manuscript(self):
        self.write_record(record(role="COVER"))
        qc = mv.build(self.records, self.root / "out")
        self.assertEqual(qc["counts"]["covers_excluded"], 1)
        self.assertEqual(qc["status"], "BLOCKED_DATA")

    def test_bbox_detects_invalid_types(self):
        for box in ([0,0,0,1], [-1,0,10,1], [0,0,201,20], ["1",0,10,20]):
            with self.subTest(box=box):
                with self.assertRaises(ValueError):
                    mv.check_bbox(box,200,100)


if __name__ == "__main__":
    unittest.main()
