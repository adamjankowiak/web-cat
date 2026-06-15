# web-cat

Webowa platforma CAT (Computer-Assisted Translation) do wspomagania pracy tłumacza.

## Główna idea

Projekt ma być samodzielną, ciekawą platformą CAT, a nie prostym przepisaniem notebooków laboratoryjnych. Notebooki z `translation-labs` są tylko opcjonalnym tłem: pokazują techniki, które były już przećwiczone, ale decyzje projektowe powinny wynikać z wymagań aplikacji.

Najciekawszy kierunek to edytor CAT z hybrydową pamięcią tłumaczeń: exact match, fuzzy match, semantyczne podobieństwo, słownik kontekstowy, kontrola terminologii i sprawdzanie pisowni po stronie docelowej.

## Zakres MVP

- Webowy frontend z edytorem segmentów.
- Pamięć tłumaczeń: dokładne i rozmyte dopasowania segmentów.
- Słownik kontekstowy: terminy, definicje, przykłady użycia i ograniczenia domenowe.
- Sprawdzanie pisowni po stronie języka docelowego.

## Struktura

- `apps/frontend` - aplikacja webowa.
- `apps/api` - backend HTTP/API.
- `apps/worker` - zadania asynchroniczne, np. import, indeksowanie, analiza dokumentów.
- `libs/shared` - wspólne kontrakty API i typy.
- `libs/nlp` - logika segmentacji, fuzzy matchingu i sprawdzania pisowni.
- `data` - przykładowe dane developerskie.
- `docs` - decyzje architektoniczne i plan prac.
- `infra` - konfiguracje Docker, Postgres, Nginx.
- `notebooks` - opcjonalne notebooki lub eksporty z laboratoriów.
- `tests` - testy end-to-end i fixture'y.

## Dokumentacja projektowa

- [Wprowadzenie](docs/00-wprowadzenie.md)
- [Stack i architektura](docs/01-stack-i-architektura.md)
- [Plan etapów](docs/02-plan-etapow.md)
- [Model danych](docs/03-model-danych.md)
- [Moduły CAT](docs/04-moduly-cat.md)
- [Notebooki i eksperymenty](docs/05-notebooks-i-eksperymenty.md)
- [Kontrakty API](docs/06-api-kontrakty.md)
- [DevOps i testy](docs/07-devops-i-testy.md)
- [Opcjonalna mapa laboratoriów](docs/08-mapa-laboratoriow.md)
- [Koncepcja projektu i narzędzia](docs/09-koncepcja-projektu-i-narzedzia.md)

## Uruchomienie Etapu 1

Wariant kontenerowy:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Po starcie:

- API: `http://localhost:8000/health`
- dokumentacja OpenAPI FastAPI: `http://localhost:8000/docs`
- frontend: `http://localhost:5173`

Wariant lokalny:

```powershell
Copy-Item .env.example .env
cd apps/api
python -m pip install -e .[dev]
alembic upgrade head
python -m uvicorn cat_api.main:app --reload
```

Frontend lokalnie wymaga Node.js i NPM:

```powershell
cd apps/frontend
npm install
npm run dev
```

Pomocniczy skrypt PowerShell:

```powershell
.\scripts\dev.ps1 compose
.\scripts\dev.ps1 api
.\scripts\dev.ps1 frontend
.\scripts\dev.ps1 migrate
.\scripts\dev.ps1 test-api
```
