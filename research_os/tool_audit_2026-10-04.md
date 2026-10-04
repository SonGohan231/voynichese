Failed to connect to bus: Operation not permitted
# Audyt narzędzi — 2026-10-04

## TelefonMCP2 / Agent OS

Faktycznie sprawdzono publiczne endpointy diagnostyczne TelefonMCP2 3.0.0.

- Agent OS / Railway / Neon: połączony.
- Worker: zdrowy, tryb `qualified-real`, provider `gpt-6-luna`.
- Rejestr: 14 agentów, w tym 11 `persistent` i 3 `candidate`.
- Przydatni agenci trwa­li: Mission Architect, Research Scout, Evidence Judge, Adversarial Critic, Synthesis Lead, Artifact Integrity Auditor, Run Quality Auditor, Workflow State Guardian i Execution Boundary Guard.
- Agent Architect jest kandydatem, nie należy uznawać go automatycznie za zakwalifikowanego specjalistę.
- Misja badawcza została rzeczywiście utworzona i zakończona: `ce415186-4323-4d79-8f73-b8e124585264`.
- Werdykt misji: `INCONCLUSIVE`; zapisano trzy raporty wykonania i ich digesty.
- Zarejestrowany koszt misji: 0,061238 USD, z czego 0,06 USD to rezerwa górnej granicy dla etapu Dyrygenta, a nie potwierdzona opłata API.
- Ograniczenie: router wybrał Agent Architect do planowania i syntezy mimo statusu `candidate`; wymaga to kontroli jakości i nie jest dowodem kwalifikacji.

## Dyrygent

Dyrygent jest dostępny jako integracja hosta. Dwie próby audytu zakończyły się awaryjnym fallbackiem Astra po błędzie parsera planera. Uzyskano użyteczne uwagi metodologiczne, ale nie pełny wieloagentowy audyt. Wynik zapisano w misji Agent OS jako częściowy, z jawnym ograniczeniem.

## Voynich Spatial Lab / Sites

- Projekt Sites `Voynich Spatial Lab` istnieje i jest aktywny, wersja 6.
- Dostęp: prywatny/custom, właściciel dostępny w bieżącym workspace.
- Witryna nie deklaruje serwera MCP; nie można obecnie pobierać danych laboratoryjnych przez konektor Sites.
- Zewnętrzny URL wymaga logowania ChatGPT.

## Google Drive

- Odnaleziono `VOYNICH_MODEL_BOOTSTRAP_SORTED_INDEX_2026-05-17.md`.
- Odczytano jego pełną treść oraz raport transferu `VOYNICH_CURRENT_TRANSFER_EXECUTION_REPORT_20260517.md`.
- Nie pobrano masowo ZIP-ów ani dużych obrazów.

## GitHub

- Kanoniczne repo użytkownika: `SonGohan231/voynichese` (uprawnienia push/admin potwierdzone przez konektor).
- Repo sklonowano lokalnie bez modyfikowania zdalnej historii.
- Zidentyfikowano istniejącą gałąź `research/spatial-perspective-layer-model` oraz atlas 206 stron.

## Bramki

Eksperyment wizualny nie może otrzymać statusu RUNNING, dopóki nie zostaną zweryfikowane: dane obrazowe/cropy, definicje jednostek analizy, proweniencja oraz zamrożony podział TRAIN/VALIDATION/HELD-OUT.
