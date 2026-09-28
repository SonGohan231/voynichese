# 0.3.1 — czytnik i wiarygodność źródeł

Zgłoszenie: księga nie przewija stron, dolna część skanu glitchuje, baseny,
struktury, kolory i korzenie modeli odbiegają od ilustracji.

## Co poprawiono

- Księga na stole była statycznym GLB z dwoma skanami. Teraz ma dynamiczne
  powierzchnie i własne przyciski: poprzednia/następna strona, wyjęcie skanu,
  lupa/RGB. Wybór w galerii, panel i księga używają jednego kursora.
- Wszystkie 206 skanów jest dostępne kolejno; na końcach nie ma skoku do początku.
  Zapis układu obejmuje wybrany skan. Rozłożona księga pokazuje sąsiednie skany;
  nie jest potwierdzoną rekonstrukcją historycznych składek ani oprawy.
- Czytnik wczytuje oryginalne JPEG po sprawdzeniu SHA-256 i wymiarów. Omija
  stratne tekstury importowane. Podgląd ma limit 2048 px i mipmapy, zachowuje
  proporcje i używa materiału bez oświetlenia. Nie jest to podgląd 1:1 każdego
  piksela; lupa/próbnik pracuje na pełnym dekodowanym źródle.
- Odstęp powierzchni skanu wyjętej karty od podkładu zwiększono z 0,2 do 6 mm.
  Usuwa to konkretną sytuację sprzyjającą z-fighting, ale dokładna przyczyna
  zgłoszonego błędu od 1/3 strony nie została odtworzona na goglach.
- Domyślny tryb Źródła ukrywa niezweryfikowane podglądy brył i dodaje skany do
  wystaw. Przełącznik Badania → Źródła / hipotezy przywraca bryły do eksploracji.
  Nie kasuje modeli ani swobodnych układów użytkownika. Istniejące obiekty robocze
  pozostają na miejscu. Etykiety wskazują brak weryfikacji geometrii.
- Tryb Źródła wyłącza dynamiczną foweację na obsługujących ją goglach; to zmiana
  jakości czytania, a nie potwierdzona diagnoza glitcha.

## Wierność modeli — nieukończona

Żaden z 254 dotychczasowych zestawów nie otrzymuje statusu naukowo zweryfikowanej
rekonstrukcji. Obecne baseny, struktury i korzenie wymagają przebudowy i kontroli
przy konkretnym skanie. Nie zastąpiono ich kolejną serią podobnych brył.

Plik Blendera `Wzorce_10_fragmentow.blend` zawiera 10 osobno wybieralnych wzorców
źródłowych z f1v, f2r, f75r i f78r. Oryginalne pliki są spakowane w `.blend`,
zweryfikowane SHA-256, z UV opartymi na współrzędnych natywnych. To powierzchnie
odniesienia do poprawiania geometrii, **nie 10 ukończonych rekonstrukcji 3D**.

Przed uznaniem modelu za zgodny należy dla każdego obiektu zapisać: źródło i
współrzędne, kontur i otwory, liczbę i połączenia części, pozycje ozdobników i
tekstu, porównanie projekcji z obrazem oraz maskę różnic. Głębia i niewidoczne
powierzchnie muszą być osobną, wyłączalną hipotezą. Kolor porównuje się ze skanem
w widoku bez oświetlenia; nie jest to pomiar pigmentu ani kalibracja ekranu Quest.

## Sprawdzenie

- 228 asercji czytnika: pełna kolejność skanów, galeria → dalej, granice,
  asynchroniczne przełączanie, rozkładówka, wspólna tekstura księgi i panelu,
  próbki tekstury, odrzucenie złego SHA, cache i zapis/odtworzenie.
- Regresja chwytania, obrotu, oddzielania, łączenia i zapisu układów przeszła.
- Dotychczasowe 34 pary testowe ΔE00 przeszły.
- Wyrenderowano księgę, baseny, rozkładówkę i osobną kartę przez Godot 4.6 /
  OpenGL Compatibility na desktopie. Nie zaobserwowano ucięcia dolnej części.
- Nie wykonano testu na fizycznym Meta Quest. Logi desktopu zawierają oczekiwany
  brak natywnej biblioteki Android OpenXR Vendors dla Linuksa.

APK jest poprawką zasobów nad dokładnie zweryfikowanym APK 0.3.0; nie zmienia
natywnych bibliotek, klas Android ani uprawnień. Nowe skrypty odpowiadają testom.
Pakiet `pl.manuskrypt.quest`, versionCode 4 / 0.3.1, ten sam certyfikat podpisu,
wyrównanie bibliotek 16 KiB. Nie odinstalowywać poprzedniej wersji: instalacja
jako aktualizacja zachowuje dane aplikacji.

Whisper.cpp i MCP nie zostały dodane w tej poprawce — priorytetem było zgłoszenie
czytnika oraz niedopuszczenie do mylenia hipotetycznej geometrii ze źródłem.
