# Voynichese / Voynich Research OS

This repository contains the historical Voynichese query/data project together with the current reproducible research environment used to test falsifiable hypotheses about the Voynich Manuscript.

## Scientific status

No translation, alphabet, phonetic system, or semantic decoding is claimed here.

The current Research OS experiment (`EXP-2026-001`) is deliberately fail-closed. Until independent human annotation, freeze/receipt evidence, adjudication, and the sealed split chain are complete, its status remains **DRAFT / INCONCLUSIVE_NOT_RUN** and HELD-OUT must remain unexposed.

## Repository map

- `atlas/` — canonical per-page/folio records and visual inventory.
- `data/` — source datasets and manuscript scan material used by the project.
- `research/` — earlier experiments, preregistrations, results, and hypothesis-specific packages.
- `research_os/` — current reproducible research pipeline: provenance, blind annotation, freeze, adjudication, readiness gates, and sealed split tooling.
- `tools/` — legacy/general corpus and atlas utilities.
- `.github/workflows/` — reproducibility and validation checks.

Start with [`research_os/README.md`](research_os/README.md) for the current research workflow and [`research_os/experiments/EXP-2026-001/preregistration.md`](research_os/experiments/EXP-2026-001/preregistration.md) for the active experiment contract.

## Verification

The Research OS is intentionally implemented with the Python standard library where practical. From the repository root:

```bash
python3 -m unittest discover -s research_os/tools -p 'test_*.py' -v
python3 research_os/tools/readiness.py atlas/records \
  --report research_os/experiments/EXP-2026-001/readiness_report.json
```

Before real annotation exists, the expected readiness result is `INCONCLUSIVE_NOT_RUN` with `held_out_exposed=false`.

## Research integrity boundaries

Production annotation uses separate pseudonymized A/B handoffs. Canonical IDs, filenames, source hashes, section/scribe tables, model outputs, predictions, and split assignments are withheld from annotators. The original manuscript pixels remain visible, so this is **metadata blinding rather than perfect visual-identity blinding**; external folio lookup is prohibited and spontaneous recognition must be logged.

A local custodian receipt is not sufficient evidence of external registration merely because it contains an HTTPS URL. The current chain requires a separately signed external-registry witness binding the exact receipt bytes and receipt signature to the registry URI and sequence.

HELD-OUT is never materialized in clear text by the model-development workflow. Full split assignments and the seed are sealed for the custodian; model developers receive only isolated TRAIN/VALIDATION data with pseudonymous identifiers.

## Legacy Voynichese project

This repository originated from the Voynichese project, which provided a query interface over Voynich Manuscript transcription data. Historical documentation and links may refer to the original `voynichese/voynichese` project and website; they should be treated as legacy context, not as the current Research OS entrypoint.
