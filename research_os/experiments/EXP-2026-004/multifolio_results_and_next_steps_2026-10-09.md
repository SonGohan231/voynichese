# EXP-2026-004 — multifolio object, perspective, color and text pilot

**Date:** 2026-10-09. **Agent OS mission:** `6bc4aa31-a68a-48a1-adb9-4e0d6a3271ff` (do not infer completion or scientific success from mission admission). **Current scientific verdict: INCONCLUSIVE / no established same-object other-perspective instance.**

## Audited computer results

| Workstream | Real workflow result | Actual measurement | Important limit |
|---|---|---|---|
| All-Yale computer candidate atlas | [#37890540768](https://github.com/SonGohan231/voynichese/actions/runs/37890540768) SUCCESS, artifact `11598316336` | 206 independent archived photographic canvases; 4,800 digital ROI candidates, 991 cross-folio similarities, 125 queued | Images are source-verified in upstream EXP003; shapes are *not* semantically identified |
| Updated background-aware ranking | [#37892002245](https://github.com/SonGohan231/voynichese/actions/runs/37892002245) SUCCESS, artifact `11598509078` | Top 125 contains 89 dark-ink components, 11 red, 1 green, 24 ochre; ochre has background confound so deprioritized | Short shape dHash does not prove object identity |
| Ring/spoke geometry | [#37890949802](https://github.com/SonGohan231/voynichese/actions/runs/37890949802) SUCCESS, artifact `11598497317` | 37 proposed circular regions in 7 original foldout canvas photos; 186 comparisons of different physical units, 25 candidate rich radial profiles | Radial edge peaks are NOT human-verified ring, star or sector counts |
| Placa spatial tokens of Nine Rosettes | [#37891194941](https://github.com/SonGohan231/voynichese/actions/runs/37891194941) SUCCESS, artifact `11598078968` | 539 positioned token entries; 44 token-bearing regions; 363 unique forms and 63 forms appearing in more than one region | 46 polygon/regions in source; only 44 have listed tokens; Placa image coordinates not yet matched to Yale original JPEG |
| ZL3b Voynich text by folio | [#37892110672](https://github.com/SonGohan231/voynichese/actions/runs/37892110672) SUCCESS, artifact `11598618811` | 227 text page headings, 5,385 IVTFF loci parsed, 64 folios containing L/C/R tokens; 742 pairs of folio headings share at least one selectively filtered L/C/R form | Different folio numbering and partial foldout sheets; labels are not actual ROIs without registration, numerous generic forms |

### Specific folios (only review candidates, never scientific discoveries)

**Ink-contour appearance candidate shortlist** from reranked 206-photo digital atlas:
- **f30v ↔ f31v**: dHash Hamming 2 / 64;
- **f28v ↔ f34v**: dHash Hamming 2 / 64;
- **f22v ↔ f23v**: Hamming 3 / 64;
- **f32v ↔ f33v**: Hamming 3 / 64;
- **f28v ↔ f31v**: Hamming 3 / 64;
- **f45r ↔ f46r**: Hamming 3 / 64.

All are visually unverified digital ink components. dHash is not invariant to arbitrary 3D projection. The presence of a similar little dark mark on two scans is not historical evidence they are the same thing.

**Roundel/radial review priorities**: f67v ↔ f85v/f86r and f67v ↔ parts of f86v (exploratory matching scores ~0.45–0.46, insufficient to establish correspondence). Outlines from foldout views belonging to the same physical sheet cannot be independent heldouts.

**Text comparison**: IVTFF locus types P (paragraph), L (label), C (circular text), R (radial text) enable controlled comparison of signs and labels; source-derived token forms `ol`, `or`, `otedy` recur in multiple annotated Nine Rosettes regions. No decipherment; compare after independent source-coordinate registration and sensitivity to alternative transcription.

### Provenance of third-party data

- Yale Beinecke MS 408 archival JPEG source: `https://collections.library.yale.edu/manifests/2002046`; base 206-photo corpus already SHA-verified in EXP003, original per-image SHA references carried through the atlas and native-image radial pilot.
- `https://github.com/alessandroplaca-uro/voynich-spatial-data`: Alessandro Placa, **CC BY 4.0**, snapshot commit `7580dafa624cf23a63665f4819022003f8d128ef`, 539 positioned tokens; attribution includes Takahashi and Zandbergen–Landini where used. This is a derivative transliteration, not a historically deciphered language.
- `https://www.voynich.nu/data/ZL3b-n.txt`: René Zandbergen ZL3b version dated 2025-05-13, observed source SHA256 `bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc` (hash based on retrieved source bytes). Full original not republished in our repo, only derived counts and folio recurrence.

### Falsification / requirements to claim same object in another view

1. Require two independent annotators to label object class, segmentation polygon, number and order of merlons, spokes, rings, stars, faces, limbs and attachments at full native Yale resolution.
2. Human presence, presentation as a woman and direction of a face must NOT be output from shape proposals, and a machine **miss** is an unknown rather than a zero figure count.
3. Enumerate all colored regions, *unpainted after native-resolution confirmation*, physical folds vs paint and digitization shadow. No chemical inference from RGB or deliberate intentional blankness from low color bounding-box overlap.
4. Characterize every candidate object as graph degree/ports/cyclic order, angular sector and fringe sequence, scale-invariant landmark lengths, separate similarity/rotation/reflection and limited 2.5D consistency tests.
5. Test 2D medieval ornamental null, section/Currier/scribe and physical-unit matched null, an unexamined foldout-level heldout; correct multiple tests and use independent Keeper verification before any PASS.
6. Register text ROIs via checked coordinate transform. No word or direction semantics inferred from token co-location by itself.

**Scientific status:** actual 206-canvas proposals have been produced, but `accepted_same_object_across_different_perspectives=0`. This **does not disprove** recurrence; it marks current absence of evidence. Distinct from workflow `SUCCESS` and from independent Agent OS Keeper acceptance.

### Reproducibility / artifacts

- `research_os/tools/exp004_multifolio_object_atlas.py`; workflow `.github/workflows/exp004-multifolio-atlas.yml`
- `research_os/tools/exp004_radial_rosette_comparison.py`; workflow `.github/workflows/exp004-rosette-radial.yml`
- `research_os/tools/exp004_rosettes_positioned_tokens.py`; workflow `.github/workflows/exp004-rosettes-token-layout.yml`
- `research_os/tools/exp004_ivtff_folio_token_recurrence.py`; workflow `.github/workflows/exp004-ivtff-folio-tokens.yml`
- `research_os/tools/exp004_native_candidate_contact_sheet.py`; workflow contact-sheet step added to `.github/workflows/exp004-multifolio-atlas.yml` (verify latest run before claiming its artifact success).
- Source-linked candidate gallery, rankings and token positioning are GitHub Action artifacts; public repo includes the generator code and this report. No master merge requested or performed.
