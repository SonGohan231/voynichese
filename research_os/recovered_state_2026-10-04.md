# Odtworzony stan wcześniejszego projektu

## Pochodzenie

Główne źródło: `VOYNICH_MODEL_BOOTSTRAP_SORTED_INDEX_2026-05-17.md` z Google Drive. Jest mapą poprzedniej pracy, a nie niezależnym źródłem prawdy.

## Deklarowany stan bootstrapu

| Pole | Wartość | Status audytowy |
|---|---:|---|
| źródła | 285 | deklaracja bootstrapu |
| zaindeksowane źródła | 285 | deklaracja bootstrapu |
| hipotezy | 126 | deklaracja bootstrapu |
| aktywne hipotezy | 108 | deklaracja bootstrapu |
| `confirmed` | 18 | wymaga ponownego audytu kryteriów |
| evidence cards | 236 | wymaga kontroli proweniencji i niezależności |
| testy | 46 | rodzina analiz nieodtworzona |
| kontrtesty | 724 | niezależność i zakres nieodtworzone |
| literalization candidates | 0 | blokada |
| ready for literalization | 0 | blokada |

## Twarde ograniczenia odzyskane z dokumentów

- Nie rozpoczynać od alfabetu, fonetyki ani tłumaczenia.
- Stage1126 i Stage1127–1140 pozostają warstwami kandydackimi.
- Osiem loci G1+B2 nie może być ocenione wizualnie bez realnych cropów i wyników reviewerów.
- R166B nie posiadał wystarczającego zwrotu thumbnail/contact-sheet; R166C był awaryjną ścieżką.
- Structure Finder wykazywał serię błędów auto-sync HTTP 404.
- `f82v_b1` pozostawał INCONCLUSIVE; `f77v` był fallbackiem, nie zamiennikiem pozytywnego wyniku.
- Raport transferu stwierdzał `FAIL_FOR_PHONETIC_READING_NOW`.

## Dane widoczne w repozytorium

- Atlas 206 rekordów stron, schemat JSON i raport walidacji.
- Gałęzie z atlasem, skanami Yale, eksperymentami held-out i badaniami przestrzennymi.
- Sam fakt istnienia gałęzi lub pliku nie dowodzi poprawności naukowej wyniku.

## Sprzeczności i ryzyka

1. Etykieta `confirmed` jest silniejsza niż obecnie dostępny audyt kryteriów.
2. Raporty funkcjonalno-klasowe zawierają interpretacje semantyczne, podczas gdy most znak→dźwięk pozostaje zablokowany.
3. Duża liczba kontrtestów może oznaczać rygor albo szeroką rodzinę wielokrotnych prób; bez ledgerów nie da się rozstrzygnąć.
4. Brak dostępu do artefaktu jest INCONCLUSIVE, nie dowodem przeciw hipotezie.

## Następna bramka danych

Pobrać tylko manifesty i małe artefakty potrzebne do EXP-2026-001: definicje homologii, współrzędne/cropy wybranych foliów, źródła obrazów, checksumy, kryteria wcześniejszych statusów oraz evidence cards bez ujawniania ślepym annotatorom oczekiwanego efektu.
