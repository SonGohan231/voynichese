# Manuskrypt Quest 0.3.2 — pierwsza przebudowana partia 20 fragmentów

Pakiet `pl.manuskrypt.quest`, versionCode 5. Aktualizacja nad zweryfikowaną
0.3.1 z tym samym certyfikatem podpisu. Nie trzeba odinstalowywać wcześniejszej wersji.

## Zmiany

- Katalog zawiera 274 wpisy: 254 wcześniejsze i 20 fragmentów partii F01.
- W VR: **Katalog → Przebudowane 20 → Model ▶ → Dodaj model**.
  Przycisk otwiera tryb hipotez, w którym bryły są widoczne; źródłowy skan pozostaje obok.
- Dwa osobno odrysowane korzenie f1v/f2r, dwie struktury wachlarzowe, siedem tulei,
  dwa baseny oraz siedem odcinków przepływów z f78r.
- Siedem tulei ma modelowaną ściankę, obrzeże, jamę wewnętrzną i dno.
  Okrągły przekrój, grubość ściany i zamknięte dno są jawnymi założeniami
  rekonstrukcji, których rysunek nie potwierdza jednoznacznie.
- Tekstury VR to bezstratne wycinki skanów w oryginalnej rozdzielczości.
  Materiały unlit zachowują barwy niezależnie od światła pomieszczenia.
- Modele używają istniejących mechanizmów podnoszenia, obracania, łączenia,
  rozdzielania oraz zapisywania układu. Numer strony jest w danych obiektu.

## Sprawdzenie

150 kontroli w Godot 4.6 przeszło: katalog, wszystkie 20 zasobów, materiały,
dokładna zgodność pikseli wszystkich 20 tekstur po imporcie, skróty katalogu,
podgląd, chwytanie, obrót 360°, zapis i odzyskanie właściwego fragmentu oraz pozycji.
To test silnika na komputerze, nie test na fizycznym Quest.

Składanie APK zachowuje wcześniejsze skrypty czytnika, 206 skanów, biblioteki
natywne, klasy Android i uprawnienia. Nowe są skrypt katalogu, jego dane i
skompilowane zasoby 20 fragmentów. APK wymaga prawidłowego podpisu i wyrównania
16 KiB po użyciu `tests/repack_batch.py`.

## Stan nieukończony

**Pełny manuskrypt nie jest jeszcze przebudowany. Żaden model nie uzyskał
potwierdzenia pełnej geometrii 1:1.**

Baseny nadal mają postacie przedstawione na powierzchni; osobne przestrzenne
ciała pozostają do wykonania. Obrysy wszystkich fragmentów wymagają niezależnej
kontroli. Brakuje części połączeń f78r i rekonstrukcji pozostałych ilustracji.
254 wcześniejsze wpisy katalogu nie są pełnym spisem wszystkich rysunków.
Whisper.cpp i MCP pozostają poza tą aktualizacją — priorytetem są modele.

## Wznowienie

1. Zachować 20 identyfikatorów `rebuilt_*` i `rebuild_batch: F01` — nie dodawać ich drugi raz.
2. Dla następnych 20 użyć kolejnej partii F02 i zachować pochodzenie każdego fragmentu.
3. Ukończyć postacie, wnętrza i brakujące połączenia; nie zgłaszać płaskich
   tekstur jako pełnych modeli tych obiektów.
4. Po każdej partii: sprawdzić geometrię i obrazy, zaktualizować katalog,
   zbudować APK, podpisać tym samym prywatnym kluczem i zapisać efekt.
5. Użytkownik 2026-09-28 jawnie zezwolił na udostępnianie kolejnych APK i
   kopii projektu w GoFile. Klucze podpisujące, tokeny i PIN nie trafiają do paczek.

Edytowalne mastery i GLB są osobnymi artefaktami. Skrypty Blendera i dokładne
adnotacje znajdują się w `blender-progress/source-volumes-2026-09-28`.
