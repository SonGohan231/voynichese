# EXP-2026-003 — branch and protrusion geometry after scale normalization (09 October 2026)

## Execution record

- Requested by user through **Dyrygent V3.8.1**; real Agent OS mission: `99adfca9-c79d-46f2-a79e-d0eb745d506d` (not a scientific PASS; keep orchestration result separate from GitHub CI).
- Reproducible GitHub Actions: [branch-geometry run 37888811268](https://github.com/SonGohan231/voynichese/actions/runs/37888811268), job **success** after repair.
- Output artifact: `exp003-branch-geometry-exploratory`, ID **11596969656**, archive SHA-256 `e98de3def030b78a4df2a1a9c799d9ae098ee2826f1974d3cffd31e26b717893`.
- Source code: `research_os/tools/exp003_branch_geometry_pilot.py`; pinned workflow `.github/workflows/exp003-branch-geometry.yml`.
- Yale archival JPEG bytes re-downloaded and SHA256 checked by the existing `fetch_image()` before analysis, then working image capped at 1600 px long axis. This does NOT mean native-resolution structural lines were annotated.
- **Scientific verdict: `INCONCLUSIVE_NONCONFIRMATORY`**. CI success means code ran; it does not establish real object identity, botanical classification, semantic color coding, directed flows or 2.5D perspective.

## Scope, calculations and data

Earlier exploratory silhouette pilot examined f9r, f10r, f75v, f76r, the f85v–f86r Rosettes foldout and f94v–f95r. This follow-up reused the same discovery folios and 112×112 normalized colored-contour ROI masks. For each contour it computed digital morphological skeleton, numbers of detected endpoints and junction clusters, significant convexity defects/indentations and radial profile peaks and gap spacing; composite exploratory similarity incorporates baseline IoU. Rotations and mirrored comparisons remain recorded from the baseline.

| Technical count | Result |
|---|---:|
| Irregular digital color regions | 188 |
| Same-color comparisons between source canvases | 4,103 |
| Filtered structurally eligible comparisons | 3,625 |
| 50th / 90th / 95th / 99th percentile of exploratory score among eligible candidate pairs | 0.2134 / 0.38693 / 0.44983 / 0.58156 |

**Previously selected examples**, NOT statistically independent test cases:

| Discovery pair | Prior normalized silhouette IoU | New structural score | Differential digital skeleton features | Rank among eligible candidate comparisons |
|---|---:|---:|---|---:|
| f10r:green:2 ↔ f94v–f95r:green:22 | 0.7858 | **0.52065** | 1 endpoint, 1 junction, 1 notch, 2 radial peaks | 72 / 3625 |
| f10r:green:3 ↔ f94v–f95r:green:35 | 0.7545 | **0.43277** | **12 endpoints, 10 junctions**, 0 notches, 1 radial peak | 217 / 3625 |
| f10r:green:0 ↔ f94v–f95r:green:34 | 0.7405 | 0.35216 | 8 endpoints, 5 junctions, 5 notches, 1 radial peak | 508 / 3625 |
| f9r:green:13 ↔ f94v–f95r:green:0 | 0.6040 | 0.31008 | 9 endpoints, 9 junctions, 4 notches, 1 radial peak | 731 / 3625 |

Unlike previous contour matching, topologically inconsistent examples are penalized; a superficially similar simple leaf need not have the same underlying skeleton.

## Caveats and remaining scientific gates

1. Color-region extraction is not independently adjudicated botanical/architectural segmentation. A thin line interrupted by low pigment intensity can introduce multiple artificial endpoints and junctions. Automated counts represent **extracted masks**, not established historic branching facts.
2. Folios and four interesting pairs were chosen during development. The empirical distribution and ranks are useful diagnostics, **not p-values**; there is no preregistered, independent held-out, no multiple-testing corrected claim, no true section/scribe matched nulls or physical-bifolio cluster bootstrap.
3. Scientific controls still required: neutral complexity-matched motifs from independent medieval diagrams, source-original full-resolution hand-reviewed ROI polygons, two blind annotators, calibrated orientation/mirroring choices, physical group-aware split, null maximum-statistic correction and reviewer disagreement adjudication. The sealed EXP001/EXP002 HELD-OUT must remain untouched.
4. Semantic inference (same plant, coded system, 2.5D depth or Voynichese translation) is not established by a high morphology score.
5. If there are substantial self-intersecting contours, OpenCV convexity cannot be measured reliably; the implementation marks such objects *ineligible*, rather than treating unknown as zero notches. A synthetic branch shape and simple convex control passed CI unit checks.

## Interpretation

The targeted comparison supports a **methodological improvement**: contour IoU alone is insufficient; complexity, junctions and notch sequence should be checked jointly. It does **not** yet support an encoded scale-independent vocabulary. Further progress depends on neutral, independently reviewed source annotations and proper held-out controls.
