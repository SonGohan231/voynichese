import json
import tempfile
import unittest
from pathlib import Path

from build_strata_manifest import build


class BuildStrataManifestTests(unittest.TestCase):
    def test_merges_exact_record_universe(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            section = root / "section.json"
            scribe = root / "scribe.json"
            section.write_text(json.dumps({
                "claim_class": "DATA",
                "source": {"register_path": "section-source.json", "register_sha256": "a" * 64},
                "records": [{"record_id": "R1", "section_label": "BOTANICAL"}],
            }))
            scribe.write_text(json.dumps({
                "claim_class": "DATA",
                "source": {"source_url": "https://example.test/ZL.txt", "source_sha256": "b" * 64},
                "records": [{"record_id": "R1", "scribe_label": "MIXED_1_5"}],
            }))
            result = build(section, scribe)
            self.assertEqual(result["records"][0]["scribe_label"], "MIXED_1_5")
            self.assertEqual(result["records"][0]["section_label"], "BOTANICAL")

    def test_refuses_mismatched_record_universe(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            section = root / "section.json"
            scribe = root / "scribe.json"
            section.write_text(json.dumps({
                "claim_class": "DATA", "source": {},
                "records": [{"record_id": "R1", "section_label": "A"}],
            }))
            scribe.write_text(json.dumps({
                "claim_class": "DATA", "source": {},
                "records": [{"record_id": "R2", "scribe_label": "HAND_1"}],
            }))
            with self.assertRaisesRegex(ValueError, "same records"):
                build(section, scribe)


if __name__ == "__main__":
    unittest.main()
