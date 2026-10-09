# EXP-2026-004 — multifolio, multiview object-recurrence study

**Execution**: Agent OS / Dyrygent V3.8.1, mission `6bc4aa31-a68a-48a1-adb9-4e0d6a3271ff`.
**Code**: `research_os/tools/exp004_multifolio_object_atlas.py`.
**Executed CI**: [GitHub Actions #37890540768](https://github.com/SonGohan231/voynichese/actions/runs/37890540768) — SUCCESS.
**Evidence**: artifact `exp004-multifolio-candidate-atlas` ID `11598316336`, SHA256 ZIP `9b5b1c38908eccf69cbaa155986ac5f29895f58797a4452eb35a35e2b24a07b1`.

## Research question

Which physically distinct pages of Yale MS 408 show the *same historic depicted object* in other sizes, rotations or 2.5D projections, not merely images sharing generic ornament, drawing style, genre, pigments or curved strokes? The null hypothesis is ordinary medieval manuscript iconography, stylistic repetition and low-level shape similarities without 3D identity.

## Scope of 15 separate annotation types

| Category | Explicit field/protocol | Evidence to accept |
|---|---|---|
| Towers, turrets, crenellations, arches | object contour + merlon count; shape descriptor; connection ports; shade/no-shade | source-native image + blind two-annotator agreement |
| Botanical structure | axes, root/leaf/flower partitions, branch-degree signature, scale-free lengths | independent source mask + invariant landmarks |
| Rosette circular diagram | total visible ring counts, radii, center, sector count, spoke count, angular intervals, perimeter decorations | each ring human verified, machine Hough = proposal |
| Star motifs | exact number per system and star-point counts; direction and radial arrangement | original resolution, explicit no-visibility/ambiguity states |
| Human figures | all depicted figures, position, probable presentation, left/right/front face, gaze, arm orientation, pose + overlaps | two blind annotated poses and unknown rather than inferred sex |
| Ducts, passages, perimeter | connection graphs and ports, bridge/crossing/no join; colored vs uncolored | physically observed ink junctions before any direction inference |
| Paint, grayscale and absent paint | optical color mask vs outlines and uncolored areas | digital absence = NOT painted only after verified full native-resolution survey |
| Text and labels | EVA/IVTFF readings with transcriber variants and lines, nearest ROI by physical distance | independent folio/token and bbox provenance; no invented translation |

## Per-object record schema / reviewer workflow

Every candidate record has source Yale canvas OID, original JPEG SHA-256, folio label, physical bifolio, source-native pixel bounding box + normalized polygon, source IIIF crop URI, class probability and uncertainty, color appearance bin, actual manual material status, array of subparts, orientation, front/back occlusion edges, angular/radial attributes, associated text-line ID, token variants, annotator and blinded peer-review verdict.

For human figures: `face_orientation={LEFT,RIGHT,FRONT,UP,DOWN,OBSCURED,UNKNOWN}`, head-line direction measured in degrees only when a clear front-back face axis exists. Record figure counts `count_verified` with ambiguity interval `[min,max]`; do not turn undetected figures into zero.

For rosette: independently count outer rings, internal concentric rings, radial spokes, sectors, adjacent connections, stars in the region and each tiny point; machine-detected circles are hypotheses, not nine verified structures. Counts belong to one physically independent foldout sheet.

For shading: categorize `PAINTED_CHEMICALLY_UNVERIFIED`, `APPEARS_UNCOLORED_HIGH_RES`, `MASKED_OR_HIDDEN`, `NOT_EXAMINED`. Do not conflate parchment with yellow pigment; grayscale pHash alone does not prove intentionally blank drawing.

For textual evidence: lookup authoritative EVA/IVTFF transcriptions by independently verified folio and paragraph/label coordinates, de-duplicate hands/scribe and Currier A/B; treat unprovided text as `UNAVAILABLE`, **never OCR a marked-up crop as an authenticated translation**.

## Identity and perspective decision gates

**Gate 0:** existence of original source JPEG, hash, and objective source-to-page ID. Else STOP.
**Gate 1:** one semantic object category confirmed by two blinded annotators; if disagreement → UNCERTAIN.
**Gate 2:** near-matching topology: branch degree, limb count, cyclical port order, tower merlons, ornaments, ring sector/gap sequence, star arrangement, or figure arm-body-landmark layout. Shape-size normalizations preserve aspect unless independent reason.
**Gate 3:** geometry of alternate views: allow similarity transform (translation, uniform scale, discrete rotations); allow mirrored comparison only in separate, penalized branch; perspective homography/2.5D depth requires independent multi-point correspondences, coherent occlusion graph and consistent landmark cyclic order. Avoid optimizing arbitrary deformations.
**Gate 4:** exclude layout/common motif nulls matched by section/genre, scribe, pigment use and complexity, plus signed physical folio-group heldout; adjust for 4,800 ROIs/multiple pair search via permutation max-statistic/BH-FDR.
**Gate 5:** hold out entire independent bifolio; candidate must predict unseen landmark/count relation. If validation fails → SIMILAR_OUTLINE, not SAME_OBJECT.

Acceptance verdict categories:
`IDENTITY_SUPPORTED_INDEPENDENT` (requires all gates),
`SIMILAR_MOTIF_UNCONFIRMED`,
`DIFFERENT_TOPOLOGY`,
`UNOBSERVABLE`,
`INCONCLUSIVE`.
Current prior: all potential matches in `SIMILAR_MOTIF_UNCONFIRMED`; zero established SAME_OBJECT.

## Pilot results and next targeted folios

EXP004 source-index reuse, produced from 206 SHA-verified Yale archived image scans:
- 4,800 automated region proposals
- 991 candidate pairs under dHash threshold (after different canvas, physical-group and class controls)
- 125 retained in review queue
- 80 grayscale outline regions with less than 5% normalized bounding-box overlap with color candidates. **No evidence of intentional non-coloring**.
- First queue includes **f30v↔f32v, f47v↔f48v, f55r↔f57r**, and f105r↔f106r, but the strongest proposals are yellow-ochre digital shape components and **are not yet reliable identifiable objects**.
- No accepted annotations for actual towers, women, face directions, stars, sector subdivisions or textual labels.

These are to be reviewed in source-native image crops, with lower priority to parchment-ochre/saturated artifacts, and higher priority to unique structural landmarks.

## Subagent deliverables

1. Source/codicology — verify folio OIDs and independent physical-unit grouping; distinguish foldouts and uncertain rebindings.
2. Architectural CV — contours, crenellations and decorated borders in original Yale crops; count nubs/towers only following manual pass.
3. Rosette/star geometry — ring/spoke/sector templates + original color comparisons, with controls.
4. Human iconography — count faces and postures, relative orientation and uncertainty with independent annotation; no automated inference accepted alone.
5. Writing and labels — EVA/IVTFF source alignment; dynamic token table by section/Currier/scribe; no word meanings.
6. Red-team and statistics — predict withheld folios; exclude simple leaves/ovals and pigment confounds; independent Keeper not identical to executor.

**Scientific status (as of initial run): EXPLORATORY / NOT CONFIRMATORY.** Source integrity and candidate-generation tests passed; same-object 2.5D hypothesis has not passed.
