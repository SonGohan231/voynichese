# Voynich evidence packet and replication plan — 2026-10-08

Status: SOURCE PACKET + EXPLORATORY ANALYSIS; NOT A CONFIRMATORY FINDING.

This packet is independent of the existing visual-grammar EXP-2026-001. Never edit its preregistration or inspect, write, regenerate, or unseal HELD-OUT, seeds, custodial maps, annotations, or signed receipts.

## 1. Agent OS status audit

- Main program 3ca158c5-cd9b-4f12-ad75-8fbfb1c7f6d3: FAILED. Red-team review exists, final synthesis blocked.
- Data 60fc7529-165e-4929-af97-641cbcf42762: COMPLETED, but NO VERIFIED RESEARCH DATA. The agents returned explicit_none under NO_EFFECTIVE_TOOL with zero tool calls.
- Literature retry 695b0318-d404-4db9-a66a-2e0c4be7afd9: FAILED; REVALIDATE decisions after missing real URL evidence.
- Text locality 61d932a4-1acf-48dd-a51b-a0034f0a94c2: FAILED after attempted review and repair. No independent numerical replication accepted.
- Quantitative plan fd2e6cdb-54ba-4716-9b8f-23712e53e733: FAILED; a host-side testing artifact was saved but its mission synthesis not accepted.

Do not equate a technical PASS for reporting unavailable tools with successful source retrieval or a scientific discovery. Agent OS provider state or assigned permissions do not prove that web tools were actually live.

## 2. Source register (retrieved by ChatGPT host, NOT by local Agent OS workers)

PRIMARY MANUSCRIPT:
- Yale Beinecke MS 408 official collection: https://beinecke.library.yale.edu/beinecke/collections/beinecke-cipher-voynich-manuscript
- Yale catalog: https://collections.library.yale.edu/catalog/2002046
- IIIF source: https://collections.library.yale.edu/manifests/oid/2002046
- High-resolution image tests must verify canvas ID, image version and original resolution. The IIIF manifest was not fetched during this host review.

PRIMARY TRANSCRIPTION:
- Zandbergen–Landini ZL3b, 2025-05-13: https://www.voynich.nu/data/ZL3b-n.txt
- Byte-length 411671 public mirror: https://github.com/Aspect-Research/voynich-autoexploration/blob/master/data/transcriptions/eva_zl3b.txt
- Git blob SHA (not SHA256 of bytes): 2a4533ab9bdfa85db9bad602d590978953055df1
- Third-party verification record: https://github.com/noah-chelednik/voynich-data/blob/main/reports/source_verification_report.md
- ZL records physical loci and $Q (quire), $H (scribe), $L (Currier language), $I (illustration). EVA glyphs and separators are analytical conventions, not established plaintext units.

RESEARCH:
1. Colin Layfield and Lisa Fagin Davis, Singulion Structure and the Voynich Manuscript, Digital Medievalist 19 (July 2026), DOI https://doi.org/10.4000/16k0a ; journal https://journals.openedition.org/digitalmedievalist/2331 . Peer reviewed. Abstract: LSA comparison against Aberdeen Bestiary and Speculum Humanae Salvationis is used to argue for originally sequential folded bifolia (singulions) instead of currently nested quires. Full article was blocked by journal bot challenge in this session; effect sizes and controls remain unverified. The proposal is a hypothesis, not demonstrated reconstruction.
2. Layfield and Davis, The Application of Latent Semantic Analytics to the Voynich Manuscript, Digital Humanities Quarterly 20(1), 2026, DOI https://doi.org/10.63744/2ezxpskcezq4 . Exact protocol needs independent reading.
3. Liudmila Rozanova and Alexander Temerev, A Glyph Is Not a Letter, a Token Is Not a Word, a Space Is Not a Space, August 2026 preprint, https://arxiv.org/abs/2608.17096 . ZL3b, matched prose/cipher/pseudo-text controls and quire-level resampling. Important challenge to letter/word/space assumptions, not a decipherment.
4. Christophe Parisel, Evidence of Layered Positional and Directional Constraints in the Voynich Manuscript, 2026 preprint, https://arxiv.org/abs/2604.19762 . Competing positional interpretation; test null model and transfer.
5. Nicolas Turenne, A Generative Grammar Underlying the Voynich Manuscript, the Pastiche Hypothesis, 2026 preprint, https://arxiv.org/abs/2609.20835 . Competing generator hypothesis; no accepted reading demonstrated.

## 3. Host-run exploratory numerical diagnostic

Files on this branch:
- research_os/tools/voynich_section_exploratory.py
- research_os/experiments/EXP-2026-002/exploratory_snapshot_2026-10-08.json

This is separate from and does not modify EXP-2026-001 or its sealed dataset. Inputs were primary ZL3b transcription and the already public section+scribe metadata file research_os/experiments/EXP-2026-001/section_scribe_strata.json. No HELD-OUT splits were created or accessed.

Parsing: 204 atlas records for 102 numbered folios; 3,895 prose lines, 31,610 separator-delimited entries, 28,109 tokens retained by conservative a-z filter. Ninety folios had >=40 confident tokens, unmixed scribe and Currier A/B classification.

Statistical feature: per-folio L2-normalized frequency vectors of 2-character token prefixes and suffixes. Compare cosine similarities only for pairs with identical scribe AND Currier language, with at least 5 numeric folios between them.

Observations:
- Same section: mean cosine 0.8289917181; 889 pairs.
- Different section: mean cosine 0.7978091161; 552 pairs.
- Difference: +0.0311826020.
- 999 folio-label permutations within scribe+Currier strata (LCG seed 1729), one-sided exploratory p=0.001, which is also the minimum possible p-resolution for this permutation count.

INTERPRETATION: This is a non-preregistered EXPLORATORY signal, NOT an independently replicated discovery. Counted pairs are correlated; numeric folio groups are not verified physical bifolio groups. Residual section-hand-layout/physical-order confounding and transcriber/segmentation artifacts may survive. The selection of a feature family and preprocessing within this exploratory run prevents confirmatory inference. Independent source reproduction and alternative controls are mandatory.

## 4. Follow-up experiments (DRAFT; do not retrospectively preregister this test)

A. Independently reproduce the exploratory numerical diagnostics by running the Python file on an original byte-verified ZL3b corpus, checking parser events, exclusions and relative float tolerance. Inspect nonlocal pairing and exact section/scribe mapping before scientific acceptance.

B. Prospectively freeze a separate test on true physical bifolia groups with multiple representations (original EVA, composite-collapsed EVA, uncertain-space merged, optionally independent transcriptions). Evaluate section locality with blocked permutations, material layout controls and leakage-safe cross-quire transfer.

C. Test current reading order, documented physical connectivity and singulion-reconstructed order as competing hypotheses rather than assuming any one ordering. Reproduce the LSA baseline and compare size-matched controls.

D. Calibrate stitch-detection using synthetic positive seams at diverse widths/intensities and untouched natural gutters/curl shadows as negatives. Never generalize an earlier p<0.001 beyond its null model.

E. Design two independent blind codings for corner-face orientation; define one primary target and composition-matched permutation test. Treat pigment/state interpretation (four colors plus absence) as a separate experiment with explicit no-pigment vs indeterminate vs unavailable states.

## 5. Scientific and safety acceptance

- Scientific output requires validated source access, versioned inputs, full code, actual data and independently checked numerical outputs.
- If tools are unavailable, return BLOCKED_NO_SOURCE, not science-completed.
- Executor and verifier must be distinct.
- It is correct for unready experiments to remain INCONCLUSIVE_NOT_RUN.
- No decoding/translation claims on the basis of structural regularities.
- Do not touch EXP-2026-001 HELD-OUT, annotations, freeze or custodian material.
