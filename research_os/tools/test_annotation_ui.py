import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "annotation" / "ui"


class AnnotationUiContractTests(unittest.TestCase):
    def test_static_entrypoint_and_design_reference_exist(self):
        for relative in ("index.html", "styles.css", "app.js", "README.md", "design/concept.png"):
            self.assertTrue((UI / relative).is_file(), relative)

    def test_ui_preserves_blindness_boundary(self):
        source = (UI / "app.js").read_text(encoding="utf-8")
        self.assertNotIn("AUTO_CANDIDATE", source)
        self.assertNotIn("analysis_output", source)
        self.assertNotIn("held_out", source.lower())
        self.assertIn("crypto.subtle.digest", source)
        self.assertIn("localStorage", source)

    def test_export_matches_required_submission_contract(self):
        source = (UI / "app.js").read_text(encoding="utf-8")
        for field in (
            "other_annotation_unseen",
            "automated_candidates_unseen",
            "model_predictions_unseen",
            "hypothesis_labels_unseen",
            "split_assignment_unseen",
            "record_id",
            "source_sha256",
            "objects",
            "occlusions",
        ):
            self.assertIn(field, source)

    def test_hidden_empty_state_has_explicit_css_override(self):
        css = (UI / "styles.css").read_text(encoding="utf-8")
        self.assertIn(".empty-canvas[hidden]{display:none!important}", css)


if __name__ == "__main__":
    unittest.main()
