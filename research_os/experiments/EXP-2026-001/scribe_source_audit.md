# EXP-2026-001 — audit źródła mapy skrybów

Status: **VERSIONED_COMPLETE_SCRIBE_MAP_RECOVERED / ANNOTATION STILL BLOCKS SPLIT**  
Data audytu: 2026-10-04

## Źródło

Odzyskano kompletną, wersjonowaną mapę stron i paneli do rąk skrybów z Zandbergen–Landini `ZL3b-n.txt`, IVTFF 2.0, wersja 3b z 13.05.2025. Pole `$H` przechowuje klasyfikację rąk opartą na pracy Lisa Fagin Davis.

Zamrożona proweniencja:
- źródło: `https://www.voynich.nu/data/ZL3b-n.txt`;
- SHA-256: `bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc`;
- przypięte lustro: `matthewdgreen/cipher_benchmark`, commit `729aad62d12483c549e64a2541d4f9255538c8cf`;
- Git blob: `2a4533ab9bdfa85db9bad602d590978953055df1`;
- lokalny rejestr: `research_os/sources/zl3b_scribe_source.json`.

Źródło jest traktowane jako `DATA`, a nie niepodważalny `FACT`.

## Mapowanie do kanonicznego uniwersum

`build_scribe_assignments.py` mapuje nagłówki `$H` do 204 rekordów treści rękopisu, weryfikuje SHA-256 i agreguje ręce na tej samej nierozdzielnej jednostce co splitter: connected manuscript leaf group.

Wynik:
- 204 rekordy;
- 94 leaf-groups;
- Hand 1: 49 grup;
- Hand 2: 20 grup;
- Hand 3: 14 grup;
- Hand 4: 5 grup;
- Hand 5: 3 grup;
- `MIXED_1_5`: 1 grupa — folio 57;
- `MIXED_2_4`: 1 grupa — połączony foldout 85–86, w tym `fRos`;
- `MIXED_2_3`: 1 grupa — folio 115.

Etykiety `MIXED_*` oznaczają agregację znanych rąk w nierozdzielnej grupie, a nie dodatkowych skrybów. Nie wolno rozbijać tych grup pomiędzy TRAIN, VALIDATION i HELD-OUT ani zastępować ich arbitralnie ręką dominującą.

Dla `f115r` zachowano źródłowe `$H=@`: linie 1–12 należą do Hand 2, pozostała część do Hand 3. Cały liść 115 ma zatem etykietę grupową `MIXED_2_3`.

## Decyzja

Poprzedni bloker `MISSING_AUTHORITATIVE_FOLIO_TO_SCRIBE_MAP` jest zamknięty. Gotowy manifest `section_scribe_strata.json` pokrywa dokładnie 204 rekordy i łączy zamrożoną mapę sekcji z mapą skrybów.

Nie oznacza to `READY_FOR_SPLIT`. EXP-2026-001 pozostaje `DRAFT / NOT RUN`, ponieważ rekordy nadal nie mają wymaganej niezależnej anotacji, adjudykacji i kompletnego podpisanego łańcucha dowodowego. HELD-OUT pozostaje nieujawniony.
