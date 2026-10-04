Failed to connect to bus: Operation not permitted
# Independent blind annotation contract

This package defines the annotation gate that must precede any TRAIN / VALIDATION / HELD-OUT split for `EXP-2026-001`.

## Independence firewall

Each annotator works from original, checksum-verified scans and the neutral instructions in this directory. Before submitting, each annotator attests that they have not seen:

- the other annotator's work;
- automated candidates or overlays;
- model predictions or hypothesis labels;
- any future split assignment.

The automated `AUTO_CANDIDATE_FINAL_V1` bundle may be used only after both independent submissions are frozen, for adjudication support and software QA. It is not an annotation.

## Coordinate and object contract

- Coordinates are normalized to `[0, 1]` relative to the original scan.
- A bounding box is `[x_min, y_min, x_max, y_max]` with positive area.
- Neutral object classes are `ILLUSTRATION_OBJECT`, `ILLUSTRATION_FIELD`, `TEXT_FIELD`, and `DIAGRAM`.
- Ports use eight frozen sectors: `N`, `NE`, `E`, `SE`, `S`, `SW`, `W`, `NW`.
- Occlusions are directed and use only `IN_FRONT_OF`, `BEHIND`, or `AMBIGUOUS`.
- Local IDs are private to one submission; matching is performed geometrically and never by copying IDs.

## Frozen agreement gates

The thresholds below are fixed before any independent submission is inspected:

- object detection F1 `>= 0.80` at same-class IoU `>= 0.50`, using maximum-cardinality then maximum-IoU bipartite matching;
- median IoU of matched objects `>= 0.75`;
- exact port-sector-set agreement on matched objects `>= 0.80`;
- directed occlusion F1 across the union of submitted matched-endpoint relations `>= 0.80`; missing and conflicting relations are penalized;
- complete record and source-checksum agreement;
- both submissions cover the complete canonical `FOLIO` record universe (covers and non-folio positions are excluded);
- all blindness attestations true and annotator IDs distinct.

If a denominator is zero, that metric is `NOT_ASSESSED` and the gate fails closed. Passing produces `READY_FOR_ADJUDICATION`, never ground truth and never `READY_FOR_SPLIT`. Adjudication must be performed without model predictions and recorded separately.

`IN_FRONT_OF(A,B)` is normalized as equivalent to `BEHIND(B,A)`. `AMBIGUOUS`, a missing relation, and a contradictory direction remain distinct outcomes. Metrics must be invariant to swapping submissions A and B.

## Freeze before comparison

Do not run the agreement gate directly on mutable annotator exports in an operational experiment. After both exports have arrived independently, freeze the exact pair and disclose metrics only from that frozen run:

```bash
python3 research_os/tools/freeze_annotation_pair.py \
  atlas/records annotation-a.json annotation-b.json \
  research_os/runs/EXP-2026-001/annotation-freeze-001
```

The destination must not already exist. The command atomically reserves it, validates stable byte snapshots against both complete source universes and packet/protocol agreement, records SHA-256 digests, writes all artifacts exclusively, and writes `COMMIT.json` last. Existing and partial run directories are never overwritten or automatically removed. A frozen pair never unlocks HELD-OUT and never becomes ground truth automatically.

`LOCAL_FREEZE_COMMITTED` is intentionally not a globally accepted experimental run. Before production collection, an independent custodian or append-only registry must precommit exactly one acceptance slot for the experiment, round, packets, protocol, universe, and two annotator bindings, then receipt the final manifest digest before metrics are accepted. This prevents adaptive retries in fresh directories; local filesystem rules cannot prove that property across machines. See `dyrygent_balanced_freeze_red_team_2026-10-04.md`.

## Diagnostic gate only

The lower-level gate remains available for tests and diagnostics:

```bash
python3 research_os/tools/annotation_gate.py \
  atlas/records annotation-a.json annotation-b.json \
  --report agreement-report.json
```

Both tools return `0` only for `READY_FOR_ADJUDICATION`; all incomplete or invalid inputs return `2`. The freeze directory remains valid evidence even when the agreement gate fails.
