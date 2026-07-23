# ZODIAC-30-ORDINAL-LABEL-TRANSFER-01 + sky 1404–1430

Pakiet wykonuje dwa rozdzielone zadania:

1. ślepy test, czy pozycja etykiety 1–30 przenosi właściwości tekstowe między znakami zodiaku Voynicha;
2. reprodukowalną rekonstrukcję ruchu Słońca, Księżyca i pięciu planet widocznych gołym okiem w latach 1404–1430 oraz ranking zdarzeń potencjalnie istotnych dla późnośredniowiecznego autora.

## Zasada rozdzielenia

Dane astronomiczne nie są ujawniane skryptowi testującemu etykiety. Wynik testu etykiet nie wpływa na wybór zdarzeń astronomicznych. Zapobiega to dopasowaniu tekstu pod rok lub planetę.

## Źródło etykiet

Reference Transliteration RF1b-er, Basic EVA:
`https://www.voynich.nu/data/RF1b-er.txt`

Zamrożone mapowanie znaków:

- Pisces: f70v2;
- Aries: f70v1 + f71r;
- Taurus: f71v + f72r1;
- Gemini: f72r2;
- Cancer: f72r3;
- Leo: f72v3;
- Virgo: f72v2;
- Libra: f72v1;
- Scorpio: f73r;
- Sagittarius: f73v.

W teście głównym kalibracją są Aries i Taurus. Held-out stanowią wszystkie zachowane znaki mające 30 etykiet. Znak z 29 etykietami jest testem jednego brakującego slotu.

## Ograniczenie

Numer locus w transkrypcji jest deterministycznym przybliżeniem porządku wizualnego, ale nie jest jeszcze certyfikowanym numerem stopnia zodiaku. FAIL odrzuca zatem dokładny model `REFERENCE_LOCUS_ORDER = DEGREE_ORDER`, a nie każdą możliwą geometrię 30 stopni.

## Astronomia

Skrypt używa kalendarza juliańskiego oraz Swiss Ephemeris/Moshier do obliczenia geocentrycznych długości ekliptycznych i lokalnych okoliczności zaćmień dla czterech punktów referencyjnych: Paryża, Mediolanu, Pragi i Wiednia. Punkty te nie są twierdzeniem o miejscu powstania rękopisu; reprezentują zachodnią i środkową Europę.

## Szczególny kandydat

Rok 1425 zawiera potrójną koniunkcję Jowisza i Saturna w Skorpionie. Zdarzenie było analizowane przez późnośredniowiecznych astrologów i zachował się jego horoskop. Jest to kandydat historycznie możliwy, ale nie jest automatycznie interpretacją f73r.
