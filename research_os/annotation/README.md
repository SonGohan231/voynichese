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
- both submissions cover the complete canonical manuscript-content universe: `FOLIO` plus
  numeric `UNRESOLVED` canvases representing compound pages and foldout parts; covers are excluded;
- all blindness attestations true and annotator IDs distinct.

If a denominator is zero, that metric is `NOT_ASSESSED` and the gate fails closed. Passing produces `READY_FOR_ADJUDICATION`, never ground truth and never `READY_FOR_SPLIT`. Adjudication must be performed without model predictions and recorded separately.

`IN_FRONT_OF(A,B)` is normalized as equivalent to `BEHIND(B,A)`. `AMBIGUOUS`, a missing relation, and a contradictory direction remain distinct outcomes. Metrics must be invariant to swapping submissions A and B.

## Freeze before comparison

Do not run the agreement gate directly on mutable annotator exports in an operational experiment. Before collection, an independent custodian must copy `acceptance_slot.template.json`, replace both annotator commitments and custodian fields, change the state to `SEALED_BEFORE_COLLECTION`, and sign the exact bytes with OpenSSH namespace `voynich-research-os-acceptance-slot-v1`:

```bash
ssh-keygen -Y sign -f CUSTODIAN_PRIVATE_KEY \
  -n voynich-research-os-acceptance-slot-v1 acceptance-slot.json
```

The two slot bindings are SHA-256 digests of the exact pseudonymous annotator IDs that will be typed into the editor. The custodian assigns each pseudonym privately, verifies that two different people receive A and B, and keeps the real-identity mapping outside the repository. Never place the private key or real-identity mapping here. `allowed_signers` contains only the approved public key and custodian identity in OpenSSH allowed-signers format.

After both exports have arrived independently, freeze the exact pair and disclose metrics only from the path signed into that slot:

```bash
python3 research_os/tools/freeze_annotation_pair.py \
  atlas/records annotation-a.json annotation-b.json \
  research_os/runs/EXP-2026-001/annotation-freeze-001 \
  --slot acceptance-slot.json \
  --slot-signature acceptance-slot.json.sig \
  --allowed-signers allowed_signers \
  --custodian-identity CUSTODIAN_IDENTITY
```

The destination must not already exist. The command atomically reserves it, validates stable byte snapshots against both complete source universes and packet/protocol agreement, records SHA-256 digests, writes all artifacts exclusively, and writes `COMMIT.json` last. Existing and partial run directories are never overwritten or automatically removed. A frozen pair never unlocks HELD-OUT and never becomes ground truth automatically.

The CLI rejects unsigned, altered, draft, path-traversing, multi-pair, or duplicate-ID slots. It verifies the exact A/B pseudonym hashes and packet bytes again from the snapshots that are frozen, then binds the verified slot digest into the manifest. `LOCAL_FREEZE_COMMITTED` is still not a globally accepted experimental run: the custodian or append-only registry must receipt the final manifest digest before metrics are accepted. This prevents adaptive retries in fresh directories; local filesystem rules cannot prove that property across machines. See `dyrygent_balanced_freeze_red_team_2026-10-04.md`.

Before requesting that final receipt, independently reverify the complete local evidence bundle:

```bash
python3 research_os/tools/verify_annotation_freeze.py \
  research_os/runs/EXP-2026-001/annotation-freeze-001
```

This rechecks `COMMIT.json`, the manifest digest, every annotation, packet, report and acceptance artifact, the embedded custodian signature, filesystem write barriers, and unexpected files. Success is only `LOCAL_FREEZE_INTEGRITY_VERIFIED`; it still reports `custodian_final_receipt_required=true` and cannot unlock HELD-OUT.

The custodian then records the verified manifest and commit digests in an externally append-only registry, fills `custodian_receipt.template.json`, and signs the exact receipt bytes in the separate namespace `voynich-research-os-freeze-receipt-v1`. Verify the returned evidence against the local freeze:

```bash
python3 research_os/tools/verify_custodian_receipt.py \
  research_os/runs/EXP-2026-001/annotation-freeze-001 \
  custodian-receipt.json custodian-receipt.json.sig allowed_signers \
  --identity CUSTODIAN_IDENTITY
```

Only `FREEZE_RECEIPT_VERIFIED` with `ready_for_adjudication=true` permits independent adjudication. A valid receipt for a failed agreement gate remains preserved evidence but does not permit adjudication. Receipt verification never promotes annotations to ground truth and never unlocks HELD-OUT.

## Diagnostic gate only

The lower-level gate remains available for tests and diagnostics:

```bash
python3 research_os/tools/annotation_gate.py \
  atlas/records annotation-a.json annotation-b.json \
  --report agreement-report.json
```

Both tools return `0` only for `READY_FOR_ADJUDICATION`; all incomplete or invalid inputs return `2`. The freeze directory remains valid evidence even when the agreement gate fails.
