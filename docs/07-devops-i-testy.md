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

Po Etapie 4 dodano testy:

- wyszukiwania terminu jednowyrazowego i wielowyrazowego z pozycjami w segmencie,
- filtrowania slownika po parze jezykowej, domenie i projekcie,
- obslugi `case_sensitive`,
- obslugi terminu zakazanego,
- CRUD terminow slownikowych,
- importu CSV i walidacji wymaganych kolumn,
- zatwierdzania segmentu, gdy wymagany termin docelowy jest obecny,
- bledu `409`, gdy wymagany termin docelowy nie wystepuje,
- bledu `409`, gdy w tlumaczeniu wystepuje termin zakazany,
- braku zapisu do pamieci tlumaczen po odrzuconym zatwierdzeniu.

Po Etapie 5 dodano testy:

- sprawdzania tekstu docelowego w jezyku polskim,
- sprawdzania tekstu docelowego w jezyku angielskim,
- sprawdzania tekstu docelowego w jezyku niemieckim,
- czytelnego bledu dla nieobslugiwanego jezyka,
- zwracania pozycji `start` i `end`,
- zwracania sugestii poprawek,
- ignorowania slowa dla projektu i jezyka,
- braku bledu dla zignorowanego slowa,
- idempotentnego dodawania ignorowanego slowa,
- usuwania ignorowanego slowa,
- walidacji pustego tekstu i brakujacego jezyka.

Po Etapie 6 dodano testy:

- eksportu TXT z segmentami w kolejnosci `position`,
- fallbacku eksportu TXT do `source_text`, gdy brakuje `target_text`,
- eksportu XLIFF z `source`, `target`, statusem i jezykami dokumentu,
- eksportu TMX z tekstami, jezykami, data utworzenia, `domain` i `project_id`,
- importu TMX i zapisu wpisu pamieci tlumaczen,
- idempotencji importu TMX,
- walidacji niepoprawnej struktury TMX,
- eksportu TBX z definicja, domena, `project_id`, `case_sensitive` i `forbidden`,
- importu TBX i zapisu terminu slownikowego,
- walidacji niepoprawnej struktury TBX.

Po Etapie 7 dodano:

- wspolna fixture `test_client` w `apps/api/tests/conftest.py` dla nowych testow
  integracyjnych na deterministycznym SQLite in-memory,
- test przeplywu MVP w `apps/api/tests/test_mvp_flow.py`, ktory laczy import dokumentu,
  segmentacje, zapis draftu, approve, zapis do TM, sugestie TM dla podobnego segmentu,
  wyszukiwanie slownika, walidacje terminologii, spellcheck, eksport TXT oraz import/eksport
  TMX i TBX,
- pelny zestaw testow backendu uruchamiany przez `python -m pytest`.

Weryfikacja Etapu 4:

- `cd apps/api && python -m pytest` - przechodzi,
- `cd apps/api && python -m ruff check .` - przechodzi,
- `cd apps/frontend && npm run build` - przechodzi.

Weryfikacja Etapu 5:

- `cd apps/api && python -m pytest` - przechodzi,
- `cd apps/api && python -m ruff check .` - przechodzi,
- `cd apps/frontend && npm run build` - przechodzi.

Weryfikacja Etapu 6:

- `cd apps/api && python -m pytest` - przechodzi,
- `cd apps/api && python -m ruff check .` - przechodzi,
- `cd apps/frontend && npm run build` - przechodzi.

Weryfikacja finalna MVP po Etapie 7:

- `cd apps/api && python -m pytest` - przechodzi,
- `cd apps/api && python -m ruff check .` - przechodzi,
- `cd apps/frontend && npm run build` - przechodzi,
- `cd apps/frontend && npm run test` - przechodzi,
- `cd apps/frontend && npm run test:e2e` - przechodzi po instalacji przegladarki przez
  `npx playwright install chromium`.

## Testy frontendu

Zakres minimalny:

- render listy segmentow,
- edycja segmentu,
- pokazanie sugestii TM,
- pokazanie terminow slownikowych,
- pokazanie bledow pisowni.

Stan finalny MVP:

- frontend uzywa Vitest, React Testing Library, `@testing-library/jest-dom` i `user-event`,
- `apps/frontend/package.json` zawiera skrypty `test` i `test:e2e`,
- `apps/frontend/vite.config.ts` ma srodowisko testowe `jsdom` i setup testowy,
- test edytora obejmuje stan pusty, import TXT, wybor segmentu, zapis targetu,
  approve i blad API,
- test panelu TM obejmuje pobranie sugestii, zastosowanie sugestii i blad API,
- test panelu slownika obejmuje wyswietlanie terminu, uzycie terminu i stan pusty,
- test panelu spellcheck obejmuje sprawdzenie targetu, zastosowanie sugestii,
  ignorowanie slowa i blad API.

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

Stan finalny MVP:

- test jest w `tests/e2e/editor.spec.ts`,
- konfiguracja jest w `apps/frontend/playwright.config.ts`,
- fixture importu jest w `tests/fixtures/sample_source.txt`,
- test uruchamia frontend Vite przez `webServer` i mockuje API, dzieki czemu nie wymaga
  lokalnej bazy danych,
- scenariusz obejmuje import TXT, wybor segmentu, wpisanie `Zapisz plk.`, spellcheck,
  zastosowanie sugestii `plik`, zatwierdzenie segmentu, sugestie TM dla podobnego segmentu,
  terminy slownikowe i eksport TXT.

## CI

Minimalny pipeline planowany:

- lint frontendu,
- testy frontendu,
- testy backendu,
- walidacja OpenAPI,
- build obrazow Docker bez publikacji.

Stan finalny MVP:

- dodano `.github/workflows/ci.yml`,
- job backendowy instaluje `apps/api`, uruchamia `python -m pytest` i
  `python -m ruff check .`,
- job frontendowy uruchamia `npm ci`, `npm run build`, `npm run test`,
  `npx playwright install --with-deps chromium` i `npm run test:e2e`,
- walidacja OpenAPI i build obrazow Docker pozostaja rozszerzeniami po MVP.

## Dane demonstracyjne

Dane demo powinny byc male i przewidywalne:

- kilka segmentow EN-PL,
- jeden slownik domeny software,
- jeden plik tekstowy do importu,
- kilka celowych bledow pisowni w tlumaczeniu docelowym.

Stan finalny MVP:

- `data/samples/documents/software-cat-source.txt`,
- `data/samples/translation-memory/software-cat-memory.tmx`,
- `data/samples/glossaries/software-cat-glossary.csv`,
- `data/samples/glossaries/software-cat-glossary.tbx`,
- `data/samples/spellcheck-target-with-error.txt`.

Dane wspieraja jeden spojny scenariusz EN-PL dla domeny software/CAT i sa opisane
w `README.md`.
