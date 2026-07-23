---
name: voynich-zodiac-30-sky-discrimination
description: Rozróżnia konkurencyjne wyjaśnienia około 30 elementów na diagramach zodiakalnych Voynicha: format, stopnie, dekany, cykl księżycowy, kalendarz, historyczne niebo i model lokalny.
---

# Voynich Zodiac 30 and Historical Sky Discrimination

## Cel

Testuj modele `M_FORMAT`, `M_DEGREE`, `M_DECAN`, `M_LUNAR`, `M_CALENDAR`, `M_SKY` i `M_FREE` bez zakładania z góry, że liczba 30 oznacza dni, stopnie albo gwiazdy.

## Obowiązkowe przygotowanie

1. Odczytaj `references/MODEL_REGISTRY.md`.
2. Odczytaj `references/DECISION_PROTOCOL.md`.
3. Odtwórz wcześniejsze eksperymenty dotyczące liczby 30, siatek, Ptolemeusza i historycznego nieba.
4. Nie powtarzaj prawidłowo odrzuconej implementacji bez nowego, rozróżniającego przewidywania.

## Kanoniczna brama danych

Pełny atlas zawiera dokładnie **299 elementów obwodowych**:

- f70v2 = 29;
- f70v1 = 15;
- f71r = 15;
- f71v = 15;
- f72r1 = 15;
- f72r2 = 30;
- f72r3 = 30;
- f72v1 = 30;
- f72v2 = 30;
- f72v3 = 30;
- f73r = 30;
- f73v = 30.

Cztery dodatkowe postacie centralne nie należą do mianownika 299.

Każdy rekord musi mieć: `element_id`, panel, natywne współrzędne z dwóch niezależnych pomiarów, różnicę pomiarów, `ring_index`, status audytu, plik źródłowy i `source_sha256`.

Przy niezgodności zwróć `BLOCKED_INCOMPLETE_ATLAS`. Liczności są bramą kontrolną, nie instrukcją dodawania lub usuwania figur.

## Kolejność testów

1. liczebność i podział 29/30 oraz 15+15;
2. neutralna periodyczność granic i topologia wewnętrzna;
3. transfer na całe panele held-out;
4. dopiero po przejściu bramy — historyczne źródła i katalogi nieba.

Nie mieszaj testu liczebności z geometrią. Nie ujawniaj katalogu historycznego procedurze tworzącej atlas.

## Held-out i kontrola

- dziel całe panele, nie pojedyncze figury;
- zamroź orientację, fazę, progi, koszt i regułę korespondencji przed held-out;
- porównaj z równomiernym formatem 30, permutacjami zachowującymi panel i pierścień, lokalnym modelem bez znaczenia i historycznymi systemami 28–30;
- opłać pełny koszt MDL: rotację, odbicie, skalę, fazę, wybór katalogu, wybór gwiazd, próg, przypisania, wyjątki i nieprzypisane punkty.

## Decyzje

`PASS_M_SKY` wymaga przewagi na held-out nad formatem 30 i nullami, dodatniego pełnego MDL, odporności orientacyjnej oraz historycznej dostępności danych.

`FAIL_EXACT_MODEL` dotyczy wyłącznie prerejestrowanej implementacji. `INCONCLUSIVE` nie jest wsparciem. Zmiana modelu lub kryteriów po otwarciu held-out daje `INVALID`.

## Aktualnie zamrożony następny test

`BOUNDARY-PERIODICITY-10-vs-15-HELDOUT-01`.

Nie uruchamiaj dopasowania Ptolemeusza ani innego historycznego nieba przed `PASS` walidatora atlasu 299.

## Zapis

Zachowaj prerejestrację, atlas i SHA, kod, kalibrację, held-out, null, seed, pełny MDL, wyniki per panel i wpływ na każdy model. Raportuj według `references/OUTPUT_TEMPLATE.md` i dołącz kompletny handoff.
