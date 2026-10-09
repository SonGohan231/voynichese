# H-SPATIAL-PERSPECTIVE-LAYER-MODEL-01

## Cel

Zbudować testowalny model pozwalający rozpoznawać, czy ilustracje Manuskryptu Voynicha przedstawiają:

- różne widoki tego samego obiektu;
- różne poziomy lub warstwy jednej konstrukcji;
- przekroje, widoki z góry, z boku, od spodu lub ukośne;
- relacje przestrzenne zakodowane przez kolor, zasłanianie, topologię, kierunek linii i powtarzalne obrysy.

Model ma służyć nie do swobodnego interpretowania ilustracji, lecz do przewidywania brakujących lub niewykorzystanych cech na stronach held-out.

## Założenie główne

Ilustracje mogą być rozproszonym atlasem przestrzennym. Ten sam obiekt może pojawiać się na wielu foliach w różnych rzutach, przekrojach, wysokościach lub stanach działania.

Kolor nie jest traktowany jako samodzielny dowód perspektywy. Jest jedną z warstw sygnału, obok:

1. topologii połączeń;
2. relacji zasłaniania;
3. geometrii obrysu;
4. kierunku linii i kanałów;
5. pozycji tekstu;
6. skali i położenia postaci;
7. intensywności pigmentu;
8. ciągłości między stronami.

## Obserwacja pilotażowa: układ 12+1

W centralnym diagramie rozważany jest układ, w którym można dopasować około 12 łuków lub krzywych radialnych, lecz dwa sąsiednie wierzchołki po lewej stronie nie dają się jednocześnie połączyć w ten sam schemat. W konsekwencji pozostaje struktura typu:

- 12 pozycji cyklicznych;
- 1 dodatkowy lub wyróżniony wierzchołek;
- albo 13 wierzchołków, z których tylko 12 należy do jednej reguły połączeń.

Nie wolno od razu interpretować dodatkowego punktu jako „centrum”, „wejścia” lub „pozycji zerowej”. Najpierw należy sprawdzić, czy:

- jest rzeczywiście geometrycznie odmienny;
- nie wynika z błędu lokalizacji;
- nie należy do innej warstwy ilustracji;
- nie jest punktem zasłoniętym, uszkodzonym lub niedokończonym;
- podobny układ 12+1 powtarza się na innych diagramach.

## Model reprezentacji

Każda ilustracja ma zostać zapisana jako wielowarstwowy graf przestrzenny.

### 1. Warstwa obiektów

Każdy obiekt otrzymuje:

- `object_id`;
- `folio`;
- `region_id`;
- `object_class_neutral`;
- `geometry_type`: `BBOX`, `POLYGON` albo `MASK`;
- `polygon_or_mask_ref`;
- `centroid_x`, `centroid_y`;
- `orientation_deg`;
- `scale_px`;
- `parent_object_id`;
- `visibility_fraction`;
- `occlusion_status`;
- `uncertainty`.

Neutralne klasy opisowe powinny unikać przedwczesnych interpretacji, np.:

- `LOOPED_CONTOUR`;
- `TAPERED_CHANNEL`;
- `RIMMED_CONTAINER`;
- `RADIAL_LOBE`;
- `TUBE_END`;
- `SCALLOPED_EDGE`;
- `HUMAN_FIGURE`;
- `STAR_MARK`;
- `TEXT_BLOCK`.

### 2. Warstwa relacji

Każda para istotnych obiektów może mieć relację:

- `ABOVE`;
- `BELOW`;
- `IN_FRONT_OF`;
- `BEHIND`;
- `INSIDE`;
- `CONTAINS`;
- `TOUCHING`;
- `CONNECTED_BY_STROKE`;
- `CONNECTED_BY_CHANNEL`;
- `ALIGNED_WITH`;
- `RADIAL_TO`;
- `SAME_CONTOUR_FAMILY`;
- `POSSIBLE_SAME_OBJECT_DIFFERENT_VIEW`.

Dla relacji geometrycznych należy zapisywać tolerancję i źródło decyzji:

- `relation_tolerance_px`;
- `relation_method`;
- `relation_confidence`;
- `review_status`.

### 3. Warstwa koloru

Dla każdego obiektu i jego części zapisuje się:

- kolor w przestrzeni CIELAB;
- medianę i rozrzut koloru;
- intensywność pigmentu;
- odległość próbki od konturu obiektu;
- odległość od brzegu folio;
- lokalny poziom jasności pergaminu;
- obecność zabrudzenia, prześwitu, zagięcia lub uszkodzenia;
- czy próbka pochodzi z wnętrza, krawędzi czy obszaru zasłoniętego.

Kolor musi być normalizowany co najmniej na poziomie folio i lokalnego regionu. Bez tego ciemniejszy pigment może wynikać z:

- większej ilości farby;
- różnej konserwacji;
- zabrudzenia;
- nierównego oświetlenia skanu;
- prześwitu z drugiej strony;
- różnicy między partiami pigmentu;
- późniejszych poprawek.

### 4. Warstwa perspektywy

Dla każdej ilustracji model ma rozważać skończony zestaw hipotez:

- `TOP_VIEW`;
- `SIDE_VIEW`;
- `FRONT_VIEW`;
- `BOTTOM_VIEW`;
- `OBLIQUE_VIEW`;
- `VERTICAL_SECTION`;
- `HORIZONTAL_SECTION`;
- `MULTI_LEVEL_COMPOSITE`;
- `NON_SPATIAL_SYMBOLIC`.

Dla każdej hipotezy zapisuje się przewidywania dotyczące:

- zasłaniania;
- widoczności otworów i ujść;
- relacji skali;
- przebiegu kanałów;
- kierunku gradientu koloru;
- kolejności elementów na obrysie;
- pozycji tekstu;
- orientacji postaci.

## Test perspektywy oparty na kolorze

### Hipoteza

Jeżeli intensywność koloru koduje głębokość lub oddalenie od granicy widocznej powierzchni, to po normalizacji lokalnej ciemniejsze próbki powinny systematycznie występować dalej od odpowiedniego brzegu lub konturu.

### Minimalne wymagania

Nie wolno uznać PASS na podstawie samego kierunku gradientu w jednym obiekcie. Potrzebne są:

1. co najmniej trzy niezależne obiekty tego samego typu;
2. z góry ustalona definicja brzegu;
3. z góry ustalony kierunek przewidywanego gradientu;
4. normalizacja pergaminu i skanu;
5. kontrola grubości warstwy pigmentu;
6. porównanie z kontrolnymi obiektami, dla których model nie przewiduje perspektywy;
7. test held-out na innych foliach.

### Metryki

- korelacja Spearmana między intensywnością a odległością od brzegu;
- model mieszany z efektem losowym folio;
- różnica median między strefą brzegową i wewnętrzną;
- zgodność znaku efektu między obiektami;
- AUC klasyfikacji „bliżej/dalej” na podstawie koloru;
- stabilność efektu po wykluczeniu 10–20% najciemniejszych pikseli.

### Kryterium PASS

PASS tylko wtedy, gdy:

- kierunek efektu jest zgodny z prerejestracją;
- efekt utrzymuje się po normalizacji lokalnej;
- efekt powtarza się w większości niezależnych obiektów;
- wynik jest lepszy niż w kontrolach;
- model przewiduje kierunek gradientu na foliach held-out.

### Kryterium FAIL

FAIL, gdy:

- efekt zmienia znak między obiektami;
- zanika po normalizacji;
- równie dobrze występuje w kontrolach;
- zależy głównie od pojedynczych plam pigmentu;
- nie przewiduje wyniku na held-out.

## Model składania perspektyw

Każda kandydacka grupa ilustracji ma być testowana jako jeden ukryty obiekt 3D lub 2.5D.

### Dane wejściowe

Dla każdej strony:

- uporządkowany obrys;
- lista punktów charakterystycznych;
- liczba wejść i wyjść;
- graf połączeń;
- relacje zasłaniania;
- orientacja otworów;
- kierunki kanałów;
- względna wysokość postaci i murków;
- rozkład pigmentu;
- położenie lokalnych fragmentów tekstu.

### Dopasowanie między stronami

Dwie ilustracje mogą być uznane za widoki tego samego obiektu tylko wtedy, gdy zachowują zgodność wielu niezależnych cech naraz:

- topologia połączeń;
- kolejność punktów charakterystycznych na obrysie;
- liczba portów;
- relacja „wejście–wyjście”;
- sąsiedztwo nietypowych elementów;
- zgodność możliwego rzutu lub przekroju;
- brak sprzeczności w zasłanianiu.

Podobny kolor lub ogólne podobieństwo kształtu nie wystarczają.

### Funkcja kosztu

Proponowany wynik dopasowania:

`TOTAL_COST = w1*TOPOLOGY_ERROR + w2*LANDMARK_ORDER_ERROR + w3*PORT_MISMATCH + w4*OCCLUSION_CONFLICT + w5*COLOR_LAYER_ERROR + w6*TEXT_POSITION_ERROR + w7*FREE_PARAMETER_PENALTY`

Największą wagę powinny mieć:

1. topologia;
2. niezgodność portów;
3. sprzeczności zasłaniania;
4. kara za dowolne deformowanie modelu.

Kolor ma mniejszą wagę i nie może samodzielnie przesądzać wyniku.

## Budowanie warstw od dołu

Docelowa rekonstrukcja powinna powstawać od poziomu najbardziej podstawowego:

### Poziom 0 — źródło

- pełny skan;
- SHA źródła;
- rozdzielczość;
- rotacja;
- transformacja między oryginałem a cropem.

### Poziom 1 — piksele i pigment

- maska pergaminu;
- maski atramentu;
- maski pigmentów;
- atlas kolorów;
- mapa niepewności.

### Poziom 2 — kontury i punkty charakterystyczne

- obrysy;
- wypustki;
- zagłębienia;
- otwory;
- zakończenia linii;
- przecięcia i styki.

### Poziom 3 — obiekty lokalne

- neutralne klasy obiektów;
- hierarchia rodzic–dziecko;
- części powtarzalne;
- relacje przestrzenne.

### Poziom 4 — widok strony

- osie lokalne;
- kandydacka perspektywa;
- kolejność głębokości;
- warstwy zasłaniania;
- przepływy i kanały.

### Poziom 5 — połączenia między ilustracjami

- graf podobieństw;
- kandydackie odpowiedniki obiektów;
- możliwe rzuty tego samego modelu;
- zgodność topologii;
- konflikty.

### Poziom 6 — model wielostronicowy

- wspólny model 2.5D lub 3D;
- poziomy wysokości;
- wspólne kanały;
- punkty połączeń;
- warianty orientacji;
- przewidywania held-out.

## Wizualizacje

System powinien generować co najmniej pięć typów wizualizacji:

1. **Overlay strony** — identyfikatory obiektów, kontury, maski i relacje.
2. **Mapa głębokości** — uporządkowane warstwy od przodu do tyłu.
3. **Graf połączeń** — węzły jako obiekty lub ilustracje, krawędzie jako możliwe odpowiedniki i kanały.
4. **Plansza widoków** — zestawienie potencjalnych widoków tego samego obiektu: góra, bok, przekrój, spód.
5. **Rekonstrukcja warstwowa** — interaktywny lub statyczny model pokazujący, jak strony nakładają się od dołu ku górze.

Każda krawędź grafu musi mieć:

- typ relacji;
- wynik dopasowania;
- źródło danych;
- poziom pewności;
- listę cech za;
- listę cech przeciw;
- status `CANDIDATE`, `SUPPORTED`, `REJECTED` albo `INCONCLUSIVE`.

## Eksperyment pierwszy

### Nazwa

`SPATIAL-PERSPECTIVE-PILOT-01`

### Cel

Sprawdzić, czy jedna wybrana ilustracja ma mierzalną, przewidywalną strukturę głębokości, a nie tylko dekoracyjny rozkład koloru.

### Procedura

1. Wybrać jedną ilustrację z wyraźnym obrysem, pigmentem i elementami zasłaniającymi.
2. Zamrozić źródło, crop, rotację i maski.
3. Zdefiniować co najmniej dwie konkurencyjne osie perspektywy.
4. Przed pomiarem zapisać, gdzie model przewiduje obszar bliższy i dalszy.
5. Pobrać próbki pigmentu w regularnej siatce, bez ręcznego wybierania wyłącznie korzystnych punktów.
6. Przetestować gradient intensywności.
7. Sprawdzić zgodność z zasłanianiem i orientacją konturów.
8. Powtórzyć procedurę na kontrolnym obiekcie.
9. Zamrozić wynik.
10. Sprawdzić tę samą regułę na drugim folio held-out.

### Wynik

- `PASS`: kolor, zasłanianie i topologia niezależnie wskazują tę samą oś głębokości, a kierunek przewiduje wynik na held-out;
- `FAIL`: sygnały są sprzeczne albo efekt nie przechodzi kontroli;
- `INCONCLUSIVE`: dane są zbyt słabe lub pigment zbyt nieregularny.

## Eksperyment 12+1

### Nazwa

`RADIAL-12-PLUS-1-TOPOLOGY-01`

### Cel

Sprawdzić, czy trzynasty wierzchołek jest rzeczywiście elementem innej klasy lub warstwy.

### Procedura

1. Zamrozić wszystkie kandydackie wierzchołki bez dopasowywania krzywych.
2. Oszacować centroid i osie radialne.
3. Dopasować modele z 12 i 13 pozycjami.
4. Porównać:
   - regularność kątową;
   - długości łuków;
   - krzywiznę;
   - zgodność topologii;
   - relacje do otaczających obiektów.
5. Sprawdzić, czy wyróżniony punkt zachowuje się odmiennie także pod względem:
   - koloru;
   - sąsiedztwa;
   - tekstu;
   - zasłaniania;
   - połączenia z inną warstwą.
6. Poszukać analogicznego układu na innych diagramach.

### Kryterium PASS

PASS dla modelu 12+1 tylko wtedy, gdy model 12 pozycji ma wyraźnie lepszą regularność niż model 13, a dodatkowy punkt posiada co najmniej jedną niezależną cechę funkcjonalną odróżniającą go od pozostałych.

## Kolejność wdrożenia

1. Zamrożenie schematu danych.
2. Atlas pigmentów i lokalna normalizacja.
3. Segmentacja konturów i obiektów.
4. Relacje zasłaniania i połączeń.
5. Pilotaż perspektywy na jednej ilustracji.
6. Test 12+1.
7. Grupowanie podobnych ilustracji.
8. Budowa grafu między stronami.
9. Rekonstrukcja 2.5D.
10. Predykcja held-out.

## Zasada rozstrzygająca

Model jest wartościowy tylko wtedy, gdy przewiduje cechy niewykorzystane podczas budowy. Najmocniejszym dowodem będzie poprawne przewidzenie na nowej stronie:

- położenia brakującego portu;
- kierunku kanału;
- kolejności punktów obrysu;
- warstwy zasłaniania;
- gradientu koloru;
- odpowiadającego fragmentu tekstu.

Bez takiej predykcji model pozostaje interpretacją opisową.
