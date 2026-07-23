# Voynich Folio Inventory PDF v1

## Deliverable

Human-readable PDF inventory generated from the canonical 206-position Yale MS 408 atlas and the user-supplied `Voynich_Folio_Inventory_Schema_v1`.

- PDF filename: `Voynich_Folio_Inventory_Filled_All_Folios_v1.pdf`
- PDF pages: 419
- Folio/source cards: 206
- Pages per record: 2
- PDF outline entries: 206
- Embedded attachments:
  - `Voynich_Folio_Inventory_Filled_Data.zip`
  - `Voynich_Folio_Inventory_Schema_v1.zip`
- PDF SHA-256: `a4253dffc24fd504582f36d0cd49ca991de21659a9196fe252c3ba0c54e3c4b6`

## Inputs

- Repository source commit: `b9f4f089ac7d102431e98064119c115a2b5433cf`
- Annotated atlas ZIP SHA-256: `e02c702dd618252157832dbb6461b13b27f8082757bd266d36de067eb16c9f6e`
- User schema ZIP SHA-256: `413190303882f307faf231bc832e225744a173397a5ce2e01901af8959f39e73`
- User XLSX template SHA-256: `5b65c62a4402488202d6b3dd44a1d5e420efff6f6a8f8c7a1b1a37804a668a48`

## Scope

Each record contains:

- source identity, SHA-256, dimensions, rotation and provenance;
- parchment field;
- text fields and line candidates;
- illustration fields and neutral object hierarchy;
- diagram, damage and text-illustration overlap candidates;
- margins and edge-continuity candidates;
- local geometric relations;
- candidate cross-page graph links with consistent features, inconsistent features, method and negative control;
- overlay and validation references;
- every remaining schema field filled with a value or an explicit status such as `NOT_ASSESSED`, `UNCERTAIN` or `NOT_APPLICABLE`.

## Scientific status

The document is an `AUTO_CANDIDATE_FINAL_V1` inventory. It does not fabricate specialist identifications that were not supported by the automated geometry pass. Fields such as exact root, leaf, petal, human-sex or star-arm counts remain explicitly `NOT_ASSESSED` where a reliable result was unavailable.

## Validation

- source records: 206/206;
- overlay images: 206/206;
- PDF openable with PyMuPDF: PASS;
- page count: 419;
- embedded fonts: Noto Sans regular and bold;
- visual spot checks: title, index, early, middle and final folio cards rendered without clipping or broken glyphs.

The binary PDF is delivered to the user through the ChatGPT file channel; this manifest preserves its provenance and checksum in the repository.
