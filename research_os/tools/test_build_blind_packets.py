import json
import tempfile
import unittest
from pathlib import Path

from build_blind_packets import build_packet


class BlindPacketTests(unittest.TestCase):
    def test_packets_share_universe_and_exclude_nonfolio(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = root / "records"
            records.mkdir()
            protocol = root / "README.md"
            protocol.write_text("frozen protocol", encoding="utf-8")
            base = {
                "record_id": "R1",
                "source": {
                    "logical_role": "FOLIO",
                    "relative_path": "data/original.jpg",
                    "sha256": "a" * 64,
                    "image_file_grid_px": {"width": 10, "height": 20},
                },
            }
            (records / "1.annotation.json").write_text(json.dumps(base), encoding="utf-8")
            cover = json.loads(json.dumps(base))
            cover["record_id"] = "COVER"
            cover["source"]["logical_role"] = "COVER"
            (records / "2.annotation.json").write_text(json.dumps(cover), encoding="utf-8")
            left = build_packet(records, protocol, "A")
            right = build_packet(records, protocol, "B")
            self.assertEqual(left["record_count"], 1)
            self.assertEqual(left["record_universe_sha256"], right["record_universe_sha256"])
            self.assertNotEqual(left["packet_id"], right["packet_id"])
            rendered = json.dumps(left).lower()
            self.assertNotIn("overlay_path", rendered)
            self.assertNotIn("split_assignment", rendered)
            self.assertNotIn("prediction", left["records"][0])


if __name__ == "__main__":
    unittest.main()
