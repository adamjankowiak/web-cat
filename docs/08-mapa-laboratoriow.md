# Opcjonalna mapa laboratoriów do funkcji CAT

Ten dokument łączy materiały z `C:\Users\adamy\PycharmProjects\translation-labs` z planowanymi funkcjami aplikacji `web-cat`. Mapa jest opcjonalna: pokazuje, które znane z zajęć techniki można wykorzystać, ale nie definiuje docelowej architektury.

## Wymaganie: pamięć tłumaczeń

Źródła laboratoryjne:

- `lab_01.ipynb` - podstawowe `tm_lookup`, ignorowanie wielkości liter, ignorowanie interpunkcji, dopasowanie różniące się jednym słowem.
- `lab_02.ipynb` - `ice_lookup`, Levenshtein, `levenshtein_similarity`, `fuzzy_lookup`.

Implementacja w projekcie:

- `apps/api/src/cat_api/services/translation_memory.py`
- `libs/nlp/similarity/fuzzy_match.py`
- `apps/api/tests/test_translation_memory.py`

Proponowana ścieżka:

1. Exact match po znormalizowanym tekście.
2. Case-insensitive i punctuation-insensitive lookup.
3. One-word-apart match jako prosty fuzzy wariant.
4. Levenshtein similarity z progiem dopasowania.
5. ICE/context match z poprzednim i następnym segmentem.

## Wymaganie: słownik kontekstowy

Źródła laboratoryjne:

- `lab_01.ipynb` - `glossary_lookup` i optymalizacja złożoności wyszukiwania.
- `lab_03.ipynb` - pozycje wystąpień terminów, odmienione słowa, spaCy, rzeczowniki i ekstrakcja terminologii.
- `lab_04-05.ipynb` - TF-IDF i topic modeling do późniejszego wykrywania domeny lub kandydatów terminologicznych.

Implementacja w projekcie:

- `apps/api/src/cat_api/services/glossary.py`
- `apps/api/src/cat_api/models/glossary.py`
- `apps/frontend/src/features/glossary/GlossaryPanel.tsx`
- `apps/api/tests/test_glossary.py`

Proponowana ścieżka:

1. Proste wyszukiwanie terminów w segmencie.
2. Wyszukiwanie case-insensitive.
3. Indeks terminów po pierwszym tokenie albo n-gramach, żeby uniknąć pełnego skanowania słownika.
4. Zwracanie pozycji terminu w segmencie.
5. Opcjonalna ekstrakcja kandydatów terminologicznych ze spaCy i TF-IDF.

## Wymaganie: sprawdzanie pisowni po stronie docelowej

Źródła laboratoryjne:

- `lab_13-14.ipynb` - podstawowa korekta pisowni, `L1(w)`, sugestie Levenshtein 1.
- `lab_15.ipynb` - LanguageTool, wykrywanie błędów w tekście pobranym z webu i w komentarzach Java.

Implementacja w projekcie:

- `apps/api/src/cat_api/services/spellcheck.py`
- `libs/nlp/spellcheck/adapters.py`
- `apps/frontend/src/features/spellcheck/SpellcheckPanel.tsx`
- `apps/api/tests/test_spellcheck.py`

Proponowana ścieżka:

1. Prosty adapter słownikowy jako fallback demonstracyjny.
2. Sugestie dla słów w odległości Levenshteina 1.
3. Adapter LanguageTool jako bogatszy mechanizm sprawdzania.
4. Ignorowanie nazw własnych i słów zaakceptowanych w projekcie.
5. Zwracanie pozycji błędu, komunikatu i listy sugestii.

## Moduły dodatkowe przydatne w CAT

### Segmentacja i import

Źródła:

- `lab_06-07.ipynb` - tagi XML, segmenty nietłumaczalne, daty i transfer tagów.
- `lab_11.ipynb` - segmentacja zdań, obsługa skrótów, pobieranie widocznego tekstu.

Docelowe moduły:

- `apps/api/src/cat_api/services/segmentation.py`
- `apps/api/src/cat_api/services/import_export.py`

### XLIFF i budowanie TM z tekstów równoległych

Źródła:

- `lab_11.ipynb` - Hunalign i przygotowanie plików.
- `lab_11_hunalign.py` - `prepare_hunalign_inputs`, `run_hunalign_alignment`, `convert_hunalign_ladder_to_xliff`.
- `results/lab_11` - przykładowe pliki wynikowe, w tym `.xliff`.

Docelowe moduły:

- `apps/api/src/cat_api/services/import_export.py`
- `apps/worker/src/cat_worker/jobs/import_documents.py`
- `apps/worker/src/cat_worker/jobs/reindex_memory.py`

### QA tłumaczenia

Źródła:

- `lab_06-07.ipynb` - zgodność tagów i dat.
- `lab_08.ipynb` - BLEU, WER i Levenshtein do oceny korpusowej.

Możliwe funkcje po MVP:

- ostrzeżenie o brakujących tagach,
- ostrzeżenie o innej liczbie dat,
- ostrzeżenie o zmianie wartości daty,
- statystyki jakości dla zaimportowanego korpusu.
