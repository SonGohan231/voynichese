# Start human annotation — EXP-2026-001

This is the minimum operational handoff for the first production annotation pair. It does not replace the frozen annotation rubric in `research_os/annotation/README.md`.

## Roles

Use four distinct humans:

- **Custodian** — creates pseudonymized handoffs, keeps the private unblinding maps/seeds, controls pseudonymous annotator IDs, acceptance slot, freeze and receipts.
- **Annotator A** — receives only blinded handoff A, the neutral protocol, the annotation UI and their pseudonymous ID.
- **Annotator B** — receives only blinded handoff B, the same neutral protocol/UI and a different pseudonymous ID.
- **Adjudicator** — acts only after freeze + receipt. They do not receive annotator identities, model output, hypothesis labels or split assignments.

Annotators A and B must be different people. Re-running the same AI, account or operator is not independent annotation.

## Before collection

1. Confirm PR/branch artifacts and Research OS CI are green.
2. Confirm canonical packets A/B each contain exactly 204 manuscript-content records and the same canonical universe commitment.
3. Create **two different private pseudonym seeds** (at least 32 random bytes each) with mode `0600`.
4. Build two isolated handoff bundles with `build_blind_handoff.py`. Use separate seeds, bundle directories and custody maps for A and B.
5. Verify that each handoff exposes only `BLI-...` record IDs, opaque image filenames and `source_commitment_sha256`; it must not expose canonical record IDs, folio filenames, raw source SHA-256, section labels, scribe labels, predictions or split assignments.
6. Keep both custody maps and both seeds outside every annotator bundle and outside the repository.
7. Assign two different pseudonymous annotator IDs privately.
8. Fill one `SEALED_BEFORE_COLLECTION` acceptance slot. Besides the canonical packet/protocol/universe commitments, bind for A and B:
   - exact blinded handoff packet SHA-256;
   - private custody-map SHA-256;
   - pseudonym-seed commitment SHA-256.
9. Sign the exact slot bytes with the existing OpenSSH acceptance-slot namespace.
10. Give each annotator only their isolated bundle and pseudonymous ID. Do not give either annotator repository access.

No TRAIN / VALIDATION / HELD-OUT assignment exists at this stage. HELD-OUT remains unexposed.

## Example handoff build

Use separate values for A and B:

```bash
python3 research_os/tools/build_blind_handoff.py \
  . \
  research_os/annotation/packets/annotator-a.packet.json \
  research_os/annotation/ui \
  research_os/runs/EXP-2026-001/private/pseudonym-seed-a.bin \
  research_os/runs/EXP-2026-001/handoff-a \
  research_os/runs/EXP-2026-001/private/custody-map-a.json
```

Serve **the handoff directory**, never the repository root:

```bash
python3 -m http.server 8000 --bind 127.0.0.1 \
  --directory research_os/runs/EXP-2026-001/handoff-a
```

Then open:

```text
http://127.0.0.1:8000/research_os/annotation/ui/?packet=../packets/handoff.packet.json
```

## During annotation

- A and B work independently and do not discuss judgments.
- Questions go privately to the custodian.
- Substantive clarifications must be identical for both and logged.
- Preserve uncertainty and ambiguous relations; do not remove difficult records.
- Each annotator exports exactly one blinded submission.
- Do not attempt to identify `BLI-...` records by outside lookup.

## Custodian unblinding

After both original blinded exports are received, but before agreement comparison, the custodian converts each export to the canonical record IDs locally:

```bash
python3 research_os/tools/unblind_annotation.py \
  research_os/runs/EXP-2026-001/handoff-a/research_os/annotation/packets/handoff.packet.json \
  research_os/runs/EXP-2026-001/private/custody-map-a.json \
  annotation-a.blinded.json \
  research_os/runs/EXP-2026-001/private/annotation-a.canonical.json
```

Repeat separately for B. Do not edit labels during unblinding.

## Freeze and agreement

Freeze only the two canonicalized submissions, while also supplying the exact blinded handoff packets and custody maps committed in the signed slot:

```bash
python3 research_os/tools/freeze_annotation_pair.py \
  atlas/records \
  research_os/runs/EXP-2026-001/private/annotation-a.canonical.json \
  research_os/runs/EXP-2026-001/private/annotation-b.canonical.json \
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

Then reverify the frozen evidence bundle and obtain the external append-only custodian receipt before adjudication. Passing agreement means only `READY_FOR_ADJUDICATION`; it is not ground truth and does not unlock HELD-OUT.

## Human-only checklist

Before collection starts:

- [ ] Custodian is a real person.
- [ ] Annotator A and B are different real people.
- [ ] Adjudicator is a distinct human role.
- [ ] Both production handoffs use opaque IDs, opaque filenames and source commitments.
- [ ] Custody maps and seeds are outside the handoffs and repository.
- [ ] Signed slot binds canonical packets plus exact handoff/custody/seed commitments.
- [ ] A/B have not seen the other submission, automated candidates, model predictions, hypothesis labels, section/scribe tables or split assignments.
- [ ] HELD-OUT remains uncreated/unexposed.
- [ ] Experiment stays `INCONCLUSIVE_NOT_RUN` until real data and the preregistered analysis exist.
