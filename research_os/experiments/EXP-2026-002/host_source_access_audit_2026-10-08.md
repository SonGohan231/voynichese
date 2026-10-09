# EXP-2026-002 — host-side source access and physical-evidence triage (2026-10-08)

**Status:** PARTIAL_EXTERNAL_SOURCE_REVIEW; **NOT** an image-by-image codicological audit, physical-order freeze, external preregistration or science result.  
**Agent OS mission:** `aa42d413-6ecf-455f-863a-095a79901ac1` (Dyrygent 3.8.1 / ChatGPT host workstream).  
**Baseline:** PR #14, issue #15; do not overwrite historical data or revise preregistration in response to experimental outcomes.  
**Method:** host web lookup of accessible public descriptions plus comparison to files already present on the PR branch. Source lookup and page reading are not direct examination of all MS408 folio scans, not a commissioned palaeographic/codicological review. No inference from token similarities was performed.

## Audited source pointers and access observations

| ID | Source and address | Host observation | Status and limitations |
| --- | --- | --- | --- |
| YALE-01 | Yale Beinecke's MS408 overview: https://beinecke.library.yale.edu/beinecke/collections/beinecke-cipher-voynich-manuscript | Yale describes high-resolution manuscript images and a catalog record with collation/missing leaves. | ACCESSIBLE: library overview **only**, not an IIIF canvas-by-canvas check. |
| YALE-MANIFEST | Proposed Yale manifest URL: https://collections.library.yale.edu/manifests/oid/2002046 | Host web retrieval rejected access; raw manifest bytes and canvas inventory unavailable in this workstream. | NOT_INSPECTED. **No** assertion of 52/52 canvas verification or manifest SHA. |
| Q9-01 | René Zandbergen, Quire 9: https://www.voynich.nu/q09/ | HTML description states f67/f68 one bifolio, joined foldouts, additional sewn parchment strip, quire mark at f67r1; cited Yale links for scans. | SECONDARY_DESCRIPTIVE corroboration of draft ledger; no direct stitching-hole scan adjudication. |
| Q9-02 | René Zandbergen, origin/binding note: https://www.voynich.nu/extra/sp_origin.html | Note discusses different physical reading of f67/f68 fold axis and quire mark, while folio numbers favor current binding position. | RIVAL_HYPOTHESIS. Do not hard-code old sewing or a new original order. |
| Q14-01 | René Zandbergen, Quire 14: https://www.voynich.nu/q14/index.html | Describes one large f85/f86 sheet divided by one horizontal and two vertical creases into six panels (3×2), joined Rosettes imagery on one side. | SECONDARY_DESCRIPTIVE corroboration; crease coordinates/repair traces not independently measured. |
| LFD-01 | Lisa Fagin Davis, codicology: https://manuscriptroadtrip.wordpress.com/2025/01/19/voynich-codicology/ | Existing PR #14 review cites Davis's manuscript examinations and warns about debated previous binding. | EXISTING_SOURCE_REFERENCE; not newly reexamined in this host workstream. |
| IT2a | https://www.voynich.nu/data/IT2a-n.txt | PR #14 source audit records a pinned mirrored IT2a artifact: SHA-256 `7f27a8b0feed8f6de0a99900df6bf912dd1d295c38e5f830bac8b41c3f536fb5`, 225 headers. | PRIOR_PROJECT_EVIDENCE; hash **not recomputed by this host**. |
| ZL3b | https://www.voynich.nu/data/ZL3b-n.txt | PR #14 source audit records pinned ZL3b SHA-256 `bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc`. | PRIOR_PROJECT_EVIDENCE; hash **not recomputed by this host**. |
| 1996-COLLATION | https://ic.unicamp.br/~stolfi/voynich/mirror/reeds/docs/quires.txt | PR #14 already preserves physical grouping discrepancy QA-B2: chart f2/f6 vs IT2a f2/f7. | UNRESOLVED_SOURCE_DISCREPANCY; raw historical source bytes not independently hashed. |

**Specific Yale scan pointer checks (not inspection):**
- q9 `f67r1/f67r2`: Zandbergen's scan link resolved to `https://collections.library.yale.edu/catalog/2002046?child_oid=1006194`; host fetch returned **HTTP 403**. This URL is a source pointer, **not** evidence of having viewed the scan.
- q14: Zandbergen's Yale scan pointer resolved to `https://collections.library.yale.edu/catalog/2002046?child_oid=1006228`; host fetch returned **HTTP 403**. The mapping of that pointer to exact faces/panels still requires machine-readable manifest confirmation.

## Implications for workstreams A–D

- **A — physical scans:** **BLOCKED FOR COMPLETE COVERAGE.** Existing geometry graph counts 20 numbered quires / 52 surviving physical groups / 6 missing-bifolio placeholders, but the requested cross-index of all 52 groups to exact Yale IIIF canvases and visible sewing/folding details does not exist as verified output of this host run. Distinguish source-pointer recovered from image actually inspected.
- **B — quire collation:** descriptive independent-source corroboration exists for q9 and q14. Do not claim that repaired creases, sewing cuts, original binding axis or every q8–q20 group were directly observed from scans here. Record `OBSERVED_FROM_DESCRIPTION`, `SCAN_NOT_INSPECTED`, `RIVAL`, and `UNKNOWN` distinctly.
- **C — IT2a/ZL3b:** existing draft reports header parity 225/225 and source checks. This host workstream did not re-download/re-hash their raw bytes; no new independent validator PASS. The 1996 QA-B2 duplicate remains explicitly retained.
- **D — order variants:** O1 requires actual current bound order vs Yale scan verification; O2 remains **NOT_READY/UNKNOWN** without independently sourced full physically permissible ordering; O3 restrictions and seed must be independently frozen **before** evaluating lexical metrics. Mathematical control permutations are NOT a proposed historical order.

## Evidence and next review gates

1. Obtain Yale IIIF JSON by a legitimately functioning source reader; pin manifest hash and exact canvas IDs to each extant folio/page/panel. Log URL, provenance, bytes/hash, observed marks, crop/coordinate and who examined the pixel data. This step must fail-closed on 403 rather than treating descriptions as visual inspection.
2. Commission a **different** codicology reviewer to collate photographed bifolia independently of our proposed O2 and of lexical statistics. Preserve disagreement and the six absent components; q9, q13, q14 and q20 are mandatory exception cases.
3. Re-fetch independently the original and mirrors for IT2a and ZL3b, confirm hashes, source headers and differing category definitions (Currier language vs LFD hand), report QA-B2 discrepancy.
4. After an independent evidence-quality verdict, freeze each admissible structural edge with one of `HARD/PHYSICAL`, `CANDIDATE`, `UNKNOWN`; only then may the separated analyst inspect IT2a inferential outputs. No HELD-OUT from EXP-2026-001 may be exposed.
5. Report final status as **INCONCLUSIVE_NOT_RUN** pending physical-image completeness, external preregistration where required and prospective primary-statistic verification.

**Review integrity:** This file documents *only* source accesses completed by the host and clearly marked pre-existing PR assertions. It does not certify Agent OS subworkstream output, true original manuscript order, decoding or any positive statistical significance.
