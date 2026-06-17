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
- Status po Etapie 3: wdrozone. Zatwierdzanie wymaga niepustego `target_text`, ustawia status
  `approved` i zapisuje pare zrodlo-docelowy do pamieci tlumaczen.

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
- Status po Etapie 1: zaplanowane na Etap 4.

### Spellcheck

- `POST /spellcheck`
- `POST /spellcheck/ignore`
- Status po Etapie 1: zaplanowane na Etap 5.

Przykladowe zapytanie:

```json
{
  "language": "pl",
  "text": "To jest przykladowe tlumacznie docelowe.",
  "projectId": "project-id"
}
```

## Zasady projektowania API

- Frontend nie powinien znac szczegolow implementacji fuzzy matchingu.
- Backend powinien zwracac `score` i uzasadnienie typu dopasowania.
- Spellcheck powinien zwracac pozycje bledow, a nie tylko liste slow.
- Importy i reindeksowanie powinny byc zadaniami asynchronicznymi, jesli trwaja dluzej niz kilka sekund.
