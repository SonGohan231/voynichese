# Przebudowa geometrii z zachowaniem obrazu źródłowego

Aktualizacja 2026-09-28. Priorytet: barwy, ornamenty i obrysy rysunku.

## Rzeczywisty stan

To dwie partie po 10 **roboczych brył fragmentów**, nie 20 ukończonych roślin
ani pełna rekonstrukcja manuskryptu. Każdy plik GLB ma zamkniętą siatkę
z objętością. Kontury są ręcznie wskazanymi kandydatami; głębokość jest
interpretacją. Baseny są na tym etapie bryłami z zagłębieniem i obrazem postaci
na powierzchni. **Postacie nie mają jeszcze osobnych, pełnych brył ciał.**
Tuleje także wymagają dalszego modelowania wnętrza. To nie są zatwierdzone
modele naukowe 1:1. Nie włączono ich automatycznie do APK.

Wszystkie 254 wcześniejsze wpisy katalogu pozostają niezweryfikowane.
Ta liczba jest liczbą wpisów katalogu, nie pełnym spisem rysunków. Żadnej
strony nie oznaczono jako całkowicie odtworzonej na podstawie tych fragmentów.

## Co zmieniono

- Oba korzenie (f1v i f2r) mają osobne obrysy; nie korzystają ze wspólnego szablonu.
- Ozdobne struktury, siedem tulei, dwa baseny i wybrane przepływy pochodzą z f78r.
- Siatki są budowane w Blenderze 4.5.4 na podstawie współrzędnych skanu.
- Tekstury są oryginalnymi, sprawdzonymi SHA-256 plikami JPEG. Nie generuje
  się nowych kolorów, kropek, łusek ani pisma; nie wykonuje się ponownej kompresji JPEG.
- UV zachowuje położenie w oryginalnej stronie. Każdy obiekt zawiera numer
  strony, sumę źródła i status rekonstrukcji.
- Materiał źródłowy jest niezależny od świateł; GLB używa KHR_materials_unlit.
  Niewidoczny w źródle tył ma neutralny materiał i jawny status interpretacji.
- Plik Blender i rejestr postępu są zapisywane po każdym obiekcie.

## Kontrola

Kontrola obejmuje zamknięcie siatki, dodatnią objętość, oryginalne bajty
tekstury wewnątrz GLB, eksport materiału unlit i porównanie renderu z oryginałem.
Kamera kontrolna jest ortograficzna, patrzy w +Y; pion strony odpowiada +Z.
Widok jest renderowany w rozdzielczości wycinka źródłowego, z próbkowaniem
Closest, jednym samplem, Standard/sRGB, bez ditheringu i zmiany ekspozycji.
Porównanie pomija pas 7 pikseli przy ręcznie wyznaczonej krawędzi. Wynik 0
oznacza zgodność RGB w porównanych pikselach, **nie** potwierdzenie obrysu,
interpretacji przestrzennej ani obrazu widzianego w konkretnych goglach.

Odcień papieru, uszkodzenia i nierówności skanu pozostają w teksturze; nie są
automatycznie interpretowane jako cechy przedstawionego obiektu. Nie jest to
pomiar fizycznego pigmentu na oryginalnym pergaminie.

## Odtwarzanie

W Pythonie Blendera 4.5.4 zainstaluj `triangle`, `numpy`, `opencv-python-headless`,
`Pillow`. Rozpakuj oryginalne archiwa 7z i zachowaj oryginalne nazwy JPEG.

```bash
python build_source_volumes.py --sources SCANS --pages ../../quest-native/assets/pages.json --output PARTIA_01 --render
python build_source_volumes.py --sources SCANS --pages ../../quest-native/assets/pages.json --output PARTIA_02 --annotations annotations_02.json --batch 02 --render
```

## Kolejne konieczne prace

1. Korekta i niezależna kontrola każdego obrysu w nakładce ze skanem.
2. Osobne bryły postaci, wnętrza tulei, rozwarstwienie nakładających się części.
3. Brakujące połączenia f78r oraz całe pozostałe rośliny, korzenie, baseny,
   diagramy i inne rysunki: kontrolowany spis obiektów strona po stronie.
4. Dopiero po kontroli modelu: aktualizacja katalogu VR i próba w goglach.
