# EXP-2026-003 — Voynich visual motif, color and 2.5D protocol

**Status 2026-10-09:** exploratory machine indexing completed for 206 unique archived high-resolution Yale JPEGs. **NO** confirmed visual interpretation, botanical identification, physical 3D geometry or historical order. No EXP-2026-001 held-out data used.

## Locked provenance, levels of evidence

- Digital source: Yale IIIF manifest `https://collections.library.yale.edu/manifests/2002046`, 213 canvases, 206 unique JPEG images in historical archive branch `import-voynich-yale-scans-2026-07-23`, 207 files because `11r` is duplicated across source batches.
- Existing physical group map: 52 extant/partly surviving groups plus six wholly missing placeholders. **Never** infer missing photo pixels for lost material.
- Authenticity check: GitHub Actions [37866714094](https://github.com/SonGohan231/voynichese/actions/runs/37866714094) independently recomputed 207/207 archived JPEG SHA-256 values; this is **bit-level archive integrity only**, not proof of scan color accuracy, historical paint layer or physical binding.
- Exploratory CV [EXP003 full-run workflow](https://github.com/SonGohan231/voynichese/actions/runs/37869959870) decoded 206 images, downscaled image working copies at max 960 px on longest side and generated ROI proposals + color masks. Native resolution original is retained for independent crop-based examinations. Do not claim full-resolution semantic classification from low-resolution proposals.
- The initial HSV `v1` mask grossly confounded warm parchment with yellow/ochre paint. Its percentages **must not** be interpreted as historical pigment frequencies. `v2` adds per-image parchment-background estimation and stricter chroma/brightness thresholds. Neither v1 nor v2 is color-chart calibrated or equivalent to chemical analysis.

## Four independent research packages

### A. Manuscript-wide reference atlas, including sections

Every validated region must identify `canvas_oid`, image original JPEG SHA-256, actual image width/height, normalized `bbox_xywh` or polygon, category label, source/date, annotator, evidence tier and reviewer verdict. Folio, composite canvas and physical bifolio are distinct units, even when printed labels look similar. Every ROI requires an original high-resolution crop, not solely a resized image. All 206 image canvases plus seven ancillary Yale photo canvases must be listed; mark unavailable bytes as `NOT_ARCHIVED`, never fabricate.

### B. Color use / material science

Reference: McCrone Associates, *Materials Analysis of the Voynich Manuscript* (2009), made available by Yale at `https://beinecke.library.yale.edu/sites/default/files/files/voynich_analysis.pdf`:
- f26r: green copper complex/possible atacamite; blue azurite; red-brown root ochre/hematite; iron-gall ink.
- f47r: green copper-based material, red-brown root ochre/hematite and ink.
- f78r: blue passage/water azurite and black ink.

**Do not universalize** these locally sampled compounds to every similar-looking pixel. The chronological order of painting and ink application is disputed; present Rene Zandbergen, Lisa Fagin Davis and others as source-attributed and distinguish physical microscopy from online interpretative claims.

Predefined exploratory comparisons to prepare *after independent manual labels*:
1. Color visibility (HSV/Lab) versus visually confirmed **object category**, controlling for folio/section and low-quality scan conditions.
2. Color variation between repeated outlines in different folios: first align grayscale edges; test whether coloration differs while geometry persists.
3. Painted-color transfer across putative physical opposite pages, **subject to codicological physical constraints**; do not infer binding order by fitting the color result.
4. Baseline: section-preserving permutation, quire-clustered bootstrap CIs and negative-control pseudo-objects cut from the parchment background. Apply BH-FDR within preregistered color tests.

Blind independent annotators must identify *foliage, flower, root, stem, water/channel, garment, vessel* without colors, then a second phase can test color association; the labeler must not be given the predicted textual interpretations.

### C. Matching repeating parts and architectural forms

Taxonomy:
- `BOTANICAL_ROOT`, `BOTANICAL_LEAF`, `BOTANICAL_STEM`, `BOTANICAL_FLOWER`, `BOTANICAL_OTHER`.
- `ROUND_DIAGRAM`, `STAR_LIKE`, `VESSEL`, `PIPE_CHANNEL`, `WAVE`, `TOWER_CRENEL`, `BUILDING_OR_WALL`, `GEOMETRIC_CONTOUR`.
- `FOLD_OR_STITCH`, `PARchMENT_DAMAGE`, `UNKNOWN`.

Propose candidate parallels using dHash and contour descriptors, optionally ORB/SIFT + RANSAC; freeze thresholds and calibrate against shuffled candidate pairs matched by scale, page section and background. Report all selected *and rejected* candidates with full ROI coordinates and uncertainty. A pixel-shape match is **not** a botanical species match, nor proof of identical tower or symbol.

For `TOWER_CRENEL`, do not force the famous swallowtail crenellations on Rosettes to be a named castle; two rival interpretations (generic iconographic style vs. depicted specific architecture) should be coded separately and reviewed by a medieval architecture specialist.

### D. Test the *representation* of 2.5D

Primary probes: f85v/f86r Rosettes (Yale canvas OID `1006231`; related `1006228–1006230`) and q9 foldouts f67/f68 (OIDs `1006194–1006197`). For each:
- Trace true **physical** fold axes, seams and present paper joins only from externally validated scans and conservation-source evidence.
- Record observed overlap ordering, edge termination/T-junctions, size gradients, shading differences and drawing-direction/orientation. Require source crop and explicit alternative 2D explanation.
- Create two annotated renders: purely 2D flat drawing and *assumption-labeled* layered 2.5D. Assign arbitrary per-layer depth only in sandbox; never advertise it as measured.
- Predeclare rotations consistent with independently validated fold topology. Do not optimize rotation or fold sequence to maximize perceived 3D coherence.
- Compare blind reviewer consistency and orientation-dependent alignment against a flat 2D control. Without independently verified depth cues, verdict `GEOMETRY_UNDETERMINED`.

## Decision gates

| Gate | Requirement |
| --- | --- |
| JPEG byte provenance | Confirmed in CI, 207/207 |
| Full set of 206 photo candidates | First pass completed (960-pixel working copies) |
| Background-aware digital colors | V2 rerun required before interpretation |
| Independent semantic ROI verification | **0 accepted so far** |
| Physical review of all 52 preserved units | **NOT DONE** |
| Historical original order | `UNKNOWN` |
| Decipherment / semantic significance | `INCONCLUSIVE_NOT_RUN` |

Visual candidates may be shown in the dashboard only if `human_reviewed=false` and `semantic_identity=UNKNOWN` are preserved. Local manual annotations must retain reviewer-state distinction and be exportable as source-backed JSON.

## Research software and interface

- Public dashboard: https://voynich-research-atlas.vercel.app
- Branch PR: https://github.com/SonGohan231/voynichese/pull/14
- Initial computer-vision pipeline: `research_os/tools/exp003_yale_visual_inventory.py`
- Annotator output: `research_os/experiments/EXP-2026-003/visual_scan_index_2026-10-09.json`
- Independent codicology queue: `research_os/experiments/EXP-2026-002/physical_photo_expert_review_queue_2026-10-09.json`

**No scientific PASS** can be granted solely on CI passing or impressive-looking depth/parallax visualizations.
