# Recipes Server

The recipes server provides CRUD operations for recipes and meal planning. It supports importing recipes from URLs (with intelligent HTML parsing), OCR-based recipe extraction from images, and meal plan generation.

## Quick Reference

| | |
|---|---|
| **Port** | 7030 |
| **Health endpoint** | `GET /health` |
| **Source** | `jarvis-recipes-server/` |
| **Framework** | FastAPI + Uvicorn |
| **Database** | PostgreSQL |
| **Tier** | 3 - Specialized |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/recipes` | List recipes |
| `GET` | `/recipes/{id}` | Get a recipe |
| `POST` | `/recipes` | Create a recipe |
| `PATCH` | `/recipes/{id}` | Update a recipe |
| `DELETE` | `/recipes/{id}` | Delete a recipe |
| `POST` | `/recipes/import/url` | Import a recipe from a URL |
| `POST` | `/recipes/import/image` | Import a recipe from an image (via OCR) |
| `POST` | `/recipes/parse-url` | Parse a recipe URL synchronously (also `/parse-url/async` + `/jobs/{job_id}` for the async path) |
| `POST` | `/meal-plans/generate/jobs` | Queue meal-plan generation (poll `GET /meal-plans/generate/jobs/{job_id}`) |
| `GET` | `/planner/current` | Get the current meal plan (also `POST /planner/draft` + `/planner/commit`) |

## Key Components

- **URL Parsing** (`app/url_parsing/`) -- modular URL recipe parser, split from a 1498-line monolith into focused modules

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `AUTH_SECRET_KEY` | JWT validation key — must match jarvis-auth's `AUTH_SECRET_KEY` |
| `JARVIS_CONFIG_URL` | Config service URL for service discovery |
| `JARVIS_APP_ID` / `JARVIS_APP_KEY` | App-to-app credentials for outbound calls (OCR, LLM proxy) |

## Dependencies

- **PostgreSQL** -- recipe and meal plan storage
- **jarvis-auth** -- app-to-app auth validation
- **jarvis-logs** -- structured logging
- **jarvis-settings-client** -- runtime settings
- **jarvis-ocr-service** -- image-based recipe import (optional)

## Dependents

- **jarvis-command-center** -- recipe-related voice commands

## Impact if Down

No recipe CRUD or meal planning. Voice commands related to recipes (search, add, plan meals) will fail. Other voice commands are unaffected.
