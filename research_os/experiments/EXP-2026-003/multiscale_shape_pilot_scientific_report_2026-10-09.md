# EXP-2026-003 — multisize contour matching on original Yale archive, exploratory 2026-10-09

## Evidence and status
- GitHub Actions [scale-invariant workflow #37887442679](https://github.com/SonGohan231/voynichese/actions/runs/37887442679): **success**, including synthetic ×3 invariance self-test and six original-source-image audits, each re-fetched and SHA-256-verified against the pinned archive ledger. This is technical pipeline verification ONLY.
- Unaltered GitHub workflow artifact: \`exp003-multiscale-geometry-candidates\`, artifact ID **11597071868**, archive digest \`sha256:b27e2f3907192a2561eadefdc512d18f6dcd9e9c8bc40c0ac9225507d641df4f\`. It contains \`multiscale_shape_candidates_2026-10-09.json\` and \`multiscale_shape_contact_sheet_2026-10-09.png\` with original-image crop/shape-mask pairs.
- Primary source archive: Yale MS408 via repo branch \`import-voynich-yale-scans-2026-07-23\`. Sampling: f9r, f10r, f75v, f76r, Rosettes f85v–f86r, botanical f94v–f95r. **f10r was an additional comparison folio, not one of the user's six images.**
- Technical counts: **188** candidate colored irregular regions (solidity <= 0.90) and **4,103** cross-canvas same-color-region comparisons.
- Score distribution of all tested pairs: p50=0.2380, p90=0.4654, p95=0.5528, p99=0.6760. The threshold is descriptive and non-confirmatory; maxima among thousands of pairs are expected and are affected by selection.
- **Scientific status:** EXPLORATORY NON-CONFIRMATORY. No validated botanical identity, common object, 2.5D perspective, directional flow or decipherment.

## Best scale-change examples among different canvas images

| Candidate regions | Working-photo linear-size ratio | Bbox width/height A vs B | Normalized binary silhouette IoU | Composite shape score | Rotation/mirror |
|---|---:|---|---:|---:|---|
| f10r:green:2 — f94v–f95r:green:22 | 7.185× | 1.236 : 1.500 | 0.7858 | 0.7965 | 0° / no |
| f10r:green:3 — f94v–f95r:green:35 | 8.000× | 0.938 : 1.333 | 0.7545 | 0.7690 | 180° / no |
| f10r:green:0 — f94v–f95r:green:34 | 9.125× | 0.781 : 0.833 | 0.7405 | 0.7354 | 0° / no |
| f10r:green:1 — f94v–f95r:green:30 | 9.429× | 0.980 : 0.952 | 0.6960 | 0.7166 | 270° / no |
| f9r:green:13 — f94v–f95r:green:0 | 0.1353× (or reciprocal ~7.39×) | 0.806 : 0.929 | 0.6040 | 0.6226 | 90° / no |

All size ratios are **working-image-pixel ratios after capping each source to a 1600px maximum image dimension**; they are NOT centimetres, not calibrated historical object size, and should not be used to hypothesize equal physical sizes without a folio-scale calibration.

### Critical interpretation
- The strongest matches are predominantly **simple leaf-like silhouettes** rather than distinctive knotted branching diagrams. Generic medieval leaf morphology, fill density and scanning can plausibly explain them; many apparent scale similarities are expected.
- Strong 7–9× leaf-like matches on f10r/f94v–95r warrant review, but do **not** establish that both pages depict identical botany/plant specimens, or hidden references.
- The source-native test yields a stricter result on f9r versus f94v–95r (IoU 0.604), weaker than the earlier unmasked marked-up screenshot pilot. Different segmentation, scope and non-independent candidate selection mean neither score is confirmatory.
- Contact sheet contains native source crops and normalized masks; modern user arrows are not present in the official archival input. RGB does not identify pigment chemistry.
- Source list is selective. Family-wide correction, independent blinded ROI annotations, and an out-of-sample foldout/bifolio-held-out evaluation are still missing.

## Required next actions
1. Review top matched contours in original resolution, not only the 1600px downscaled exploratory inputs. Reject isolated pigments, generic leaf silhouettes and artifacts, and annotate 3+ point landmarks and branch structure by two independent reviewers.
2. Add a manually measured or conservation-verified folio physical width/height calibration for cross-folio dimensional claims. Compare *dimensionless* aspect ratio and topology before physical magnification.
3. Independently preregister stricter nulls, including physically unrelated folios and same-section/same-scribe controls; test a graph + landmark feature combination, not mere silhouette IoU.
4. Preserve the 2026 Layfield/Fagin Davis singulion ordering alternative as external codicological sensitivity; never derive page order from visual matches.
5. Do not expose sealed EXP-2026-001/002 held-out, and do not claim scientific PASS from a GitHub CI PASS.
