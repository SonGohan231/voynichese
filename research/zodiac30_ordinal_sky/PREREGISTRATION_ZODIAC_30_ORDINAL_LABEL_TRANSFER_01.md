# Preregistration: ZODIAC-30-ORDINAL-LABEL-TRANSFER-01

## Jedna hipoteza

Jeżeli etykiety oznaczają uporządkowane pozycje 1–30 wspólne dla znaków, właściwości tekstowe etykiety na pozycji `i` powinny przenosić się z Barana i Byka na niewidziane znaki lepiej niż po losowym przesunięciu całej sekwencji etykiet w obrębie znaku.

## H0

Etykiety są zależne od znaku, lokalnego układu lub słownika etykiet, ale numer pozycji 1–30 nie przewiduje ich formy między znakami.

## Zamrożone dane

- źródło: RF1b-er Basic EVA;
- typ locus: Lz;
- kalibracja: Aries i Taurus;
- held-out: wszystkie zachowane znaki z dokładnie 30 etykietami poza kalibracją;
- znak z 29 etykietami: test odporności z dokładnie jednym brakującym slotem;
- kolejność: kolejność locus w pliku źródłowym;
- Aries = f70v1 następnie f71r;
- Taurus = f71v następnie f72r1.

Nie wolno zmieniać kolejności po zobaczeniu wyniku.

## Normalizacja

- komentarze IVTFF są usuwane;
- niepewne spacje oznaczone przecinkiem są ignorowane;
- w alternatywie `[a:b]` używany jest pierwszy wariant;
- kropka między członami etykiety pozostaje;
- znaki niealfabetyczne i znaczniki edytorskie są usuwane;
- etykieta pusta albo nieczytelna pozostaje jawnie brakująca.

## Podobieństwo dwóch etykiet

Średnia pięciu równoważnych składowych:

1. znormalizowane podobieństwo Levenshteina;
2. względna długość wspólnego prefiksu;
3. względna długość wspólnego sufiksu;
4. Dice dla bigramów znakowych;
5. podobieństwo długości.

Wagi nie są uczone.

## Statystyka główna

Dla każdej pozycji `i` powstaje profil kalibracyjny z etykiet Aries[i] i Taurus[i]. Dla każdego znaku held-out oblicza się średnie podobieństwo jego etykiety na pozycji `i` do obu etykiet kalibracyjnych. Statystyka główna jest średnią po wszystkich pozycjach i znakach held-out.

## Null

100 000 permutacji. W każdej permutacji każdy znak held-out otrzymuje niezależne losowe przesunięcie kołowe 0–29. Skład etykiet i lokalna kolejność w znaku pozostają zachowane.

Seed: `3001425`.

## Kryteria

PASS wymaga jednocześnie:

- `p_perm <= 0.01`;
- efekt `observed - null_mean >= 0.02`;
- wynik dodatni względem średniej wszystkich przesunięć w co najmniej 5 z 7 znaków held-out.

FAIL_EXACT_MODEL, gdy:

- `p_perm > 0.05`, albo
- efekt jest niedodatni, albo
- zgodny kierunek występuje w najwyżej 3 z 7 znaków.

Pozostałe wyniki: INCONCLUSIVE.

## Test jednego brakującego slotu

Dla znaku z 29 etykietami sprawdza się wszystkie 30 możliwych położeń pojedynczej luki. Najlepsze dopasowanie jest porównywane z nullem, który również maksymalizuje wynik po wszystkich lukach, dzięki czemu koszt wyboru luki jest uwzględniony.

## Zakaz interpretacyjny

PASS nie oznacza, że etykiety są nazwami stopni, dniami albo współrzędnymi. Oznacza jedynie transfer informacji pozycyjnej. FAIL nie odrzuca geometrii 30 stopni, jeżeli kolejność locus nie odpowiada kolejności fizycznej na diagramie.
