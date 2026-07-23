# Count-only model report

## Dane

Po zsumowaniu rozdzielonych paneli Barana i Byka otrzymujemy dziesięć znaków/tematów zodiakalnych:

`[29, 30, 30, 30, 30, 30, 30, 30, 30, 30]`

Suma elementów obwodowych: **299**.

## Kontrola kontraktu

Dostarczony skill podawał sumę 329, lecz jawnie wymienione liczności sumują się do 299. Niezależne opisy sekcji rozróżniają 299 nymf obwodowych od 303 wszystkich postaci po doliczeniu czterech figur centralnych.

## Porównanie prostych modeli

Wynik skryptu `scripts/count_model_comparison.py`:

| Model dokładny | Koszt opisowy (bity; niżej lepiej) | Status |
|---|---:|---|
| stałe 30 z jednym pominięciem | 5.55 | SURVIVES |
| niezależne 29/30, p=0.5 | 10.00 | DISFAVORED_EXACT_MODEL |
| ścisła alternacja 29/30 | 8.71 | DISFAVORED_EXACT_MODEL |
| dokładnie 28 mansji | 15.26 | FAIL_EXACT_MODEL |
| proste mapowanie na miesiące 30/31 | ≥10.56 | DISFAVORED_EXACT_MODEL |

## Interpretacja

Liczebność wspiera **rodzinę stałego 30**, ale nie rozróżnia:

- `M_FORMAT` — pojemność diagramu;
- `M_DEGREE` — 30 stopni znaku;
- `M_DECAN` — 3 × 10 stopni.

Nie jest to PASS dla żadnego z tych trzech modeli. To `INCONCLUSIVE_BETWEEN_M_FORMAT_M_DEGREE_M_DECAN`.

## Dokładnie jeden następny test

`BOUNDARY-PERIODICITY-10-vs-15-HELDOUT-01`.
