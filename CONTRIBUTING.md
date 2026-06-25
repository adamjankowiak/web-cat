# Współpraca

Dziękujemy za zainteresowanie projektem **web-cat**. Ten dokument opisuje, jak
przygotować środowisko i co sprawdzić przed wysłaniem zmian.

## Środowisko

Pełne instrukcje uruchomienia znajdują się w [README](README.md) w sekcjach
[Uruchomienie lokalne](README.md#uruchomienie-lokalne) i
[Uruchomienie przez Docker](README.md#uruchomienie-przez-docker).

W skrócie:

```powershell
# backend
cd apps/api
python -m pip install -e .[dev]
alembic upgrade head

# frontend
cd apps/frontend
npm install
```

## Zanim wyślesz Pull Request

Uruchom komplet testów i kontrolę jakości. Te same kroki uruchamia pipeline CI:

```powershell
# backend
cd apps/api
python -m ruff check .
python -m ruff format --check .
python -m pytest

# frontend
cd apps/frontend
npm run lint
npm run build
npm run test
```

Pomocniczo dostępne są skróty: `make lint`, `make test-api`, `make test-frontend`
oraz `scripts/dev.ps1` (np. `.\scripts\dev.ps1 test-api`).

## Styl commitów

Repozytorium używa stylu [Conventional Commits](https://www.conventionalcommits.org/)
(`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`, `build:`, `ci:`). Pisz
zwięzły opis tego, co faktycznie zmienia commit.

## Zgłoszenia

Błędy i propozycje zgłaszaj przez [Issues](../../issues). Sprawy bezpieczeństwa opisuje
[SECURITY.md](SECURITY.md).
