# Schemat pełnej inwentaryzacji foliów Manuskryptu Voynicha — v1

## Cel

Pakiet służy do identycznego, powtarzalnego opisu każdej folii lub innego rekordu źródłowego:
- pola pergaminu, tekstu, ilustracji, diagramów i marginesów;
- uszkodzenia i miejsca nakładania tekstu z ilustracją;
- pełna hierarchia obiektów rodzic–dziecko;
- liczby elementów albo jawny status niemożności policzenia;
- kolory części i obiektów;
- geometria tekstu bez wymuszania granic przez transliterację;
- relacje lokalne;
- ciągłość kompozycji w kierunkach N/S/E/W;
- kandydacki graf podobieństw między stronami z kontrolą negatywną.

## Najważniejsza zasada konstrukcyjna

Nie należy wpisywać wszystkich danych w jeden bardzo szeroki rekord. `FOLIO_MASTER` identyfikuje stronę, a pozostałe tabele zawierają dowolną liczbę obiektów, tekstów, relacji i obserwacji kolorów powiązanych przez identyfikatory.

## Układ współrzędnych

- Początek obrazu: narożnik NW.
- Oś X rośnie w stronę E.
- Oś Y rośnie w stronę S.
- Kierunki N/S/E/W odnoszą się do orientacji obrazu roboczego.
- Każdą geometrię zapisuj w pikselach i — gdy to możliwe — także jako wartości znormalizowane 0–1.
- Dla nieregularnych obiektów wybierz `POLYGON` lub `MASK`, nie wymuszaj prostokątnego BBOX.
- Zapisuj transformację między oryginalnym skanem i obrazem roboczym.

## Liczenie

Każda liczba ma status:
- `EXACT` — policzone jednoznacznie;
- `LOWER_BOUND` / `UPPER_BOUND` — tylko granica;
- `RANGE` — przedział;
- `ESTIMATED` — szacunek;
- `NOT_COUNTABLE` — elementy niepoliczalne;
- `OBSCURED` — zasłonięte;
- `DAMAGED` — uszkodzenie uniemożliwia policzenie;
- `NOT_APPLICABLE` — pole nie dotyczy folii;
- `UNCERTAIN` — niejednoznaczne;
- `NOT_ASSESSED` — jeszcze nie oceniono.

Nie wpisuj zera, gdy pole nie dotyczy strony. Wpisz `NOT_APPLICABLE`.

## Neutralność opisu

Używaj klas morfologicznych i geometrycznych. Nazwa interpretacyjna może pojawić się wyłącznie w notatce jako hipoteza, a nie jako podstawowa klasa obiektu.

Przykład:
- właściwe: `SUN_LIKE_DISK`, 23 promienie, czerwone wypełnienie;
- niewłaściwe jako klasa główna: „Słońce marca”.

## Tekst

- Granice wyznaczaj wizualnie.
- Transliteracja jest referencją.
- Kolejność czytania wpisuj tylko, gdy jest obserwowalna.
- Związek tekstu z ilustracją opisuj relacją geometryczną, np. `INSIDE`, `TEXT_SURROUNDS_OBJECT`, `ABOVE`.

## Identyfikatory

Zalecany format:
- folio: `VM-FOLIO-f1r`;
- region: `VM-FOLIO-f1r-R001`;
- obiekt: `VM-FOLIO-f1r-O001`;
- grupa tekstowa: `VM-FOLIO-f1r-TG001`;
- linia: `VM-FOLIO-f1r-L001`;
- relacja: `VM-FOLIO-f1r-REL001`;
- overlay: `VM-FOLIO-f1r-OV001`.

## Pełnostronicowy overlay

Każda folia powinna mieć:
1. obraz bazowy;
2. warstwę granicy pergaminu;
3. pola tekstowe;
4. pola ilustracji i diagramów;
5. obiekty z identyfikatorami;
6. uszkodzenia;
7. nakładanie tekst–ilustracja;
8. opcjonalnie linie tekstu;
9. legendę.

Overlay nie zastępuje tabel. Jest wizualnym indeksem do identyfikatorów.

## Graf między stronami

Każda krawędź musi zawierać:
- cechy zgodne;
- cechy niezgodne;
- metodę;
- kontrolę negatywną;
- wynik kontroli;
- status i pewność.

Nie wolno tworzyć krawędzi wyłącznie na podstawie ogólnego podobieństwa tematycznego.

## Skład pakietu do pobrania

- `Voynich_Folio_Inventory_Template.xlsx` — główny arkusz z 206 slotami źródłowymi i tabelami bez limitu liczby obiektów;
- `folio_card_template.md` — karta pojedynczej folii;
- `voynich_folio.schema.json` — schemat rekordu maszynowego;
- `controlled_vocabularies.json` — słowniki;
- `tables/*.csv` — puste nagłówki tabel do importu do baz danych;
- `OVERLAY_MANIFEST` i `CROSS_PAGE_GRAPH` — specyfikacja overlay oraz powiązań między stronami.
