# EXP-2026-001 — held-out visual-grammar prediction

Status: **DRAFT / NOT RUN**  
Cel: wybrać test o największej wartości informacyjnej, zdolny osłabić H1 bez używania koloru do budowy geometrii.

## Audyt gotowości 2026-10-04

`research_os/tools/readiness.py` sprawdził 206 rekordów atlasu. Proweniencja źródeł i checksumy przechodzą, ale żaden rekord nie zawiera jeszcze kwalifikowanej kombinacji jednostki wizualnej, relacji lokalnej i niezależnego przeglądu. Wynik to `INCONCLUSIVE_NOT_RUN`; generator splitu odmówił pracy i nie ujawnił HELD-OUT. Pełny, maszynowy dowód znajduje się w `readiness_report.json`.

Testy narzędzia używają wyłącznie syntetycznych rekordów i sprawdzają odmowę dla danych niegotowych, deterministyczność, rozłączność splitów oraz połączenie stron złożonych/foldoutów w jedną grupę.

## Zamrożona bramka anotacji

Przed obejrzeniem jakiejkolwiek niezależnej anotacji zamrożono kontrakt w `research_os/annotation/README.md`. Dwa różne identyfikatory annotatorów muszą pokryć pełny kanoniczny zbiór 183 rekordów o roli `FOLIO`, pracując z oryginalnymi skanami i bez dostępu do automatycznych kandydatur, predykcji, etykiet hipotez, drugiej anotacji ani przyszłego splitu.

Przejście do adjudykacji wymaga jednocześnie: F1 detekcji obiektów `>= 0.80` przy IoU klasy zgodnej `>= 0.50`, mediany IoU `>= 0.75`, dokładnej zgodności zbiorów sektorów portów `>= 0.80` i F1 skierowanych relacji okluzji na unii zgłoszonych relacji `>= 0.80`. Dopasowanie obiektów maksymalizuje najpierw liczebność, potem łączny IoU. Pusty mianownik lub brak relacji daje `NOT_ASSESSED` i blokuje bramkę. PASS tej bramki oznacza wyłącznie `READY_FOR_ADJUDICATION`; nie tworzy ground truth i nie odblokowuje HELD-OUT.

## Zamrożony plan mocy

183 rekordy `FOLIO` tworzą 93 niezależne grupy liści po połączeniu recto/verso i stron złożonych. Planowany HELD-OUT 20% daje około 19 grup. Dla jednostronnego `alpha = 0.01` i mocy 0,80 normalne przybliżenie dla sparowanych różnic wyniku na poziomie grupy wymaga 18 grup dla standaryzowanego efektu `d = 0.75`; przy 19 grupach minimalny wykrywalny efekt wynosi około `d = 0.727`.

Oznacza to moc wyłącznie dla dużego efektu. Mniejszy efekt nie może być po fakcie przedstawiony jako potwierdzenie: otrzymuje `INCONCLUSIVE`, chyba że przed odślepieniem zostanie zamrożona osobna dokładna analiza mocy. Pseudoreplikacja rekordów, obiektów lub portów jako niezależnych obserwacji jest zabroniona. Raport: `power_plan.json`.

## Hipoteza i null

- H1: mały, zamrożony katalog transformacji geometrii przewiduje porty i relacje okluzji homologicznych struktur na niewidzianych foliach lepiej niż proste baseline.
- H0: trafność nie przekracza baseline uwzględniającego częstości klas, sekcję, folio i złożoność rysunku.

H2a/H2b nie są testowane w fazie geometrii. Kolor pozostaje zasłonięty.

## Jednostka analizy

Jednostką jest wcześniej zdefiniowany obiekt/region z jednoznacznym identyfikatorem folio, zamrożonym obrysem, listą portów i relacjami okluzji. Jednostki nie mogą być tworzone po obejrzeniu HELD-OUT.

## Dane minimalne i bramki

1. Oryginalne identyfikatory foliów i źródła skanów.
2. Checksumy wszystkich obrazów i masek.
3. Zamrożony katalog homologii i dopuszczalnych transformacji.
4. Kontury/wypełnienia znormalizowane tak, aby nie przekazywać informacji o kolorze ani intensywności.
5. Co najmniej dwa niezależne blind annotations dla portów i okluzji oraz adjudykacja bez znajomości predykcji modelu.
6. Grupowy split po folio, z kontrolą sekcji i skryby; żaden crop z jednego folio nie może trafić do różnych części splitu.

Jeśli dowolna z bramek 1–6 nie przejdzie, wynik eksperymentu to `INCONCLUSIVE_NOT_RUN`.

## Podział

- TRAIN: 60% foliów.
- VALIDATION: 20% foliów; wyłącznie wybór z góry ograniczonego wariantu modelu.
- HELD-OUT: 20% foliów; niedostępny dla Geometry, Homology i Perspective do chwili zamrożenia modelu i predykcji.
- Split jest deterministyczny z zapisanym seedem, stratyfikowany według sekcji i poziomu złożoności.

Mapa sekcji musi pochodzić z jawnego źródła z checksumą i pokrywać dokładnie wszystkie
kwalifikowane rekordy zgodnie z `section_strata.schema.json`. Indeks bootstrap Drive z
2026-05-17 oraz ukierunkowane wyszukiwanie Drive nie ujawniły autorytatywnej mapy
folio→sekcja, dlatego żadna mapa nie została odtworzona z pamięci ani domysłu. Brak mapy,
brak proweniencji lub różne sekcje wewnątrz połączonej grupy liścia blokują split.

Poziom złożoności jest wyliczany przez custodiana dopiero z zamrożonej adjudykacji jako
suma liczby obiektów i skierowanych relacji okluzji w grupie liścia. Grupy uszeregowane
deterministycznie według `(wynik, group_id)` są dzielone na tertyle LOW/MEDIUM/HIGH.
Kolor, intensywność, wynik modelu ani HELD-OUT nie uczestniczą w tej definicji.

Dokładna liczebność zostanie wpisana przed uruchomieniem po audycie dostępnych jednostek; nie wolno dobierać liczby po wyniku.

### Korekta firewalla przed uruchomieniem — 2026-10-04

Pierwotny interfejs diagnostyczny `readiness.py --split` mógł zapisać wszystkie trzy listy, w tym HELD-OUT, jawnym tekstem. Został wyłączony przed powstaniem adnotacji, adjudykacji, seedu lub splitu. Nie zmienia to proporcji 60/20/20, jednostki grupowania, hipotezy, metryki ani planu mocy.

Produkcyjny split musi zostać utworzony w środowisku custodiana. Pełne przypisania, seed i mapowanie identyfikatorów muszą zostać zaszyfrowane dla custodiana. Geometry/Perspective otrzymują wyłącznie izolowany pakiet TRAIN/VALIDATION z nieodwracalnie zamaskowanymi identyfikatorami i bez repozytorium, atlasu, ścieżek źródłowych oraz listy pełnego uniwersum. Zamrożony model jest później uruchamiany przez custodiana na HELD-OUT; deweloper modelu nie otrzymuje jego rekordów ani etykiet.

Samo ukrycie listy HELD-OUT przy jednoczesnym ujawnieniu pełnego uniwersum oraz TRAIN/VALIDATION byłoby niewystarczające, ponieważ dopełnienie zdradzałoby przypisanie. Każdy pakiet deweloperski zawierający taki przeciek unieważnia eksperyment jako `INCONCLUSIVE`.

## Role i firewall

- Data custodian: przygotowuje split i przechowuje HELD-OUT.
- Geometry agent: widzi wyłącznie znormalizowaną geometrię TRAIN.
- Homology agent: korzysta tylko z zamrożonego katalogu transformacji.
- Perspective agent: buduje minimalną gramatykę na TRAIN i zamraża predykcje.
- Statistics agent: otrzymuje predykcje i etykiety po zamrożeniu; liczy baseline, uncertainty i permutacje.
- Red team: sprawdza leakage, selekcję, zależności wewnątrz foliów i alternatywne wyjaśnienia.
- Color agent nie uczestniczy w EXP-2026-001.

## Predykcje

Dla każdego obiektu HELD-OUT przed odsłonięciem etykiet model zapisuje:

- liczbę portów,
- położenie portów w zamrożonych sektorach,
- relacje przed–za / okluzję,
- orientację lokalną,
- pewność predykcji.

## Baseline i statystyka

- baseline większościowy,
- baseline warunkowy na sekcję i złożoność,
- prosty model bez homologii,
- permutacje etykiet w obrębie właściwych bloków folio/sekcja,
- bootstrap klastrowy po folio dla przedziałów ufności,
- jedna pierwotna miara: makro-F1 dla wspólnego wektora portów i relacji,
- miary wtórne raportowane opisowo z kontrolą FDR.

## Zamrożone kryteria decyzji

- PASS: przewaga nad najlepszym baseline ma dolną granicę 95% klastrowego CI > 0 oraz permutacyjne `p < 0.01`, a efekt utrzymuje się w każdej z co najmniej dwóch sekcji bez odwrócenia znaku.
- FAIL: wynik nie przewyższa najlepszego baseline albo wcześniej określona predykcja kierunkowa ma stabilnie przeciwny znak przy wystarczającej mocy.
- INCONCLUSIVE: niedostateczna moc, niezgodność annotatorów poniżej zamrożonego progu, naruszenie firewalla, brak artefaktów albo wynik zależny od jednej sekcji/specyfikacji.

Próg zgodności annotatorów i analiza mocy muszą zostać dodane przed odślepieniem; ich brak blokuje start.

## Zakazy

- Zakaz zmiany homologii i transformacji po obejrzeniu HELD-OUT.
- Zakaz doboru foliów lub regionów na podstawie tego, czy pasują wizualnie.
- Zakaz używania grayscale zachowującego informację o intensywności jako jedynego zabezpieczenia koloru.
- Zakaz interpretacji semantycznej wyniku jako odszyfrowania manuskryptu.
