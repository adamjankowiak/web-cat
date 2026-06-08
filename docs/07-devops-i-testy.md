# DevOps i testy

## Uruchamianie lokalne

Docelowo projekt moze miec dwa tryby uruchomienia:

- tryb prosty: backend i frontend uruchamiane lokalnie,
- tryb kontenerowy: Docker Compose z baza danych i uslugami pomocniczymi.

Komponenty w Docker Compose:

- `frontend`,
- `api`,
- `worker`,
- `postgres`,
- `redis`,
- opcjonalnie `languagetool`.

## Testy backendu

Zakres minimalny:

- normalizacja tekstu dla pamieci tlumaczen,
- exact match,
- fuzzy match,
- wyszukiwanie terminow slownikowych,
- odpowiedz spellcheckera,
- import prostego dokumentu.

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
