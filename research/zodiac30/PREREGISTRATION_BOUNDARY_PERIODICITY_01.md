# Preregistration

## ID

`BOUNDARY-PERIODICITY-10-vs-15-HELDOUT-01`

## Jedno twierdzenie

Po zamrożeniu obiektywnej kolejności 30 elementów, strukturalne granice pełnych paneli skupiają się w jednej wspólnej fazie co 10 pozycji (`3 × 10`, model dekaniczny), co 15 pozycji (`2 × 15`, model połówkowy), albo nie tworzą przenośnej periodyczności.

## Dlaczego ten test

Liczności same rozróżniają rodzinę stałego 30 od prostych modeli 28 i 29/30, ale nie rozróżniają 30 stopni, 3 × 10 dekanów i zwykłego formatu. Test granic jest następnym najtańszym rozróżnieniem i nie powtarza odrzuconej siatki 30 × 12°.

## Dane

Audytowany atlas 299 nymf/elementów obwodowych. Dodatkowych postaci centralnych nie wolno włączać do 299. Wymagane: dwa niezależne pomiary, centroid, ring_index, neutralne cechy wizualne, status PASS i SHA źródła.

## Kalibracja

- Aries: f70v1 + f71r;
- Taurus: f71v + f72r1.

Kalibracja ustala wyłącznie:

1. definicję centrum panelu;
2. kierunek porządkowania;
3. globalną fazę H10 i H15;
4. neutralny boundary score.

Nie wolno dobierać osobnej rotacji ani fazy dla panelu held-out.

## Held-out

- f72r2, f72r3, f72v1, f72v2, f72v3, f73r, f73v.

f70v2 = 29 jest testem odporności, nie częścią wyniku głównego.

## Boundary score

Dla granicy pomiędzy elementami `k` i `k+1` oblicz średnią rangę percentylową pięciu neutralnych składowych:

- przerwa kątowa;
- zmiana promienia;
- zmiana ring_index;
- zmiana orientacji elementu;
- zmiana neutralnej klasy wizualnej/połączenia.

Wagi są równe. Brak składowej oznacza brak tej składowej w całym teście, a nie imputację po panelu.

## Modele

- H10: dwie granice w odstępie 10 pozycji, wspólna faza zamrożona na kalibracji;
- H15: jedna granica naprzeciw początku, wspólna faza zamrożona na kalibracji;
- HNONE: granice bez wspólnej fazy;
- HLOCAL: faza osobna dla każdego panelu, z pełną karą MDL.

## Null i seed

100 000 blokowanych permutacji faz między całymi panelami, z zachowaniem kolejności, liczności i ring_index. Seed: `30152026`.

## PASS/FAIL

PASS dla H10 albo H15 wymaga jednocześnie:

- `p_perm <= 0.05` na held-out;
- przewagi co najmniej 10 bitów MDL nad HNONE i HLOCAL;
- zgodnego kierunku efektu w co najmniej 5 z 7 paneli;
- odporności po usunięciu każdego pojedynczego panelu;
- braku przewagi decoy faz przesuniętych o 1–4 pozycje.

W przeciwnym razie: `INCONCLUSIVE` albo `FAIL_EXACT_MODEL` dla dokładnej wersji.

## Zakaz

Nie używać tekstu etykiet, nazw znaków, katalogu Ptolemeusza ani jasności gwiazd do wyznaczania granic. Historyczne niebo pozostaje zamknięte do czasu rozstrzygnięcia tego testu.
