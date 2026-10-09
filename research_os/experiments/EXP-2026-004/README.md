# EXP-2026-004 — breakthrough search / discriminating hypotheses

**Orchestrator:** Dyrygent V3.8.1 + Agent OS mission `675bab7d-0c4a-4cd6-b325-06d3901a151a` (initial budget cap USD 0.30; do **not** equate mission success with scientific proof).
**Source:** MS 408 Yale IIIF, archived source JPEGs (207/207 bit-integrity checks passed in [CI run 37866714094](https://github.com/SonGohan231/voynichese/actions/runs/37866714094)); 206 distinct digitally processed images. Existing material EXP-2026-001/002/003, [six-image pilot hypothesis](../EXP-2026-003/user_six_image_hypothesis_2026-10-09.md) and historic color/fold/order documents. **Manuscript not deciphered.**

## Most important NEW audit finding

**EXP003 v2: 4,800 machine-selected ROIs**, including **229 contour-defined shape candidates**: 21 circular, 18 elongated, 190 irregular. Matching resulted in 608 pre-limitation pairs, of which the first 180 were retained. But **178/180 retained matches were same-color yellow/ochre segmentation candidates** and **2/180 red segmentation candidates**. **Zero of the first 180 were independent structural contour matches.** This is a crucial confound, *not* a claim that there are no repeating shapes in the manuscript: color-matching-first pipeline did not adequately test structural/topological equivalence.

The source-backed EXP004 [structural ROI review queue](structural_roi_source_native_review_queue_2026-10-09.json) contains all **229 machine contour proposals** with original JPEG URL, SHA256 from the archived ledger (previously verified by byte rehash), original photo pixel dimensions, native-projected crop box and physical group IDs. These are **not human-confirmed masks**, because segmentation used working downscales max 960px.

Priority physical cases: q9 f67/f68 and q14 f85/f86. The geometric contour algorithm found only **3** candidates across the eight selected reference image canvases, and **no** candidates on **6** reference canvases (including the major Rosettes panorama). Zero detections **do not** establish absence of structural motifs. These six images require native-scale manual/independent CV review, not a negative scientific conclusion.

## Independent competing hypotheses and predeclared discriminating evidence

| Branch | H1 and task | Best rival (H0) | Acceptable potential signal | Hard veto |
| --- | --- | --- | --- | --- |
| T1 H-G/H-V | The same network of branch/junction/port shapes recurs in *different, physically independent* leaves, including rotations/views | Common medieval iconography, page layout, trees/rosettes commonly drawn similarly | Blind topology matching preserving degree, port count, cyclic order and unusual branching; external reference negatives, grouped out-of-sample test | Colour/dHash-only, multiple crops from one foldout counted as different leaves, zero human review |
| T2 H-C | Color carries repeatable compositional role; test old four-colors-plus-empty-mark model | Parchment background/scan illumination, common pigment palette, different painter or section | Gray-first blind object category, Lab-adjusted color predicts class across physical groups beyond stratified permutation | Digital color ≠ chemically identified pigment; v1 ochre/paper confounding |
| T3 H-D | Rosettes/q9 give true consistent 2.5D layering and front/back graph | Strong planar diagram 2D + illustrator’s overdraw and paper fold | Blinded native T-junction and occlusion labeling; compare MDL-penalized 2D vs constrained 2.5D on unseen junctions | Arbitrary parallax widget, unconstrained folding/rotation, depth cycles not resolved |
| T4 H-T | Text near independently defined visual classes differs beyond layout and scribe | Section-specific transcriptions / Currier / line count / page geometry | Independent IT2a/EVA text extraction, leave-bifolio-out predictive gain over null controls | Famous six screenshots, text with obscuring markup, unsealed EXP001 holdout |
| T5 codicological | Colour/topology/text correlations survive scientifically motivated *physical* ordering, including singulion scenarios | Result selected by optimizing alternative fold/order to visual score | Sensitivity bounds over pre-frozen physically admissible alternative order, not chosen after seeing outcomes | Fictional historical original order inferred from image similarity |

**Research ranking, not claimed findings:** T1 (potential distinct morphology signal) and T3 (falsifiable q9/q14 layering) first; T2 next (requires blind manually annotated object classes), T4 next (requires text alignment), T5 physical constraint across all, not a free parameter. Historical special-case hypotheses (4 colors+missing band, orientation of corner faces, possible five-line diagram) are preregistered *within* T2/T3 as specifically named tests with negative controls—not post-hoc narratives.

## Evidence grading and reproducibility gates

1. `E0_SOURCE`: verify original Yale canvas/photo identity, archive bytes SHA-256, original size and actual crop; note if image includes modern markup.
2. `E1_UNVERIFIED_MACHINE`: independent shape/color/composition candidate + precise ROI. **No claim of biological species or tower identity.**
3. `E2_BLIND_SEMANTIC`: two independent blinded annotation rounds and adjudicated disputes; maintain genuine UNKNOWN.
4. `E3_NULL_CONTROLLED`: preregister actual independent physical units, train/test split, thresholds and all tested families; null-model permutation preserves section / hand / Currier, page layout, physical group. Correct multiple comparisons via BH-FDR *q*≤0.05 (but never fake p-values).
5. `E4_INDEPENDENT_REPLICATION`: different reviewer/implementation, originally withheld physically distinct material, effect size + bootstrap confidence interval, controls, available code and full evidence.
6. `BREAKTHROUGH_CANDIDATE`: only if E4 passes *and* a specific rival H0 is rejected; not equivalent to decipherment. Otherwise use `EXPLORATORY`, `INCONCLUSIVE`, or `FALSIFIED_BY_CONTROL`.

Human semantic annotations to date: **0**; current baseline **EXPLORATORY**. Sealed `EXP-2026-001` HELD-OUT remains unopened.

## Agent tasks and source-access issues

- Research scout: scientific external comparisons including 2026 singulion [10.4000/16k0a](https://doi.org/10.4000/16k0a) and Yale McCrone material analysis, primary source quotations only.
- Morphology/graph science: source-native crop queue, explicit protocol comparison against matching by color/dHash.
- 2.5D: q9/q14 fold geometry with source-driven constraints and complexity-penalized 2D rival.
- Text and physical mapping: IT2a validation and corresponding potential visual ROI.
- External evidence judge: check whether each read actually happened, insist on REVIEW_PENDING where necessary.

**Current known orchestration blocker:** researched agent run `3125bc55-9e8c-4f7a-a9f0-a2d76e0d8900` failed, and read-only `get_effective_tools` showed `effectiveTools=[]` on this and another scout run, despite active connected host GitHub/read search tools. Generic QA/game-CI or agent-retention roles were selected for some scientific Keeper slots. Do not claim they supplied expert physical signoff. Routing issue: https://github.com/SonGohan231/agent-army-os/issues/175.

## Next executable units

1. Native-resolution manual or constrained CV inspection of all 229 structural candidate ROIs and six focus canvases where the 960px detector produced no candidates. Preserve explicit negative examples.
2. Convert verified original-shape ROIs to grayscale, silhouette skeleton, junction-port graphs; compare across **different physical bifolio groups**, then negative controls.
3. Validate q9/q14 folds, occlusions and authentic border intersections from primary conservation evidence.
4. Freeze T1–T5 with independent physical split and sample-size plan before significance checks. Preserve all FAILED or INCONCLUSIVE results, not only visually attractive pairs.
5. Publish evidence-linked results to the existing https://voynich-research-atlas.vercel.app; no simulated depth is scientific evidence.
