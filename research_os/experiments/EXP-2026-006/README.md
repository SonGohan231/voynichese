# EXP-2026-006 — independent native illustration labeling and spatial matching

**Started:** 2026-10-09. **Authenticated Agent OS research mission:** `fbd4f598-1246-4634-90b4-83ebb60ef626`. The first Dyrygent attempt `17857bc3-6290-4b3a-b2f2-068ea6a53804` was retained in audit history but its specialist routing picked an inappropriate execution domain; it must not be credited as scientific image labeling. The second mission uses science specialists / evidence checking, with known mismatches in generic CI-QA roles; independent art-historical human review is still unassigned.

**Scope:** Read 9 original SHA-verified Yale MS408 photos via the existing source ledger; source groups q9/q14 etc; priority 67v↔86v fragment, 67v↔85v/86r foldout, 32r↔8v, 93r↔18v; include 55r↔34v as a deliberately selected hard negative, not a random unconditioned null. Original EXP005 image pack from 27 source-derived ROIs.

## Verifiable artifacts and code

1. `research_os/tools/exp006_blind_object_mask_queue.py`: computes two separately coded image segmentation passes (`A_LOCAL_INK` and `B_MULTISCALE_BLACKHAT`) on every source-identified crop, yielding bounded native photo pixel-coordinate polygon proposals, SHA lineage, *UNKNOWN* semantics and the spatial relation of pixel components (not object connections). Generates 54 transparent-on-photo polygon overlays, two separate source proposal JSON files, algorithm overlap candidates and a **blank** two independent reviewers' JSON schema. Each pixel object `annotation_status=NOT_SEMANTICALLY_REVIEWED`.
2. `research_os/tools/exp006_text_registration_gate.py`: independent dual review and four physically verified landmarks required before mapping third-party text transcription to Yale photo. Tests geometric homography on explicitly synthetic fixture data only. Without original independently checked landmarks, outputs `BLOCKED_NO_INDEPENDENT_LANDMARKS` and **zero** verified text↔drawing co-location claims.
3. `.github/workflows/voynich-exp006-independent-annotation.yml`: runs real source photo SHA validation, all images and tests, asserts no fake semantic discovery, publishes source-linked artifacts.

## The independent annotation that is still needed

**Two distinct observations** on each *full native photo*, with identical source crop IDs but hidden candidate-pair ranks. Pass A and B must not see the other's interpretation. Each submitted object mask/reviewer form must carry original image source SHA, pixel polygon, canonical folio/canvas OID, category `architecture/rosette/plant_part/person/ornament/writing/other/UNKNOWN`, subtype or UNKNOWN, confidence plus uncertainty, and source-referenced landmark list.

Human agreement requires two *actual humans*; two algorithms can only support robustness against different pixel thresholds and are not evidence of human consensus. If reviewing with two different multimodal AI agents, flag `AI_REVIEW_ONLY`; never imply their observations are expert ground truth. Truth values `is_tower`, `is_person`, `ring_count`, `branch_ports` must remain NULL unless directly observed. Disagreements remain unresolved until another independent judge checks original photos.

## Geometry and text comparison acceptance

- Compare an actual semantic object polygon to another object polygon, not cropped neutral windows or photographic borders.
- Preserve original drawing outline at source resolution and measure invariant graph cycles, port count and clockwise cyclic order of attachments; mirror or 2.5D perspective options carry separately reported complexity penalties.
- Line crossing is not automatically occlusion, junction, tunnel, bridge or 3D layering.
- Compare against at least four null families: component-count-only, digital-color-only, outline-only, and text-only **only when text coordinates are registered**. Require matched physical group separation, section/Currier/scribe when established; unreached controls remain `NOT_ASSESSED`.
- All relevant alternative folio orderings must be physically admissible; do not make copies of q14 foldout pieces into independent held-out folios.
- Avoid the proven pitfall: 67v–86v scored 0.84983 under best-of-9 windows in EXP005 but fell to 0.519459 (22/22 controls matched or exceeded) using first fixed neutral photo windows. These are **selection-sensitive 2D image features** and not independent MV3 evidence.

## Completion gate

- **Technical readiness PASS** only if SHA-proven source images, 54 actual labeled-only-as-pixel overlays, original-photo-coordinate polygons, 2 machine proposal sets, multiple per-crop disagreement objects, and a completed CI log/artifact exist.
- **Independent semantic labeling PASS** only when two independent reviewers truly inspect and submit complete object-level records with uncertainty and separately tracked provenance.
- **Text spatial alignment PASS** only when >=4 manually verified source landmarks and reviewer agreement yield a valid transform with bounded error.
- **MV2+** requires confirmed semantic classes + topology, physically separate original pages, negative controls and independent acceptance. No such evidence exists yet.
- Sealed EXP-2026-001 HELD-OUT must stay closed; no fabricated p-values, historic tower/muscle/women semantics, astrological interpretation or decoding.

**Current scientific verdict until independent semantic labels arrive:** `INCONCLUSIVE / REVIEW_PENDING`. All machine polygons and graph edges are image segmentation artifacts/proposals, not validated objects. This is a runnable evidence-generation handoff for the agents and later independent expert reviewers, not a completed decipherment.
