# Voynich Research OS

Ten katalog rozpoczyna reprodukowalną warstwę badawczą zgodną z master promptem z 2026-10-04.

## Stan startowy

- Repozytorium: `SonGohan231/voynichese`, gałąź bazowa `master`, commit `a909dd6`.
- Istniejąca gałąź przestrzenna: `research/spatial-perspective-layer-model` (`50e5d10`).
- Atlas zawiera 206 rekordów stron oraz schemat i raport walidacji.
- Główny indeks wcześniejszego projektu został odnaleziony na Google Drive.
- Finalna literalizacja, alfabet, fonetyka i tłumaczenie pozostają zablokowane (`readyForLiteralization = 0`).
- Pierwsza misja Agent OS: `ce415186-4323-4d79-8f73-b8e124585264`, zakończona jako `INCONCLUSIVE`.
- Bieżąca misja wykonawcza Agent OS: `0856f1aa-60a8-4fea-a82e-8d15239f5542`.

## Artefakty tej inicjalizacji

- `tool_audit_2026-10-04.md` — faktycznie sprawdzone narzędzia i ograniczenia.
- `recovered_state_2026-10-04.md` — odtworzony stan poprzedniej pracy.
- `dyrygent_max_audit_2026-10-04.md` — częściowy audyt MAX wraz z dowodem awarii planera.
- `evidence_register.csv` — początkowy rejestr dowodów i hipotez.
- `experiments/EXP-2026-001/preregistration.md` — zamrożony szkic pierwszego testu.
- `experiments/EXP-2026-001/manifest.json` — maszynowy manifest stanu eksperymentu.
- `artifacts/AUTO_CANDIDATE_FINAL_V1.json` — proweniencja pełnego przebiegu 206 automatycznych kandydatur; nie są ground truth ani blind annotations.
- `annotation/packets/` — dwa hermetyczne pakiety źródłowe dla niezależnych annotatorów; każdy obejmuje ten sam zamrożony zbiór 183 foliów i nie zawiera kandydatur, predykcji ani splitu.

Status dokumentów jest jawny. Prerejestracja jest projektem protokołu, nie wynikiem eksperymentu.

## Reprodukowalny audyt gotowości

Uruchom z katalogu głównego repozytorium:

```bash
python3 -m unittest discover -s research_os/tools -p 'test_*.py' -v
python3 research_os/tools/readiness.py atlas/records \
  --report research_os/experiments/EXP-2026-001/readiness_report.json
```

Kod wyjścia `2` oznacza bezpieczne niespełnienie bramek naukowych. W tym stanie split nie jest zapisywany, a HELD-OUT pozostaje nieodsłonięty. Split można zmaterializować dopiero po statusie `READY_FOR_SPLIT`, z jawnie zamrożonym seedem i ścieżką `--split`.
