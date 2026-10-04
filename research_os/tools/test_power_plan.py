import json
import tempfile
import unittest
from pathlib import Path

from power_plan import build_power_plan


class PowerPlanTests(unittest.TestCase):
    def test_compound_pages_reduce_independent_group_count(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, folio in enumerate(("1r", "1v", "2r_and_3v", "3r"), 1):
                record = {
                    "record_id": f"R{index}",
                    "source": {"logical_role": "FOLIO", "folio_or_cover_id": folio},
                }
                (root / f"{index}.annotation.json").write_text(json.dumps(record), encoding="utf-8")
            report = build_power_plan(root, held_out_fraction=0.5, target_standardized_effect=4.0)
            self.assertEqual(report["inventory"]["folio_records"], 4)
            self.assertEqual(report["inventory"]["independent_folio_groups"], 2)
            self.assertEqual(report["inventory"]["planned_held_out_groups"], 1)

    def test_underpowered_plan_fails_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = {
                "record_id": "R1",
                "source": {"logical_role": "FOLIO", "folio_or_cover_id": "1r"},
            }
            (root / "1.annotation.json").write_text(json.dumps(record), encoding="utf-8")
            report = build_power_plan(root, target_standardized_effect=0.1)
            self.assertEqual(report["status"], "UNDERPOWERED")


if __name__ == "__main__":
    unittest.main()
