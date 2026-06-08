# Notebooki i eksperymenty

Lokalna kopia laboratoriów znajduje się w `C:\Users\adamy\PycharmProjects\translation-labs`. Te materiały nie są podstawą projektu i nie muszą być przepisywane do aplikacji. Można je traktować jako opcjonalne źródło inspiracji, bo pokazują techniki już znane z zajęć.

## Rola laboratoriów w projekcie

Laboratoria mogą pomóc w trzech sytuacjach:

- gdy trzeba szybko przypomnieć sobie algorytm, np. Levenshteina, segmentację albo prosty spellcheck,
- gdy potrzeba przykładowych danych lub wyników eksperymentów,
- gdy warto pokazać w dokumentacji, że projekt rozwija zagadnienia przerabiane wcześniej.

Nie należy jednak ograniczać architektury do notebooków. Docelowa aplikacja powinna mieć własne moduły, testy, API, frontend i model danych.

## Dostępne materiały

- `lab_01.ipynb` - pamięć tłumaczeń i słownik kontekstowy.
- `lab_02.ipynb` - ICE match, dystanse, Levenshtein i fuzzy lookup.
- `lab_03.ipynb` - wyszukiwanie terminologii, pozycje terminów, spaCy, rzeczowniki.
- `lab_04-05.ipynb` - TF-IDF, ekstrakcja terminów z korpusu, word cloud, LDA/topic modeling.
- `lab_06-07.ipynb` - tagi XML, segmenty nietłumaczalne, daty, transfer tagów.
- `lab_08.ipynb` - BLEU, WER, Levenshtein dla oceny jakości tłumaczenia.
- `lab_09-10.ipynb` - web scraping i pozyskiwanie danych tekstowych.
- `lab_11.ipynb` - segmentacja, pobieranie tekstu, Hunalign, XLIFF.
- `lab_11_hunalign.py` - gotowe funkcje przygotowania Hunalign i konwersji ladder do XLIFF.
- `lab_12.ipynb` - keylogger i analiza procesu pisania.
- `lab_13-14.ipynb` - podstawowa korekta pisowni i generowanie sugestii Levenshtein 1.
- `lab_15.ipynb` - LanguageTool i sprawdzanie komentarzy w kodzie Java.

## Jak korzystać bez uzależniania projektu od notebooków

1. Najpierw projektować funkcję aplikacji, np. „panel pamięci tłumaczeń pokazuje 5 sugestii z oceną”.
2. Dopiero potem sprawdzić, czy w notebooku istnieje algorytm, który można wykorzystać.
3. Przenieść tylko małe, testowalne funkcje do modułów `.py`.
4. Nie importować notebooków jako zależności aplikacji.
5. W dokumentacji opisać inspirację, ale kod produkcyjny trzymać w `apps` i `libs`.

## Funkcje, które mogą się przydać

| Źródło | Funkcje/tematy | Możliwe zastosowanie |
| --- | --- | --- |
| `lab_01.ipynb` | `tm_lookup`, `glossary_lookup` | prosty prototyp TM i glosariusza |
| `lab_02.ipynb` | `ice_lookup`, `fuzzy_lookup` | rozmyte i kontekstowe dopasowania |
| `lab_03.ipynb` | `terminology_lookup`, `extract_terms` | wykrywanie terminów w segmencie |
| `lab_06-07.ipynb` | `find_tags`, `correct_dates`, `transfer_tags` | QA tagów i dat |
| `lab_11.ipynb` | `sentence_split` | segmentacja dokumentu |
| `lab_11_hunalign.py` | Hunalign, XLIFF | import tekstów równoległych |
| `lab_13-14.ipynb` | `correct_text`, `generate_suggestions` | prosty spellcheck fallback |
| `lab_15.ipynb` | LanguageTool | lepszy spellcheck i gramatyka |

## Priorytet

Najpierw realizować wymagania aplikacji. Laboratoria są pomocne, ale drugorzędne wobec celu: stworzyć webową platformę CAT z czytelną architekturą, działającymi modułami i sensownym doborem narzędzi.
