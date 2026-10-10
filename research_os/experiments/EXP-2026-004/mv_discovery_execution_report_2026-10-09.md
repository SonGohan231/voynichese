# Voynich MV target discovery — wykonane testy z 2026-10-09

**Agent OS**: `0d53a9f6-26d1-4728-8a5c-c3f1ebbee378`, **PR**: [#18](https://github.com/SonGohan231/voynichese/pull/18). **Status naukowy**: `EXPLORATORY_NOT_CONFIRMED`. Nie udowodniono przedstawienia tego samego historycznego obiektu z dwóch perspektyw.

## 1. q9 ↔ q14: folio 67v versus foldout 85–86

Źródło: [GitHub Actions 37894901398](https://github.com/SonGohan231/voynichese/actions/runs/37894901398), artefakt `voynich-mv-native-geometry-20261009` (id `11599413309`), checksum artefaktu `sha256:64670a65f068a8d9baca20a55d4bf3e4843478669f80e19c51511b6dc0d65679`.

- 7 źródłowych skanów Yale weryfikowanych przy pobieraniu przez SHA256; 37 automatycznych kandydatów regionów promienistych.
- 186 zestawień spoza tej samej fizycznej grupy kart, w tym 31 par obejmujących 67v i fragmenty składki 85–86.
- Najwyższe eksploracyjne wyniki podobieństwa profili radialnych: 67v↔86v (część) **0.4627**, 67v↔85v/86r (rozkładana) **0.4481**.
- **0 z 186** par osiągnęło 5 dopasowanych punktów ORB pod wspólną sztywną transformacją 2D; negatywny *w tym konkretnym teście*, nie uniwersalna falsyfikacja identyczności obiektów z innych rzutów.
- Plansza 16 par z oryginalnych skanów: w artefakcie `targeted_source_native_contact_sheet.png`; szczegółowa lista/metadata w `targeted_pairs.json`.

Wniosek: Hough-kandydaty wykazują słabe podobieństwo rozkładu kreskowego, ale brak wzajemnie zgodnych źródłowych punktów geometrycznych; **MV1 maksymalnie jako motyw do ręcznej weryfikacji**, żadnej klasy MV2/3/4.

## 2. Cały rękopis: prześwietlenie 229 konturów

Źródło: [GitHub Actions 37895155729](https://github.com/SonGohan231/voynichese/actions/runs/37895155729), artefakt `voynich-mv-contour-source-review-20261009` (id `11600380698`, SHA256 `10158e21846687a084a3e72e51dbf2887b86453ab47c352a809a0127d74f4c8b`).

- 229 niezweryfikowanych propozycji maski obrysu, z nich **184** nieleżące blisko zewnętrznych granic obrazu, po odrzuceniu zdjęć okładek / braku grupy fizycznej.
- **41** par o tej samej maszynowej klasie konturu, osobnych grupach fizycznych, log-ratio boków ≤0,5 oraz dHash Hamming ≤18/64, w tym **24** porównania wewnątrz sekcji i **17** pomiędzy sekcjami.
- Zredundowane warianty tej samej pary zdjęć → 12 par do kontaktowej planszy. **0 z 12** osiągnęło ≥5 zgodnych natywnych punktów ORB pod sztywnym dopasowaniem 2D.
- Przykładowe propozycje *do wizualnej adjudykacji, nie potwierdzone podobne obiekty*: **32r↔8v (dHash 11/64)**, **55r↔34v (16/64)**, **93r↔18v (16/64, pomiędzy sekcjami)**, **39r↔21v (16/64)**, **7v↔101v część (16/64, pomiędzy sekcjami)**. DHash nie jest niezmienniczy względem perspektywy.
- Wyprodukowana plansza `contour_review_board.png`, raport `contour_screen_report.json`.

## 3. Obowiązkowe ograniczenia i niewykonane testy

1. 0 niezależnych ręcznych/ślepych adnotacji obiektów semantycznych, obrysów historycznych, krenelaży, kobiet, gwiazd, liczby sektorów, kierunku twarzy. Brak detekcji maszynowej ≠ zero rzeczywistych obiektów.
2. Nulle `color-only` i `text-only` **nie zostały ocenione** w tych dwóch wykonaniach. Kontrola `count-only` i `outline-only` jest opisowa i korzysta z pokrewnych sygnałów krawędziowych; nie jest niezależną statystyczną falsyfikacją. W próbie konturowej `count-only` w ogóle nie oceniono.
3. Niezależna replikacja na odłożonych fizycznych bifoliach i korekta wielokrotnych testów nadal nie są wykonane. Nie wolno wyliczać p-value ze wstępnie dobranych par ani opisywać dHash jako dowód obiektu 3D.
4. Wcześniejsze top-dHash porównania **30v↔31v**, **28v↔34v** itd. red-team uznał za granice fotografii/pergaminu. Ten protokół usuwa ROI przy brzegu zdjęć z głównej ścieżki, ale taki filtr może również ukrywać prawdziwe marginalne ornamenty; dla nich konieczny jest osobny tor.
5. EXP-2026-001 chroniony HELD-OUT pozostaje odrębny i nie był użyty do tworzenia tych wyników.

## 4. Następna próba falsyfikacyjna

Ręcznie oznaczyć źródłowe rysunki **32r↔8v**, **93r↔18v** oraz kandydatów **67v↔85/86** przez dwóch niezależnych anotatorów z pełnych JPEG, nie z wycinków znalezionych przez ten sam algorytm. Dla anatomicznych/architektonicznych obiektów policzyć topologię portów, pierścienie, rzeczywiste sektory/gwiazdki/kobiety/ornamenty i relacje przestrzenne; oddzielić transformacje płaskie i 2.5D, uwzględnić tło i styl skryby. Z góry zamrozić cztery null modele i korektę wielokrotnych porównań.

**Ostateczna klasa obecnych par:** tylko MV0/MV1 *propozycje przeglądu*, brak zaakceptowanego MV2/MV3/MV4. Wykonane porównania są realnymi wynikami analizy obrazów, lecz nie stanowią tłumaczenia ani odkrycia tożsamości obiektu.
