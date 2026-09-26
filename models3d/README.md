# Manuskrypt — Atlas przestrzenny, v2

206 skanów z dziesięciu archiwów użytkownika. Kolekcja zawiera okładki, składki, skany częściowe, ilustracje, tekst i drobne znaki. Liczba skanów nie jest liczbą fizycznych kart.

## Modele

- `dist/assets/pages/`: osobny teksturowany model każdego pełnego skanu.
- `dist/assets/art/`: zespoły automatycznie wydzielonych konturów w układzie źródła.
- `dist/assets/parts/`: kontury i wybrane wycinki jako osobne GLB.
- `dist/assets/manuscript_all.glb`: cały korpus jako osobne obiekty w jednym pliku, w układzie atlasu.
- `dist/assets/atlas.json`: identyfikatory, SHA-256 źródeł/modeli, współrzędne fragmentów.
- `dist/assets/validation.json`: walidacja strukturalna wszystkich modeli i sumy kontrolne.

To **reliefy 2.5D z geometrią, grubością, ścianami i teksturą**, nie odtworzenie potwierdzonej anatomii ani fizycznej oprawy kodeksu. Głębokość jest umowna. Status modeli i segmentacji: **CANDIDATE**. Automatyczne kontury nie są pełnym, ręcznie zweryfikowanym katalogiem semantycznych rysunków. Mogą zawierać przebicia, elementy tekstu, tła oraz pomijać blade linie. Pełne skany zachowują całą treść obrazową. Nie przypisano gatunków ani znaczeń.

## Praca

Wybierz skan, rysunek lub fragment i dodaj go do wspólnej sceny. Każdy dodany obiekt można przesuwać, obracać, skalować, ukrywać i usuwać. „Układ źródłowy” ustawia transformację na zero; fragmenty tego samego skanu składają się bez wyrównywania. Skan ma wysokość jednej jednostki; skala fizyczna nie jest znana.

„Wytnij fragment” umożliwia zaznaczenie prostokąta na skanie i dodanie go jako osobnego modelu z umowną grubością. Eksport GLB zapisuje widoczne obiekty sceny. Zapis projektu JSON zachowuje wszystkie obiekty, transformacje i własne wycinki; wczytanie projektu zastępuje bieżącą scenę. Nie ma automatycznego zapisu.

`manuscript_all.glb` jest lekką reprezentacją zbiorczą (tekstury do370px). Modele pojedynczych skanów mają tekstury do1200px. Podgląd źródła ma do1550px. Oryginalne rozdzielczości podaje manifest. GLB otwiera się np. w Blenderze; `scripts/import_blender.py` importuje wybrany zestaw do kolekcji.

## Pochodzenie i sprawdzenie

Każdy z206 identyfikatorów występuje raz. Powtórzony00023_11r został rozpoznany jako identyczny plik. Dziewięć niekompletnych JPEG-ów z archiwów zastąpiono pełnymi wersjami z repozytorium użytkownika `SonGohan231/voynichese`, zachowując obie sumy kontrolne i pochodzenie. To odzyskane wersje tego samego obrazu, nie identyczne bajtowo kopie niepełnych plików.

Walidacja sprawdza format GLB, zakres indeksów, skończoność współrzędnych i kompletność206 identyfikatorów. Pierwsze trzy rośliny (skany4–6, f1v/f2r/f2v) sprawdzono wizualnie na poziomie masek. Nie wykonano pełnego ręcznego audytu wszystkich konturów ani testu interakcji w przeglądarce.

## Odtwarzanie

Python3 + numpy scipy Pillow opencv-python-headless. `scripts/build_atlas.py` czyta manifest w `../work/source_manifest.json` i względne ścieżki z jego `source_path`. W repozytorium użytkownika skany istnieją w `data/yale_hq_scans/`. Przed ponownym uruchomieniem należy przygotować manifest i ścieżki wejściowe zgodnie z `source_manifest.json`. Następnie: `python scripts/build_atlas.py` i `python scripts/optimize_validate.py`. Podgląd jest statyczny, używa lokalnej kopii Three.js0.180.0. Stronę należy serwować przezHTTP(S); samo otwarcie HTML przezfile:// nie ładuje modeli.
