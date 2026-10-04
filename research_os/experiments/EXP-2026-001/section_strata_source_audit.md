# EXP-2026-001 — audit źródła mapy sekcji

Status: **MISSING_AUTHORITATIVE_SECTION_MAP / SPLIT BLOCKED**  
Data audytu: 2026-10-04

## Sprawdzone źródła

1. Google Drive: `VOYNICH_MODEL_BOOTSTRAP_SORTED_INDEX_2026-05-17.md`, plik
   `1jHVEPehk3VmvVKW2iAK45i5f_wd0aIxq`.
2. Indeksowane pozycje `source_inventory`, rejestry projektu oraz wyszukiwania Drive:
   `folio section`, `Currier quire mapping` i wcześniejsze warianty zapytań o
   klasyfikację sekcji.

Indeks jest miarodajnym punktem wejścia do wcześniejszych prac i potwierdza istnienie
materiałów Spatial/XML/Color Gate, lecz nie zawiera kompletnej, wersjonowanej mapy
każdego kwalifikowanego `record_id`/folio do sekcji. Wyniki wyszukiwania również nie
ujawniły takiego artefaktu.

## Decyzja

Nie rekonstruujemy mapy z pamięci, standardowych zakresów foliów ani interpretacji
ilustracji. Produkcyjny split jest blokowany, dopóki custodian nie dostarczy manifestu
zgodnego z `section_strata.schema.json`, obejmującego dokładnie kwalifikowany zbiór i
zawierającego referencję oraz SHA-256 źródła dla każdego przypisania.

Klasyfikacja w manifeście jest wyłącznie `FACT` albo `DATA`; nie wolno użyć etykiety
sekcji pochodzącej wyłącznie z hipotezy lub interpretacji. Poziom złożoności nie jest
częścią źródła zewnętrznego — pipeline wylicza go mechanicznie z zamrożonej adjudykacji.
