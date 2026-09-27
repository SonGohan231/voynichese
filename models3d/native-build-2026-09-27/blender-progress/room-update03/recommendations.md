# Pięć najlepiej dopasowanych projektów GitHub

Dobór do aktualnego projektu Godot 4.6 / Meta Quest, sprawdzony 27.09.2026 w repozytoriach autorów. Nie instaluję pięciu nakładających się systemów chwytania.

| Projekt | Zastosowanie w Manuskrypcie VR | Stan |
|---|---|---|
| [Godot XR Tools 4.5.1](https://github.com/GodotVR/godot-xr-tools) | Komfort przemieszczania i sprawdzone elementy interakcji XR. | Włączono oryginalny moduł Fade podczas przenoszenia między salami. Dotychczasowe chwyty i swobodne łączenie zachowane. MIT. |
| [Godot OpenXR Vendors 5.1.0](https://github.com/GodotVR/godot_openxr_vendors) | Obsługa platformy Quest, rozszerzenia Meta i passthrough. | Jest już w natywnej APK; zachowany przypięty pakiet. Funkcje sprzętowe wymagają próby na goglach. |
| [gfiumara/CIEDE2000](https://github.com/gfiumara/CIEDE2000) | Porównywanie barw próbek skanu. | Włączono port algorytmu do GDScript, z licencją MIT. Przypięty commit af1de42515f3916c16e75980a4635962489af56a. Przechodzi 34 referencyjne pary; najgorszy błąd <0.00005 ΔE. |
| [whisper.cpp 1.9.4](https://github.com/ggml-org/whisper.cpp) | Gotowe rozpoznawanie polskiej mowy; dostępny przykład Android. | Rekomendowany następny moduł. Nie ma jeszcze transkrypcji w APK 0.3. Nagrania WAV i zdjęcia widoku są lokalne. Trzeba zbudować i sprawdzić most Android oraz dobrać model i opóźnienie na Quest. |
| [MCP Python SDK 2.2.0](https://github.com/modelcontextprotocol/python-sdk) | Serwer do organizowania notatek, źródeł i powiązań dla ChatGPT. | Rekomendowany most serwerowy, nie jest wdrożony ani sparowany z APK. Wymaga wybranego serwera, uwierzytelnienia i testu całej ścieżki głos–notatka. MIT. |

Wersje sprawdzono także przez API GitHub. OpenXR Vendors 5.1.0 był już obecny; nie zmieniano działającej wersji bez powodu. Dołączone części XR Tools i CIEDE2000 zachowują licencje w quest-native/third_party.

Próbnik korzysta z pełnych bajtów JPEG o zweryfikowanym SHA-256. Wszystkie 206 źródeł mają osadzony profil sRGB. RGB jest pobierane z obrazu zdekodowanego na CPU, przed oświetleniem, filtrowaniem i kompresją tekstury GPU. JPEG może dawać minimalne różnice pomiędzy dekoderami. ΔE00 porównuje cyfrowe kolory skanów; bez kalibracji fotografii nie dowodzi zgodności pigmentów.
