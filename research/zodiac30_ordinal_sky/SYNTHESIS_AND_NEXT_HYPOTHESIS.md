# Synthesis after ZODIAC-30-ORDINAL-LABEL-TRANSFER-01

## 1. Executed result

`ZODIAC-30-ORDINAL-LABEL-TRANSFER-01` returned:

`FAIL_EXACT_REFERENCE_LOCUS_ORDER_MODEL`

- 299 Lz loci were parsed from RF1b-er;
- counts: Pisces 30, Aries 30, Taurus 30, Gemini 29, all other preserved signs 30;
- observed held-out similarity: 0.237534;
- circular-shift null mean: 0.239453;
- effect: -0.001919;
- permutation p: 0.730373;
- concordant signs: 4/7.

The exact RF1b locus order therefore does not behave as a transferable degree index shared across signs. Best shifts differ substantially between signs.

The Gemini one-gap stress test selected candidate slot 29 only after maximizing over gap and rotation; corrected p = 0.0667. It is not evidence for a specific missing degree.

## 2. What this eliminates

It weakens the claim:

> label number 1, 2, ... 30 has the same textual function in every preserved zodiac sign.

It does not eliminate:

- 30 as the number of degrees in a sign;
- 30 as a calendar or graphical capacity;
- a geometric ordering different from the RF1b locus order;
- sign-specific names of stars, paranatellonta, days, patients, remedies or operations.

## 3. Corrected anomaly

Two different denominators must never again be mixed:

- Pisces f70v2: 29 peripheral figures but 30 Lz labels;
- Gemini f72r2: 30 figures but 29 Lz labels.

This pattern is more consistent with independent drawing and labeling omissions than with a deliberate alternating lunar 29/30 scheme.

## 4. Computed sky 1404–1430

The ephemeris reconstruction found two Jupiter–Saturn conjunction epochs:

- 1405-01-16 at 23.77° tropical Aquarius; angular separation 0.488°; only 18.2° from the Sun;
- a triple conjunction in 1425 at approximately 17.30°, 16.55° and 12.67° tropical Scorpio; angular separations 1.18–1.26° and good solar elongations.

The strongest sampled European solar eclipses were:

- 1406-06-16 — total at the Paris reference point;
- 1409-04-15 — large partial in the central-European sample, annular farther north-west;
- 1415-06-07 — total at Milan and Prague reference points;
- 1424-06-26 — near-total partial at Prague and Vienna reference points.

A total lunar eclipse visible in the reference belt occurred on 1425-11-25. The preceding 1425-11-10 solar eclipse was small in the sampled locations, so the pair is not by itself an exceptional European visual signature.

General precession across the 26-year interval is only about 0.363°. Fixed-star geometry therefore cannot identify one year in this interval at manuscript drawing precision.

## 5. Historical significance of 1425

A late-medieval horoscope for the 1425 triple Jupiter–Saturn conjunction survives. Scholarly work on the notebooks of S. Belle treats this conjunction as a detailed case study and shows that late-medieval practitioners calculated and judged such events using the Parisian Alfonsine Tables tradition.

This establishes historical availability, not a Voynich identification.

## 6. Structural reading of the astronomical folios

Published inventories of Quire 9 describe a repeated family of canonical counts:

- f67r1: 24 sectors around a central lunar face;
- f67r2: 12 sectors/moons, 12 sector labels and a subset of seven labeled moons;
- f68r1: 29 scattered labeled stars with Sun/Moon imagery;
- f68r2: paired Sun and Moon circles inside a larger star field;
- f68r3: a small seven-star group connected to the Moon;
- zodiac folios: 29–30 figures and 29–30 labels per sign.

The most economical current interpretation is not a literal fixed-star atlas. It is a family of circular astronomical/astrological cycle tables combining units such as:

- 24 parts of a day;
- 12 months or signs;
- 7 classical planets or a seven-star asterism;
- 29–30 lunar/calendar positions;
- 30 degrees of a zodiac sign;
- Sun–Moon relations and possible syzygies.

The counts alone do not determine which meaning belongs to each folio.

## 7. Ranked model update

### A. Astronomical–calendar operational handbook

Status: `BEST_CURRENT_FAMILY`.

The diagrams likely organize cycles and correspondences used in astrology, calendrics or astro-medicine rather than reproduce one realistic sky view.

### B. Sun–Moon phase, eclipse and syzygy tables

Status: `PLAUSIBLE_COMPONENT`.

Repeated Sun/Moon faces, lunar shading and star fields support this as one component, but no unique dated eclipse has been demonstrated.

### C. f73r as a 1425 Scorpio conjunction chart

Status: `LOW_PROBABILITY_BUT_TESTABLE`.

Arguments for:

- the event is inside the manuscript date window;
- it occurred three times in Scorpio;
- medieval practitioners demonstrably cast a horoscope for it;
- f73r contains a central seven-pointed star tethered to the Scorpio figure.

Arguments against:

- the central symbol is one star, not an explicit Jupiter–Saturn pair;
- similar tethered-star iconography may be generic;
- no certified ordinal zero maps the 13/16/17-degree targets;
- selecting f73r after discovering the 1425 event incurs a major model-selection cost.

### D. Literal year-specific fixed-star map

Status: `DISFAVORED`.

Fixed stars change too little between 1404 and 1430, and the ordinal label-transfer test failed.

## 8. Exactly one next falsifiable experiment

`ASTRO-CYCLE-FUNCTIONAL-LABEL-TRANSFER-01`

### Claim

Labels attached to the same functional astronomical role—Sun, Moon, seven-planet position, star field, connecting line and circular sector—share stronger textual features across Quire 9 than labels matched only by page or by random location.

### Why this test

The failed ordinal test says the useful invariant is probably not slot number 1–30. The repeated diagram types suggest that the invariant may instead be **functional role**.

### Required data

A neutral geometry-first inventory of all labels and their attachment roles on f67r1–f68v2, blinded to their EVA transcription until roles are frozen.

### PASS

- held-out role classification above a preregistered baseline;
- permutation p <= 0.01;
- at least 10 bits MDL advantage over page-only and random-role models;
- transfer to a whole held-out folio.

### FAIL

No held-out role transfer or no positive full-cost MDL.

## 9. Decision

Do not continue searching arbitrary years until a page feature predicts a year-specific event. Preserve 1425 as a deferred candidate. The next high-information move is to test functional label roles across the astronomical diagrams.
