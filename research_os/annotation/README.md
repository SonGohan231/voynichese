# Independent blind annotation contract

This package defines the annotation gate that must precede any TRAIN / VALIDATION / HELD-OUT split for `EXP-2026-001`.

## Independence firewall

Each annotator works from original, checksum-verified scans and the neutral instructions in this directory. Before submitting, each annotator attests that they have not seen:

- the other annotator's work;
- automated candidates or overlays;
- model predictions or hypothesis labels;
- any future split assignment;
- section or scribe lookup tables;
- external folio-identity lookup intended to recover canonical IDs from the blinded handoff.

The automated `AUTO_CANDIDATE_FINAL_V1` bundle may be used only after both independent submissions are frozen, for adjudication support and software QA. It is not an annotation.

## Production pseudonymization firewall

Production annotators must not receive the repository or the canonical A/B packets directly. Before collection, the custodian builds a separate isolated handoff for each annotator with `build_blind_handoff.py`, using different private seeds. The handoff replaces canonical record IDs, source filenames and raw source SHA-256 values with opaque IDs, opaque image filenames and secret-keyed source commitments. The private custody map and seed remain outside the bundle and repository.

After the two blinded exports are received, the custodian converts them locally with `unblind_annotation.py`. Unblinding may restore only canonical record IDs and source SHA-256 bindings; it must not alter objects, ports, occlusions or blindness attestations.

The signed acceptance slot must bind the exact blinded handoff packet, private custody-map hash and pseudonym-seed commitment for both A and B before collection begins. Pseudonymization reduces avoidable metadata lookup; it cannot hide visual section cues or distinctive folio identity inherent in the manuscript pixels themselves. This is metadata blinding, not a claim of perfect visual-identity blinding. Annotators must not use external lookup to recover canonical folio identity, and any spontaneous recognition must be disclosed to the custodian as a protocol deviation.

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
  --custodian-identity CUSTODIAN_IDENTITY \
  --handoff-packet-a research_os/runs/EXP-2026-001/handoff-a/research_os/annotation/packets/handoff.packet.json \
  --handoff-packet-b research_os/runs/EXP-2026-001/handoff-b/research_os/annotation/packets/handoff.packet.json \
  --custody-map-a research_os/runs/EXP-2026-001/private/custody-map-a.json \
  --custody-map-b research_os/runs/EXP-2026-001/private/custody-map-b.json
```

The destination must not already exist. The command atomically reserves it, validates stable byte snapshots against both complete source universes and packet/protocol agreement, records SHA-256 digests, writes all artifacts exclusively, and writes `COMMIT.json` last. Existing and partial run directories are never overwritten or automatically removed. A frozen pair never unlocks HELD-OUT and never becomes ground truth automatically.

The CLI rejects unsigned, altered, draft, path-traversing, multi-pair, or duplicate-ID slots. It verifies the exact A/B pseudonym hashes and packet bytes again from the snapshots that are frozen, then binds the verified slot digest into the manifest. `LOCAL_FREEZE_COMMITTED` is still not a globally accepted experimental run: the custodian or append-only registry must receipt the final manifest digest before metrics are accepted. This prevents adaptive retries in fresh directories; local filesystem rules cannot prove that property across machines. See `dyrygent_balanced_freeze_red_team_2026-10-04.md`.

Before requesting that final receipt, independently reverify the complete local evidence bundle:

```bash
python3 research_os/tools/verify_annotation_freeze.py \
  research_os/runs/EXP-2026-001/annotation-freeze-001
```

This rechecks `COMMIT.json`, the manifest digest, every annotation, packet, report and acceptance artifact, the embedded custodian signature, filesystem write barriers, and unexpected files. Success is only `LOCAL_FREEZE_INTEGRITY_VERIFIED`; it still reports `custodian_final_receipt_required=true` and cannot unlock HELD-OUT.

The custodian then submits the verified manifest and commit digests to an external append-only registry, fills `custodian_receipt.template.json`, and signs the exact receipt bytes in namespace `voynich-research-os-freeze-receipt-v1`. A URL-shaped string is not accepted as proof of external registration. The external registry must produce a separate `registry-witness.json` using `registry_witness.template.json`, bind the SHA-256 of the exact receipt bytes and its custodian signature, and sign the witness under a distinct registry identity in namespace `voynich-research-os-registry-witness-v1`. The registry signer identity must differ from the custodian identity.

Verify the complete evidence chain against the local freeze:

```bash
python3 research_os/tools/verify_custodian_receipt.py \
  research_os/runs/EXP-2026-001/annotation-freeze-001 \
  custodian-receipt.json custodian-receipt.json.sig allowed_signers \
  --identity CUSTODIAN_IDENTITY \
  --registry-witness registry-witness.json \
  --registry-witness-signature registry-witness.json.sig \
  --registry-allowed-signers registry_allowed_signers \
  --registry-identity REGISTRY_IDENTITY
```

Only `FREEZE_RECEIPT_VERIFIED` with `registry_witness_status=REGISTRY_WITNESS_VERIFIED` and `ready_for_adjudication=true` permits independent adjudication. The verifier does not infer append-only behavior from HTTPS or fetch arbitrary network content; it verifies a cryptographic attestation from the separately trusted registry signer. A valid receipt for a failed agreement gate remains preserved evidence but does not permit adjudication. Receipt verification never promotes annotations to ground truth and never unlocks HELD-OUT.

## Diagnostic gate only

The lower-level gate remains available for tests and diagnostics:

```bash
python3 research_os/tools/annotation_gate.py \
  atlas/records annotation-a.json annotation-b.json \
  --report agreement-report.json
```

Both tools return `0` only for `READY_FOR_ADJUDICATION`; all incomplete or invalid inputs return `2`. The freeze directory remains valid evidence even when the agreement gate fails.
