# Voynich zodiac: około 30 elementów

Ten katalog odtwarza i zamraża stan wcześniejszej pracy nad diagramami zodiakalnymi Voynicha.

## Stan roboczy

- kanoniczna brama liczebności: 12 paneli, 299 elementów;
- obserwowany układ: jeden panel 29, cztery półpanele po 15, siedem pełnych paneli po 30;
- wcześniejsza wspólna siatka 30 × 12°: FAIL dla przetestowanej implementacji;
- wcześniejszy model Ptolemeusz „jedna gwiazda = jeden wpis / absolutny slot”: FAIL dla przetestowanej implementacji;
- globalny próg jasności: FAIL;
- historyczna topologia nieba: NOT_RUN, ponieważ brak kompletnego audytowanego atlasu 299 punktów.

## Najważniejszy wniosek historyczny

Liczba 30 ma co najmniej cztery historycznie sensowne, konkurencyjne źródła:

1. 30 stopni każdego znaku zodiaku;
2. trzy dekany po 10 stopni;
3. 29–30 dni lunacji lub miesiąca;
4. pojemność/format diagramu bez zewnętrznego referentu.

System 28 mansji księżycowych jest osobną hipotezą i nie może być mieszany z 29–30 dniami lunacji.

## Dokładnie jeden następny test

`BOUNDARY-PERIODICITY-10-vs-15-HELDOUT-01`

Najpierw sprawdzamy, czy neutralne granice strukturalne pełnych paneli powtarzają się co 10 pozycji (`3 × 10`), co 15 pozycji (`2 × 15`), czy nie mają wspólnej fazy. Dopiero po tym wolno wrócić do kosztownego dopasowania historycznego nieba.

## Wynik etapu liczebności

Count-only: rodzina stałego `30` przeżywa; proste modele `28 mansji`, symetryczne `29/30` i ścisła alternacja 29/30 są osłabione. Liczebność sama nie rozróżnia `M_FORMAT`, `M_DEGREE` i `M_DECAN`. Szczegóły: `COUNT_MODEL_REPORT.md`.

## Status

`BLOCKED_INCOMPLETE_ATLAS`

Brak 299 rekordów z dwiema niezależnymi lokalizacjami, ring_index, audytem i SHA źródła. Plik `data/atlas_299_skeleton.csv` zawiera komplet oczekiwanych identyfikatorów, ale nie udaje wykonanych pomiarów.
