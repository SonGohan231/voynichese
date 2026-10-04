import json
import tempfile
import unittest
from pathlib import Path

from build_section_assignments import build


class BuildSectionAssignmentsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.records = self.root / "records"
        self.records.mkdir()
        self.source = self.root / "source.json"
        self.source.write_text(json.dumps({
            "claim_class": "DATA", "source_id": "TEST", "source_url": "https://example.test",
            "ranges": [
                {"section_label": "A", "first_folio": 1, "last_folio": 2},
                {"section_label": "B", "first_folio": 3, "last_folio": 4},
            ],
        }))

    def tearDown(self):
        self.temporary.cleanup()

    def add_record(self, record_id, folio_id, role="FOLIO"):
        (self.records / f"{record_id}.annotation.json").write_text(json.dumps({
            "record_id": record_id,
            "source": {"logical_role": role, "folio_or_cover_id": folio_id},
        }))

    def test_builds_complete_reproducible_assignment(self):
        self.add_record("R1", "1r")
        self.add_record("R2", "3v")
        self.add_record("COVER", "front", "COVER")
        result = build(self.records, self.source)
        self.assertEqual(result["record_count"], 2)
        self.assertEqual([item["section_label"] for item in result["records"]], ["A", "B"])
        self.assertEqual(len(result["assignments_sha256"]), 64)

    def test_refuses_uncovered_folio(self):
        self.add_record("R5", "5r")
        with self.assertRaisesRegex(ValueError, "no unique catalog section"):
            build(self.records, self.source)

    def test_refuses_cross_section_compound(self):
        self.add_record("R2", "2v_and_3r")
        with self.assertRaisesRegex(ValueError, "no unique catalog section"):
            build(self.records, self.source)

    def test_refuses_overlapping_ranges(self):
        data = json.loads(self.source.read_text())
        data["ranges"][1]["first_folio"] = 2
        self.source.write_text(json.dumps(data))
        self.add_record("R1", "1r")
        with self.assertRaisesRegex(ValueError, "ordered, disjoint"):
            build(self.records, self.source)


if __name__ == "__main__":
    unittest.main()
