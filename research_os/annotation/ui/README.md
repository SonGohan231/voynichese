# Blind annotation UI

Static, local-only editor for independent annotation. It has no network integrations, automated overlays, predictions, hypothesis labels, section/scribe tables or split information.

## Production use

Do **not** serve the repository root to production annotators. Build an isolated pseudonymized handoff with `research_os/tools/build_blind_handoff.py` and serve only that directory.

Example:

```bash
python3 -m http.server 8000 --bind 127.0.0.1 \
  --directory research_os/runs/EXP-2026-001/handoff-a
```

Open:

```text
http://127.0.0.1:8000/research_os/annotation/ui/?packet=../packets/handoff.packet.json
```

The production packet exposes opaque `BLI-...` IDs, opaque image filenames and a secret-keyed `source_commitment_sha256`. It does not expose canonical folio IDs, original source paths or raw source SHA-256 values. The export therefore remains blinded and must be converted by the custodian with `unblind_annotation.py` before the canonical annotation gate/freeze.

Use a separate handoff, private seed, custody map, browser profile/device and pseudonymous annotator ID for B.

## Diagnostic/development use

Canonical packets under `research_os/annotation/packets/` remain useful for local developer QA. They are **not** the production annotator handoff because their record IDs and original source paths reveal folio identity.

The editor verifies its packet universe commitment with Web Crypto, stores progress only in browser `localStorage`, and exports the packet's source binding unchanged:
- canonical diagnostic packet → `source_sha256`;
- production blinded packet → `source_commitment_sha256`.

Design reference: `design/concept.png`.
