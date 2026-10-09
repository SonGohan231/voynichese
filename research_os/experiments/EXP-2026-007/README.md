# EXP-2026-007 — rzeczywista niezależna analiza wizualna MS408

**Data:** 2026-10-09. **Gałąź:** `research/voynich-dualvision-exp007-20261009`. **PR:** [#21](https://github.com/SonGohan231/voynichese/pull/21). **Główny workflow:** [voynich-exp007-dualvision.yml](https://github.com/SonGohan231/voynichese/actions/workflows/voynich-exp007-dualvision.yml).

## Cel, nowy względem EXP006

Zamiast porównywać wyłącznie geometryczne maski konturów, przeprowadzić rzeczywiste wejście **obrazów źródłowych** do **dwóch różnych modeli wizualnych** z oddzielnymi, izolowanymi przebiegami. To jest ślepa niezależność wejść inferencyjnych, **nie** recenzja dwóch niezależnych ekspertów historycznych i **nie** walidacja historycznej semantyki.

1. `frozen-yale-evidence` – pobiera 9 oryginalnych źródłowych JPEG Yale MS408, ponownie weryfikuje SHA256 źródeł, tworzy 27 wycinków z zapisem OID, SHA, fizycznego bifolium. Z każdego zdjęcia pobiera **pierwsze 2 ROI według wcześniej istniejącego ID**, dokładnie 18 wycinków. Proces zamraża manifest z hashem całego bazowego manifestu i identyfikatorów 18 cropów **zanim** wyniki modeli lub wcześniejsze wyniki rankingu zostaną ujawnione do dalszej analizy.
2. `blind-caption-A` – uruchamia publiczny pretrained `Salesforce/blip-image-captioning-base` (opis otwarty) na oryginalnych pikselach cropów i zapisuje **surowy opis modelu**, bez automatycznego zatwierdzenia kategorii historycznej.
3. `blind-contrast-B` – uruchamia inną architekturę `openai/clip-vit-base-patch32` jako zero-shot image–prompt similarity. Przechowuje **wszystkie siedem wyników** porównywania z jawnymi, z góry ustalonymi opisami: diagram kołowy, architektura, rośliny, postacie, elementy nieba, zapis, artefakt obrazu. Jeśli top-score<0.38 lub różnica top-2 <0.15, przypisuje `UNKNOWN`; softmax CLIP **nie** jest skalibrowanym prawdopodobieństwem prawdziwości klasy.
4. `blind-disagreement-audit` – pobiera oba surowe pliki po zakończeniu inferencji na wszystkich 18 obrazach i łączy je **dopiero wtedy**, zachowując sprzeczności bez automatycznego nadawania zatwierdzonej klasy. Rekordy obejmują `source_oid`, `source_photo_sha256`, `crop_sha256`, oryginalny bbox, oba wyniki i brak ludzkiej adjudykacji.

**Ważna kontrola niezależności:** jobs A i B mają dostęp jedynie do zamrożonego oryginalnego pakietu, nie do wyników drugiej metody. Każdy jest izolowany w osobnym runnerze. Wyniki modeli mogą się zgodzić przypadkiem lub przez podobne uprzedzenia treningowe; nie jest to dowód historyczny.

## Zasady kontroli naukowej

- **Nie rozpoznajemy z definicji** „tej samej wieży / kobiety / gwiazdy / mapy / obiektu” tylko dlatego, że algorytm BLIP napisał takie słowo lub CLIP wybrał odpowiedni prompt. Mylne etykiety mogą być częste na historycznych rysunkach.
- **Nadal potrzebne:** dwa niezależne ręczne lub wiarygodne eksperckie oglądy **pełnych oryginalnych stron** i dobór polygonów do rzeczywistych obiektów, a potem graf zależności, liczby promieni, orientacja twarzy/postaci, tekst w udokumentowanych współrzędnych.
- Model prompt scores są współzależne; nie liczymy ich jako niezależnej replikacji założeń. Bliskość kolorów i wspólne tło mogą prowadzić do fałszywych dopasowań.
- Porównanie 67v↔86v w EXP005 było silnie zależne od wyboru wycinka (0.84983 „best of nine”, 0.519459 „pierwszy neutralny ROI”); dlatego te wyniki są tylko eksploracyjną hipotezą, nie kryterium selekcji 18 nowych wejść.
- Formalne testy `COUNT_ONLY`, `COLOR_ONLY`, `OUTLINE_ONLY` wykonano opisowo w EXP005, `TEXT_ONLY` pozostał `NOT_ASSESSED` bez rzeczywistej rejestracji współrzędnych transcript↔photo. Dla EXP007 brak wniosków MV2, MV3 czy MV4.
- Żadne skrypty nie odczytują `EXP-2026-001` HELD-OUT; gromadzenie danych i walidację logiczną robimy na jawnych zdjęciach EXP005/006.
- Zachowujemy ślady porażek technicznych i nie oznaczamy wykonania dwóch modeli na podstawie jedynie pomyślnego generowania źródłowych cropów.

## Agent OS – udokumentowane zlecenia i ryzyko routingu

- Misja `7255e2be-7ef9-4232-aed6-db3e921fbccc`: routowanie jednego zadania `work-02` do agenta wyspecjalizowanego w niepasującym obszarze; nie może stanowić naukowego dowodu. Rozdzielone badania agentów naukowych nie zastępują rzeczywistego image model.
- Misja naukowej kontroli źródeł `18996072-17d9-42b6-85d6-95227a021b02` przydziela poprawnych dwóch `scientific-literature-scout`, ale osobno przydzielone QA-techniczne nie jest uprawnione do merytorycznego Keepera ilustracji.
- Kontrolę merytoryczną mogą zaakceptować jedynie członkowie z realną dostępnością obrazu oryginalnego i audytem adnotacji. Nie należy udawać tego etapu.

## Kryterium wyniku końcowego

`CI_SUCCESS` wymaga rzeczywistego zakończenia obu jobów multimodalnych, **36 surowych odpowiedzi** (18 BLIP + 18 CLIP), oryginalnego manifestu SHA, logów, tabeli sprzeczności i artefaktów; bez danych obu modeli `NOT_RUN_OR_FAILED`.

`SCIENTIFIC_SEMANTIC_VERIFIED` wymaga odrębnych ekspertów/ocen udokumentowanych poza tym automatycznym eksperymentem. Domyślny status: `AI_ONLY_EXPLORE / HUMAN_REVIEW_PENDING`.
