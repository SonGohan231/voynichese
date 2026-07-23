# Protokół decyzji

## PASS

PASS dla modelu wymaga spełnienia wszystkich z góry zamrożonych kryteriów, w tym held-out i pełnego kosztu modelu.

## FAIL

FAIL dotyczy dokładnej implementacji i zakresu prerejestracji. W raporcie wskaż:

- co dokładnie zostało odrzucone;
- które szersze wersje nadal przeżywają;
- czy wynik osłabia model ogólnie, czy tylko konkretną wersję.

## INCONCLUSIVE

Użyj, gdy:

- metryki dają sprzeczne wyniki;
- atlas nie przeszedł bramy;
- moc jest zbyt mała;
- wynik zależy od jednej reprezentacji;
- dodatni efekt nie pokrywa kosztu modelu;
- held-out jest niepełny lub naruszony;
- kontrola artefaktu daje równie dobry wynik.

## INVALID

Użyj, gdy:

- zmieniono kryteria po otwarciu held-out;
- źródło lub SHA nie zgadza się z zamrożeniem;
- punkty atlasu zostały dopasowane przy znajomości katalogu historycznego;
- doszło do przecieku między kalibracją i held-out;
- wynik nie jest reprodukowalny z zapisanych danych.

## Minimalne dane raportowe

- nazwa i wersja modelu;
- zamrożona próbka;
- kalibracja i held-out;
- metryka główna;
- null i liczba permutacji;
- seed;
- pełny MDL;
- wyniki per panel;
- kontrole negatywne;
- ograniczenia;
- wpływ na każdy model.
