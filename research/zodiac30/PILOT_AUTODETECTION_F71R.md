# Pilot automatycznej lokalizacji — f71r

## Cel

Sprawdzić, czy prosty algorytm może bezpiecznie utworzyć atlas figur obwodowych bez ręcznego audytu.

## Źródło

- plik: `data/yale_hq_scans/8/0129_71r.jpg`;
- rekord kanoniczny: `atlas/records/0129_71r.annotation.json`;
- oczekiwana liczba: 15;
- roboczy środek: `(1400, 1800)` px;
- roboczy promień: `1250` px.

## Metoda pilota

1. transformacja polarna wokół środka diagramu;
2. profil kątowy z nasycenia barw i energii krawędzi;
3. wybór 15 lokalnych maksimów z minimalnym odstępem;
4. wybór promienia o najwyższej lokalnej energii dla każdego kąta;
5. wizualna kontrola punktów na obrazie natywnym.

## Wynik

- około 11 z 15 punktów trafiło na figury;
- 4 punkty trafiły na gwiazdy, tekst albo pustą przestrzeń;
- część niebarwionych figur została pominięta;
- radialne linie, etykiety i gwiazdy tworzą konkurencyjne maksima.

## Decyzja

`FAIL_AS_FULL_ATLAS_SEGMENTER`.

Algorytm może służyć wyłącznie do wstępnego podpowiadania kandydatów. Nie wolno nadać jego wynikom `audit_status=PASS`, używać ich w held-out ani dopasowywać do katalogu historycznego. Każdy punkt wymaga niezależnej lokalizacji i kontroli wizualnej.

## Wpływ na następny ruch

Nie rozwijać kolejnego swobodnie strojenego detektora na tych samych panelach. Najpierw wykonać ręczny, neutralny atlas kalibracyjny Barana i Byka, a algorytm traktować tylko jako niewidoczną dla mierzącego kontrolę pomocniczą.
