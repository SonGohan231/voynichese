# MV-2026-10-09 — Voynich cross-folio multiview research protocol

**State:** REGISTERED / NOT_YET_EVALUATED. **Mission:** `56845b5c-754a-4500-ac85-82cc45f6b082`. **Base:** `master`, reviewed 2026-10-09. **Status:** no MV2/MV3/MV4 pair is asserted by this protocol.

## Objective, unit, prior work

Find possible instances of the **same illustrated object** shown on different folios, canvases, scales, rotations, or perspectives, not merely generic motifs. Each unit is an **object crop on a named Yale canvas**, with canonical folio and physical connected-leaf group as distinct identifiers. Compound/foldout canvases must retain region-specific references. Source inventory: `atlas/atlas_project.json` (206 canvases, including two covers), `atlas/records/`, `atlas/cross_page_graph.json`, `data/yale_hq_scans/`, `research_os/sources/beinecke_ms408_section_register.json` and `research_os/sources/zl3b_scribe_source.json`. Keep source-byte SHA-256 and coordinates anchored to the raw JPEG. Do **not** use the unrelated `EXP-2026-001` sealed HELD-OUT samples to design features, tune scores, select examples, estimate prevalence or validate.

**Mandatory data-readiness gate.** At baseline, checked records `0158_85v_and_86r_foldout.annotation.json`, `0129_71r.annotation.json`, and `0003_1r.annotation.json` are `SCHEMA_READY` with empty illustration objects; their QC says visual annotation has not yet been performed. `research_os/artifacts/AUTO_CANDIDATE_FINAL_V1.json` references a separate 206-overlay workflow archive, classified **AUTOMATED_CANDIDATE_NOT_INDEPENDENT_ANNOTATION**. If this archive is unavailable, do NOT infer objects from canvas names or zero-valued object counts. First run verified object extraction from original source images, or import, provenance-tag and independently audit available automatic overlays. Null/UNKNOWN differ from a counted zero or confirmed unpainted part.

## Research packages and DAG

1. **Object Comparison Catalog** — Detect and register each object instance with source crop; output `objects.jsonl`, `catalog_qc.json` and overlay PNG/SVG with identifiers. Capture per-region bbox in pixels and normalized [0,1] coordinates, object class, size, aspect ratio, curve signature, contour, skeleton, enclosed cycles, terminal/port count, topology, counts, pigments, absence of pigment, labels, face and body orientation, hands and other scene graph edges.
2. **Rosette Structure** — For all radial structures record actual sector divisions, junctions, link graph, cycle depths, counts of towers/stars/women, ordering, central/peripheral relationships, occlusions, counting uncertainty. Avoid imposing 12+1.
3. **Woman Orientation & Scene Graph** — Body heading, face direction, arm/hand configuration, pose, nearby vessels, pools, women, crossings, mutual gaze and figure ordering. Unknown orientation must not be silently made left or right.
4. **Tower / Border / Decoration Matching** — Towers, crenellations, walls, bounded regions, ornaments, perimeters, internal silhouettes and openings, geometry under calibrated scale, rotation and hypothetical view changes. Reflection is a **separate** hypothesis, not a free default transform.
5. **Text / Token Context** — Geometry of local inscriptions and token sequence with attributed source/transliteration; radial relation to objects and distance normalized by crop size. Never claim translation or semantics from token match; missing transcription is UNKNOWN.
6. **Multiview Hypothesis** — Rank object A/B pairs with per-family match/mismatch/confounds; compare full structure and topological constraints. Keep "similar motif" distinct from "same object". Export paired overlays, registration transforms, CSV/JSONL ranked candidates, accepted/rejected comparisons, and independent reviewer adjudication.

**Dependency order:** catalog → four parallel specialists (rosettes, women, towers/decorations, tokens) → multiview plus independent null tests → separate verifier and release gate. Assigned execution must preserve these six **logical work packages** even when Agent OS internally generates fewer generic work tasks.

## Machine-readable instance fields

`source_id`, `source_sha256`, `folio`, `canvas_id`, `connected_leaf_group`, `section`, `scribe_class`, `bbox_xywh_px`, `bbox_xywh_norm`, `crop_path`, `object_class`, `geometry` (contour/perimeter/aspect/rotation and uncertainty), `topology` (nodes/edges/cycles/ports/adjacency), `counts` (known / obscured / unknown), `pigment` (observed hues, confirmed UNPAINTED, UNKNOWN, damage and restoration), `text_context` (tokens, labels, distance, orientation, provenance), `figure_orientation` (face/body/arms/uncertain), `relations` (typed subject-predicate-object edges), `evidence` (raw crop + hashes + reviewer), `observation_status` (MEASURED/AUTO_CANDIDATE/REVIEWED/UNKNOWN), `disagreements`. Do not replace unknown with zero, empty string, or absence-of-color.

Pair fields: source/target object IDs, folios and canvases, same/between section, connected-leaf-group status, similarity per feature family plus contradictions, fitted view transform and residual, evidence independent of training, tested null results, uncertainty, and MV class. Preserve common-source correlations and crop overlap.

## Multiview decision levels

- **MV0 weak resemblance:** weak visual overlap, no structural demonstration.
- **MV1 similar motif:** measurable shared motif; identity unsupported.
- **MV2 structure+arrangement match:** separately measured geometry/topology and relative layout agree; not proof of identity.
- **MV3 strong same-object-different-view candidate:** at least three non-redundant feature families agree, topology and relational ordering are consistent with a physically plausible transform, substantive contradictions addressed, four nulls survived and independent review performed.
- **MV4 breakthrough candidate:** only after preregistered confirmatory evaluation, validated independent manual annotations, positive evidence from independent leaf groups, separate replication, correction for search/multiplicity, and independent negative-control PASS. Never auto-promote MV3. MV4 is a **candidate**, never a decipherment claim.

Automated detections cannot satisfy review gates by comparing the algorithm's own labels against itself.

## Negative controls and design

Four independent restricted-information comparators are mandatory: **count-only**, **color-only**, **outline-only**, and **text-only**, evaluated on the identical candidate universe and equivalent selection/tuning budgets. Include random-pair and permuted-label controls preserving section, physical connected-leaf cluster, scribal provenance, artwork density and metadata confounds where possible. Analyze **within-section** and **between-section** subsets separately, report sample size, number of independent groups, effect size, confidence interval and multiplicity-corrected p value, and precommit acceptance threshold and split strategy before running confirmatory tests. Do not leak all-feature information into restricted comparators. Testing only shape or color never licenses MV3. Same-section high prevalence must be checked against copying of motif, workshop convention and compositional repetition rather than assumed identity.

## Deliverables / end-to-end QA

- Valid source manifest (raw sha, dimensions, folio/canvas/physical group mapping) and append-only provenance log.
- `objects.jsonl`, `pairs.jsonl`, `rosette_structure.jsonl`, `scene_graph.jsonl`, `tower_decorations.jsonl`, `text_context.jsonl`, `null_models.json`, `mv_verdicts.json` and overlays/crops; fail closed when absent.
- Tests: atlas empty-instance input never yields match; bbox bounds; coordinate normalization; physical foldout grouping; missing pigment != UNPAINTED; zero count != UNKNOWN; label-leak detection; transform/rotation/scale/occlusion synthetic controls; within/between counts; four nulls isolated; pair symmetry where applicable.
- Each candidate includes both supporting and conflicting observations, review status, and falsifiable alternative explanations.
- Report actual source revision and run ID, modified files, test output, issue/PR and hashes. Missing evidence → `INCONCLUSIVE_NOT_RUN` or `BLOCKED_DATA`, never `PASS`. Independent Keeper cannot be the executor.

**Pre-registration boundary:** this document pre-registers fields and controls, not a claim of a completed statistical analysis. Specific scoring weights, sampling and thresholds must be frozen *before looking at confirmatory data*, with an audit record.
