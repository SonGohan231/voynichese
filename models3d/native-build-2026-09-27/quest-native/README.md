# Manuskrypt VR · natywna pracownia Quest 0.1.0

Wersja testowa APK dla Meta Quest 2, 3/3S i Pro (ARM64, Horizon OS 69 lub nowszy). Godot 4.6 stable, OpenXR,
oficjalny Godot OpenXR Vendors 5.1.0. Nie jest opakowaniem strony w Android WebView.

## Zawartość i sterowanie

- Katalog 173 roboczych zestawów przestrzennych; 206 dostarczonych skanów dostępnych offline.
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

## Instalacja

Włącz tryb deweloperski Questa i zaakceptuj debugowanie USB. Z komputera z Android Platform Tools:

```sh
adb devices
adb install -r Manuskrypt_Quest_0.1.0.apk
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

To pierwsza natywna wersja testowa, a nie ukończenie całego projektu VR.

- Nie przetestowano fizycznego Questa, stabilności liczby klatek, mikrofonu gogli ani passthrough na urządzeniu.
- Skany w APK to istniejące pochodne do podglądu (do 1550 px); oryginały pozostają w dostarczonych ZIP-ach.
- 173 zestawy nie oznaczają wiernej rekonstrukcji każdego pojedynczego rysunku. 33 pozostałe skany nie mają osobnych pełnych brył rysunków. Tyły i głębokość modeli są interpretacją; identyfikacja gatunków nie jest potwierdzona.
- Wewnętrzne proporcje geometrii są zachowane. Domyślna skala ekspozycyjna nie oznacza wymiarów oryginalnych roślin lub przedmiotów.
- Wirtualny kodeks jest indeksem 206 skanów, nie rekonstrukcją historycznego szycia, oprawy ani liczby fizycznych kart. Rozkładówki pozostają pojedynczymi skanami. Zmiana kolejności jest dozwolona.
- Pięć przestrzeni ma na razie wspólny stół i układ pracowni ze zmiennym tłem. Pełne wyposażenie ogrodu, hydrauliki i astronomii wymaga dalszego przeniesienia do wersji natywnej.
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
godot --headless --xr-mode off --path . --script tests/integration.gd
godot --headless --xr-mode off --path . --export-debug "Meta Quest" ../Manuskrypt_Quest_0.1.0.apk
```

Kopia kodu w GitHub zawiera skrypty i konfigurację. prepare_assets.py odtwarza zasoby
z zapisanych ZIP-ów modeli, aktualizacji partii 01, kodeksu, katalogu skanów
z wcześniejszego projektu Sites i oficjalnego archiwum dodatku XR.
Nie przechowuj kluczy API ani PIN-u VCT w projekcie.

Dokumentacja bazowa:
- https://docs.godotengine.org/en/4.6/tutorials/xr/deploying_to_android.html
- https://docs.godotengine.org/en/4.6/tutorials/export/exporting_for_android.html
- https://github.com/GodotVR/godot_openxr_vendors/releases/tag/5.1.0-stable

