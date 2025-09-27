#!/usr/bin/env bash
set -euo pipefail

echo "[rebuild] Build images"
docker compose build --pull

echo "[rebuild] Restart services"
docker compose up -d

echo "[rebuild] Done. Current containers:"
docker compose ps

