# EXP-2026-003 — First pixel-backed foldout geometry observations

**Date:** 2026-10-09 · **Status:** `EXPLORATORY / NOT INDEPENDENTLY REVIEWED`

## Evidence chain

- Archived native Yale source image hashes recomputed from actual JPEG bytes: [207/207 earlier baseline](https://github.com/SonGohan231/voynichese/actions/runs/37866714094).
- Real Hough/Canny geometry measurement: [run #37883162521](https://github.com/SonGohan231/voynichese/actions/runs/37883162521), job 113667203643. Its **source processing step succeeded**, all 8/8 JPEGs decoded and SHA-verified, synthetic nine-circle test passed. **The GitHub job's overall conclusion was failure because the publishing stage rebased against a simultaneously committed version of the same JSON**; the report is independently present in the branch. Source-publishing collision fixed in workflow commit `e5a866c6ca931ca6401c68c457e83b43e57faae3`.
- [Stored full result and normalized coordinates](./foldout_geometry_probe_2026-10-09.json), schema `exp-2026-003/foldout-geometry-exploratory-v1`, original full-size photographic dimensions and per-candidate Hough edge support.

## Eight-source results

| Yale OID | Source folio label | Hough circular candidates after edge-support filter | Long line candidates |
|---|---|---:|---:|
| 1006194 | f67r | 2 | 21 |
| 1006195 | f67v | 1 | 9 |
| 1006196 | f68r | 0 | 15 |
| 1006197 | f68v | 3 | 16 |
| 1006228 | f85r part | 6 | 24 |
| 1006229 | f85r part / f86v part | 8 | 24 |
| 1006230 | f86v part | 10 | 24 |
| 1006231 | f85v and f86r Rosettes recto foldout | 7 | 20 |
| **Total** | | **37** | **153** |

These are detector proposals after de-duplicating nearby Hough centers and applying a radial edge-support threshold 0.32; they are **not** a census of drawn rosettes nor a list of identified physical creases. Some long-line counts hit the code's per-canvas cap of 24 and cannot be interpreted as true line totals.

## Rosettes native high-resolution photograph

Yale canvas **1006231**, label `85v and 86r (foldout)`, original 7925 × 7268 JPEG. Seven Hough center coordinates (unit-square fractions, not historical topology):

| Center x | Center y | Radial edge support | Triage |
|---:|---:|---:|---|
| 0.5560 | 0.1788 | 0.771 | Stronger image-line fit |
| 0.2387 | 0.1992 | 0.808 | Stronger image-line fit |
| 0.5409 | 0.4947 | 0.675 | Stronger image-line fit |
| 0.8333 | 0.4976 | 0.633 | Stronger image-line fit |
| 0.6964 | 0.6071 | 0.325 | Marginal; possible false positive |
| 0.5329 | 0.6963 | 0.358 | Marginal; possible false positive |
| 0.8084 | 0.8194 | 0.508 | Stronger image-line fit |

The **seven machine responses are not a contradiction of the commonly described nine-roundel composition**. Hough misses weak, interrupted or noncircular ink rings and may also overfit large circular arcs; two candidate centers barely pass the .32 cutoff. The upper-right and some lower-left geometries will require crop-based visual annotation. From this photograph alone we **cannot** determine true depth, historical fold axis, named castle, plant identity or geographic map correspondence.

Edge density was highest in the middle 3×3 image tile (row 2 / col 2), 0.080457 of pixels at the working scale. This reports drawn-line density **only**, not a physical height, topographic center or semantic importance.

## Three preregisterable rival hypotheses

- `H0_PLANAR`: all loops, passages and tower-like line segments are a planar medieval schematic. Any depth impression can result from a conventional ornamental diagram and restoration/photo geometry.
- `H1_2POINT5D`: occlusion cues (T-junctions, relative sizes and coherent layer ordering) agree across independent crops and different drawing motifs better than a planar null. Test blind annotator agreement against orientation/permutation controls. Do not generate a visual illusion and then use that illusion as its own evidence.
- `H2_PHYSICAL_FOLD_TOPOLOGY`: a geometry model supported by documented parchment folds and binding, independently of the interpreted image content; no rotation may be optimized against matching colored marks without physical validation.

## Immediate next steps

1. Native-resolution expert reviews of the five stronger and two marginal Rosettes candidate centers using their original Yale OIDs and coordinates. Independently annotate all nine visually present roundels from original high-res crops, including Hough false negatives.
2. Isolate plausible tower/merlon silhouettes versus botanical/astronomical symbols with grayscale contours; record their source bboxes, background confounds, attribution, and explicit `UNKNOWN` for any ambiguous object.
3. Have two independent codicology reviewers trace photographed crease and sewing features; any confidence score must be based on *the observed surface*, not an assumed 3D reconstruction.
4. Run negative-control blank parchment tiles, rotated drawings and adjacent-quire copies to calibrate Hough false alarms and dHash correlations.
5. Keep EXP-2026-001 held-out unopened and EXP-2026-002 original O2 ordering `UNKNOWN`; current science verdict remains `INCONCLUSIVE_NOT_RUN`.

Visible numeric output is a reproducible **photograph geometry measurement**, not proof of the manuscript's historical meaning.
