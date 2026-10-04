import copy
import hashlib
import subprocess
import sys
import unittest
from pathlib import Path

from readiness import (
    bind_adjudication_evidence_chain,
    build_readiness_report,
    deterministic_group_split,
    group_keys,
)


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

    def strata_inputs(self, records):
        manifest = {
            "schema_version": "1.0",
            "experiment_id": "EXP-2026-001",
            "records": [{
                "record_id": item["record_id"],
                "section_label": "SECTION_A" if index < len(records) / 2 else "SECTION_B",
                "section_claim_class": "DATA",
                "section_provenance": {
                    "source_reference": "drive:test-section-register",
                    "source_sha256": "c" * 64,
                },
                "scribe_label": "SCRIBE_1" if index % 2 else "SCRIBE_2",
                "scribe_claim_class": "DATA",
                "scribe_provenance": {
                    "source_reference": "test:scribe-register",
                    "source_sha256": "d" * 64,
                },
            } for index, item in enumerate(records)],
        }
        adjudication = {"records": [{
            "record_id": item["record_id"],
            "objects": [{}] * (1 + index % 5),
            "occlusions": [{}] * (index % 3),
        } for index, item in enumerate(records)]}
        return manifest, adjudication

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
        manifest, adjudication = self.strata_inputs(records)
        left = deterministic_group_split(records, report, "frozen-seed", manifest, adjudication)
        right = deterministic_group_split(
            copy.deepcopy(records), report, "frozen-seed", manifest, adjudication
        )
        self.assertEqual(left, right)
        sets = [set(left["assignments"][name]) for name in ("TRAIN", "VALIDATION", "HELD_OUT")]
        self.assertFalse(sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])
        self.assertEqual([12, 4, 4], [len(value) for value in sets])
        self.assertGreaterEqual(len(left["stratum_group_counts"]), 6)

    def test_split_refuses_missing_strata(self):
        records = self.eligible_records()
        report = build_readiness_report(records)
        with self.assertRaisesRegex(ValueError, "section strata manifest"):
            deterministic_group_split(records, report, "seed")

    def test_split_refuses_incomplete_strata(self):
        records = self.eligible_records()
        report = build_readiness_report(records)
        manifest, adjudication = self.strata_inputs(records)
        manifest["records"].pop()
        with self.assertRaisesRegex(ValueError, "cover exactly"):
            deterministic_group_split(records, report, "seed", manifest, adjudication)

    def test_split_refuses_section_conflict_inside_connected_leaf_group(self):
        records = [record(f"R{i:02d}", f"{i}r") for i in range(1, 20)]
        records.extend([record("R69", "69v_and_70r"), record("R70", "70v")])
        report = build_readiness_report(records)
        manifest, adjudication = self.strata_inputs(records)
        by_id = {item["record_id"]: item for item in manifest["records"]}
        by_id["R69"]["section_label"] = "SECTION_A"
        by_id["R70"]["section_label"] = "SECTION_B"
        by_id["R69"]["scribe_label"] = by_id["R70"]["scribe_label"]
        with self.assertRaisesRegex(ValueError, "crosses section or scribe labels"):
            deterministic_group_split(records, report, "seed", manifest, adjudication)

    def test_split_refuses_unknown_scribe(self):
        records = self.eligible_records()
        report = build_readiness_report(records)
        manifest, adjudication = self.strata_inputs(records)
        manifest["records"][0]["scribe_label"] = "UNKNOWN"
        with self.assertRaisesRegex(ValueError, "invalid or duplicate"):
            deterministic_group_split(records, report, "seed", manifest, adjudication)

    def test_compound_folio_prevents_leaf_leakage(self):
        records = [record("R69", "69v_and_70r"), record("R70", "70v")]
        keys = group_keys(records)
        self.assertEqual(keys["R69"], keys["R70"])

    def test_validated_adjudication_can_supply_independent_review(self):
        records = [record(f"R{i:02d}", f"{i}r", reviewed=False) for i in range(1, 21)]
        for item in records:
            item["page_inventory"]["regions"] = []
            item["local_relations"] = []
        adjudication = {
            "packet_sha256": "b" * 64,
            "records": [{
                "record_id": item["record_id"],
                "source_sha256": item["source"]["sha256"],
                "objects": [{"adjudicated_id": "O1"}],
                "occlusions": [],
            } for item in records],
        }
        validation = {
            "status": "ADJUDICATION_VALIDATED",
            "structurally_valid_for_readiness_chain": True,
            "packet_sha256": "b" * 64,
        }
        report = build_readiness_report(records, adjudication, validation)
        self.assertEqual(report["status"], "READY_FOR_SPLIT")
        self.assertTrue(report["gates"]["adjudication_revalidated"])
        self.assertTrue(report["gates"]["adjudication_covers_all_folios"])
        self.assertFalse(report["held_out_exposed"])

    def test_unvalidated_adjudication_fails_closed(self):
        records = self.eligible_records()
        adjudication = {"records": []}
        validation = {"status": "ADJUDICATION_REJECTED", "structurally_valid_for_readiness_chain": False}
        report = build_readiness_report(records, adjudication, validation)
        self.assertEqual(report["status"], "INCONCLUSIVE_NOT_RUN")
        self.assertFalse(report["gates"]["adjudication_revalidated"])

    def test_adjudication_chain_binds_exact_receipt_and_manifest(self):
        receipt = b"signed receipt bytes\n"
        validation = {
            "status": "ADJUDICATION_VALIDATED",
            "structurally_valid_for_readiness_chain": True,
            "errors": [],
        }
        verified = {
            "status": "FREEZE_RECEIPT_VERIFIED",
            "ready_for_adjudication": True,
            "manifest_sha256": "a" * 64,
        }
        packet = {
            "receipt_sha256": hashlib.sha256(receipt).hexdigest(),
            "freeze_manifest_sha256": "a" * 64,
        }
        self.assertEqual(
            bind_adjudication_evidence_chain(validation, verified, receipt, packet), validation
        )

    def test_adjudication_chain_rejects_forged_packet_status(self):
        validation = {
            "status": "ADJUDICATION_VALIDATED",
            "structurally_valid_for_readiness_chain": True,
            "errors": [],
        }
        verified = {
            "status": "FREEZE_RECEIPT_VERIFIED",
            "ready_for_adjudication": True,
            "manifest_sha256": "a" * 64,
        }
        forged = {"receipt_sha256": "0" * 64, "freeze_manifest_sha256": "a" * 64}
        result = bind_adjudication_evidence_chain(validation, verified, b"receipt", forged)
        self.assertEqual(result["status"], "ADJUDICATION_REJECTED")
        self.assertIn("adjudication_evidence_chain_invalid", result["errors"])

    def test_cli_refuses_cleartext_heldout_materialization(self):
        tool = Path(__file__).with_name("readiness.py")
        process = subprocess.run(
            [sys.executable, str(tool), "unused-records", "--split", "forbidden.json", "--seed", "seed"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(process.returncode, 2)
        self.assertIn("cleartext --split materialization is disabled", process.stderr)

    def test_cli_refuses_command_line_seed(self):
        tool = Path(__file__).with_name("readiness.py")
        process = subprocess.run(
            [sys.executable, str(tool), "unused-records", "--seed", "leaky-seed"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(process.returncode, 2)
        self.assertIn("command-line --seed is disabled", process.stderr)


if __name__ == "__main__":
    unittest.main()
