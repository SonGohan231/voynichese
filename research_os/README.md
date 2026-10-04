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
- `artifacts/AUTO_CANDIDATE_WORKLOAD_PROFILE.json` — wyłącznie profil obciążenia anotacyjnego, bez prawa użycia jako etykiety lub dowód hipotezy.
- `annotation/packets/` — dwa hermetyczne pakiety źródłowe dla niezależnych annotatorów; każdy obejmuje ten sam zamrożony zbiór 204 skanów treści, łącznie z częściami foldoutów, i nie zawiera kandydatur, predykcji ani splitu.
- `annotation/ui/` — lokalny edytor niezależnych adnotacji bez kandydatur i splitu.
- `annotation/acceptance_slot.*` oraz `custodian_receipt.*` — podpisywane bramki jednej pary i zewnętrznego receipt.
- `experiments/EXP-2026-001/scribe_assignments.json` — kompletna, wersjonowana mapa 204 rekordów do 94 grup skrybów, z trzema jawnymi grupami `MIXED_*`.
- `experiments/EXP-2026-001/section_scribe_strata.json` — zamrożony manifest sekcja+skryba dla przyszłego splitu.
- `adjudication/` — neutralny kontrakt adjudykacji oraz schemat zweryfikowanego wyniku.

Status dokumentów jest jawny. Prerejestracja jest projektem protokołu, nie wynikiem eksperymentu.

## Reprodukowalny audyt gotowości

Uruchom z katalogu głównego repozytorium:

```bash
python3 -m unittest discover -s research_os/tools -p 'test_*.py' -v
python3 research_os/tools/readiness.py atlas/records \
  --report research_os/experiments/EXP-2026-001/readiness_report.json
```

Kod wyjścia `2` oznacza bezpieczne niespełnienie bramek naukowych. W tym stanie split nie jest zapisywany, a HELD-OUT pozostaje nieodsłonięty. Dawna ścieżka `--split` jest twardo wyłączona także po `READY_FOR_SPLIT`, ponieważ zapisywała HELD_OUT jawnym tekstem. Produkcja wymaga zaszyfrowanego splitu custodiana i izolowanego pakietu TRAIN/VALIDATION bez pełnego uniwersum rekordów.

Po podpisanym freeze, receipt i zakończonej adjudykacji readiness sam ponownie sprawdza dokładne bajty pakietu i submission:

```bash
python3 research_os/tools/readiness.py atlas/records \
  --freeze-directory research_os/runs/EXP-2026-001/annotation-freeze-001 \
  --custodian-receipt custodian-receipt.json \
  --receipt-signature custodian-receipt.json.sig \
  --allowed-signers allowed_signers \
  --custodian-identity CUSTODIAN_IDENTITY \
  --adjudication-packet adjudication-packet.json \
  --adjudication adjudication-submission.json \
  --sealed-split-directory research_os/runs/EXP-2026-001/sealed-split-001 \
  --custodian-certificate custodian-encryption-cert.pem \
  --seed-file private-split-seed.bin \
  --strata-manifest custodian-section-strata.json \
  --report research_os/experiments/EXP-2026-001/readiness_report.json
```

Nie należy przekazywać gotowego raportu walidacyjnego jako substytutu danych wejściowych. `readiness.py` ponownie weryfikuje podpisany receipt, lokalny freeze, powiązanie receipt→pakiet, dokładne bajty adjudykacji, kompletny zbiór `FOLIO`, checksumy źródeł i co najmniej 15 niezależnych grup liści. Manifest sekcja+skryba musi spełniać `experiments/EXP-2026-001/section_strata.schema.json`, pokrywać dokładnie kwalifikowane rekordy i zawierać proweniencję z SHA-256 dla obu warstw; bez niego split jest odrzucany. Seed musi mieć co najmniej 32 losowe bajty, być zwykłym plikiem bez dostępu dla grupy/innych i nigdy nie trafić do repozytorium. Certyfikat jest publicznym certyfikatem szyfrującym custodiana; klucz prywatny pozostaje poza środowiskiem badawczym.

Wynikiem sealed workflow są: zaszyfrowany CMS `custodian-split.p7m`, publiczny manifest commitmentów oraz `model-development.json`. Ten ostatni zawiera wyłącznie TRAIN/VALIDATION, pseudonimowe ID HMAC i geometrię/etykiety adjudykacyjne; nie zawiera folio, ścieżek, source checksum, source refs ani rekordów HELD_OUT.
