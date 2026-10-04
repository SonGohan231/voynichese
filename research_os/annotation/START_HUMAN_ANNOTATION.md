# Start human annotation — EXP-2026-001

This is the minimum operational handoff for the first production annotation pair. It does not replace the frozen contract in `research_os/annotation/README.md`.

## Roles

Use four distinct humans:

- **Custodian** — controls packet release, pseudonymous annotator IDs, acceptance slot, receipts, and the private identity mapping. The custodian must not provide substantive labeling guidance or expose HELD-OUT.
- **Annotator A** — receives only packet A, the frozen neutral protocol, the annotation UI, and their pseudonymous ID.
- **Annotator B** — receives only packet B, the same frozen neutral protocol, the annotation UI, and a different pseudonymous ID.
- **Adjudicator** — acts only after both submissions are frozen and the receipt gate permits adjudication. The adjudicator must not receive annotator identities, model output, hypothesis labels, or split assignments.

Annotators A and B must be different people. Running the same AI, account, or operator twice is not independent annotation.

## Before collection

1. Confirm PR/branch artifacts and the Research OS CI gate are green.
2. Confirm packets A and B each contain the frozen 183-FOLIO universe and match the frozen protocol/universe hashes.
3. Select two different human annotators and record conflicts or prior exposure outside the repository.
4. Assign different pseudonymous annotator IDs privately.
5. The custodian fills and signs one `SEALED_BEFORE_COLLECTION` acceptance slot using the existing procedure in `README.md`.
6. Give each annotator only:
   - their own packet;
   - the frozen protocol;
   - the local annotation UI;
   - their pseudonymous ID;
   - the same written operational instructions.
7. Do not provide automated candidates, overlays, model predictions, hypothesis labels, the other annotation, or any TRAIN/VALIDATION/HELD-OUT assignment.

If a substantive protocol clarification becomes necessary after collection starts, stop both annotators. Do not silently change the rubric mid-run.

## During annotation

- A and B work independently and do not discuss judgments.
- Questions go privately to the custodian.
- Administrative answers may differ when necessary; substantive clarifications must be given identically to both annotators and logged.
- Preserve uncertainty, ambiguous relations, abstentions, and difficult records. Do not remove records to improve agreement.
- Each annotator exports exactly one original submission artifact and completes all blindness attestations.

## Freeze and agreement

1. Each annotator submits directly to the custodian.
2. The custodian checks identity, completeness, packet binding, and source checksums without correcting labels.
3. Lock both original submissions before any comparison.
4. Freeze the pair with the existing signed-slot procedure.
5. Reverify the freeze bundle and obtain the external append-only custodian receipt.
6. Only then inspect the frozen agreement report.
7. Passing agreement means only `READY_FOR_ADJUDICATION`. It is not ground truth and does not unlock HELD-OUT.
8. Preserve original A/B submissions and pre-adjudication agreement even after adjudication.

## Human-only checklist

Before declaring collection started, all boxes must be true:

- [ ] Custodian is a real person.
- [ ] Annotator A is a real person.
- [ ] Annotator B is a different real person.
- [ ] Adjudicator is a distinct human role and has not received A/B identities or forbidden model/split information.
- [ ] A and B have not seen the other submission.
- [ ] A and B have not seen automated candidates, model predictions, hypothesis labels, or split assignments.
- [ ] One signed acceptance slot binds the exact packets, protocol, universe, and two different pseudonymous IDs.
- [ ] HELD-OUT remains sealed and unexposed.
- [ ] Experiment status remains `INCONCLUSIVE_NOT_RUN` until real data are collected and the preregistered analysis is actually run.
