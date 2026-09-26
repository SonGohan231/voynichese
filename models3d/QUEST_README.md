# Pracownia Manuskryptu — Meta Quest WebXR

Wejście: `quest.html` na opublikowanej stronie HTTPS, otwarte bezpośrednio w Meta Quest Browser. Gogle muszą zezwolić na sesję XR. Przycisk VR lub MR pojawia się jako aktywny dopiero po `navigator.xr.isSessionSupported`. MR używa `immersive-ar` z przezroczystym tłem; VR używa `immersive-vr` z wirtualną pracownią. To aplikacja WebXR uruchamiana z adresu strony.

## Zawartość

W aplikacji jest206 skanów,2619 oddzielnych fragmentów i model zbiorczy korpusu. Fragmenty są teksturowanymi reliefami2.5D. Głębokość i powierzchnie niewidoczne na rysunku są umowne. Automatyczna segmentacja jest CANDIDATE, wymaga ręcznego przeglądu i nie jest pełną klasyfikacją każdego rysunku. Pełne skany zachowują całą treść.

## Kontrolery

- Spust: celowanie laserem i chwyt pojedynczego fragmentu. Ruch/obrót kontrolera daje sześć stopni swobody.
- Grip/przycisk boczny: chwyt całego zestawu.
- Drążek podczas chwytu: przysuwanie i odsuwanie obiektu wzdłuż promienia kontrolera.
- Dwa kontrolery mogą trzymać różne zestawy. Jednego zestawu nie można równocześnie chwycić dwoma kontrolerami.
- Menu w goglach: wybór wszystkich kart, typ modelu, dodawanie, rozsuwanie, składanie, proporcjonalna skala, wzorzec skanu, przyciąganie, cofanie, zapis i wyjście.
- Przyciąganie działa dla przesunięcia mniejszego niż3.5cm w przestrzeni aplikacji, kąta mniejszego niż14° i zgodnej skali. „Złóż” przywraca dokładne macierze źródłowe.

## Perspektywa

Macierze widoku i projekcji każdego oka dostarcza WebXR. Aplikacja nie narzuca FOV, IPD ani płaskiego widoku w goglach. OrbitControls działają wyłącznie poza sesjąXR. Jednostki przestrzeniXR są metrami, natomiast wysokość skanu źródłowego to1 jednostka umowna. Nie oznacza to znajomości fizycznych wymiarów oryginału.

Zestawy są skalowane równomiernie wXYZ. Wspólny układ współrzędnych i proporcje skanów są zachowane. Reparentowanie podczas chwytu zachowuje macierz światową. Przesunięcie obiektu ręką daje naturalną paralaksę; nie jest to rekonstrukcja rzeczywistej głębi rysunku.

MR pokazuje otoczenie udostępnione przez urządzenie, bez pobierania pikseli kamer. Nie ma mapowania ścian ani okluzji przez prawdziwe meble. Pozycje zapisane w projekcie nie są trwałymi kotwicami fizycznego pomieszczenia; przycisk „Przed sobą” pozwala ustawić zestaw wygodnie po ponownym wejściu.

## Zapis

Automatyczny zapisJSON następuje w pamięci lokalnej tej przeglądarki po zakończeniu manipulacji. Przycisk zapisu potwierdza zapis ręczny. ZapiszJSON/WczytajJSON na stronie przenosi projekty między urządzeniami. EksportGLB zapisuje widoczną scenę. Zestawy zachowują identyfikatory źródła; pełnej jakości pliki są w pakiecie395853886 bajtów (SHA256:1b5673fe4949372968601b8e9016bff4816f09cfed93404293d54b0f18accdbd).

## Walidacja i ograniczenia

Testy`node scripts/test_xr.mjs` sprawdzają zachowanie pozycji przy chwycie, serializację trzymanych obiektów bez puszczania drugiej ręki, przeliczenia układów współrzędnych, warunki przyciągania i jednolitą skalę. Sprawdzono składnięJS, kompletność zasobów i zakresy buforówglTF.

Nie przeprowadzono testu na fizycznych goglachQuest. Wydajność, komfort, passthrough i obsługa kontrolerów wymagają odbioru na urządzeniu. Nie twierdzimy, że taka próba została wykonana. Cały atlas ma206 obiektów, więc na słabszych urządzeniach wygodniejsza może być praca z pojedynczymi kartami.

ŹródłaAPI: https://developers.meta.com/horizon/documentation/web/webxr-mixed-reality/ oraz https://threejs.org/docs/pages/WebXRManager.html
