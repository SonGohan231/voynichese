# Pracownia Manuskryptu — VR 2 / własne układy

Otwórz w Meta Quest Browser: https://voynich-herbarium-3d.songoku222.chatgpt.site/quest.html

Wybierz **Wejdź do VR** (wirtualne tło) albo **MR / otoczenie** (przezroczyste tło i widok otoczenia, jeżeli urządzenie obsługuje immersive-ar). To aplikacja WebXR, uruchamiana z adresu HTTPS. Nie wymaga APK.

## Własny układ — domyślny tryb

1. Wybierz kartę, dodaj Fragmenty i użyj Rozsuń części, jeśli potrzebujesz oddzielić elementy.
2. Spustem chwyć część. Przesuń ją i obróć nadgarstkiem; puść w dowolnym miejscu. Nie ma wymuszonej kolejności ani przyciągania do oryginału.
3. Naciśnij **Dołącz wybrany** w menu. Element dołączy do aktywnej własnej grupy, zachowując dokładnie swoje położenie, obrót i skalę.
4. Ustaw następne części i dołączaj je tak samo. Mogą pochodzić z różnych kart manuskryptu.
5. Chwycenie części należącej do grupy porusza całą grupą. **Odłącz wybrany** uwalnia wskazaną część bez zmiany jej położenia.
6. **Nowa grupa** rozpoczyna kolejny niezależny zestaw. **Następna grupa** wybiera istniejący cel dołączania. Wybranie części już zgrupowanej aktywuje jej grupę; aby przenieść ją do nowej, wybierz tę część, następnie Nowa grupa i Dołącz wybrany.

Menu ma zakładki Karty, Składanie i Własny układ. Przycisk Własny / skan przełącza zasady łączenia. Górny wiersz pokazuje bieżący tryb i numer aktywnej własnej grupy. Nie ma obowiązku odtwarzania kompozycji manuskryptu.

## Składanie według skanu — opcjonalne

Po przełączeniu na Według skanu luźna część otrzymuje półprzezroczysty podgląd właściwego miejsca, linię do celu oraz odległość i kąt. Zielony obrys oznacza gotowość do połączenia: puść spust. Tolerancja wynosi mniej niż 6 cm i 22° w przestrzeni aplikacji, przy zgodnej skali. Sprawdzany jest środek widocznej geometrii, także dla przesuniętych geometrii i grup trzymanych drugą ręką.

Jedną ręką możesz trzymać połączoną grupę z danej karty, a drugą dokładać luźne części tej samej karty. Spust na połączonej części chwyta całą połączoną grupę. Dołącz wybrany w tym trybie ustawia część dokładnie według skanu. Złóż wszystkie przywraca źródłowy układ aktywnej karty i usuwa jej części z własnych grup; **Cofnij** pozwala wrócić. Automatyczne dopasowanie źródłowe nie łączy różnych kart.

## Widoczność i kontrolery

- Błękitny obrys wskazuje obiekt, bursztynowy — trzymany, zielony — gotowy do dopasowania źródłowego.
- Kolory / światło przełącza oryginalne tekstury bez cieni i oświetlenie 3D. Domyślnie aktywne są czytelne kolory bez cieni.
- Ciemny podkład i Skan wzorcowy są opcjonalne, widoczne przy aktywnym zestawie źródłowym. Podkład nie podąża za dowolną własną kompozycją z wielu kart.
- Spust: pojedyncza luźna część albo jej grupa. Grip: cały zestaw źródłowy; gdy wskazujesz własną grupę, chwytasz tę grupę.
- Drążek podczas chwytu: bliżej / dalej. Skala zmienia wszystkie osie proporcjonalnie; dla wybranego członka własnej grupy skaluje tę grupę.
- Przed sobą ustawia aktywny zestaw albo własną grupę wybranej części przed użytkownikiem.
- Zestaw nie może być chwycony jako całość, gdy druga ręka trzyma jego luźny element. Dwie różne luźne części tej samej karty mogą być trzymane równocześnie.
- Na komputerze kliknięcie wybiera część, a obrót i zoom działają myszą. Manipulacja sześcioma stopniami swobody jest obsługiwana kontrolerami XR.

## Perspektywa, źródła i zapis

Widok i projekcję obu oczu dostarcza WebXR. Aplikacja nie zmienia FOV ani IPD gogli. OrbitControls działają wyłącznie poza sesją XR. Jednostki świata to metry, lecz fizyczne wymiary oryginału nie są ustalone. Proporcje geometrii są zachowane; głębokość reliefów 2.5D jest umowna.

Dostępne są 206 skanów, 2619 fragmentów oraz atlas zbiorczy. Automatyczna segmentacja ma status CANDIDATE, obejmuje także szum/tekst i wymaga przeglądu. Nie jest to potwierdzona rekonstrukcja anatomii roślin. Pełne skany zachowują całą treść.

Projekt zapisuje się lokalnie po manipulacjach. JSON w wersji 3 zachowuje własne grupy, dowolne położenia i grupy źródłowe. Starsze projekty wersji 1 i 2 nadal można wczytać. Zapisz projekt JSON / Wczytaj JSON przenosi pracę między urządzeniami. Eksport GLB zapisuje widoczną scenę, również własne grupy. Limit jednej pracowni: 30 zestawów i 30 własnych grup; zbiorczy atlas wszystkich 206 skanów liczy się jako jeden zestaw.

MR nie mapuje ścian ani nie zasłania modeli prawdziwymi meblami. Zapis nie jest trwałą kotwicą fizycznego pomieszczenia. W razie potrzeby użyj Przed sobą po kolejnym wejściu.

## Weryfikacja

Przeszły testy matematyki Three.js (`node scripts/test_xr.mjs`), testy rzeczywistych procedur aplikacji z zastąpionym wejściem/wyjściem DOM i XR (`node --experimental-vm-modules scripts/test_quest_runtime.mjs`) oraz kompletności zasobów i kontrolek (`node scripts/check_site.mjs`). Testy obejmują grupowanie między kartami bez zmiany pozycji, rozłączanie, zapis/odczyt wersji 3, odczyt wersji 1, grupy źródłowe, dwa trzymane obiekty, podgląd celu oraz zachowanie poprzedniej sceny po błędzie wczytywania.

Nie wykonano renderowanego testu w przeglądarce ani testu na fizycznych goglach Quest. Komfort, czytelność w passthrough i płynność wymagają odbioru na urządzeniu.

Pełnej jakości modele: https://drive.google.com/drive/folders/1l2nL2ZkjsyhgHJQF2FXIhDjcHXBqn9YX
Kod: https://github.com/SonGohan231/voynichese/tree/models3d/atlas-206-2026-09-26/models3d
