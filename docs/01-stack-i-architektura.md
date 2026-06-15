# Stack i architektura

Ten dokument opisuje możliwe warianty stosu technologicznego. Rekomendowany wariant to Python + React, bo dobrze pasuje do webowego edytora, NLP, pamięci tłumaczeń, glosariusza i spellchecka. Laboratoria mogą pomóc, ale nie powinny ograniczać projektu.

## Decyzja architektoniczna

Backend projektu będzie oparty o FastAPI. Django było sensowną alternatywą ze względu na panel administracyjny, ORM i gotowe mechanizmy użytkowników, ale w tym projekcie ważniejszy jest lekki backend API, prosta integracja z Reactem, szybkie kontrakty OpenAPI oraz wygodne podłączanie modułów NLP.

Django można nadal traktować jako punkt odniesienia dla funkcji administracyjnych, ale nie jest częścią rekomendowanego stacku.

## Wariant rekomendowany: Python + React

- Frontend: React, TypeScript, Vite, TanStack Query, Zustand, CSS Modules lub Tailwind.
- Backend: FastAPI, Pydantic, SQLAlchemy, Alembic.
- Baza danych: PostgreSQL.
- Wyszukiwanie podobieństwa: PostgreSQL `pg_trgm` na start, później `pgvector` dla embeddingów.
- Kolejka: Redis + RQ/Celery dla importu i reindeksowania.
- Sprawdzanie pisowni: Hunspell jako szybki lokalny adapter, LanguageTool jako bogatszy adapter.
- Konteneryzacja: Docker Compose dla frontendu, API, Postgresa, Redis i opcjonalnego LanguageTool.

Zalety: dobry kompromis między prostotą, NLP i webowym frontendem.

Ryzyka: trzeba utrzymywać dwa ekosystemy zależności, Python i Node.

## Dlaczego ten stack pasuje do wymagań

- CAT editor wymaga responsywnego frontendu i dobrej obsługi stanu, dlatego React + TypeScript jest praktycznym wyborem.
- Pamięć tłumaczeń wymaga wyszukiwania tekstowego i podobieństwa, dlatego PostgreSQL + `pg_trgm` dobrze działa w MVP.
- Semantyczne sugestie są dobrym rozszerzeniem, dlatego można dodać `pgvector` i embeddingi.
- Backend NLP jest wygodniejszy w Pythonie, bo dostępne są RapidFuzz, spaCy, SentenceTransformers, Hunspell i adaptery LanguageTool.
- FastAPI daje szybkie API i kontrakty OpenAPI, co ułatwia połączenie z frontendem.
- W porównaniu z Django, FastAPI ma mniej narzutów dla API-first backendu i łatwiej utrzymać w nim osobne serwisy NLP.

## Wariant fullstack TypeScript

- Frontend: Next.js albo Remix.
- Backend: API routes/server actions lub osobny NestJS.
- ORM: Prisma.
- Baza danych: PostgreSQL.
- Spellcheck: LanguageTool HTTP, ewentualnie bibliotki Node dla Hunspell.
- Background jobs: BullMQ + Redis.

Zalety: jeden język w większości kodu aplikacji.

Ryzyka: mniej wygodna praca z NLP i modelami lokalnymi.

## Wariant lekki na MVP

- Frontend: React + Vite.
- Backend: FastAPI.
- Baza danych: SQLite na początek, PostgreSQL jako kolejny etap.
- Fuzzy matching: RapidFuzz albo `python-Levenshtein`.
- Spellcheck: prosty adapter słownikowy albo LanguageTool.
- Uruchomienie: lokalnie bez Dockera.

Zalety: najszybsze uruchomienie i mniejsza liczba komponentów.

Ryzyka: słabsza skalowalność i konieczność migracji przy rozwoju projektu.

## Wariant z funkcjami AI

- Baza: wariant Python + React.
- Embeddingi segmentów: SentenceTransformers albo zewnętrzne API embeddingów.
- Semantyczna pamięć tłumaczeń: `pgvector` lub osobny vector store.
- Sugestie tłumaczenia maszynowego: moduł opcjonalny, oddzielony od pamięci tłumaczeń.
- Kontrola jakości: reguły QA dla liczb, tagów, terminologii i długości segmentu.

Zalety: ciekawszy projekt i lepsze sugestie dla segmentów parafrazowanych.

Ryzyka: większa złożoność, wymagania sprzętowe i konieczność oceny jakości modelu.

## Proponowany wybór na start

Najbardziej praktyczny start to React + Vite, FastAPI, PostgreSQL, RapidFuzz, LanguageTool/Hunspell i Docker Compose. Potem można dodać `pgvector` oraz model embeddingowy do semantycznej pamięci tłumaczeń.

## Stan po Etapie 1

W repozytorium wdrożono fundament rekomendowanego stacku:

- Frontend: React, TypeScript i Vite.
- Backend: FastAPI, Pydantic Settings, SQLAlchemy i Alembic.
- Baza danych: PostgreSQL w Docker Compose.
- Usługi pomocnicze: Redis w Docker Compose, przygotowany pod przyszłe zadania asynchroniczne.
- Kontrakt API: startowy OpenAPI w `libs/shared/contracts/openapi.yaml`.

Elementy wymienione w wariancie rekomendowanym, ale jeszcze niewdrożone funkcjonalnie:

- TanStack Query i Zustand.
- Worker RQ/Celery.
- RapidFuzz, Hunspell/LanguageTool.
- `pgvector` i embeddingi.
