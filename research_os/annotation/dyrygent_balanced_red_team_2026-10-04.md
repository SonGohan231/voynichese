# Dyrygent BALANCED red-team — blind annotation gate

Date: 2026-10-04  
Mode: `BALANCED`, preset `research`  
Input scope: frozen protocol description only; no source images, annotations, model predictions, or split assignments.  
Initial verdict: `INCONCLUSIVE` for starting annotation.

## Material findings

Dyrygent identified four consequential measurement defects in the first gate version:

1. Greedy same-class IoU matching can lose valid matches and depend on ordering.
2. Equal port counts do not establish agreement about port sectors.
3. Scoring occlusions only on the intersection can hide missing relations.
4. `IN_FRONT_OF(A,B)` and `BEHIND(B,A)` require canonical equivalence, while missing, ambiguous, and contradictory relations must remain distinct.

It also warned that agreement is not validity, conditional median IoU does not cover missed objects, dense folios may dominate micro-aggregates, identical packet hashes do not prove operational blindness, and segmentation/adjudication rules must be explicit.

## Changes made before annotation

- Replaced greedy matching with maximum-cardinality, then maximum-total-IoU bipartite assignment.
- Replaced port-count agreement with exact port-sector-set agreement.
- Replaced common-edge agreement with directed occlusion F1 over the union of submitted matched-endpoint relations.
- Canonicalized `BEHIND(B,A)` to `IN_FRONT_OF(A,B)`.
- Added tests for order symmetry, a greedy-cardinality trap, missing-relation penalty, inverse-relation equivalence, and port-sector disagreement.
- Regenerated both frozen packets after the protocol changed and updated the protocol hash.

## Remaining limitations

- Per-folio diagnostics and macro object F1 are now emitted to expose density concentration; no separate gate threshold is inferred from them before data.
- Two annotators can share systematic errors; passing agreement remains only `READY_FOR_ADJUDICATION`.
- Operational separation of annotators must be evidenced at execution time. A declaration or identical packet hash is insufficient.
- No independent annotations exist yet, so no scientific hypothesis has been tested.
