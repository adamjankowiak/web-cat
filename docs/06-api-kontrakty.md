# Kontrakty API

Kontrakty API powinny byc trzymane w `libs/shared/contracts/openapi.yaml`, aby frontend i backend mialy jedno zrodlo prawdy.

Po Etapie 1 kontrakt wspoldzielony opisuje wdrozony endpoint `GET /health` oraz startowe schematy danych `Project`, `Document` i `Segment`. Pozostale endpointy ponizej sa kontraktem planowanym dla kolejnych etapow i beda dopisywane do OpenAPI wraz z implementacja.

## Endpointy startowe

### Healthcheck

- `GET /health`
- Zwraca status API i wersje aplikacji.
- Status po Etapie 1: wdrozone w backendzie i opisane w `libs/shared/contracts/openapi.yaml`.

### Dokumenty

- `POST /documents` - importuje dokument TXT z tresci przekazanej w JSON, tworzy projekt gdy
  `project_id` nie zostal podany, segmentuje tekst po zdaniach albo akapitach i zwraca dokument
  z segmentami.
- `GET /documents` - zwraca liste zaimportowanych dokumentow.
- `GET /documents/{document_id}` - zwraca dokument z segmentami.
- `GET /documents/{document_id}/segments` - zwraca segmenty dokumentu.
- `PATCH /segments/{segment_id}` - zapisuje robocze tlumaczenie lub status segmentu.
- `POST /segments/{segment_id}/approve`
- Status po Etapie 4: wdrozone. Zatwierdzanie wymaga niepustego `target_text`, sprawdza
  terminologie slownikowa, ustawia status `approved` i zapisuje pare zrodlo-docelowy do pamieci
  tlumaczen. Przy naruszeniu terminologii zwraca `409` z lista naruszen i nie zapisuje TM.

### Pamiec tlumaczen

- `POST /translation-memory/search`
- `POST /translation-memory/entries`
- `GET /translation-memory/entries`
- `DELETE /translation-memory/entries/{entry_id}`
- Status po Etapie 3: wdrozone i opisane w `libs/shared/contracts/openapi.yaml`.

Wyszukiwanie zwraca obiekt z lista `suggestions`. Kazda sugestia zawiera wpis TM, `score`
oraz `match_type` (`exact` albo `fuzzy`). Exact match ma score 100. Fuzzy match jest liczony
przez RapidFuzz po stronie backendu.

Przykladowe zapytanie wyszukiwania:

```json
{
  "sourceLanguage": "en",
  "targetLanguage": "pl",
  "sourceText": "Save the file before closing the window.",
  "domain": "software",
  "limit": 5
}
```

### Slownik

- `POST /glossary/search`
- `POST /glossary/terms`
- `GET /glossary/terms`
- `PATCH /glossary/terms/{term_id}`
- `DELETE /glossary/terms/{term_id}`
- `POST /glossary/import-csv`
- Status po Etapie 4: wdrozone i opisane w `libs/shared/contracts/openapi.yaml`.

Wyszukiwanie zwraca obiekt z lista `matches`. Kazde dopasowanie zawiera termin slownikowy,
pozycje `start`/`end` oraz faktyczny fragment `matched_text` z segmentu zrodlowego.

Przykladowe zapytanie wyszukiwania:

```json
{
  "source_language": "en",
  "target_language": "pl",
  "source_text": "Save the file before closing the window.",
  "domain": "software",
  "project_id": "project-id"
}
```

Import CSV przyjmuje `text/csv`. Wymagane kolumny to `source_term`, `target_term`,
`source_language` i `target_language`. Obslugiwane kolumny opcjonalne to `definition`,
`domain`, `case_sensitive`, `forbidden`, `example_source`, `example_target` i `project_id`.

### Spellcheck

- `POST /spellcheck`
- `POST /spellcheck/ignore`
- `GET /spellcheck/ignore`
- `DELETE /spellcheck/ignore/{ignore_id}`
- Status po Etapie 5: wdrozone i opisane w `libs/shared/contracts/openapi.yaml`.

`POST /spellcheck` sprawdza tekst docelowy i zwraca liste `issues`. Kazdy blad zawiera
`start`, `end`, `token`, `message`, `suggestions`, `rule_code` i `language`. Obslugiwane
jezyki lokalnego fallbacku to `pl`, `en` i `de`; nieobslugiwany jezyk zwraca `400`.

`POST /spellcheck/ignore` zapisuje slowo ignorowane dla projektu i jezyka. Dodawanie jest
idempotentne dla tej samej trojki `project_id + language + word`, po normalizacji jezyka i slowa.
`GET /spellcheck/ignore` zwraca ignorowane slowa projektu, opcjonalnie filtrowane po jezyku.
`DELETE /spellcheck/ignore/{ignore_id}` usuwa wpis ignorowania.

Przykladowe zapytanie:

```json
{
  "language": "pl",
  "text": "To jest przykladowe tlumacznie docelowe.",
  "project_id": "project-id"
}
```

## Zasady projektowania API

- Frontend nie powinien znac szczegolow implementacji fuzzy matchingu.
- Backend powinien zwracac `score` i uzasadnienie typu dopasowania.
- Spellcheck powinien zwracac pozycje bledow, a nie tylko liste slow.
- Importy i reindeksowanie powinny byc zadaniami asynchronicznymi, jesli trwaja dluzej niz kilka sekund.
