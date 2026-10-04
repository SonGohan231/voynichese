# EXP-2026-001 — audit źródła mapy sekcji

Status: **AUTHORITATIVE_SECTION_MAP_RECOVERED / SCRIBE MAP STILL BLOCKS SPLIT**
Data audytu: 2026-10-04

## Sprawdzone źródła

1. Google Drive: `VOYNICH_MODEL_BOOTSTRAP_SORTED_INDEX_2026-05-17.md`, plik
   `1jHVEPehk3VmvVKW2iAK45i5f_wd0aIxq`.
2. Indeksowane pozycje `source_inventory`, rejestry projektu oraz wyszukiwania Drive:
   `folio section`, `Currier quire mapping` i wcześniejsze warianty zapytań o
   klasyfikację sekcji.

Indeks jest miarodajnym punktem wejścia do wcześniejszych prac i potwierdza istnienie
materiałów Spatial/XML/Color Gate, lecz nie zawierał kompletnej mapy. Następnie sprawdzono
oficjalny katalog Beinecke MS 408, który publikuje sześć rozłącznych zakresów foliów.
Zakresy zapisano w `research_os/sources/beinecke_ms408_section_register.json`, a
`build_section_assignments.py` przypisał deterministycznie wszystkie 204 rekordy treści.

Plik `tm0696-description.pdf` z Drive został sprawdzony i odrzucony: opisuje inny
rękopis (*Recipes and Extracts...*, 101 foliów), a nie Beinecke MS 408. Nie jest dowodem
dla sekcji Voynicha.

## Decyzja

Mapa sekcji jest gotowa jako `DATA`, ale produkcyjny split nadal jest blokowany przez brak
kompletnej mapy skrybów wymaganej w prerejestracji. Nie rekonstruujemy jej z pamięci.

Klasyfikacja w manifeście jest wyłącznie `FACT` albo `DATA`; nie wolno użyć etykiety
sekcji pochodzącej wyłącznie z hipotezy lub interpretacji. Poziom złożoności nie jest
częścią źródła zewnętrznego — pipeline wylicza go mechanicznie z zamrożonej adjudykacji.
