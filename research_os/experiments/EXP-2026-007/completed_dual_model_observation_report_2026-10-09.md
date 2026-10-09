# EXP007 — wyniki dwóch niezależnych przebiegów rzeczywistego modelu obrazu

**Zbiór:** 18 SHA-zweryfikowanych wycinków z 9 źródłowych fotografii Yale MS408, wybrane deterministycznie jako pierwsze dwa ROI na zdjęcie **przed** rozpoznawaniem ich treści. **Uruchomienie końcowe:** [GitHub Actions #37911408289](https://github.com/SonGohan231/voynichese/actions/runs/37911408289): 4/4 jobs **SUCCESS**, praca na 18 cropach dla każdego modelu, **36 prawdziwych wyników modelowych, 0 zweryfikowanych historycznie identyfikacji**.

Dwa wcześniejsze nieudane uruchomienia workflow #37911140161 i #37911193732 przerwano z powodu błędnej ścieżki rozpakowywania źródłowego ZIP-a — nie z powodu niezgodności modeli. Naprawa w commicie `91335e359409c2ecb32c7ffa5d3c42f72ea877fc` pozwoliła ukończyć oba przebiegi i audyt. Te awarie pozostają widoczne.

| Zamrożony fragment | BLIP (oryginalne słowa modelu, opis niezatwierdzony) | CLIP (najwyższy prompt, względny wynik) |
| --- | --- | --- |
| 67v:R1 | "a drawing of a man ' s head and hands" | celestial_symbols 0.649 |
| 67v:R2 | "a drawing of a sun with stars and a face" | celestial_symbols 0.964 |
| 85v/86r:R1 | "a drawing of a circular design with blue and white circles" | round_diagram 0.523 |
| 85v/86r:R2 | "a drawing of a circle with a man in the center" | celestial_symbols 0.609 |
| 86v fragment:R1 | "an old manuscript with writing on it" | handwriting 0.840 |
| 86v fragment:R2 | "an old manuscript with writing on it" | handwriting 0.814 |
| 32r:R1 | "the green paint is being applied on the floor" | plant_part 0.831 |
| 32r:R2 | "a piece of green paint on the ground" | plant_part 0.518 |
| 8v:R1 | "a piece of paper with green paint on it" | plant_part 0.389 / UNKNOWN |
| 8v:R2 | "a close up of a green leaf on a white background" | nonsemantic_markings 0.337 / UNKNOWN |
| 93r:R1 | "a painting of a woman with green hair" | plant_part 0.542 |
| 93r:R2 | "a piece of green tile with a white circle on it" | nonsemantic_markings 0.490 |
| 18v:R1 | "a close up of a tile with green leaves on it" | celestial_symbols 0.260 / UNKNOWN |
| 18v:R2 | "an old book with a drawing of a flower on it" | plant_part 0.960 |
| 55r:R1 | "a painting of a plant with leaves on it" | human_figure 0.738 |
| 55r:R2 | "an old manuscript with writing on it" | handwriting 0.716 |
| 34v:R1 | "a drawing of a flower on a wall" | human_figure 0.691 |
| 34v:R2 | "a drawing of a rabbit on a wall" | human_figure 0.558 |

**Wszystkie wpisy powyżej to rzeczywiste wnioski niesprawdzonych modeli, nie obserwacja rękopisu po niezależnej ocenie ekspertów.** Stwierdzenia o „farbie na podłodze”, „króliku” oraz „kobiecie z zielonymi włosami” są potencjalnymi halucynacjami. Dla pozornie interesującej pary 67v↔86v w tych wycinkach CLIP wybrał różne klasy (celestial vs handwriting), a BLIP 86v opisał wyłącznie jako pismo. Nie jest to dowód, że inne fragmenty nie zawierają wspólnych motywów.

### Ścisły wykaz dowodów

- [Run #37911408289](https://github.com/SonGohan231/voynichese/actions/runs/37911408289) — 4 z 4 jobs SUCCESS.
- `exp007-frozen-Yale-source-pixels`, ZIP artifact ID **11607325734**, digest SHA256 `c1b45fdaa0afb23276a8c95bcd069694325a987a9b29e079f687308dece071dc`.
- `exp007-real-blind-blip-model-A`, artifact ID **11607470708**, digest SHA256 `d67caed5a4c4be7d25ae80d338ca8f8901b1f06ae4fe271021a66e4e1f052188`.
- `exp007-real-blind-clip-model-B`, artifact ID **11607306118**, digest SHA256 `bcfe6a81642489c11ad868950f46e4de29c9942cdc2416f3cb6d0053d054b0ee`.
- `exp007-independent-AI-vision-disagreement-audit`, artifact ID **11606533698**, digest SHA256 `28d0981a48a137b520607ed1077a94262ae8abb0be2ca01c7de8ca2f9ddb399b`.
- QA log: `EXP007_AUDIT_PASS 18 REAL_MULTIMODAL_OBSERVATIONS 36 HUMAN_SEMANTIC_VALIDATIONS 0`; `EXP007_AI_INDEPENDENCE_QA_PASS 18 images, 2 distinct real models, human annotations pending`.

### Co trzeba zrobić przed identyfikacją obiektu

1. Ponieważ oba AI mogły popełnić błędy i były trenowane na podobnych ogólnych danych, nadaj wynikowi `AI_CANDIDATE_ONLY`. Dwie różne architektury są niezależne informacyjnie na poziomie dostępu do wyniku, ale **nie** dwoma ludzkimi ekspertami.
2. Pobrać ponownie oryginalne JPEG Yale, połączyć obserwacje z **pełnym obiektem w pełnej stronie**, a nie z neutralnym/częściowym ROI. Zrobić osobne ślepe ręczne polygony obiektów, landmarków i typów (wieża, roślina, koło, postać, UNKNOWN).
3. Sprawdzić zgodność historycznych obiektów nie po samym podpisie BLIP/CLIP, tylko po topologii i relacjach przestrzennych na sprawdzonych poligonach, kontrolach stylu/sekcji/bifolium, bez niezweryfikowanych perspektyw 2.5D.
4. Dopasować sąsiednie napisy **dopiero po** sprawdzonym odwzorowaniu współrzędnych transkrypcji↔Yale (EXP006 text registration gate 0/9 zweryfikowanych zdjęć). `TEXT_ONLY` pozostaje `NOT_ASSESSED`.
5. **Brak obiektów MV2+/MV3/MV4**, brak potwierdzonego odczytania manuskryptu. `EXP-2026-001` HELD-OUT nie został dotknięty. PR zachować jako szkic.

**Metodologiczne ograniczenie reprodukowalności:** pliki modelowe pobrano z domyślnych rewizji HuggingFace, więc zapis samych identyfikatorów modeli bez hashy rewizji nie wystarcza do przyszłej bitowej replikacji. Archiwizowane surowe wyniki oraz hashe ZIP i obrazu stanowią dowód wykonania tej sesji.
