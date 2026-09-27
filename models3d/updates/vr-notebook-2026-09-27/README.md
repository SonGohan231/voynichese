# Kopia kodu do przeglądu — Manuskrypt VR

To kopia zmian, nie samodzielny pakiet do publikacji. Pełne zasoby (GLB, obrazy, biblioteki przeglądarkowe, lockfile i pozostałe moduły) pozostają w kanonicznym repozytorium Sites. Istniejąca gałąź badawcza i poprzednia aplikacja są zachowane. Pliki .blend oraz GLB zapisano w 19 paczkach i zbiorczym archiwum.

# Manuskrypt VR — stan aktualizacji

173 robocze zespoły brył dla 173 skanów: 125 roślinnych, 19 scen, 12 farmaceutycznych, 9 diagramów, 8 zodiakalnych. 19 partii Blendera. Cały atlas nadal obejmuje 206 skanów i 2619 automatycznych fragmentów reliefowych. To NIE jest potwierdzenie wiernego, kompletnego odwzorowania każdego rysunku; kontury, liczby szczegółów, tyły i głębia wymagają dalszej ręcznej weryfikacji. 33 skany mają dotąd tylko reprezentację skanu/reliefu (szczegóły w MODEL_STATUS.json).

## Obsługa
- Katalog: /volumes.html, kategorie i wyszukiwanie folio.
- Rośliny: /garden.html. Ogród ładuje jedną partię na raz.
- Pracownia: /quest.html?volume=s0004. Spust wybiera, grip chwyta. Dostępne obroty, podział, cięcie, grupowanie między stronami i zapis projektu.
- Notatki: panel NOTATKI w VR albo /notes.html. Nagranie, obraz wirtualnej sceny z pozycji głowy, szkic przypięty do modelu. Bez dostępu do kamer passthrough.
- Mikrofon wymaga zgody przeglądarki. Ręczny start albo gotowy Silero VAD (@ricky0123/vad-web). Maks. 2 minuty nagrania. Niedokończony zapis można odzyskać jako osobną notatkę.

## AI i dane
Oficjalny OpenAI SDK: gpt-transcribe (głos), gpt-4.1 Responses z obrazem i wymuszonym schematem notatki, text-embedding-3-small (wyszukiwanie możliwych połączeń). Źródła zapisane w kontekście: folio, pozycja głowy, macierz projekcji, pozycje elementów i szkice. D1 przechowuje notatki, prywatny R2 media, IndexedDB kopie robocze. API jest oddzielone między użytkownikami i sprawdza Origin przy zapisie. Klucz wyłącznie po stronie serwera.

Brak skonfigurowanego OPENAI_API_KEY. Analiza AI nie jest uruchomiona. Integracja testowana z atrapą dostawcy; brak testu żywego API. Nowa pełna wersja pozostaje zapisana bez publikacji: procedura Sites wymaga bezpiecznej konfiguracji klucza przed wdrożeniem. W tej sesji brak umiejętności openai-platform-api-key mimo widocznej integracji OpenAI Developers. Nie wklejaj klucza do czatu.

## Testy i ograniczenia
Realny parser GLTFLoader i meshopt wczytuje modele; testy sprawdzają geometrię, nazwy i przekształcenia. Testy obsługi VR używają prawdziwego kodu i Three.js, ale zastępują urządzenie XR, DOM i mikrofon. Brak testu na fizycznym Meta Quest i brak potwierdzenia liczby klatek. Sprawdzono renderowane podglądy w Blenderze. Modele szkicowe nie są dowodem identyfikacji roślin ani odszyfrowania tekstu.

Kod źródłowy i wszystkie zasoby aplikacji są w repozytorium źródłowym Sites. GitHub zawiera kopię kodu do przeglądu i skrypty generowania; ciężkie zasoby pozostają w zapisie Sites oraz paczkach Blender.
