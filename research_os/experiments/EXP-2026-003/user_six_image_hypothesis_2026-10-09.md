# EXP-2026-003 / UIMG-20261009 — Directed-graph, color and 2.5D user hypothesis

## Status and scope

**Status: EXPLORATORY / PROTOCOL DRAFT / NOT CONFIRMATORY.** These six images were already used to motivate the hypotheses, so they are training/pilot material, NEVER a clean held-out test. This note is linked to the existing EXP-2026-003 visual atlas; it does not replace EXP-2026-001/002 preregistrations, overturn source binding reconstruction, or claim manuscript decipherment.

- Image manifest: [user_six_image_manifest_2026-10-09.json](user_six_image_manifest_2026-10-09.json). SHA-256 in the manifest hashes the *uploaded and sometimes marked-up screenshot files*, not Yale originals.
- Prior spatial model: [PR #12](https://github.com/SonGohan231/voynichese/pull/12), H-SPATIAL-PERSPECTIVE-LAYER-MODEL-01.
- Current exploratory image indexing: [PR #14](https://github.com/SonGohan231/voynichese/pull/14), [EXP-2026-003 protocol](research_protocol_2026-10-09.md): 206 unique Yale historical JPEG photos indexed at low working resolution, **zero independently accepted semantic ROIs**.
- Yale original bound manuscript collection: https://collections.library.yale.edu/manifests/2002046 ; all identity assertions require exact canvas/source-native crop/hash mapping.
- Reviewer must not see proposed meanings before neutral annotation.

**Image observations are observations of these screenshots, not authenticated interpretations of the underlying historical original.** Contemporary arrows and colored outlines may obscure genuine edges. The fourth image is white-obscured text and cannot support transcription or word-frequency claims. Image six is a montage of three apparent folios, not a single independent manuscript page. Image five appears to be the Rosettes foldout but exact folio/canvas metadata still requires source verification.

## Explicitly competing explanations

H0-A: Conventional medieval illustrative convention (plants, nymphs, diagram geometry) explains strokes and pigment without universal directed mechanism.

H0-B: Illustration composition, available pigments, illustrator/section identity, region shape and conservation/sampling artifacts explain colors, local links, and apparent layers.

H-G (topology): Certain neutral local visual object graphs recur across physically distinct folios more often than matched iconographic null models.

H-C (color zoning): After parchment- and scan-aware normalization, local color predicts pre-annotated object/region class above section/hand/Currier/folio-controlled controls. Color is NOT equivalent to a historical pigment diagnosis or depth.

H-D (depth): Independent occlusion/T-junction, border termination and depth-order cues support consistent layered 2.5D relations beyond a flexible flat 2D diagram.

H-V (views): Two or more seemingly different illustrations can be matched as alternative views of one stable structural object using topology, port counts, contour-order and occlusion constraints with out-of-sample predictions.

H-T (text): Local illustration classes and textual token distributions co-vary beyond section/scribe/Currier/page layout and local text baseline. This is NOT a translation.

*Conditional arrows*: H-G begins as an **UNDIRECTED graph** with edge classes TRUE_JOINT / OVERLAP_NO_JOIN / UNCERTAIN. A directed arrow may be inferred ONLY from at least two independently identifiable native cues at that very junction (taper, open/closed terminal morphology, authentic directional ornament, asymmetrical branch insertion, etc.), checked in original scan and agreed by blinded annotators. User drawn arrows NEVER count as native cues.

## Preprocessing / manifest audit

1. Review matching of six screenshot SHA-256 entries to source-native Yale canvas and exact full-resolution cropping coordinates. Record verified, ambiguous, and failed matches. Do not force a folio assignment.
2. Explicitly annotate source-image content separate from contemporary markup: thick red/black/white arrows, handwritten “407”, blue ellipse and white text obscuration. Remove/mask added marks; any overlap with authentic strokes must be an UNOBSERVABLE pixel zone, not AI-inpainted evidence.
3. Use independent no-color/neutral class pass on original-resolution source ROI. Record polygon coordinates, folio, canvas OID, source native image hash, annotator, obscured fraction and reviewer verdict.
4. Freeze original manuscript physical groups and potential folio order **from external codicology**, never from best visual topology fit. Preserve mixed-scribe classification and physical foldout group joins.
5. Use parchment-aware photometric normalization; HSV v1 parchment/yellow confounding already documented in EXP-003. Preserve color uncertainty, no claim of pigment molecular origin from jpg RGB. Yale McCrone report applies locally sampled f26r/f47r/f78r, not all similar pixels.
6. Track archival source pixels only; resized 960px initial candidates are proposals, not high-resolution full-corpus annotation.

## Pilot case mapping, no semantic conclusions

| Screenshot | Basic independent observation | User mark / non-original confound | Next source task |
|---|---|---|---|
| IMG01 | Brown root/tuber, red branching stems, green lobed foliage, red clustered inflorescences | Thick black and red direction arrows | Match original folio; extract native botanical skeleton and real junctions |
| IMG02 | Upper/lower human figure assemblies, horizontal blue zone, radial/vertical thin strokes, thin curved conduit | Thick red arrows; thick blue ellipse | Distinguish hanging strokes vs plumbing, vertical layout vs flow; freeze true connections |
| IMG03 | Faces or head-like marks amid green/blue/red regions and overlapping contours | Black/white arrows and writing “407” | Test independently whether boundary and occlusion are authentic |
| IMG04 | Short crop of Voynichese-like glyphs | White obscuration | Exclude from EVA/transcription until unobscured source aligned |
| IMG05 | Connected concentric/radial rosette diagrams on a folded sheet | None apparent | Source-match Rosettes folio/canvas and fold geometry; no free rotation optimization |
| IMG06 | Three botanical diagrams, roots/bulbs, stems and foliage with different structures | Composite is a layout artifact | Map each original folio separately; consider unit independence |

## Prospective tests (not yet run; formal freeze required)

For all tests, final alpha is BH-FDR q <= 0.05 across five families, and independent annotation agreement should be measured before model training. Define sample sizes and evidence-based minimum detectable effects from the actual manuscript-unit count BEFORE inference; missing power gives INCONCLUSIVE, not PASS.

**T1 — Topological transfer (H-G)**. Build native-stroke undirected graphs from blind polygons and junction labels. Train matching tolerances and graph edit weights on a prespecified subset of physical manuscript groups; score disconnected test groups. Nulls: edge rewiring preserving degree/connectedness, similar-sized ordinary medieval botanical/diagram contours and section-matched shuffled assignments. Metrics: graph edit distance / normalized topology score; false match rates, bootstrap CI by physical group. Reject hypothesis if held-out separation vanishes or matches section/layout baselines.

**T2 — Color-zone consistency (H-C)**. Grayscale-only review determines object region classes FIRST. Then test whether locally corrected Lab/HSV predicts component class via leave-physical-group-out modeling. Nulls: within-section color-label permutation, similarly sized parchment pseudo-objects, alternative scan-condition controls. Metrics: macro-AUC/balanced accuracy + confidence interval, effect above null; do not count color sampled multiple times on one page as independent images. Check dark-pigment gradient sensitivity and alternate field boundaries; classify insufficient color calibration as INCONCLUSIVE.

**T3 — Occlusion and layered reconstruction (H-D)**. Blind annotators label genuine T-junctions, stroke terminations, front/back relations and ambiguous touching intersections without showing a depth model. Fit (A) strong two-dimensional symbolic/iconographic model with ordinary painter's order and (B) constrained layered 2.5D model with penalty for added parameters. Compare predictive log-loss of withheld junctions or held-out views, violation counts in depth DAG, inter-annotator reliability. Inconsistent occlusion constraints or no generalization means model 2.5D is not supported; arbitrary 3D rendering is NOT evidence.

**T4 — Same-structure multiple viewpoints (H-V)**. Source matches must preserve graph port count, cyclic landmark order, unusual branching sequence and consistent occlusion; color similarity alone has zero qualification weight. Prespecify allowable source-verified rotations (fold topology), scale transformations and projection classes. Evaluate correspondence retrieval precision@k on unseen folios/physical units against morphology- and section-matched negatives. Penalize deformable models that can fit anything. One rosette foldout contributes ONE independent physical unit even with many circles.

**T5 — Text/illustration layout linkage (H-T)**. Align actual source text lines/crops and unbiased figures; use official transliteration (EVA/IVTFF) preserving tokenization uncertainty. Compare contextual token frequencies near graph classes against same-section/same-scribe/Currier baselines, text-length and text-position matching; permutation *within physical groups or valid section/hand blocks* preserving line count and lengths. Metrics: out-of-sample predictive log-loss improvement and cluster bootstrap CI. IMG04 masked crop is NOT suitable for token extraction. No linguistic meaning can be deduced from statistical association alone.

## Operational decision table

| Gate | Current finding | Consequence |
|---|---|---|
| Six screenshot bytes and SHA | Verified at intake by host | Screenshots reproducibly identifiable; originals NOT yet matched |
| Source folio/canvas mappings | PENDING | Cannot claim iconographic correspondences to specific leaves |
| Markup masks | NOT REVIEWED | Exclude contemporary arrows/ellipse/obscured glyphs |
| Independent blinded ROI | 0 accepted in prior EXP003 status | No confirmed image class, direction, pigment role or depth |
| Prospective test freeze | NOT REGISTERED | No confirmatory p-values, PASS, or causal model claims |
| EXP001/002 control | MUST PRESERVE | Do not touch sealed held-out, scribe or physical constraints |

## Priority and division of work

- Source & Codicology: screenshot to Yale canvas and conservation archive crosswalk, physical folds, 52 surviving units and unavailable bytes.
- Vision & Annotation: at native image resolution mark T-junctions/occlusion and classify root/leaf/pipe/figure/rosette; obtain two blind reviewers.
- Color & Material Review: local parchment correction and scan normalization, McCrone material distinction vs digital color.
- Graph & Statistical Testing: implement undirected native-edge topology, negative controls, physically clustered CV and honest uncertainty.
- Keeper/Independent Check: no code-test PASS substituted for scientific PASS; log blockers and preserve prior experiment holdout.

**State:** observations described; user hypothesis formalized; no scan-aligned visual measurements or confirmatory inferential tests executed under this note. This is not evidence for an existing directed circulation diagram, universal anatomical map, astronomy chart, geometric 3D object or translation.
