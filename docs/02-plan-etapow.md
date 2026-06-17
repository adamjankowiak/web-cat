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

## Etap 5: Sprawdzanie pisowni - zakonczony

- Dodano endpoint sprawdzania tekstu docelowego `POST /spellcheck`.
- Wdrozono deterministyczny lokalny adapter slownikowy dla `pl`, `en` i `de` jako fallback
  demonstracyjny bez zaleznosci od zewnetrznego LanguageTool.
- Wyniki spellchecka zwracaja zakres `start`/`end`, token, komunikat, sugestie, kod reguly
  i jezyk.
- Wykorzystano istniejacy model `SpellcheckIgnore` do ignorowania slow dla projektu i jezyka.
- Dodano endpointy `POST /spellcheck/ignore`, `GET /spellcheck/ignore` oraz
  `DELETE /spellcheck/ignore/{ignore_id}`.
- Panel spellcheck w edytorze pobiera realne wyniki z API, sprawdza aktualny tekst docelowy,
  pozwala zastosowac sugestie w aktywnym segmencie i zignorowac slowo dla projektu.
- Spellcheck pozostaje informacyjny; nie blokuje zatwierdzania segmentu.
- Dodano testy backendowe dla kilku jezykow, pozycji bledow, sugestii, ignorowania i walidacji.

Artefakty Etapu 5:

- `apps/api/src/cat_api/services/spellcheck.py`
- `apps/api/src/cat_api/api/routes/spellcheck.py`
- `apps/api/src/cat_api/schemas/spellcheck.py`
- `apps/frontend/src/features/spellcheck/SpellcheckPanel.tsx`
- `apps/frontend/src/features/editor/TranslationEditor.tsx`
- `apps/api/tests/test_spellcheck.py`
- `libs/shared/contracts/openapi.yaml`

## Etap 6: Eksport i formaty CAT - zakonczony

- Dodano eksport przetlumaczonego TXT przez `GET /documents/{document_id}/export.txt`.
- Eksport TXT zapisuje segmenty w kolejnosci `position` i uzywa `target_text`; segmenty bez
  tlumaczenia sa pragmatycznie eksportowane jako `source_text`.
- Dodano eksport dokumentu roboczego XLIFF przez `GET /documents/{document_id}/export.xliff`
  z segmentami, jezykami dokumentu, `source`, `target` i statusem segmentu.
- Dodano eksport i import TMX dla pamieci tlumaczen przez `GET /translation-memory/export.tmx`
  oraz `POST /translation-memory/import-tmx`.
- Import TMX obsluguje deterministyczny subset MVP: `tmx`, `header`, `body`, `tu`,
  `tuv xml:lang` i `seg`, zachowuje metadane `domain` i `project_id` oraz korzysta z
  idempotentnego zapisu pamieci tlumaczen.
- Dodano eksport i import TBX dla terminologii przez `GET /glossary/export.tbx` oraz
  `POST /glossary/import-tbx`.
- Import TBX obsluguje minimalne wpisy terminologiczne, jezyki, terminy, definicje, domene,
  `project_id`, `case_sensitive` i `forbidden`; import CSV z Etapu 4 pozostaje bez zmian.
- Frontend edytora pozwala pobrac TXT, XLIFF, TMX i TBX z realnych endpointow API.
- Import XLIFF zostal swiadomie odlozony jako rozszerzenie po MVP.

Artefakty Etapu 6:

- `apps/api/src/cat_api/services/import_export.py`
- `apps/api/src/cat_api/api/routes/documents.py`
- `apps/api/src/cat_api/api/routes/translation_memory.py`
- `apps/api/src/cat_api/api/routes/glossary.py`
- `apps/frontend/src/features/editor/TranslationEditor.tsx`
- `apps/frontend/src/lib/api-client.ts`
- `apps/api/tests/test_import_export.py`
- `libs/shared/contracts/openapi.yaml`

## Etap 7: Jakosc i prezentacja - zakonczony

- Dodano wspolny backendowy fixture testowy dla nowych testow integracyjnych na SQLite.
- Dodano test przeplywu MVP obejmujacy import dokumentu, segmentacje, zapis draftu,
  zatwierdzenie segmentu, zapis do TM, sugestie TM dla podobnego segmentu, wyszukiwanie
  slownika, walidacje terminologii, spellcheck oraz eksport/import TMX i TBX.
- Dodano Vitest, React Testing Library i testy komponentow edytora, panelu TM, slownika
  oraz spellchecka z mockowanym klientem API.
- Dodano Playwright e2e dla glownego przeplywu MVP z deterministycznymi mockami API.
- Przygotowano male dane demonstracyjne EN-PL dla domeny software/CAT w `data/samples`.
- Dodano pipeline GitHub Actions dla testow backendu, ruff, builda frontendu, testow
  komponentow i testu e2e.
- Uporzadkowano README pod prezentacje projektu, komendy weryfikacyjne, scenariusz demo,
  ograniczenia MVP i mozliwe rozszerzenia.

Artefakty Etapu 7:

- `apps/api/tests/conftest.py`
- `apps/api/tests/test_mvp_flow.py`
- `apps/frontend/src/features/editor/TranslationEditor.test.tsx`
- `apps/frontend/src/features/translation-memory/TranslationMemoryPanel.test.tsx`
- `apps/frontend/src/features/glossary/GlossaryPanel.test.tsx`
- `apps/frontend/src/features/spellcheck/SpellcheckPanel.test.tsx`
- `apps/frontend/playwright.config.ts`
- `tests/e2e/editor.spec.ts`
- `data/samples/`
- `.github/workflows/ci.yml`
- `README.md`
