import copy
import unittest

from readiness import build_readiness_report, deterministic_group_split, group_keys


def record(record_id, folio, reviewed=True):
    return {
        "record_id": record_id,
        "source": {
            "source_file_id": "SRC-" + record_id,
            "folio_or_cover_id": folio,
            "logical_role": "FOLIO",
            "native_scan_grid_status": "VERIFIED_NATIVE",
            "sha256": "a" * 64,
            "provenance": {"verification_status": "VERIFIED"},
        },
        "page_inventory": {"regions": [{"id": "r"}]},
        "illustration_inventory": {"objects": []},
        "text_geometry": {"regions": []},
        "local_relations": [{"id": "l"}],
        "quality_control": {"review_status": "BLIND_REVIEWED" if reviewed else "NOT_REVIEWED"},
    }


class ReadinessTests(unittest.TestCase):
    def eligible_records(self):
        return [record(f"R{i:02d}", f"{i}r") for i in range(1, 21)]

    def test_unannotated_data_refuses_split(self):
        item = record("R1", "1r", reviewed=False)
        item["page_inventory"]["regions"] = []
        item["local_relations"] = []
        records = [item]
        report = build_readiness_report(records)
        self.assertEqual(report["status"], "INCONCLUSIVE_NOT_RUN")
        with self.assertRaisesRegex(ValueError, "split refused"):
            deterministic_group_split(records, report, "seed")

    def test_split_is_deterministic_and_disjoint(self):
        records = self.eligible_records()
        report = build_readiness_report(records)
        left = deterministic_group_split(records, report, "frozen-seed")
        right = deterministic_group_split(copy.deepcopy(records), report, "frozen-seed")
        self.assertEqual(left, right)
        sets = [set(left["assignments"][name]) for name in ("TRAIN", "VALIDATION", "HELD_OUT")]
        self.assertFalse(sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])
        self.assertEqual([12, 4, 4], [len(value) for value in sets])

    def test_compound_folio_prevents_leaf_leakage(self):
        records = [record("R69", "69v_and_70r"), record("R70", "70v")]
        keys = group_keys(records)
        self.assertEqual(keys["R69"], keys["R70"])


if __name__ == "__main__":
    unittest.main()
