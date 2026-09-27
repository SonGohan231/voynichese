# Manuskrypt VR · natywna pracownia Quest 0.3.0

Wersja testowa APK dla Meta Quest 2, 3/3S i Pro (ARM64, Horizon OS 69 lub nowszy). Godot 4.6 stable, OpenXR,
oficjalny Godot OpenXR Vendors 5.1.0. Nie jest opakowaniem strony w Android WebView.

## Zawartość i sterowanie

- Katalog 254 roboczych zestawów przestrzennych; 206 dostarczonych skanów dostępnych offline.
- Pierwsze 10 roślin rozdzielono w Blenderze na 1002 części bez zmiany trójkątów źródłowych.
- Podgląd wybranego modelu, źródłowego skanu oraz kategorii. Podgląd zmienia się przyciskami Model i Kategoria.
- `Dodaj model` wstawia osobny eksponat do Twojego układu. Maksymalnie 12 zestawów/oddzielonych fragmentów naraz.
- Spust wybiera, boczny chwyt podnosi bez przeskoku położenia. Obrót dłonią jest swobodny w 360°.
- A/X obraca wybrany element o 180°. Panel Obiekt: obroty X/Y/Z o 15° i zmiana skali.
- `Części` pozwala chwytać siatki osobno; `Oddziel część` tworzy niezależny fragment.
- `Przypnij bazę`, wybór innego obiektu, `Połącz z bazą`: połączenie w dowolnym układzie z zachowaniem pozycji.
- B/Y pokazuje/chowa panel; lewy drążek przemieszcza, prawy obraca punkt widzenia skokowo o 30°.
- `Wyjmij stronę` dodaje wybrany skan jako grubą kartę. `Cały kodeks` dodaje obiekt Blendera z 206 oddzielnymi kartami.
- `Zapisz układ` oraz automatyczny zapis co 20 sekund. Zapis używa pliku tymczasowego i kopii `.bak`.
- `Cofnij` odwraca do 12 zmian w bieżącej sesji. Wzajemne pozycje elementów odtwarzają się przy ponownym uruchomieniu.
- `VR / otoczenie` korzysta z passthrough OpenXR, jeżeli udostępnia je runtime gogli.
- `Zdjęcie + głos` zapisuje kadr sceny wirtualnej, WAV i JSON kontekstu. Mikrofon jest uruchamiany świadomie, po zgodzie systemowej, maksymalnie na 2 minuty. Ten sam przycisk kończy nagranie.
- `Pióro` rysuje prawym spustem. Wybierz wcześniej model, żeby szkic był do niego przypięty.
- `Otwórz atlas` uruchamia systemową przeglądarkę z istniejącą stroną projektu; może wyjść z aplikacji.

## Nowości 0.3.0

- Jeden budynek: pracownia, naczynia, hydraulika, diagramy, obserwatorium, wspólny korytarz i ogród. Drzwi mają rzeczywiste otwory w siatkach Blendera. Pokoje w menu są skrótami przenoszenia w tym samym świecie.
- W sali diagramów stoją obok siebie dwa modele rozkładówki f85v–86r, każdy szeroki na 8,7 m: 2.5D na podłodze i osobne przestrzenne rozwinięcie dziewięciu rozet. Rysunek ma zachowane proporcje skanu.
- 71 nowych modeli w partiach 21–28: 10 diagramów, 20 reliefów scen/przepływów, 31 reliefów stron z drobnymi znakami, 10 dodatkowych przybliżonych brył detali. Partie mają po 10 modeli; partia 27 zawiera pozostałą jedną stronę.
- Wszystkie 204 skany poza okładkami mają co najmniej jednego kandydata modelu. **To nie oznacza, że każdy pojedynczy rysunek jest już rozdzielony i wiernie wymodelowany.** Pełny spis ilustracji i ich objętości nadal wymagają kontroli.
- Kategorie wystaw ładowane są po 6 eksponatów. `Pokoje → ◀ Wystawa / Wystawa ▶` przegląda kolejne. 183 starsze zestawy mają osobne siatki ekspozycyjne z połączonymi materiałami, przygotowane w Blenderze; kopia robocza zachowuje oryginalne części.
- Chwyt wzorca daje kopię przy kontrolerze. Swobodny obrót, skala, oddzielanie i własne połączenia działają także na nowych modelach.
- `Kolory → Pokaż / schowaj`: próbnik pełnych źródeł. Wskaż obraz i naciśnij spust, aby pobrać A lub B. Wybierz próbkę przyciskiem `Próbka A / B`. Powiększenie skupia się wokół ostatnio wskazanego piksela.
- Próbnik: oryginalny JPEG sprawdzany SHA-256, 1×1 / średnia 3×3 / średnia 11×11 pikseli, zoom do 64×, RGB/HEX, współrzędne i ΔE00, zapis porównania do `color_samples.json`. Wszystkie 206 plików ma osadzony profil sRGB. Piksele są odczytywane na CPU, niezależnie od oświetlenia i kompresji tekstur wystawy.
- Wartości skanów nie są skalibrowanym pomiarem pigmentów. Różne dekodery JPEG mogą dać drobne różnice. Głębia i tyły brył są interpretacjami, a geometryczne podobieństwo nie jest odczytaniem tekstu.
- Przy przenoszeniu między salami używany jest oryginalny moduł Fade z Godot XR Tools 4.5.1. CIEDE2000 jest portem implementacji gfiumara; licencje są dołączone.
- Nadal brak testu w fizycznych goglach. Automatyczna transkrypcja i połączenie notatek z ChatGPT/MCP nie są jeszcze podłączone; gotowe biblioteki opisano w recommendations.md.

## Nowości 0.2.0: sala naczyń i tarot

- **Pokoje → Naczynia** przenosi do osobnej sali. W wersji 0.3 można również przejść przez wspólny korytarz.
- 10 naczyń / „wieżyczek” z f88r (3), f89v – część (3), f99r (4). Profile przednie są wyprowadzone z rysunków, ornamenty i znaki mają tekstury oryginalnych skanów. Pierścienie ozdobne są osobnymi bryłami.
- Głębokość obrotowa i tyły naczyń są hipotezą modelarską. Sąsiednie korzenie i liście są roboczymi bryłami do porównywania. Dokładne rysunki i wszystkie napisy pokazują trzy pełne skany na ścianie. Znaki nie zostały przetłumaczone.
- Skieruj promień na eksponat: pokazuje folio. **Chwyt tworzy kopię do pracy**; wzorzec pozostaje na wystawie. Kopie obsługują wcześniejsze obroty, rozdzielanie i łączenie.
- Obok otwartego manuskryptu stoi osobny stół tarota. **Tarot → Podejdź do tarota** ustawia widok przy stole.
- Pełna talia **78 kart** z oryginalnymi ilustracjami RWS 1909; karty są modelami Blendera z awersem, rewersem i grubością.
- `Losuj kartę` dobiera z przetasowanej pozostałej talii. `◀ Karta / Karta ▶`, `Kolor / Arkana`, `Dodaj wybraną` pozwalają wybrać kartę świadomie.
- `Pola: 3 / 5` zmienia rozkład. Pola odczytu mają numery od lewej do prawej. Możesz chwytać karty, dowolnie je przemieszczać i układać także poza polami. Po puszczeniu blisko pola karta się dopasowuje; poprzednia karta trafia obok.
- **A/X lub Odwróć 180°** odwraca wybraną kartę w płaszczyźnie stołu. Odwrócenie podczas odkładania także jest rozpoznawane.
- Po zapełnieniu pól pojawia się **interpretacja symboliczna**. `Tekst ▶` pokazuje kolejne pozycje i podsumowanie kolejności. `Interpretuj układ` odświeża odczyt. Teksty są po polsku i działają offline.
- Układ, obroty, pozostała talia i strona interpretacji zapisują się wraz z pracownią. Limit: 12 kart na stole, niezależnie od 12 modeli roboczych. `Zbierz karty` rozpoczyna nowy układ.
- Tarot służy refleksji; odczyt nie jest prognozą zdarzeń ani dowodem rozwiązania Manuskryptu. Jest lokalnym zestawem reguł i tekstów, bez wywołania AI.

## Instalacja

Włącz tryb deweloperski Questa i zaakceptuj debugowanie USB. Z komputera z Android Platform Tools:

```sh
adb devices
adb install -r Manuskrypt_Quest_0.3.0.apk
```

Uruchom **Manuskrypt VR · Pracownia** z aplikacji z nieznanych źródeł. Jest to podpisany
build debug do własnych testów, nie wydanie w sklepie Meta. Nie odinstalowuj aplikacji
przed wykonaniem kopii własnych notatek i układu.

## Kopia danych i praca bez sieci

Modele i skany są w APK. Notatki ani mikrofon nie są wysyłane automatycznie do sieci.
Godot `user://` na Androidzie wskazuje prywatne dane aplikacji. Kopia przez ADB dla tego buildu debug:

```sh
adb exec-out run-as pl.manuskrypt.quest tar -cf - files > manuskrypt-dane.tar
```

W `files/` znajdują się `workspace.json`, kopia `.bak` oraz `notes/<czas>/note.json`,
`view.png`, ewentualnie `voice.wav`. Notatki nie są jeszcze połączone z usługą AI.

## Stan i ograniczenia

To trzecia natywna wersja testowa. Cały projekt VR pozostaje w rozwoju.

- Nie przetestowano fizycznego Questa, stabilności liczby klatek, mikrofonu gogli ani passthrough na urządzeniu.
- Próbnik zawiera wszystkie 206 oryginalnych JPEG-ów sprawdzonych SHA-256. Wystawy używają lżejszych tekstur podglądowych; pomiar kolorów korzysta z oryginałów.
- 254 zestawy obejmują starsze bryły, reliefy całych stron i nowe detale. Wszystkie 204 skany poza okładkami mają model kandydujący; nie ustalono jeszcze pełnego mianownika pojedynczych ilustracji. Tyły i głębokość modeli są interpretacją; identyfikacja gatunków nie jest potwierdzona.
- Wewnętrzne proporcje geometrii są zachowane. Domyślna skala ekspozycyjna nie oznacza wymiarów oryginalnych roślin lub przedmiotów.
- Wirtualny kodeks jest indeksem 206 skanów, nie rekonstrukcją historycznego szycia, oprawy ani liczby fizycznych kart. Rozkładówki pozostają pojedynczymi skanami. Zmiana kolejności jest dozwolona.
- Pracownia, Naczynia, Hydraulika, Diagramy, Obserwatorium i ogród tworzą jeden model Blendera. Wystawy są stronicowane kategoriami. Dynamiczna symulacja hydrauliki i astronomii nie jest zaimplementowana.
- W APK nie ma jeszcze dowolnego przecinania siatek z zamknięciem przekroju, podziału 2/3/4, transkrypcji AI, MCP, automatycznego wyzwalania nagrania głosem ani wbudowanej przeglądarki. Oddzielanie istniejących części działa.
- Obraz notatki obejmuje scenę wirtualną, nie obraz kamer passthrough; kadr jest monokularny i ma własne pole widzenia 75°.
- Notatki głosowe wymagają ręcznego zakończenia albo limitu 2 minut. W razie wymuszonego zamknięcia procesu nagranie będące w toku może zostać utracone; ukończone notatki i układy są plikami lokalnymi.
- Ta wersja nie publikuje zmian na istniejącej stronie Sites. Natywny klient i witryna są oddzielnymi pakietami.

## Odtwarzanie kompilacji

Odtwórz zasoby poleceniem z scripts/prepare_assets.py, a następnie otwórz projekt w Godot **4.6 stable**. Zainstaluj jego szablony eksportu
i **Android Build Template**, pozostaw `addons/godotopenxrvendors` 5.1.0.
Ustaw OpenJDK 17, Android SDK Platform 35 i Build Tools 35.0.1.
Eksport `Meta Quest` używa ARM64, Gradle, OpenXR i wtyczki Meta.
Do aktualizowania tej samej instalacji potrzebny jest ten sam klucz podpisu;
nowy lokalnie wygenerowany klucz oznacza inną tożsamość podpisu.

```sh
godot --headless --xr-mode off --path . --editor --import
python ../blender-progress/room-update03/optimize_texture_imports.py .
godot --headless --xr-mode off --path . --editor --import
godot --headless --xr-mode off --path . --script tests/integration.gd
godot --headless --xr-mode off --path . --export-debug "Meta Quest" ../Manuskrypt_Quest_0.3.0.apk
```

Kopia kodu w GitHub zawiera skrypty i konfigurację. prepare_assets.py odtwarza zasoby
z zapisanych ZIP-ów modeli, aktualizacji partii 01, 20 i 21–28, sal i tarota, kodeksu, nowego budynku
oraz oficjalnego archiwum dodatku XR. Oryginalne piksele odtwarza z APK 0.3 i weryfikuje ich SHA-256.
W kopii Drive duże pliki podzielono na części. Pobierz je razem z manifestem i polacz_pliki.py,
a następnie uruchom `python polacz_pliki.py` (skrypt odczyta oba manifesty).
Nie przechowuj kluczy API ani PIN-u VCT w projekcie.

Dokumentacja bazowa:
- https://docs.godotengine.org/en/4.6/tutorials/xr/deploying_to_android.html
- https://docs.godotengine.org/en/4.6/tutorials/export/exporting_for_android.html
- https://github.com/GodotVR/godot_openxr_vendors/releases/tag/5.1.0-stable

