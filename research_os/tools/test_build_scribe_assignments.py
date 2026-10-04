import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from build_scribe_assignments import build


class BuildScribeAssignmentsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.records = self.root / "records"
        self.records.mkdir()
        self.source = self.root / "ZL.txt"
        self.source.write_text(
            "\n".join([
                "#=IVTFF Eva- 2.0 M 5",
                "<f57r> <! $H=1 >",
                "<f57v> <! $H=5 >",
                "<f85r1> <! $H=2 >",
                "<fRos> <! $H=4 >",
                "<f86v3> <! $H=2 >",
                "<f115r> <! $H=@ >",
                "<f115v> <! $H=3 >",
            ]) + "\n",
            encoding="utf-8",
        )
        self.register = self.root / "register.json"
        self.register.write_text(json.dumps({
            "claim_class": "DATA",
            "source_id": "TEST",
            "source_url": "https://example.test/ZL.txt",
            "source_version": "test",
            "source_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "aliases": [{"source_page": "fRos", "atlas_folio_tokens": ["85v", "86r"]}],
            "mixed_pages": {"f115r": {"hand_set": ["2", "3"]}},
        }), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def add_record(self, record_id, folio_id):
        (self.records / f"{record_id}.annotation.json").write_text(json.dumps({
            "record_id": record_id,
            "source": {"logical_role": "FOLIO", "folio_or_cover_id": folio_id},
        }), encoding="utf-8")

    def test_mixed_labels_are_aggregated_at_leaf_group_level(self):
        self.add_record("R57r", "57r")
        self.add_record("R57v", "57v")
        self.add_record("R85", "85r (part)")
        self.add_record("RROS", "85v and 86r (foldout)")
        self.add_record("R86", "86v (part)")
        self.add_record("R115r", "115r")
        self.add_record("R115v", "115v")
        result = build(self.records, self.register, self.source)
        by_id = {item["record_id"]: item for item in result["records"]}
        self.assertEqual(by_id["R57r"]["scribe_label"], "MIXED_1_5")
        self.assertEqual(by_id["R57v"]["scribe_label"], "MIXED_1_5")
        self.assertEqual(by_id["R85"]["scribe_label"], "MIXED_2_4")
        self.assertEqual(by_id["RROS"]["scribe_label"], "MIXED_2_4")
        self.assertEqual(by_id["R86"]["scribe_label"], "MIXED_2_4")
        self.assertEqual(by_id["R115r"]["scribe_label"], "MIXED_2_3")
        self.assertEqual(by_id["R115v"]["scribe_label"], "MIXED_2_3")

    def test_hash_mismatch_fails_closed(self):
        self.add_record("R57r", "57r")
        register = json.loads(self.register.read_text())
        register["source_sha256"] = "0" * 64
        self.register.write_text(json.dumps(register))
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            build(self.records, self.register, self.source)


if __name__ == "__main__":
    unittest.main()
