# Model danych

Ten model jest propozycja startowa. Powinien byc prosty, ale pozwalac na rozwoj funkcji CAT bez przepisywania bazy od zera.

## Encje glowne

### User

- `id`
- `email`
- `display_name`
- `created_at`

### Project

- `id`
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

### GlossaryTerm

- `id`
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

- Projekt ma wiele dokumentow.
- Dokument ma wiele segmentow.
- Projekt moze ograniczac widocznosc wpisow pamieci tlumaczen i slownika.
- Segment po zatwierdzeniu moze tworzyc wpis w pamieci tlumaczen.

## Normalizacja tekstu

Dla pamieci tlumaczen warto przechowywac wersje znormalizowana tekstu zrodlowego:

- trim bialych znakow,
- normalizacja wielokrotnych spacji,
- opcjonalne lowercase dla wyszukiwania,
- opcjonalne usuniecie roznic typograficznych.

Nie nalezy usuwac oryginalnego tekstu, bo jest potrzebny do eksportu i oceny jakosci.
