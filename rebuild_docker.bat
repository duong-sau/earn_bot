@echo off
setlocal enabledelayedexpansion

echo [rebuild] Building images
docker compose build --pull || goto :error

echo [rebuild] Restart services
docker compose up -d || goto :error

echo [rebuild] Current containers:
docker compose ps

echo Done.
exit /b 0

:error
echo Failed.
exit /b 1

