Failed to connect to bus: Operation not permitted
# Independent adjudication contract

Adjudication begins only after `verify_custodian_receipt.py` returns both `FREEZE_RECEIPT_VERIFIED` and `ready_for_adjudication=true`.

The adjudicator receives only:

- original source references and checksums;
- anonymized `SIDE_1` and `SIDE_2` frozen annotations;
- deterministic same-class geometric matches computed between those annotations;
- the neutral protocol in this directory.

The adjudicator must not receive annotator identities, automated image candidates, model outputs, hypothesis labels, TRAIN/VALIDATION/HELD-OUT assignments, or earlier interpretations. Geometric matching is an alignment aid, not a proposed scientific answer.

The builder writes two separate artifacts. Give only `adjudication-packet.json` to the adjudicator. Keep `operator-custody.json`, which maps the anonymized sides to frozen files, with the custodian. A completed adjudication is an adjudicated reference dataset—not ground truth—and still does not expose HELD-OUT.

```bash
python3 research_os/tools/build_adjudication_packet.py \
  research_os/runs/EXP-2026-001/annotation-freeze-001 \
  custodian-receipt.json custodian-receipt.json.sig allowed_signers \
  research_os/runs/EXP-2026-001/adjudication-packet-001 \
  --identity CUSTODIAN_IDENTITY
```

Validate the completed submission against the exact packet bytes before it enters readiness:

```bash
python3 research_os/tools/validate_adjudication.py \
  adjudication-packet.json adjudication-submission.json \
  --report adjudication-validation.json
```

The validator requires the complete packet record universe, original source checksums, exact packet SHA-256, all blindness attestations, valid canonical geometry and ports, non-orphaned relations, valid anonymized source references, and rationale/source consistency. Success is `ADJUDICATION_VALIDATED` and only establishes structural validity. It does not itself establish the signed receipt chain or produce `READY_FOR_SPLIT`.

Run the final readiness audit from the exact packet and submission, not from a previously rendered validation report:

```bash
python3 research_os/tools/readiness.py atlas/records \
  --freeze-directory research_os/runs/EXP-2026-001/annotation-freeze-001 \
  --custodian-receipt custodian-receipt.json \
  --receipt-signature custodian-receipt.json.sig \
  --allowed-signers allowed_signers \
  --custodian-identity CUSTODIAN_IDENTITY \
  --adjudication-packet adjudication-packet.json \
  --adjudication adjudication-submission.json \
  --report research_os/experiments/EXP-2026-001/readiness_report.json
```

Only `READY_FOR_SPLIT` permits entering the sealed custodian split workflow. Cleartext `--split` output is disabled. Readiness still returns `held_out_exposed=false`; downstream tooling must encrypt the full assignment and give model developers only an isolated, opaque TRAIN/VALIDATION package that does not reveal the full record universe.
