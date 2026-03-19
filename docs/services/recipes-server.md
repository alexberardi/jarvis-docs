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
| `GET` | `/api/v0/recipes` | List recipes |
| `GET` | `/api/v0/recipes/{id}` | Get a recipe |
| `POST` | `/api/v0/recipes` | Create a recipe |
| `PUT` | `/api/v0/recipes/{id}` | Update a recipe |
| `DELETE` | `/api/v0/recipes/{id}` | Delete a recipe |
| `POST` | `/api/v0/recipes/import-url` | Import a recipe from a URL |
| `POST` | `/api/v0/recipes/import-image` | Import a recipe from an image (via OCR) |
| `GET` | `/api/v0/meal-plans` | List meal plans |
| `POST` | `/api/v0/meal-plans` | Create a meal plan |

## Key Components

- **URL Parsing** (`app/url_parsing/`) -- modular URL recipe parser, split from a 1498-line monolith into focused modules

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `JARVIS_AUTH_BASE_URL` | Auth service URL |

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
