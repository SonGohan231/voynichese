# f78r — warstwowa rekonstrukcja źródłowa, wersja robocza

Zakres tej aktualizacji: jedna strona f78r, 38 oddzielnych elementów w pliku Blender i GLB.
Nowe: 15 objętości widocznych postaci, 2 części wody, 2 obrzeża oraz 3 połączenia przepływów.
Pozostałe 16 elementów to wcześniejsze robocze struktury, tuleje i odcinki przepływów,
złożone ponownie według współrzędnych źródła. Żaden z nich nie jest certyfikowaną rekonstrukcją 1:1.

## Kolory i ornamenty
Jeden oryginalny skan JPEG jest osadzony w pliku. Nie ma wygenerowanych wzorów ani dopisanego pisma.
Materiał źródłowy jest unlit, a Blender używa Standard/sRGB bez zmiany ekspozycji.
SHA-256: 6e0f3449af81da50a04a060937fdcdb4c2e2b93be98bcb9b4bd523c1e1b35ce5.
Oryginalne bajty tekstury potwierdzono wewnątrz GLB. Wszystkie 206 skanów projektu
porównano z rejestrem SHA-256: zgodne. Nie jest to pomiar barwy fizycznego pigmentu ani test ekranu Questa.

## Wyniki i ograniczenia
- Oba baseny: 1 159 460 porównanych pikseli wnętrza, zerowa różnica RGB.
- Cały zespół: 1 474 161 porównanych pikseli wnętrza; 20 różniących się pikseli na tulejach.
  Największa różnica kanału: 121/255; średnia: 0,000754/255. Nie wolno zatajać maksimum za średnią.
- Maski brzegowe nie są zatwierdzone. Siatki nowych postaci są próbkowane co 2 piksele.
  Przy obrysie górnego zespołu: 801 brakujących i 765 nadmiarowych pikseli względem maski;
  przy dolnym: 918 brakujących i 909 nadmiarowych. Sama maska jest ręcznym kandydatem.
- Każda nowa siatka przeszła kontrolę zamknięcia i dodatniej objętości.
- Są to zaokrąglone warstwy oparte na widocznych sylwetkach, nie pełne anatomiczne modele ciał.
  Zakryte kończyny, plecy, głębokość basenów i tyły konstrukcji nie są znane z rysunku.
- Rozdział wody i obrzeża jest roboczy; nie dowodzi fizycznej konstrukcji zbiornika.
- Sąsiedni tekst nie został tutaj odtworzony jako odrębne bryły; pozostaje w skanie źródłowym.
- Nie przebudowano wszystkich pozostałych stron ani wszystkich wcześniejszych 254 wpisów katalogu.
- Nie aktualizowano ani nie publikowano APK w ramach tej poprawki.

## Edycja
Otwórz f78r_Baseny_Postacie_Woda_Obrzeza.blend w Blenderze 4.5 lub nowszym.
Kolekcje: postacie; woda i obrzeża; kanały i konstrukcje robocze.
Dla każdej postaci klucz kształtu Splaszczenie_do_zrodla reguluje przejście od roboczej
objętości (0) do cienkiej warstwy (1), bez przesuwania współrzędnych obrazu.
Kamera Kontrola_ortograficzna_calej_strony pozwala porównać układ ze źródłem.
Rysunki upper/lower_source_vs_model pokazują po lewej skan, po prawej rzeczywisty render.
upper_exploded pokazuje odsunięte postacie; jest to widok kontrolny, nie historyczny układ.
GLB zachowuje oddzielne siatki i kolory, ale nie zawiera suwaków głębi z pliku Blender.

## Dalsze konieczne prace
Dokładniejsze maski konturów, wyjaśnienie 20 pikseli tulei, zatwierdzenie rozdziału warstw,
ręczne modelowanie rzeczywistych przestrzennych kształtów z jawnymi założeniami,
kontrola obiekt po obiekcie pozostałych stron. Tego pakietu nie należy przedstawiać
jako spełniającego żądanie pełnej rekonstrukcji całego manuskryptu 1:1.
