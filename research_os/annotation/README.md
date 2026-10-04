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

## Run

```bash
python3 research_os/tools/annotation_gate.py \
  atlas/records annotation-a.json annotation-b.json \
  --report agreement-report.json
```

The tool returns `0` only for `READY_FOR_ADJUDICATION`; all incomplete or invalid inputs return `2`.
