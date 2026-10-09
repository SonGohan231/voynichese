"""Synthetic 3x3 ring regression, not proof about Voynich source images.

The CV algorithm should retain substantially fewer false circle candidates than
raw Hough output, while all suggestions remain HUMAN_UNVERIFIED.
"""
from pathlib import Path
import sys
import cv2
import numpy as np

TOOLS = Path(__file__).resolve().parents[2] / "tools"
sys.path.insert(0, str(TOOLS))
from exp003_foldout_geometry_probe import derive_geometry

w, h = 1650, 1500
image = np.full((h, w, 3), 226, dtype=np.uint8)
for y in (270, 750, 1230):
    for x in (275, 825, 1375):
        cv2.circle(image, (x, y), 150, (55, 55, 55), 4, cv2.LINE_AA)
        cv2.circle(image, (x, y), 122, (55, 55, 55), 3, cv2.LINE_AA)
        cv2.putText(image, "x", (x-15, y+10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (100,100,100), 2)
result = derive_geometry(image, "1006231")
candidate_count = result["total_detected_circular_candidates"]
assert 6 <= candidate_count <= 14, result
assert candidate_count < result["unfiltered_hough_circle_count"], result
assert len(result["grid_tile_edge_density"]) == 9
assert result["confirmed_rosettes"] == 0
assert result["confirmed_towers"] == 0
assert result["confirmed_physical_fold_axes"] == 0
assert all(not x["human_verified"] for x in result["candidate_circular_regions"])
print("SYNTHETIC_IMAGE_SMOKE_PASS", "circle_candidates",candidate_count,
      "raw_hough",result["unfiltered_hough_circle_count"],
      "meaning_of_actual_Voynich_images","NOT_ESTABLISHED")
