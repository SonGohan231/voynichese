"""Unit/fixture tests for EXP-2026-002 fail-closed source parser.

These are synthetic CONTRACT tests, NOT evidence of a real IT2a replication.
"""
import hashlib
import tempfile
import unittest
from pathlib import Path

from exp002_prepare_it2a import (
    DataGateError, audited_bytes, build_audit, group_pages, parse_ivtff,
)


class Exp002SourceParserTests(unittest.TestCase):
    def test_two_leaves_of_one_bifolio_and_only_P_tokenization(self):
        synthetic = (
            "#=IVTFF EvaT 2.0 M 3\n"
            "<f1r> <! $Q=A $B=1 $L=A $H=1 $I=T $C=1>\n"
            "<f1r.1,@P0> <%>abc.def.?ghi\n"
            "<f1r.2,+L0> abc.def\n"
            "<f8v> <! $Q=A $B=1 $L=A $H=1 $I=H $C=1>\n"
            "<f8v.1,+P0> qokedy.shol\n"
        )
        pages, types = parse_ivtff(synthetic)
        self.assertEqual(types, {"P": 2, "L": 1})
        self.assertEqual(pages[0]["paragraph_tokens_strict"], 2)
        self.assertEqual(pages[0]["uncertain_fragments"], 1)
        physical = group_pages(pages)
        self.assertEqual(physical["QA-B1"]["leaves"], ["f1", "f8"])
        self.assertEqual([p["section"] for p in pages], ["BOTANICAL", "BOTANICAL"])

    def test_foldout_and_mixed_hand_never_imputed(self):
        synthetic = (
            "<f85r1> <! $Q=N $B=1 $L=B $H=4 $I=C>\n"
            "<f86v4> <! $Q=N $B=1 $H=@ $I=C>\n"
        )
        pages, _ = parse_ivtff(synthetic)
        groups = group_pages(pages)
        self.assertEqual(groups["QN-B1"]["leaves"], ["f85", "f86"])
        self.assertEqual(pages[1]["lfd_hand"], "@")
        self.assertIsNone(pages[1]["currier_language"])

    def test_digest_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "sample.ivtff"
            file.write_bytes(b"abc")
            good = hashlib.sha256(b"abc").hexdigest()
            self.assertEqual(audited_bytes(file, good), "abc")
            with self.assertRaisesRegex(DataGateError, "SHA256_MISMATCH"):
                audited_bytes(file, "0" * 64)

    def test_mismatched_locus_parent_rejected(self):
        with self.assertRaisesRegex(DataGateError, "LOCUS_PAGE_MISMATCH"):
            parse_ivtff(
                "<f1r> <! $Q=A $B=1 $H=1 $L=A>\n"
                "<f2r.1,@P0> abc.def\n"
            )

    def test_reused_page_identifier_rejected(self):
        with self.assertRaisesRegex(DataGateError, "DUPLICATE_PAGE"):
            parse_ivtff(
                "<f1r> <! $Q=A $B=1 $H=1>\n"
                "<f1r> <! $Q=A $B=1 $H=1>\n"
            )

    def test_tiny_or_incomplete_dataset_not_a_scientific_pass(self):
        with self.assertRaisesRegex(DataGateError, "PAGE_COVERAGE_CHANGED"):
            build_audit(
                "<f1r> <! $Q=A $B=1 $H=1 $L=A>\n",
                "<f1r> <! $Q=A $B=1 $H=1 $L=A>\n",
            )


if __name__ == "__main__":
    unittest.main()
