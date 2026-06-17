param(
    [ValidateSet("compose", "api", "frontend", "migrate", "test-api", "test-frontend", "test-e2e")]
    [string]$Target = "compose"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

function Invoke-InProject {
    param(
        [string]$Path,
        [scriptblock]$Command
    )

    Push-Location $Path
    try {
        & $Command
    }
    finally {
        Pop-Location
    }
}

switch ($Target) {
    "compose" {
        docker compose up --build
    }
    "api" {
        Invoke-InProject "$Root\apps\api" {
            python -m uvicorn cat_api.main:app --reload --host 127.0.0.1 --port 8000
        }
    }
    "frontend" {
        Invoke-InProject "$Root\apps\frontend" {
            npm run dev
        }
    }
    "migrate" {
        Invoke-InProject "$Root\apps\api" {
            alembic upgrade head
        }
    }
    "test-api" {
        Invoke-InProject "$Root\apps\api" {
            python -m pytest
        }
    }
    "test-frontend" {
        Invoke-InProject "$Root\apps\frontend" {
            npm run test
        }
    }
    "test-e2e" {
        Invoke-InProject "$Root\apps\frontend" {
            npm run test:e2e
        }
    }
}
