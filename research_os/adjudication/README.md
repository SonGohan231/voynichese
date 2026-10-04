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
