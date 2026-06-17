# Model danych

Ten model jest propozycja startowa. Powinien byc prosty, ale pozwalac na rozwoj funkcji CAT bez przepisywania bazy od zera.

Po Etapie 2 model bazowy jest wdrozony w SQLAlchemy i migracji Alembic oraz uzywany przez
przeplyw importu dokumentow i zapisu segmentow:

- modele: `apps/api/src/cat_api/models/`,
- migracja: `apps/api/alembic/versions/0001_initial.py`.

## Encje glowne

### User

- `id`
- `email`
- `display_name`
- `created_at`

### Project

- `id`
- `owner_id`
- `name`
- `source_language`
- `target_language`
- `domain`
- `created_at`

### Document

- `id`
- `project_id`
- `filename`
- `source_language`
- `target_language`
- `status`
- `created_at`

### Segment

- `id`
- `document_id`
- `position`
- `source_text`
- `target_text`
- `status`
- `locked`
- `created_at`
- `updated_at`

Statusy przykladowe: `new`, `draft`, `translated`, `reviewed`, `approved`.

### TranslationMemoryEntry

- `id`
- `source_language`
- `target_language`
- `source_text`
- `target_text`
- `normalized_source_text`
- `domain`
- `project_id`
- `created_by`
- `created_at`

Indeksy startowe: `normalized_source_text`, para jezykowa, opcjonalnie indeks trigramowy dla fuzzy matchingu.

Stan po Etapie 3:

- model jest uzywany przez endpointy pamieci tlumaczen i zatwierdzanie segmentow,
- `normalized_source_text` powstaje przez normalizacje Unicode, zamiane wybranych znakow
  typograficznych, trim, zwiniecie bialych znakow i `casefold`,
- exact match porownuje `normalized_source_text`,
- fuzzy match jest liczony w Pythonie przez RapidFuzz, zeby testy backendu dzialaly na SQLite,
- zapis wpisu jest idempotentny dla tej samej pary jezykowej, znormalizowanego zrodla,
  tekstu docelowego, projektu i domeny.

### GlossaryTerm

- `id`
- `project_id`
- `source_language`
- `target_language`
- `source_term`
- `target_term`
- `definition`
- `domain`
- `case_sensitive`
- `forbidden`
- `example_source`
- `example_target`

### SpellcheckIgnore

- `id`
- `project_id`
- `language`
- `word`
- `created_by`
- `created_at`

## Relacje

- Uzytkownik moze byc wlascicielem wielu projektow.
- Projekt ma wiele dokumentow.
- Dokument ma wiele segmentow.
- Projekt moze ograniczac widocznosc wpisow pamieci tlumaczen i slownika.
- Segment po zatwierdzeniu moze tworzyc wpis w pamieci tlumaczen.

## Indeksy i ograniczenia z Etapu 1

- `documents.project_id`
- `segments.document_id`
- unikalna para `segments.document_id` + `segments.position`
- `translation_memory_entries.normalized_source_text`
- trigramowy indeks GIN na `translation_memory_entries.normalized_source_text`
- para jezykowa i domena dla `translation_memory_entries`
- para jezykowa i domena dla `glossary_terms`
- unikalna para `spellcheck_ignores.project_id` + `language` + `word`

## Normalizacja tekstu

Dla pamieci tlumaczen warto przechowywac wersje znormalizowana tekstu zrodlowego:

- trim bialych znakow,
- normalizacja wielokrotnych spacji,
- opcjonalne lowercase dla wyszukiwania,
- opcjonalne usuniecie roznic typograficznych.

Nie nalezy usuwac oryginalnego tekstu, bo jest potrzebny do eksportu i oceny jakosci.
