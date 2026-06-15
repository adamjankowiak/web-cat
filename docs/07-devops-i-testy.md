# DevOps i testy

## Uruchamianie lokalne

Docelowo projekt moze miec dwa tryby uruchomienia:

- tryb prosty: backend i frontend uruchamiane lokalnie,
- tryb kontenerowy: Docker Compose z baza danych i uslugami pomocniczymi.

Po Etapie 1 oba tryby maja przygotowane pliki uruchomieniowe. Szczegolowe komendy sa opisane w `README.md`.

Komponenty w Docker Compose:

- `frontend`,
- `api`,
- `postgres`,
- `redis`,
- opcjonalnie `languagetool`.

Status po Etapie 1:

- `frontend`, `api`, `postgres` i `redis` sa skonfigurowane w `docker-compose.yml`,
- `worker` i `languagetool` pozostaja planowanymi rozszerzeniami,
- migracje uruchamia `alembic upgrade head` z katalogu `apps/api`.

## Testy backendu

Zakres minimalny:

- healthcheck API,
- normalizacja tekstu dla pamieci tlumaczen,
- exact match,
- fuzzy match,
- wyszukiwanie terminow slownikowych,
- odpowiedz spellcheckera,
- import prostego dokumentu.

Po Etapie 1 istnieje test `GET /health`; pozostale testy wejda razem z implementacja modulow CAT.

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
