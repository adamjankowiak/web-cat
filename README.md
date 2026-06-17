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

## Uruchomienie

Wariant kontenerowy:

```powershell
Copy-Item .env.example .env
docker compose up -d --build
docker compose exec -T api alembic upgrade head
```

Wymagania dla wariantu kontenerowego:

- uruchomiony Docker Desktop,
- aktywny kontekst Docker Desktop Linux Engine,
- wolne porty `5432`, `6379`, `8000` i `5173`.

Jeśli pojawi się błąd podobny do `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`, Docker Desktop nie działa albo Linux Engine nie zdążył jeszcze wystartować. Uruchom Docker Desktop, poczekaj aż pokaże status `Docker Desktop is running`, a potem sprawdź:

```powershell
docker version
docker compose config
```

Po starcie:

- API: `http://localhost:8000/health`
- dokumentacja OpenAPI FastAPI: `http://localhost:8000/docs`
- frontend: `http://localhost:5173`

Szybka weryfikacja Etapu 2:

```powershell
$payload = @{
  filename = "sample.txt"
  content = "Save the file. Close the window."
  source_language = "en"
  target_language = "pl"
  segmentation_strategy = "sentence"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/documents -Method Post -ContentType "application/json" -Body $payload
```

Szybka weryfikacja eksportu i formatow CAT z Etapu 6:

```powershell
$document = Invoke-RestMethod -Uri http://localhost:8000/documents -Method Post -ContentType "application/json" -Body $payload
$documentId = $document.document.id

Invoke-WebRequest -Uri "http://localhost:8000/documents/$documentId/export.txt" -OutFile translated.txt
Invoke-WebRequest -Uri "http://localhost:8000/documents/$documentId/export.xliff" -OutFile document.xliff
Invoke-WebRequest -Uri "http://localhost:8000/translation-memory/export.tmx" -OutFile translation-memory.tmx
Invoke-WebRequest -Uri "http://localhost:8000/glossary/export.tbx" -OutFile glossary.tbx
```

Import TMX i TBX przyjmuje XML w ciele requestu:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/translation-memory/import-tmx -Method Post -ContentType "application/xml" -InFile translation-memory.tmx
Invoke-RestMethod -Uri http://localhost:8000/glossary/import-tbx -Method Post -ContentType "application/xml" -InFile glossary.tbx
```

Eksport TXT uzywa `target_text`, a dla segmentow bez tlumaczenia eksportuje `source_text`, zeby
dokument roboczy nadal mozna bylo pobrac.

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

Backend wykorzystuje RapidFuzz do fuzzy matchingu pamieci tlumaczen. Zaleznosc jest instalowana
razem z pakietem API przez:

```powershell
cd apps/api
python -m pip install -e .[dev]
```

Pomocniczy skrypt PowerShell:

```powershell
.\scripts\dev.ps1 compose
.\scripts\dev.ps1 api
.\scripts\dev.ps1 frontend
.\scripts\dev.ps1 migrate
.\scripts\dev.ps1 test-api
```
