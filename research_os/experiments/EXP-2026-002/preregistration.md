# EXP-2026-002 — Sectional locality conditional on physical structure, hand, Currier and reading order

**Protocol version:** v1.0 — 2026-10-08  
**Status:** `PROTOCOL_COMMITTED / NOT_EXTERNALLY_REGISTERED / NOT_RUN`  
**Purpose:** a *prospective replication* of an earlier-explored effect, **not** a clean discovery on previously untouched manuscript data. This protocol must be locked before the independent preparation team sees replication statistics. Do not label the GitHub commit alone as independent external preregistration.

## 1. Pre-exposure disclosure

Prior exploratory ZL3b analysis used 204 atlas records, 90 text folios and 28,109 tokens. Within-section vs between-section cosine similarities under a partial hand/Currier matching rule were 0.82899 and 0.79781 (difference +0.03118; exploratory 999 blocked permutations, p≈0.001). One separate JavaScript implementation reproduced that exploratory calculation; it **did not** supply independent-source replication. Pairs were dependent; physical bifolio/quire, competing reading order and layout were not adequately controlled. No claim of significance from these historical observations is carried into this experiment.

Existing EXP-2026-001 tests visual-grammar prediction and is **not** amended or reinterpreted by EXP-2026-002.

## 2. Exact question and hypotheses

**H0:** After controlling for matching on scribal hand and Currier variety, token-count and distance, physical bifolio/quire structure and predefined page ordering, textual similarity does not increase for pages from the same illustrative/sectional class.

**H1 (one-sided):** Across eligible physically separate bifolia, the pre-specified section-match effect on text similarity remains **positive** on independently prepared IT2a data. A positive result is structural statistical evidence only; it is neither a translation nor proof of thematic or reading-order continuity.

**Interpretation gate:** Hand, Currier and section may be closely or perfectly confounded in some portions. If eligible overlap is insufficient, output `BLOCKED_IDENTIFIABILITY / INCONCLUSIVE_NOT_RUN` rather than relaxing controls after inspecting the result.

## 3. Dataset and source provenance

- **Discovery source (not confirmatory):** ZL3b EVA/IVTFF, historical exploratory snapshot. Retain its exact source hash, normalization and previously used parameters in the audit ledger, but do not choose features using the independent dataset.
- **Primary replication source:** independently prepared Takahashi/IT2a IVTFF text, fetched and parsed from an independently recorded source artifact by a different preparation agent than the ZL3b exploratory executor. If it is inaccessible or cannot be reliably matched to canonical folios, **do not use ZL3b as a substitute**.
- **Optional sensitivity:** RF1b / other independent transcription if license, alignment and coverage permit. This is a transcription-level rather than an independent-manuscript replication.
- **Metadata:** explicit per-side folio identifier; source/sha256; IVTFF locus and ambiguous-token conventions; section class; Lisa Fagin Davis hand (mixed-hand exceptions preserved); original Currier A/B (unknown stays unknown); physical leaf ID, **bifolio ID**, quire ID; foldout/missing/ambiguous geometry; ordering variant and source/uncertainty.
- Source catalog: Yale Beinecke MS 408 scans/catalog (https://beinecke.library.yale.edu/beinecke/collections/beinecke-cipher-voynich-manuscript), Zandbergen folio/collation/transcription material (https://voynich.nu/folios.html , https://voynich.nu/descr.html , https://voynich.nu/transcr.html , https://voynich.nu/writing.html).
- Rival physical-order hypothesis: Layfield & Davis, **Singulion Structure and the Voynich Manuscript**, *Digital Medievalist* 19 (2026), DOI 10.4000/16k0a. This is a **hypothesis** and may not be optimized against the confirmatory score.

No invented assignments: unknown / mixed / disputed metadata must appear in the coverage table. Any official-looking source URL that cannot be verified must be recorded as unverified.

## 4. Eligible universe and blinding

1. Freeze a complete source manifest, checksum map, exclusions, physical bifolio/quire table and the three ordering maps *before* running the primary calculation.
2. Count text-bearing sides/folios, available tokens, eligible unique **bifolia**, hand×Currier×section strata, and overlap. Predefine exclusions: unreadable, missing required metadata, non-running text, transcriptions not aligned, foldouts without defensible physical-group assignment; report excluded counts.
3. Primary text scope: only running paragraph loci (`P*`) with a fixed unambiguous EVA transliteration mapping common to the required sources. Labels, marginalia, diagrams and non-paragraph text excluded. Exclude alternative/uncertain readings using fixed parser rules; publish those rules and counts. No human tuning after results.
4. Aggregate running words to physical folio **leaf** (r/v together when possible). Place all sides of the same physical bifolio, same image and same text transcriptions in one leak-proof unit. No repeated training/testing on near-duplicate surfaces.
5. Dataset preparation and analysis personnel separated; analyst receives pseudonymous features/metadata, not precomputed section-locality results from replication data. A custodian retains the primary output until protocol freeze + acceptance. Log any prior exposure to IT2a/RF1b as a limitation.

## 5. One primary metric, frozen design

- Compute **TF-IDF cosine similarity** between folio-leaf lexical count vectors; IDF is estimated using the **predefined IT2a analysis universe**, without optimizing on section labels; lowercase and token filtering as frozen in the source/parser manifest. No learned dimensionality reduction or hyperparameter optimization.
- Consider only leaf pairs belonging to **different bifolia**. Require both leaves to have the **same known LFD hand** and the **same known Currier class**. Exclude mixed/unknown hands and Currier from the primary test, but tabulate them separately.
- For each candidate pair calculate source-independent covariates: same vs different quire, folio/leaf token count bins, and page-order separation bins `5–9 / 10–19 / >=20` (none below 5). Use the same cutoff for all predetermined page-order variants.
- Deterministic matching: within each `hand × Currier × same-quire-flag × order-distance-bin × token-count-ratio-bin` cell, form without-replacement equal-weight same-section and between-section pair sets using ascending hashed **canonical pair IDs** (hash and tie-break algorithm frozen before data inspection). Avoid any one bifolio appearing in two contrasts within a matched set where feasible; residual repeated use must be modeled as clustered dependence and reported.
- **Primary estimand** `Delta = mean(similarity_same_section - similarity_different_section)` across balanced matched contrasts, equally weighted across qualifying hand×Currier strata. Unique bifolio, not pair, governs effective sample size. Report number of eligible strata, contrasts, bifolia and largest concentration share.
- No imputation, pooling across hand/Currier classes, relaxing matching criteria, changing token representation or dropping unfavorable strata after looking at the test.

**Identifiability/data gate:** before comparing outcomes, require at least **20 valid balanced contrasts**, involving at least **10 distinct bifolia**, with usable pairs from **at least two separate hand×Currier strata** and neither accounting for over 70% of effective matched contrast weight. If this fails, `BLOCKED_IDENTIFIABILITY` and stop the confirmatory test. If a required order variant cannot be mapped a priori, mark **that sensitivity** unavailable; the primary bound-order variant still needs its own gate.

## 6. Physical and ordering controls

Define and freeze three reading-order maps with provenance before any analysis:
- **O1 bound/folio-order:** canonical current catalog order.
- **O2 physically admissible singulion-order candidate:** individually known bifolia kept intact; ordering only from a published, fully specified reconstruction, not similarity-optimized on this corpus. Undefined positions remain missing.
- **O3 constrained alternatives:** 999 deterministic permutations of complete bifolia *within predetermined allowable quire/physical groups*; preserve intact bifolia and the stated missing-leaf/foldout constraints.

The primary test uses **O1**. O2 and O3 are prespecified **robustness/negative controls** and never selected to maximize the observed effect. No conclusion that a reading order is historically correct can follow merely from a larger cosine value.

Further negative control: within each hand×Currier stratum compare similarity against matched **same-quire/different-quire** structural contrasts and report the change after excluding all same-quire pairs. If exclusions destroy common support, label that control non-identifiable instead of interpreting absence as robustness.

## 7. Inference and fixed decision rule

- **Primary significance:** 9,999 deterministic restricted permutations (PRNG `PCG64`, seed recorded in a SHA-256 committed, custodian-controlled manifest). Shuffle entire **bifolio-level section assignments within exchangeable hand×Currier×physical-quiring blocks**, preserving stratum counts, re-run deterministic matching each time. If the exchangeable block structure affords too few unique assignments, exact enumeration is used where possible; otherwise report `BLOCKED_PERMUTATION_NULL`. Do not permute token pairs or individual pages.
- **Uncertainty:** 99% percentile cluster bootstrap over complete bifolios (10,000 deterministic resamples; deduplicate paired leaves and identify intersecting clusters). If bootstrap cannot respect crossed dependencies, a pre-specified conservative multiway-cluster method must be documented **before** seeing the primary result; otherwise inference is inconclusive.
- **Decision:** `SCIENCE_REPLICATION_SUPPORTED` only if (a) all provenance/identifiability/independence/ordering gates pass, (b) `Delta>0`, (c) one-sided restricted-permutation `p<0.01`, (d) lower bound of 99% cluster CI > 0, and (e) the effect's direction does not reverse under O2 where this map is unambiguously defined. If (a) fails: `INCONCLUSIVE_NOT_RUN`. If gates pass but (b)–(d) fail: `NOT_SUPPORTED`; if O2 reverses: `ORDER_SENSITIVE_INCONCLUSIVE`. Failure to reject is not proof of no locality.
- Additional descriptive analyses (ZL3b re-run, optional RF1b, scribe-by-scribe effects, multiple alternative order families) are labeled `EXPLORATORY` and never treated as extra primary successes.

## 8. Independent replication and forbidden leakage

The replication executor must implement a separate IVTFF parser/feature pipeline and use an independently fetched IT2a file with its own SHA-256, source timestamp and manifest. They must provide a row-count/locus-count reconciliation table, matched folio IDs, disagreement table, commit hash and reproducibility command. The verifier must not be the executor. Same manuscript = dependence at manuscript level; refer to this as **cross-transcription / independent-pipeline replication**, not independent manuscript replication.

Do not swap the exploratory ZL3b snapshot for inaccessible IT2a, treat GitHub or agent-task `PASS` as scientific confirmation, interpret missing data as negative or positive evidence, silently drop foldouts or disputed hands, or report p-values from pseudo-independent folio pairs.

## 9. Machine-readable status contract and exit criteria

`engineering_status`: `NOT_STARTED | CODE_READY | TESTS_PASSED | TECHNICAL_BLOCKED | TECHNICAL_FAILED`.  
`data_status`: `MISSING | PARTIAL | FROZEN | VERIFIED`.  
`prereg_status`: `DRAFT | COMMITTED_INTERNAL | EXTERNALLY_WITNESSED`.  
`science_status`: `INCONCLUSIVE_NOT_RUN | BLOCKED_IDENTIFIABILITY | BLOCKED_PERMUTATION_NULL | NOT_SUPPORTED | ORDER_SENSITIVE_INCONCLUSIVE | SCIENCE_REPLICATION_SUPPORTED`.

Task-level `PASS` may imply only successfully delivered artefacts. **Mission scientific completion** requires verified source/independent replication evidence, eligible matched contrasts, valid null, cluster CI, independently reviewed report, and hashes. Missing fields **must block** science status, not be default-filled.

## 10. Deliverable checklist

- [ ] Source/physical/order manifest + hashes and coverage matrix
- [ ] Approved source tables for hand, Currier and bifolios, with mixed/unknown provenance
- [ ] Independent IT2a parser + unit tests, independent reviewer
- [ ] Frozen feasible matching table without revealing response statistic
- [ ] 9,999 restricted permutation outputs + defensible cluster CI, or explicit blocked reason
- [ ] O1/O2/O3 robustness tables / constraints audit
- [ ] Full independent science-review report and separate engineering acceptance result
- [ ] Optional external preregistration witness; without it **never** label as externally preregistered

**Maintainer note:** An internal commit is a pre-specified protocol and an auditable timestamp, not an external preregistration record. Any methodological changes after this version must be dated, diffed and marked exploratory unless explicitly approved *before* replication data are inspected.
