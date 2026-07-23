# State reconciliation — zodiac 30

## Zamrożone liczności

| Panel | Znak / rola | N | Status kompozycji |
|---|---:|---:|---|
| f70v2 | Pisces | 29 | single_29 |
| f70v1 | Aries_A | 15 | split_half |
| f71r | Aries_B | 15 | split_half |
| f71v | Taurus_A | 15 | split_half |
| f72r1 | Taurus_B | 15 | split_half |
| f72r2 | Gemini | 30 | full_30 |
| f72r3 | Cancer | 30 | full_30 |
| f72v1 | Leo | 30 | full_30 |
| f72v2 | Virgo | 30 | full_30 |
| f72v3 | Libra | 30 | full_30 |
| f73r | Scorpio | 30 | full_30 |
| f73v | Sagittarius | 30 | full_30 |

**Suma: 299.**

## Wcześniejsze testy

| Test / model | Status | Co dokładnie odrzucono |
|---|---|---|
| wspólna siatka 30 × 12° | FAIL_EXACT_MODEL | jedna globalna, równomierna siatka o wspólnej fazie/orientacji |
| PTOLEMY-1420-ABSOLUTE-SLOT-TRANSFER-HELDOUT-01 | FAIL_EXACT_MODEL | prosty transfer absolutnych slotów do gwiazd katalogowych |
| PTOLEMY-1420 one-star-one-entry | FAIL_EXACT_MODEL | bezpośrednia korespondencja jednego elementu z jedną gwiazdą |
| global brightness threshold | FAIL_EXACT_MODEL | jeden globalny próg jasności wybierający odpowiadające gwiazdy |
| HISTORICAL-SKY-vs-UNIFORM-30-HELDOUT-01 | BLOCKED_DATA_GATE | wersja topologiczna nie została otwarta bez atlasu 299 |

## Stan modeli

- `M_FORMAT`: żywy;
- `M_DEGREE`: żywy, ale prosta globalna siatka 12° została osłabiona;
- `M_DECAN`: żywy, jeszcze nieprzetestowany na przenośnych granicach co 10 pozycji;
- `M_LUNAR`: żywy; należy rozdzielić 29–30 dni od 28 mansji;
- `M_CALENDAR`: żywy;
- `M_SKY`: osłabiony w wersjach prostych, topologia historyczna nadal nierozstrzygnięta;
- `M_FREE`: żywy jako null lokalnego layoutu.

## Zakaz dryfu

Nie wolno ponownie uruchamiać odrzuconej siatki 30 × 12°, progu jasności ani one-star-one-entry bez nowej, jawnie różnicującej predykcji.
