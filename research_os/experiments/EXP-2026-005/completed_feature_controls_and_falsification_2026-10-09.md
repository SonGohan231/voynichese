# EXP005 — audyt wykonania, wyniki i bramka falsyfikacji (2026-10-09)

**Misja Agent OS:** `0869cf9d-fdb0-40cd-9339-a64e2ea73b42`; **metodologiczny red-team Dyrygent V3.8.1:** wykonany odrębnie w tej sesji. **Repo:** `SonGohan231/voynichese`, gałąź `research/mv-semantic-review-20261009`, draft PR #19. **Naukowy werdykt:** `EXPLORATORY / INCONCLUSIVE / NO VERIFIED SAME OBJECT`.

## Zweryfikowane i powtarzalne wyniki na skanach źródłowych

| Kod | GitHub Actions | Artefakt dowodowy | Wynik techniczny |
| --- | --- | --- | --- |
| Stage 0 | [37896354551](https://github.com/SonGohan231/voynichese/actions/runs/37896354551) PASS | `voynich-exp005-native-semantic-source-pack` (11599964081) | 9 źródłowych zdjęć Yale, 27 oryginalnych fragmentów, 5 par wizualnych; prawdziwe źródła SHA-256 |
| Stage 1 | [37904701474](https://github.com/SonGohan231/voynichese/actions/runs/37904701474) PASS | `voynich-exp005-multifamily-controls` (11603579263) | 35 par fotografii z różnych grup fizycznych, w tym 5 wytypowanych wcześniej i 30 kontrolnych; dwa algorytmy segmentacji; trzy opisowe cyfrowe proxy |
| Stage 2 | [37905085696](https://github.com/SonGohan231/voynichese/actions/runs/37905085696) PASS | `voynich-exp005-channel-redteam` (11604072065) | Rozdzielenie count-only, outline-only, color-only; kontrola tych samych 9 par okien przy każdym porównaniu; 0 zatwierdzonych tożsamości |
| Stage 3 | [37905464883](https://github.com/SonGohan231/voynichese/actions/runs/37905464883) PASS | `voynich-exp005-paper-roi-ablation` (11604541169) | Ablacja koloru, pseudo-tła pergaminu, oraz wybór pierwszego neutralnego ROI każdego zdjęcia |

Wcześniejszy [nieudany workflow 37904983016](https://github.com/SonGohan231/voynichese/actions/runs/37904983016) spowodowany był wyłącznie błędnym założeniem 9 zdjęć w dwu-zdjęciowym teście jednostkowym; poprawiony i **uruchomiony ponownie** workflow #37905085696 osiągnął PASS. Nie usunięto śladu wcześniejszej porażki.

## Tablica głównych porównań

**Wartości 0–1 to arbitralne, opisowe cyfrowe rankingi, a NIE pewność historyczna i NIE p-value.** Pary badawcze były uprzednio wyselekcjonowane. Kontrole w tej samej relacji sekcyjnej nie są niezależnymi i wymiennymi próbkami wszystkich historycznych przedmiotów.

| Para | Złożony score | Kontrole ≥ score | Count ≥ | Outline ≥ | Color ≥ |
| --- | ---: | ---: | ---: | ---: | ---: |
| **67v↔86v fragment** | **0.84983** | **0/22** | 4/22 | 1/22 | 8/22 |
| 34v↔55r *kontrola* | 0.83373 | 1/8 | 2/8 | 0/8 | 5/8 |
| 32r↔8v | 0.82761 | 1/8 | 7/8 | 2/8 | **0/8** |
| 18v↔93r | 0.74511 | 15/22 | 9/22 | 3/22 | 18/22 |
| 67v↔85v/86r panorama | 0.69782 | 18/22 | 20/22 | 14/22 | 2/22 |

## Rzeczywista próba falsyfikacji przewagi 67v↔86v

| Ablacja, wszystkie zreplikowane na całych 35 parach | 67v↔86v score | Kontrole ≥ score | Interpretacja metodologiczna |
| --- | ---: | ---: | --- |
| Bez koloru, najlepsza z 9 par wycinków | 0.821753 | 0/22 | Strukturalny cyfrowy wzór nie jest wyłącznie wynikiem koloru; pozostaje selekcja „best of nine” |
| Mediana LAB 25% najjaśniejszych pikseli jako przybliżenie tła fotografii | 0.975310 | 3/22 | Tła są zbliżone; nie ustalono, ile podobieństwa przypada na pergamin/ekspozycję |
| **Pierwszy wycinek neutralnej siatki z góry, bez wyboru najlepszego** | **0.519459** | **22/22** | Po zamrożeniu neutralnego okna przewaga znika; nie dowodzi to braku wspólnego obiektu w innym miejscu |

Inne ważne ablacje: **34v↔55r (kontrola)** bez koloru 0.854735 (2/8), bardziej przypomina się w tej skali niż interesująca nas 67v↔86v 0.821753; w pierwszym neutralnym oknie 0.760131 (5/8). **32r↔8v** bez koloru 0.787478 (5/8) — pierwotny dobry wynik mógł być napędzany cyfrowymi barwami. **67v↔85v/86r panorama** bez koloru 0.631525 (20/22), neutralny wycinek 0.512511 (22/22) — nie ma podstaw, by uznać ją za szczególny dopasowany graf.

W wynikach ablacji najlepsza para 67v↔86v pochodziła z **NEUTRAL_COVERAGE_GRID_NOT_OBJECT** po obu stronach, ale tylko po wybraniu najlepszego z 9 przecięć okien. Nie wystarczy, by przypisać wykrytemu fragmentowi kategorię „wieża” czy „rozeta”; etykieta neutralnego okna znaczy jedynie fragment zdjęcia, nie obiekt.

## Kontrola niezależna Dyrygent V3.8.1 — przyjęte ostrzeżenia

1. `0/22` nie oznacza p=0 ani automatycznie istotności: 22 kontrole nie są niezależnymi losowymi jednostkami, były dobrane po preselekcji, a wynik to maksimum z 9 możliwych ROI.
2. Dwie segmentacje pikseli to pomiar stabilności algorytmu, a nie dwie niezależne oceny ludzkie. Count, outline i color nie są trzema niezależnymi źródłami dowodu — bazują na tym samym materiale graficznym.
3. Podobieństwo negatywnej pary 34v↔55r oraz niestabilność z góry wybranego wycinka obniżają diagnostyczność algorytmu dla tezy o tożsamości.
4. GitHub Action PASS i oryginalne SHA JPEG potwierdzają wykonanie i tożsamość źródła, nie poprawność przypisanej semantyki.
5. `TEXT_ONLY` nie został wykonany ze względu na brak przywiązania współrzędnych transkrypcji do danego graficznego ROI; twierdzenia o tych samych słowach obok identycznych obiektów nie mają podstaw.
6. Brak dwukrotnych ślepych **ludzkich** oznaczeń i niezależnej ekspertyzy artystyczno-kodykologicznej. Krytyka Dyrygenta nie jest niezależną replikacją danych ani zastępstwem arbitra specjalisty.

## Trzy następne testy, z góry jawnie sformułowane

1. **Powtórzenie rankingów na zablokowanych grupach bifoliów:** zamrozić wszystkie wskazane ROI, dopasować sekcje i uciążliwości zdjęciowe, odtworzyć wcześniejszą procedurę wyboru maksimum z dziewięciu po obu stronach kontroli. Wymagana niepostselekcyjna kalibracja na nowych fizycznych jednostkach oraz właściwa korekta wielokrotnych sprawdzeń; jeśli brak mocy statystycznej ⇒ `INCONCLUSIVE`.
2. **Autentyczny graf rysunku:** dwóch zaślepionych anotatorów zaznacza ciągłe linie, naroża, punkty przyłączenia, rozgałęzienia, liczby sektorów i ewentualne wieże/figury na oryginalnych JPEG dla pary 67v–86v, niezależnie od starego algorytmu; porównanie z fałszywymi kopiami z tej samej sekcji i innymi 2D motywami; wiarygodność między obserwatorami, analiza spornych miejsc, bez wymuszania zgodności.
3. **Prospektywna replikacja:** pozostawić oddzielny, jawny zbiór **nowych** stron/bifoliów poza zastrzeżonym EXP001 HELD-OUT, przy zamrożonych współczynnikach, wyborze wycinków i progu, następnie sprawdzić, czy sygnał przewiduje uprzednio zdefiniowane topologiczne cechy niewidzianych ilustracji. Brak wyniku ≠ brak historycznej tożsamości, lecz brak potwierdzenia tej procedury.

### Granica wniosku

**Obecny dopuszczalny werdykt:** `MV1 / REQUIRES_NATIVE_SEMANTIC_REVIEW` wyłącznie w odniesieniu do pojedynczych podobieństw motywów; **MV2/MV3/MV4 = 0 potwierdzonych**. Nie ma dowodu, że dwie strony są widokami tej samej historycznej budowli/mapy/rosnącej rośliny. **EXP-2026-001 HELD-OUT pozostaje zamknięty**; nie wykorzystywano go w nowych skryptach. To kończy bieżącą komputerową kontrolę preselektowanych obrazów, a nie całość badania manuskryptu.
