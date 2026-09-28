# f78r — poprawka materiałów siedmiu tulei

Pliki Blender i GLB zawierają istniejący zespół 38 oddzielnych siatek f78r, z poprawionym przypisaniem materiałów na siedmiu tulejach. Nie są to 38 nowych, ukończonych modeli.

Ściany tulei są triangulowane przed przypisaniem materiału źródłowego. Materiały zamkniętych brył mają wyłączone rysowanie odwrotnej strony ścian, aby neutralny materiał tyłu nie pojawiał się w widoku źródłowym na łączeniach.

W renderze ortograficznym w oryginalnej rozdzielczości porównano 1 474 160 pikseli wnętrza: różnica RGB = 0. Względem wcześniejszego renderu zmniejszyło się pokrycie o 1 piksel; nie ukrywamy tej rozbieżności. Test wyklucza obrys, nie poświadcza geometrii 1:1. Oryginalne bajty JPEG zachowano w GLB. Barwa fizycznego pigmentu ani ekranu Questa nie była kalibrowana.

To nadal robocza rekonstrukcja warstwowa. Głębokość, ukryte strony i anatomia pozostają interpretacją. Cały manuskrypt nie jest ukończony.

Ta późniejsza poprawka Blendera NIE jest zawarta w zapisanej APK 0.3.2. Następna aktualizacja APK powinna zastąpić siedem istniejących modeli, zachowując ich identyfikatory, i ponownie przejść testy importu, materiałów oraz chwytania.

Skrypt odtwarzający: check_tube_material_seams.py. Producent kolejnych tulei upgrade_tubes.py również otrzymał poprawkę. Nie licz tej zmiany jako nowej partii 20 modeli.
