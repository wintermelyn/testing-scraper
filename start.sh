#!/usr/bin/env bash

# Instala dependencias de Playwright
poetry run playwright install --with-deps

# Inicia el servidor FastAPI
poetry run uvicorn api.main:app --host 0.0.0.0 --port 10000
