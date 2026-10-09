# EXP-2026-005 — semantyczne dopasowanie obiektów między kartami Voynicha

**Data:** 2026-10-09. **Rzeczywista misja Agent OS:** `0869cf9d-fdb0-40cd-9339-a64e2ea73b42`. **Nadzór metodologiczny:** Dyrygent V3.8.1 (preset: research, balanced). **Status naukowy na starcie:** `EXPLORATORY_NOT_CONFIRMED`, wcześniejsze zaakceptowane identyfikacje tej samej historycznej rzeczy z różnych perspektyw: **0**.

## Co dokładnie sprawdzamy

Nie wystarczy podobny kolor, liczba kresek albo kontur. Poszukujemy powtarzającego się **układu składowych** w niezależnych fizycznie kartach: porty/połączenia, kolejność sektorów, promienie, relacje między figurami, obrys obiektu, ewentualne napisy przy jego konkretnych częściach. Rywalizują H_same_object_different_view, H_same_motif, H_repeated_2D_ornament, H_unrelated_art, H_photo_artifact.

| Priorytet | Para oryginalnych źródeł | Dlaczego i czego dowód jeszcze nie pokazał |
| --- | --- | --- |
| A1 | **67v** (q9) ↔ **85v/86r** (q14, rozkładówka) | Eksploracyjne radial scores 0.4481, ale w teście źródłowej rigid-2D geometrii brak ≥5 ORB inliers |
| A2 | **67v** ↔ **86v (part)** (q14) | Radial score do 0.4627, w tym samym 2D teście również brak ≥5 inliers |
| B | **32r** ↔ **8v** | dHash różni się 11/64; nieustalona klasa obiektu; 2D inliers 0 w próbie |
| C | **93r** ↔ **18v** | Odmienna sekcja, dHash 16/64; konieczne osłabienie pułapki wspólnego stylu kreski |
| NEG | **55r** ↔ **34v** | Porównanie kontrolne, dHash 16/64; nie zakładaj tożsamości |

**Źródła poprzednich REALNYCH eksperymentów:** [radial #37894901398](https://github.com/SonGohan231/voynichese/actions/runs/37894901398), [contour #37895155729](https://github.com/SonGohan231/voynichese/actions/runs/37895155729); [PR #18](https://github.com/SonGohan231/voynichese/pull/18) zawiera generator, kontaktowe cropy i odpowiedzialne ograniczenia. Wcześniejsze „świetne” dopasowania 30v↔31v i 28v↔34v to **krawędzie zdjęć**, nie manuskryptowe przedmioty.

## DAG / wymagane role i dowody

1. **Źródła i kodyks:** sprawdzenie Yale JPEG i SHA256 przy odczycie; ważne różnice folio/canvas/physical bifolio; obrazy z q14 nierozdzielane na fikcyjnie niezależne jednostki.
2. **Pakiet scen / evidence crops:** przy każdym z 9 fizycznych skanów co najmniej 3 wycinki z potwierdzonym pochodzeniem, pełna rozdzielczość źródła, osobne metryki niewymagające kolorowego modelu. Neutralne okna siatki wyraźnie odrębne od maszynowych kandydatów przedmiotów. `exp005_semantic_source_pack.py` i CI tworzą manifest oraz pięć plansz zestawienia.
3. **Opis ślepy AI-1 / AI-2:** niezależne w znaczeniu oddzielnych uruchomień i bez ujawniania hipotez parowania; to **nie są** niezależni eksperci ani human-ground-truth. Każda strona: tower/plant/roundel/human/other/UNKNOWN; nazwa, bbox, źródło, pewność, połączenia, graficzne landmarki. Przypadki sporne do Keeper adjudication.
4. **Kierunek, topologia, zamienny rzut:** porównanie podpisów grafowych i liczby segmentów, rotacji, odbicia (karana osobno), homografii/2.5D jedynie z niezależnymi landmarkami. 2D vs 2.5D z penalizacją złożoności, bez swobodnej deformacji obiektu.
5. **Barwy, brak pigmentu i tokeny:** rozdziel papier/kolor/digitalizację; `UNPAINTED` dopiero po sprawdzeniu fizycznym, nigdy z RGB. Transkrypcja EVA/IVTFF nie jest przekładem; token z rysunkiem tylko po weryfikacji rejestracji współrzędnych.
6. **Negatywne kontrole:** oddzielne null-e `COUNT_ONLY`, `COLOR_ONLY`, `OUTLINE_ONLY`, `TEXT_ONLY`; dodatkowo relacja WITHIN/BETWEEN sekcja, niezależne grupy bifoliów, skryba/Currier gdzie jest źródło, losowe zwykłe średniowieczne ornamenty. Brak wiarygodnych danych ⇒ NOT_ASSESSED. Nulls 1–4 nie wolno uważać za zaliczone, gdy wyliczono tylko count+dHash.
7. **Red-team & Keeper:** niezależny od autora zmian; zweryfikuj zdjęcia/kody, liczby porównań, kontrolę negatywną i co najmniej kilkanaście rzeczywistych wycinków przed kwalifikacją MV2+. Brak ręcznej weryfikacji ⇒ nie nadaj MV3 ani MV4.

## Progi i falsyfikacja

- MV0: podobieństwo nieustalone lub artefakt fotograficzny.
- MV1: słaba zbieżność motywu, bez semantycznego dowodu.
- MV2: niezależnie zweryfikowana klasa oraz ≥2 cechy niebędące tą samą krawędziową projekcją.
- MV3: mocne wielorodzinne dowody tego samego obiektu w innym widoku i niezależny test fizyczny/kontrolny.
- MV4: prerejestrowana, niezależnie powtórzona replikacja z kontrolą wielu hipotez; na tym etapie nie przyznawać.

Każdy wynik (`REJECTED_PHOTO_ARTIFACT`, `RELATED_MOTIF_ONLY`, `UNOBSERVABLE`, `INSUFFICIENT_EVIDENCE`, `HYPOTHESIS_SUPPORTED_WITH_LIMITS`) ma mieć źródłowe JPEG/OID/SHA, crop, opis testu, null oraz przyczynę rozstrzygnięcia. Nie pozwalaj na liczenie statystycznych p-value bez właściwej odłożonej próby i korekty wielokrotnych porównań.

**Ochrona:** `EXP-2026-001` HELD-OUT wyłączony z analizy, inne jawne zbiory fizycznych map nie dają prawa otwierać HELD-OUT. Żadna pomyślnie zakończona praca workflow ani automatyczna anotacja nie jest dowodem historycznym. Nie scalaj gałęzi do `master` bez niezależnego raportu QA.

## Kryterium „wykonano”

Uznawane za REALNE tylko gdy istnieją: source-native cropy z hashami, manifest JSON, 5 plansz par i workflow log, dwie ślepe serie opisów (lub jawne NOT_RUN), działające testy i kontrola braków, oddzielny protokół niezależnej oceny, PR z listą zmian; naukowy verdict może pozostać negatywny/niejednoznaczny. Zakończenie z samego dokumentu planu jest zabronione.
