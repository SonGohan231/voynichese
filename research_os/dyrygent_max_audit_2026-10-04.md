Failed to connect to bus: Operation not permitted
# Dyrygent MAX — niezależny audyt metodologiczny

Data: 2026-10-04  
Preset: `Research`  
Tryb: `MAX` (jednorazowo zatwierdzony przez użytkownika)  
Status: **PARTIAL / INCONCLUSIVE**

## Dowód wykonania

- Interfejs: Dyrygent v3.7 na Google Cloud Run.
- Wywołania modeli: 1.
- Model: `gpt-6-astra`.
- Zużycie: 2202 tokeny.
- Review: `CORRECTED`.
- Ścieżka: `astra-direct-fallback`.
- Błąd: planner zwrócił niepoprawny JSON; interfejs użył jego tekstu bez dodatkowych wywołań.
- Zwrócony JSON oraz końcowa prerejestracja zostały ucięte w trakcie zdania. Raport nie spełnił kompletnego kontraktu zadania.
- Interfejs zwrócił także niepowiązaną akcję hosta `unity_executor tests` dla `SonGohan231/FantasyTD`; została zignorowana jako błąd routingu i nie została wykonana.

## Użyteczne ustalenia Astra

### Status źródeł

Liczby 285/126/236/46/724, `readyForLiteralization=0`, blokada visual crop gate, HTTP 404, atlas 206 rekordów i wskazana gałąź są deklaracjami bootstrapu, a nie niezależnie ustalonymi faktami. Status `confirmed` nie przechodzi automatycznie do nowego audytu. Brak artefaktu daje `INCONCLUSIVE`, nie `FAIL`. Liczba kontrtestów bez deduplikacji i mapy pochodzenia nie dowodzi siły dowodowej.

### H1, H2a i H2b

- H1 musi być oceniana oddzielnie. Jej sukces oznaczałby generalizację zamrożonego modelu wizualnego, nie dowód rzeczywistej przestrzenności, języka ani znaczenia.
- H2a wymaga wykazania przyrostu predykcji ponad zamrożoną geometrię, sekcję i folio.
- H2b ma najcięższy problem identyfikowalności. Jasność skanu miesza pigment, grubość i stan farby, podłoże, oświetlenie i przetwarzanie obrazu. Podobny RGB nie dowodzi tego samego pigmentu. Bez niezależnego od koloru kryterium głębokości test jest kołowy.

### Firewall

Osoby lub agenci badający historię projektu nie mogą później pełnić funkcji ślepych annotatorów. Pakiet ślepej oceny ma zawierać neutralne instrukcje, losowe identyfikatory i tylko potrzebne obrazy; bez pilota, oczekiwanego kierunku, sugestywnych nazw plików i historycznych etykiet. Folia użyte do projektowania katalogu nie są uczciwym HELD-OUT.

### Największe ryzyka

- pseudoreplikacja wielu cropów z jednego folio lub rysunku,
- podobne motywy i strony tej samej składki w różnych splitach,
- dobór najlepszych przykładów,
- zmiany katalogu po zobaczeniu wyniku,
- definicje portów zależne od hipotezy,
- przeciek przez nazwy plików i instrukcje,
- selektywne raportowanie,
- wiele wariantów analizy i skorelowane kontrtesty.

Nowa prerejestracja nie naprawia retrospektywnie wcześniejszej historii poszukiwań.

## Początek zwróconej prerejestracji

Celem ma być falsyfikacja tezy, że mały zamrożony katalog 2.5D przewiduje widoczne porty, okluzje i orientację na nowych foliach lepiej od modeli 2D. Przed otwarciem HELD-OUT należy zamrozić manifest wejść i wykluczeń, katalog z jawnymi parametrami i limitem złożoności, generator kandydatów, kod, seedy i scoring; każda wersja otrzymuje hash.

Odpowiedź urwała się przy definicji jednostki podziału. Nie wolno rekonstruować brakującej części jako wyniku Dyrygenta.

## Decyzja

Wynik wzmacnia istniejące zabezpieczenia metodologiczne, ale nie zastępuje pełnego audytu. EXP-2026-001 pozostaje `DRAFT_NOT_RUN`. Wszystkie przyszłe zadania Dyrygenta mają domyślnie używać trybu `BALANCED`.
