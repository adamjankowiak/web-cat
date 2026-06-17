# Plan etapow

## Etap 1: Fundament repozytorium - zakonczony

- Ustalono wariant stacku technologicznego: FastAPI, React/Vite, PostgreSQL, SQLAlchemy/Alembic i Docker Compose.
- Przygotowano Docker Compose, Dockerfile API/frontendu, `Makefile`, `.env.example` i `scripts/dev.ps1`.
- Dodano minimalny backend FastAPI z endpointem `GET /health`.
- Dodano minimalny frontend React/Vite z widokiem edytora CAT i panelami pomocniczymi.
- Przygotowano bazowy model danych i migracje Alembic.
- Dodano startowy kontrakt OpenAPI i wspolne typy API.

Artefakty Etapu 1:

- `docker-compose.yml`
- `apps/api/src/cat_api/main.py`
- `apps/api/alembic/versions/0001_initial.py`
- `apps/frontend/src/features/editor/TranslationEditor.tsx`
- `libs/shared/contracts/openapi.yaml`

## Etap 2: Dokumenty i segmentacja - zakonczony

- Dodano import pliku TXT przez API i frontend.
- Dodano podzial dokumentu na segmenty po zdaniach lub akapitach.
- Dodano zapis dokumentu, segmentow i statusow segmentow w bazie.
- Dodano wyswietlanie segmentow z API w frontendzie.
- Dodano zapis tlumaczenia roboczego.

Artefakty Etapu 2:

- `apps/api/src/cat_api/services/segmentation.py`
- `apps/api/src/cat_api/api/routes/documents.py`
- `apps/api/src/cat_api/api/routes/segments.py`
- `apps/frontend/src/features/editor/TranslationEditor.tsx`
- `libs/shared/contracts/openapi.yaml`

## Etap 3: Pamiec tlumaczen - zakonczony

- Po zatwierdzeniu segmentu para zrodlo-docelowy jest zapisywana w pamieci tlumaczen.
- Dodano exact match po `normalized_source_text` ze score 100 i typem `exact`.
- Dodano fuzzy match przez RapidFuzz, zgodny z testami SQLite.
- Panel edytora pobiera najlepsze sugestie z API dla aktywnego segmentu.
- Dodano metadane: para jezykowa, projekt, domena, opcjonalny autor i data utworzenia.
- Zatwierdzanie segmentu korzysta z `POST /segments/{segment_id}/approve`.

Artefakty Etapu 3:

- `apps/api/src/cat_api/services/translation_memory.py`
- `apps/api/src/cat_api/api/routes/translation_memory.py`
- `apps/api/src/cat_api/api/routes/segments.py`
- `apps/frontend/src/features/translation-memory/TranslationMemoryPanel.tsx`
- `apps/frontend/src/features/editor/TranslationEditor.tsx`
- `apps/api/tests/test_translation_memory.py`
- `libs/shared/contracts/openapi.yaml`

## Etap 4: Slownik kontekstowy - zakonczony

- Rozbudowano istniejacy model `GlossaryTerm` bez zmiany schematu bazy.
- Dodano CRUD terminow slownikowych przez API.
- Dodano wyszukiwanie terminow jedno- i wielowyrazowych w aktualnym segmencie z pozycjami wystapien.
- Wyszukiwanie uwzglednia pare jezykowa, domene, projekt, `case_sensitive` oraz terminy zakazane.
- Panel slownika w edytorze pobiera realne wyniki z API i pozwala szybko wstawic zalecany `target_term`.
- Zatwierdzanie segmentu sprawdza terminologie wymagana i zakazana przed zapisem statusu oraz TM.
- Dodano import slownika z CSV; TBX pozostaje pozniejszym rozszerzeniem.

Artefakty Etapu 4:

- `apps/api/src/cat_api/services/glossary.py`
- `apps/api/src/cat_api/api/routes/glossary.py`
- `apps/api/src/cat_api/api/routes/segments.py`
- `apps/frontend/src/features/glossary/GlossaryPanel.tsx`
- `apps/frontend/src/features/editor/TranslationEditor.tsx`
- `apps/api/tests/test_glossary.py`
- `libs/shared/contracts/openapi.yaml`

## Etap 5: Sprawdzanie pisowni

- Dodac endpoint sprawdzania tekstu docelowego.
- Podlaczyc lokalny adapter Hunspell lub LanguageTool.
- Pokazac bledy i sugestie w interfejsie.
- Dodac ignorowanie slow dla projektu/uzytkownika.
- Dodac testy dla kilku jezykow docelowych.

## Etap 6: Eksport i formaty CAT

- Dodac eksport przetlumaczonego TXT.
- Dodac import/eksport TMX dla pamieci tlumaczen.
- Dodac import/eksport TBX dla terminologii.
- Rozwazyc XLIFF dla dokumentow roboczych.

## Etap 7: Jakosc i prezentacja

- Dodac testy jednostkowe backendu.
- Dodac testy komponentow frontendu.
- Dodac test e2e przeplywu: import, tlumaczenie, sugestia TM, spellcheck, eksport.
- Przygotowac dane demonstracyjne.
- Opisac ograniczenia i mozliwe rozszerzenia.
