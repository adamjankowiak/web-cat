# DevOps i testy

## Uruchamianie lokalne

Docelowo projekt moze miec dwa tryby uruchomienia:

- tryb prosty: backend i frontend uruchamiane lokalnie,
- tryb kontenerowy: Docker Compose z baza danych i uslugami pomocniczymi.

Po Etapie 2 oba tryby maja przygotowane pliki uruchomieniowe. Szczegolowe komendy sa opisane w
`README.md`.

Komponenty w Docker Compose:

- `frontend`,
- `api`,
- `postgres`,
- `redis`,
- opcjonalnie `languagetool`.

Status po Etapie 2:

- `frontend`, `api`, `postgres` i `redis` sa skonfigurowane w `docker-compose.yml`,
- `worker` i `languagetool` pozostaja planowanymi rozszerzeniami,
- migracje lokalnie uruchamia `alembic upgrade head` z katalogu `apps/api`,
- migracje w Dockerze uruchamia `docker compose exec -T api alembic upgrade head`.

## Testy backendu

Zakres minimalny:

- healthcheck API,
- normalizacja tekstu dla pamieci tlumaczen,
- exact match,
- fuzzy match,
- wyszukiwanie terminow slownikowych,
- odpowiedz spellcheckera,
- import prostego dokumentu.

Po Etapie 2 istnieja testy:

- `GET /health`,
- segmentacji po zdaniach i akapitach,
- importu dokumentu TXT i zapisu roboczego tlumaczenia segmentu.

Po Etapie 3 dodano testy:

- normalizacji tekstu zrodlowego dla pamieci tlumaczen,
- idempotentnego zapisu wpisu TM,
- exact match ze score 100 i typem `exact`,
- fuzzy match i sortowania wynikow malejaco po score,
- wyszukiwania sugestii przez serwis,
- zatwierdzania segmentu i automatycznego zapisu do TM,
- bledu walidacji przy zatwierdzaniu segmentu bez tekstu docelowego.

Weryfikacja Etapu 3:

- `cd apps/api && python -m pytest` - przechodzi,
- `cd apps/api && python -m ruff check .` - przechodzi,
- `cd apps/frontend && npm run build` - wymagane do pelnej weryfikacji frontendu.

## Testy frontendu

Zakres minimalny:

- render listy segmentow,
- edycja segmentu,
- pokazanie sugestii TM,
- pokazanie terminow slownikowych,
- pokazanie bledow pisowni.

## Test e2e

Scenariusz demonstracyjny:

1. Uruchom aplikacje.
2. Zaimportuj plik testowy.
3. Otworz pierwszy segment.
4. Wpisz tlumaczenie z bledem pisowni.
5. Sprawdz, czy panel spellcheck pokazuje blad.
6. Zatwierdz segment.
7. Otworz podobny segment i sprawdz sugestie z pamieci tlumaczen.
8. Wyeksportuj wynik.

## CI

Minimalny pipeline:

- lint frontendu,
- testy frontendu,
- testy backendu,
- walidacja OpenAPI,
- build obrazow Docker bez publikacji.

## Dane demonstracyjne

Dane demo powinny byc male i przewidywalne:

- kilka segmentow EN-PL,
- jeden slownik domeny software,
- jeden plik tekstowy do importu,
- kilka celowych bledow pisowni w tlumaczeniu docelowym.
