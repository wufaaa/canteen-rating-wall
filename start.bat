@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Canteen Rating Wall

rem ---- 1. find a usable python ----
set "PY="
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"

if not defined PY (
  py -3 -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
  python -c "import sys" >nul 2>&1
  if not errorlevel 1 set "PY=python"
)
if not defined PY (
  echo.
  echo [ERROR] Python not found.
  echo         Install Python 3.9+ from https://www.python.org/downloads/
  echo         and tick "Add Python to PATH" during setup.
  echo.
  pause
  exit /b 1
)

rem ---- 2. first run: create venv ----
if not exist ".venv\Scripts\python.exe" (
  echo [init] Creating virtual environment .venv ...
  %PY% -m venv .venv
  if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
  ) else (
    echo [warn] venv failed, falling back to system python.
  )
)

rem ---- 3. run ----
%PY% run.py
echo.
echo Service stopped.
pause
