# Pracownia Manuskryptu — VR 3 / podgląd, kategorie i podział

Otwórz w Meta Quest Browser: https://voynich-herbarium-3d.songoku222.chatgpt.site/quest.html

Wybierz **Wejdź do VR** (wirtualne tło) albo **MR / otoczenie** (przezroczyste tło i widok otoczenia, jeżeli urządzenie obsługuje immersive-ar). To aplikacja WebXR, uruchamiana z adresu HTTPS. Nie wymaga APK.

## Własny układ — domyślny tryb

1. Wybierz kartę, dodaj Fragmenty i użyj Rozsuń części, jeśli potrzebujesz oddzielić elementy.
2. Spustem chwyć część. Przesuń ją i obróć nadgarstkiem; puść w dowolnym miejscu. Nie ma wymuszonej kolejności ani przyciągania do oryginału.
3. Naciśnij **Dołącz wybrany** w menu. Element dołączy do aktywnej własnej grupy, zachowując dokładnie swoje położenie, obrót i skalę.
4. Ustaw następne części i dołączaj je tak samo. Mogą pochodzić z różnych kart manuskryptu.
5. Chwycenie części należącej do grupy porusza całą grupą. **Odłącz wybrany** uwalnia wskazaną część bez zmiany jej położenia.
6. **Nowa grupa** rozpoczyna kolejny niezależny zestaw. **Następna grupa** wybiera istniejący cel dołączania. Wybranie części już zgrupowanej aktywuje jej grupę; aby przenieść ją do nowej, wybierz tę część, następnie Nowa grupa i Dołącz wybrany.

Menu ma zakładki Karty, Składanie, Własny układ, Edycja i Podział. Przycisk Własny / skan przełącza zasady łączenia. Górny wiersz pokazuje bieżący tryb i numer aktywnej własnej grupy. Nie ma obowiązku odtwarzania kompozycji manuskryptu.

## Składanie według skanu — opcjonalne

Po przełączeniu na Według skanu luźna część otrzymuje półprzezroczysty podgląd właściwego miejsca, linię do celu oraz odległość i kąt. Zielony obrys oznacza gotowość do połączenia: puść spust. Tolerancja wynosi mniej niż 6 cm i 22° w przestrzeni aplikacji, przy zgodnej skali. Sprawdzany jest środek widocznej geometrii, także dla przesuniętych geometrii i grup trzymanych drugą ręką.

Jedną ręką możesz trzymać połączoną grupę z danej karty, a drugą dokładać luźne części tej samej karty. Spust na połączonej części chwyta całą połączoną grupę. Dołącz wybrany w tym trybie ustawia część dokładnie według skanu. Złóż wszystkie przywraca źródłowy układ aktywnej karty i usuwa jej części z własnych grup; **Cofnij** pozwala wrócić. Automatyczne dopasowanie źródłowe nie łączy różnych kart.

## Widoczność i kontrolery

- Błękitny obrys wskazuje obiekt, bursztynowy — trzymany, zielony — gotowy do dopasowania źródłowego.
- Kolory / światło przełącza oryginalne tekstury bez cieni i oświetlenie 3D. Domyślnie aktywne są czytelne kolory bez cieni.
- Ciemny podkład i Skan wzorcowy są opcjonalne, widoczne przy aktywnym zestawie źródłowym. Podkład nie podąża za dowolną własną kompozycją z wielu kart.
- Spust: pojedyncza luźna część albo jej grupa. Grip: cały zestaw źródłowy; gdy wskazujesz własną grupę, chwytasz tę grupę.
- Drążek podczas chwytu: góra/dół — bliżej / dalej; lewo/prawo — ciągły obrót bez ograniczenia liczby obrotów. Skala zmienia wszystkie osie proporcjonalnie; dla wybranego członka własnej grupy skaluje tę grupę.
- Przed sobą ustawia aktywny zestaw albo własną grupę wybranej części przed użytkownikiem.
- Zestaw nie może być chwycony jako całość, gdy druga ręka trzyma jego luźny element. Dwie różne luźne części tej samej karty mogą być trzymane równocześnie.
- Na komputerze kliknięcie wybiera część, a obrót i zoom działają myszą. Manipulacja sześcioma stopniami swobody jest obsługiwana kontrolerami XR.

## Podgląd każdego modelu i kategorie

Po prawej stronie menu w VR/MR znajduje się osobny podgląd: obracany model 3D, karta źródłowa i zaznaczenie miejsca wybranego fragmentu. Przyciskami Karta oraz Fragment przeglądasz wszystkie dostępne modele. Cały rysunek wraca do zestawu fragmentów wybranej karty. Pełny skan i Cały atlas wybierzesz w zakładce Karty. Obrót podglądu możesz zatrzymać lub obrócić go o 180°.

**Dodaj model** dodaje dokładnie model wybrany w katalogu podglądu, także pojedynczy fragment. Wskazanie części w pracowni pokazuje jej aktualny kształt po edycji lub podziale; przycisk podglądu zmienia się wtedy na **Duplikuj część**, tworzący niezależną kopię. Podgląd nie jest częścią zapisu ani eksportowanej sceny.

Kategoria w panelu VR przełącza filtry. Sortuj kategoriami w zakładce Karty przełącza porządek według kategorii lub numerów kart. Na komputerze dostępne są listy kategorii, kolejności, kart i fragmentów oraz miniatura skanu.

Kategorie pochodzą z roboczych metadanych atlasu: Rośliny (125), Tekst i drobne znaki (30), Sceny i postacie (20), Małe rośliny i naczynia (12), Diagramy (9), Zodiak (8), Okładki (2). Filtr dotyczy katalogu, nie usuwa ułożonych modeli. Podgląd pomaga porównywać kształty i pochodzenie; nie wskazuje potwierdzonego rozwiązania manuskryptu.

## Obrót o 180° i podział na niezależne części

W zakładce **Podział** są przyciski X 180°, Y 180° i Z 180°. Na komputerze wybierz oś i naciśnij 180°. Obrót zachowuje środek fragmentu i odłącza go od grupy.

Wybierz fragment, oś podziału X/Y/Z i liczbę części: **2, 3 lub 4**. Podziel fragment przecina aktualny zakres na równe pasy w lokalnej osi. Każdy niepusty pas staje się osobno chwytanym obiektem, z zachowaną teksturą i położeniem. Dla nieregularnego rysunku liczba niepustych części może być mniejsza od wybranej; przy mniej niż dwóch podział nie zastępuje oryginału.

Oryginał jest ukryty, a nowe części początkowo przylegają do siebie — chwyć część i odsuń ją ręcznie. Możesz je dowolnie obracać, ponownie dzielić, duplikować i łączyć z innymi kartami. **Cofnij** odzyskuje stan sprzed podziału. JSON w wersji 5 odtwarza osobne części, ukryty oryginał i grupy. GLB zawiera widoczne części. Cięte powierzchnie nadal mają otwarte krawędzie.

## Obracanie i przycinanie

W zakładce **Edycja** masz osobne przyciski obrotu X, Y, Z w krokach ±15°. Każda oś pozwala wykonać pełne 360° i dowolną liczbę dalszych obrotów. Środek widocznego fragmentu pozostaje na miejscu. Swobodny obrót nadgarstkiem oraz ciągły obrót drążkiem działają podczas chwytu. Obrót pojedynczego fragmentu przyciskami odłącza go od grupy; po edycji możesz dołączyć go ponownie.

**Strona cięcia** przełącza lewą, prawą, górną, dolną, przednią i tylną stronę w lokalnych osiach wybranego fragmentu. **Przytnij 5%** usuwa kolejne 5% pierwotnego wymiaru z tej strony; **Oddaj 5%** przywraca pas. **Przywróć kształt** odzyskuje oryginał bez zmiany ułożenia. Cofnij odwraca ostatnią operację.

Przycinanie zmienia geometrię powierzchni i interpoluje współrzędne tekstury; eksport GLB zawiera przycięty model. JSON zapisuje ustawienia cięć, a oryginalny plik modelu pozostaje niezmieniony. Krawędź cięcia pozostaje otwarta — to przycinanie powierzchni, nie operacja tworząca zamknięty model do druku 3D. Jednorazowa edycja dotyczy wskazanego fragmentu; przycinanie odłącza go od grupy. Pozostawione musi być co najmniej 2% wymiaru na każdej osi.

## Perspektywa, źródła i zapis

Widok i projekcję obu oczu dostarcza WebXR. Aplikacja nie zmienia FOV ani IPD gogli. OrbitControls działają wyłącznie poza sesją XR. Jednostki świata to metry, lecz fizyczne wymiary oryginału nie są ustalone. Proporcje geometrii są zachowane; głębokość reliefów 2.5D jest umowna.

Dostępne są 206 skanów, 2619 fragmentów oraz atlas zbiorczy. Automatyczna segmentacja ma status CANDIDATE, obejmuje także szum/tekst i wymaga przeglądu. Nie jest to potwierdzona rekonstrukcja anatomii roślin. Pełne skany zachowują całą treść.

Projekt zapisuje się lokalnie po manipulacjach. JSON w wersji 7 zachowuje własne grupy, dowolne położenia i grupy źródłowe. Starsze projekty wersji 1–6 nadal można wczytać. Zapisz projekt JSON / Wczytaj JSON przenosi pracę między urządzeniami. Eksport GLB zapisuje widoczną scenę, również własne grupy. Limit jednej pracowni: 30 zestawów i 30 własnych grup; zbiorczy atlas wszystkich 206 skanów liczy się jako jeden zestaw.

MR nie mapuje ścian ani nie zasłania modeli prawdziwymi meblami. Zapis nie jest trwałą kotwicą fizycznego pomieszczenia. W razie potrzeby użyj Przed sobą po kolejnym wejściu.

## Weryfikacja

Przeszły testy kategorii, podziałów 2/3/4 i zachowania sumy pól powierzchni (`node scripts/test_catalog_split.mjs`), testy podglądu i ponownego odczytu części po podziale oraz testy przycinania trójkątów, interpolacji UV i obrotu 360° wokół środka fragmentu (`node scripts/test_mesh_edit.mjs`), testy matematyki Three.js (`node scripts/test_xr.mjs`), testy rzeczywistych procedur aplikacji z zastąpionym wejściem/wyjściem DOM i XR (`node --experimental-vm-modules scripts/test_quest_runtime.mjs`) oraz kompletności zasobów i kontrolek (`node scripts/check_site.mjs`). Testy obejmują grupowanie między kartami bez zmiany pozycji, rozłączanie, zapis/odczyt wersji 4, odczyt wersji 1, grupy źródłowe, dwa trzymane obiekty, podgląd celu oraz zachowanie poprzedniej sceny po błędzie wczytywania.

Nie wykonano renderowanego testu w przeglądarce ani testu na fizycznych goglach Quest. Komfort, czytelność w passthrough i płynność wymagają odbioru na urządzeniu.

Pełnej jakości modele: https://drive.google.com/drive/folders/1l2nL2ZkjsyhgHJQF2FXIhDjcHXBqn9YX
Kod: https://github.com/SonGohan231/voynichese/tree/models3d/atlas-206-2026-09-26/models3d


## Pracownia badawcza — zatwierdzona wersja testowa (2026-09-27)

Użytkownik zatwierdził przedstawiony pokój do wdrożenia testowego: „Jest super, zatwierdzam!”. Ta aktualizacja obejmuje pokój oraz dodatkowe narzędzia i wystroje. Akceptacja wdrożenia nie oznacza wykonanego testu na goglach.

- Pokój 6 × 5 m według układu sprawdzonego w Blenderze; osobno ukrywana architektura MR.
- Prawdziwe skany w kodeksie i stronicowanym stojaku 12 kart; pełny katalog 206 skanów zachowany.
- Wyjmowanie kopii stron, dowolne przypinanie do dwóch tablic z zachowaniem obrotu, odpinanie i cofanie.
- Grip chwyta świecę, lupę, miarkę i półprzezroczystą nakładkę. Lupa pokazuje teksturę źródłową; pomiar podaje piksele tekstury.
- Sześć checklist opartych na czterech odczytanych dokumentach GitHub/Drive, z odrębną hipotezą swobodnych układów użytkownika.
- Dźwięki Mirelo: tło pracowni i szelest strony. Dźwięk domyślnie wyłączony.
- Otwieranie wybranego adresu HTTPS lub źródła w przeglądarce, zapis przed opuszczeniem sesji XR. Nie jest to wbudowana dowolna przeglądarka 3D.
- Format projektu v6 zapisuje przypięcia, checklisty, notatki i narzędzia. Odczyt v1–v5 zachowany.

Testy matematyki i rzeczywistych procedur programu z atrapą DOM/XR przeszły. Brak testu renderowanej aplikacji i fizycznego Quest. Blender jest osobną sceną; jego render nie jest zrzutem aplikacji.

Przegląd źródeł obejmuje research/hypotheses.json, nie całą historię projektu Manuskrypt 2.0. Manusvoynus był niedostępny. Dostarczone kopie instrukcji VCT zostały odczytane; ich poufna zawartość nie jest częścią aplikacji.


## Dodatki i kolejne wystroje — projekt v7

- **Archiwum, Gabinet botaniczny, Sala diagramów**: przełączanie wystroju i wyposażenia tej samej pracowni. To wspólna przestrzeń robocza: wszystkie modele, przypięcia i znaczniki pozostają na swoich miejscach. Nie ma teleportacji między odległymi pokojami ani osobnych zapisów każdego pokoju. Dekoracyjne tarcze i puste ramki nie są dowodem badawczym.
- **Kątomierz A–B–C**: wskaż trzy punkty na tej samej części, drugi jest wierzchołkiem. Kąt jest liczony w pikselach tekstury z uwzględnieniem jej proporcji, niezależnie od perspektywy kamery. To poglądowy pomiar tekstury, nie skalibrowany pomiar natywnego skanu czy przestrzennej rośliny. Grip chwyta mosiężny kątomierz, spust przełącza jego tryb.
- **Znaczniki**: wybierz narzędzie, kliknij powierzchnię modelu. Do 100 numerowanych znaczników w trzech kolorach. Poruszają się i obracają z przypisaną częścią; zapisują identyfikator zestawu/części, lokalny punkt, UV oraz wymiary tekstury. Adnotacje są widoczne ponad modelem; nie zmieniają skanu. Znacznik nie przechodzi automatycznie na nowe fragmenty po podziale — ukrycie części ukrywa jej znaczniki. Duplikaty nie dziedziczą adnotacji. Usuń ostatni i Cofnij pozwalają poprawić oznaczenie.
- **Przywołaj narzędzia**: odkłada wszystkie pięć narzędzi w zasięgu przed aktualnym widokiem; zwalnia obiekty trzymane w kontrolerach.
- Panel narzędzi w VR znajduje się powyżej obszaru pracy, z przyciskami pokoi, koloru, usuwania znacznika i kończenia pomiaru. Po pomiarze wybierz Zakończ pomiar, aby wrócić do chwytania.
- Projekt JSON v7 zachowuje wystrój, znaczniki i wcześniejsze dane. Import v1–v6 zachowany. Eksport GLB obejmuje modele; narzędzia, checklisty i adnotacje przenoś przez JSON.

Nowe testy rzeczywistych procedur: kąt 90°, poprawna skala pikselowa tekstury, odrzucenie powtórzonych punktów i mieszania źródeł, podążanie znaczników za obrotem/przesunięciem, zapis/odczyt adnotacji, zachowanie układu podczas zmiany wystroju, przywołanie trzymanego narzędzia, odczyt v6 — PASS. DOM i XR są zastąpione w teście; brak pomiaru FPS lub testu fizycznego Quest.

Kod pracowni: https://github.com/SonGohan231/voynichese/tree/models3d/research-room-2026-09-27/models3d
