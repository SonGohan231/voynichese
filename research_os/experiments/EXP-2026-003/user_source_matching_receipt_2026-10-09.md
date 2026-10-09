# EXP-2026-003: original Yale image-source candidate matching receipt (2026-10-09)

**Execution:** GitHub Actions [run 37882705386](https://github.com/SonGohan231/voynichese/actions/runs/37882705386)
**Artifact:** exp003-user-photo-source-matching-results, GitHub artifact ID 11594493142, SHA-256 ZIP digest \`52483a29ecb67b1e7962706e89aa1d05745545dd852046ff05b67dccba4a5110\` (GitHub API report).
**Source fidelity:** 206 / 206 unique archived Yale JPEGs re-fetched and verified against independent archived SHA-256 provenance table; zero retrieval/hash failures.
**Tool evidence:** synthetic deterministic pHash self-test PASS; full 206-file source match comparison PASS. 
**Research status:** EXPLORATORY CANDIDATE RANKING, NEVER DECIPHERMENT OR DEPTH EVIDENCE.
**Input:** image fingerprints on 5 uploaded screenshots; fourth text-only/obscured screenshot excluded; three local thirds from screenshot IMG06 separately considered but not independent folios.

## Strong source candidates (no confirmatory inference)

| Uploaded example | Candidate Yale folio label | Yale canvas OID | Weighted pHash Hamming (/64) | Gap to second | Status |
|---|---|---|---:|---:|---|
| IMG01, botanical | **9r** | 1006092 | 3.143 | 13.714 | STRONG_CANDIDATE_MANUAL_REVIEW_REQUIRED |
| IMG02, balneological | 75v | 1006209 | 16.000 | 2.857 | WEAK_CANDIDATE_DO_NOT_IDENTIFY |
| IMG03, colored cropped | 23v | 1006119 | 20.000 | 0.571 | UNRELIABLE_CROP_MATCH |
| IMG05, Rosettes | **85v and 86r (foldout)** | 1006231 | 0.857 | 20.572 | STRONG_CANDIDATE_MANUAL_REVIEW_REQUIRED |
| IMG06, botanical spread | **94v and 95r** | 1006241 | 0.000 | 22.286 | STRONG_CANDIDATE_MANUAL_REVIEW_REQUIRED |

These distances compare uploaded screenshots with Yale original-image signatures across four whole-image areas, weighted 3:2:1:1 (full, central, top, bottom). Lower is more similar. Matching is NOT an externally calibrated likelihood, and manually added arrows affect signatures. IMG06 regional subcrops ranked unrelated folios; **do not** infer that IMG06 contains three independent source folios. The matching result suggests one source composite canvas covering the facing folios 94v and 95r.

**Current conclusions:** The strong image-source candidates provide a source-native starting set for tracing lines, comparing colors and testing 2D vs layered 2.5D. Weak screenshot matches require independent crop registration (e.g. ORB/SIFT+RANSAC) before attributing any folio. No physical fold geometry, edge direction, flow, hidden 3D world, translation, meaningful pigment role or visual-lexical encoding has been confirmed.

The source-reference paper by Layfield & Lisa Fagin Davis, *Singulion Structure and the Voynich Manuscript*, Digital Medievalist 19 (2026), DOI:10.4000/16k0a, is a separately established order hypothesis, NOT an order derived by optimizing these image matches.

Next recommended phase: (1) separately inspect original native Yale crops for IMG01/IMG05/IMG06; (2) subimage registration for IMG02/IMG03; (3) two independent grayscale-only object annotators; (4) original photo source color and topology pilots with nulls and physical-unit clustering; (5) foldout and singulion order sensitivity without selection bias.
