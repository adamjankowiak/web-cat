# Koncepcja projektu i narzędzia

## Proponowana koncepcja

Najciekawszy wariant projektu to `Context-Aware CAT Workbench`: webowy edytor tłumaczeń, który nie tylko przechowuje pamięć tłumaczeń, ale też wyjaśnia, dlaczego dana sugestia została pokazana.

Rdzeń projektu:

- segmentowy edytor tłumaczenia,
- hybrydowa pamięć tłumaczeń,
- kontekstowy słownik terminologiczny,
- sprawdzanie pisowni i podstawowe QA po stronie docelowej.

Element, który wyróżnia projekt:

- panel „dlaczego ta sugestia?” pokazujący typ dopasowania: exact, fuzzy, semantic, context/ICE,
- kontrola terminologii: wymagane i zakazane tłumaczenia terminów,
- inline spellcheck z sugestiami i możliwością ignorowania słów w projekcie,
- opcjonalny semantyczny ranking sugestii przez embeddingi.

## Jak spełnić wymagania

### Webowy frontend

Propozycja:

- React + TypeScript + Vite,
- TanStack Query do pobierania danych z API,
- Zustand do lokalnego stanu edytora,
- CodeMirror albo własny komponent textarea dla segmentu docelowego,
- panel boczny z sugestiami TM, glosariuszem i spellcheckiem.

Minimalne widoki:

- dashboard projektów,
- import dokumentu,
- edytor segmentów,
- zarządzanie pamięcią tłumaczeń,
- zarządzanie glosariuszem.

### Pamięć tłumaczeń

Poziom 1, wymagany:

- exact match po znormalizowanym tekście,
- fuzzy match przez RapidFuzz albo Levenshtein,
- zapis zatwierdzonego segmentu do TM.

Poziom 2, ciekawszy:

- `pg_trgm` w PostgreSQL dla szybkiego podobieństwa tekstowego,
- scoring łączący podobieństwo tekstu, domenę, projekt i datę wpisu,
- ICE/context match z poprzednim i następnym segmentem.

Poziom 3, rozszerzony:

- embeddingi segmentów,
- `pgvector` do semantycznego wyszukiwania podobnych segmentów,
- reranking: najpierw szybki kandydat z trigramów, potem ranking embeddingowy.

### Słownik kontekstowy

Poziom 1, wymagany:

- tabela terminów: source term, target term, definicja, domena, języki,
- wyszukiwanie terminów występujących w aktualnym segmencie,
- pokazanie terminu w panelu bocznym.

Poziom 2, ciekawszy:

- terminy wymagane i zakazane,
- walidacja, czy target zawiera wymagany termin,
- zwracanie pozycji terminu w segmencie,
- import CSV/TBX.

Poziom 3, rozszerzony:

- lematyzacja i odmiany przez spaCy albo Stanza,
- automatyczna ekstrakcja kandydatów terminologicznych przez TF-IDF,
- klasyfikacja domeny dokumentu i filtrowanie terminów po domenie.

### Sprawdzanie pisowni po stronie docelowej

Poziom 1, wymagany:

- endpoint `POST /spellcheck`,
- sprawdzanie tekstu docelowego,
- lista błędów z pozycją, komunikatem i sugestiami.

Poziom 2, ciekawszy:

- LanguageTool jako główny adapter,
- Hunspell jako lokalny, szybki fallback,
- osobna lista ignorowanych słów dla projektu.

Poziom 3, rozszerzony:

- reguły QA: liczby, daty, tagi XML/HTML, podwójne spacje, brakujące znaki interpunkcyjne,
- ostrzeżenia terminologiczne połączone ze słownikiem,
- profil języka docelowego, np. PL, EN, DE.

## Narzędzia i biblioteki

### Frontend

- React - interfejs edytora i paneli.
- TypeScript - bezpieczeństwo typów dla kontraktów API.
- Vite - szybki dev server i build.
- TanStack Query - cache i synchronizacja z API.
- Zustand - prosty stan aktywnego segmentu i filtrów.
- CodeMirror - jeśli edytor ma mieć podświetlanie błędów i oznaczenia inline.

### Backend

- FastAPI - API HTTP, walidacja danych, automatyczne OpenAPI.
- Pydantic - schematy wejścia/wyjścia.
- SQLAlchemy - warstwa dostępu do bazy.
- Alembic - migracje bazy.
- Celery/RQ + Redis - zadania importu, eksportu i reindeksowania.

### Baza danych i wyszukiwanie

- PostgreSQL - główna baza danych.
- `pg_trgm` - podobieństwo tekstowe przez trigramy, dobre dla fuzzy TM.
- `pgvector` - semantyczna pamięć tłumaczeń przez embeddingi.
- SQLite - tylko jako wariant bardzo prostego MVP.

### NLP i podobieństwo tekstu

- RapidFuzz - szybki fuzzy matching i porównywanie segmentów.
- python-Levenshtein - klasyczny dystans Levenshteina.
- spaCy - tokenizacja, lematyzacja, części mowy, ekstrakcja terminów.
- Stanza - alternatywa NLP, szczególnie jeśli potrzebne są konkretne modele językowe.
- NLTK - metryki i proste eksperymenty, np. BLEU.

### Spellcheck i QA

- LanguageTool - główny kandydat do spellchecka i gramatyki.
- Hunspell - szybka lokalna korekta pisowni.
- pyspellchecker - prosty fallback demonstracyjny.
- własne reguły regex - daty, tagi, liczby, spacje, segmenty nietłumaczalne.

## Modele, które można wykorzystać

### Embeddingi do semantycznej pamięci tłumaczeń

- `intfloat/multilingual-e5-large-instruct` - dobry kandydat do semantycznego wyszukiwania segmentów wielojęzycznych.
- Modele SentenceTransformers multilingual - praktyczna rodzina modeli do embeddingów, semantic search i rerankingu.
- Zewnętrzne embedding API - wariant prostszy operacyjnie, ale zależny od kosztów i limitów.

Zastosowanie:

- zamiana segmentu źródłowego na embedding,
- zapis embeddingu w `pgvector`,
- wyszukiwanie semantycznie podobnych segmentów,
- połączenie wyniku semantic score z fuzzy score.

### Tłumaczenie maszynowe jako funkcja opcjonalna

Tłumaczenie maszynowe nie jest wymagane przez zadanie. Jeśli ma się pojawić, powinno być oznaczone jako sugestia, a nie jako zastępstwo pamięci tłumaczeń.

Możliwe opcje:

- `facebook/nllb-200-distilled-600M` - model badawczy do tłumaczenia wielu języków, dobry do demonstracji, ale z ograniczeniami licencyjnymi i jakościowymi.
- MarianMT/OPUS-MT - mniejsze modele dla konkretnych par językowych.
- Zewnętrzne API MT - łatwiejsze uruchomienie, ale koszt i zależność od dostawcy.

Rekomendacja: w MVP nie dodawać MT. Lepiej mieć solidne TM, glosariusz i spellcheck. MT dodać jako opcjonalny panel „AI suggestion” po spełnieniu głównych wymagań.

## Proponowany MVP

1. Frontend z listą segmentów i edytorem targetu.
2. Backend FastAPI z dokumentami, segmentami, TM, glosariuszem i spellcheckiem.
3. PostgreSQL jako baza.
4. RapidFuzz jako pierwsza implementacja fuzzy TM.
5. LanguageTool jako spellcheck.
6. Glosariusz z CSV i kontrolą wymaganych terminów.
7. Eksport przetłumaczonego TXT lub prostego XLIFF.

## Proponowany wariant ambitny

1. Wszystko z MVP.
2. `pg_trgm` dla szybkiego fuzzy search w bazie.
3. `pgvector` i multilingual embeddings dla semantic TM.
4. Panel porównania sugestii: exact, fuzzy, semantic, glossary, spellcheck.
5. QA tagów, dat, liczb i terminologii.
6. Import TMX/TBX/XLIFF.
7. Tryb demonstracyjny z gotowym projektem i danymi testowymi.

## Linki źródłowe do narzędzi

- FastAPI: https://fastapi.tiangolo.com/
- RapidFuzz: https://rapidfuzz.github.io/RapidFuzz/
- PostgreSQL `pg_trgm`: https://www.postgresql.org/docs/current/pgtrgm.html
- pgvector: https://github.com/pgvector/pgvector
- LanguageTool API: https://languagetool.org/api-details
- SentenceTransformers: https://www.sbert.net/docs/sentence_transformer/pretrained_models.html
- multilingual-e5-large-instruct: https://huggingface.co/intfloat/multilingual-e5-large-instruct
- NLLB distilled 600M: https://huggingface.co/facebook/nllb-200-distilled-600M
