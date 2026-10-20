@echo off
title SchematicBuq
cd /d "%~dp0"

set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY (where py >nul 2>nul && set "PY=py")

if not defined PY (
  echo No se encontro Python. Instalalo desde https://www.python.org/downloads/
  pause
  exit /b 1
)

%PY% -c "import PyQt5" >nul 2>nul
if errorlevel 1 (
  echo Instalando dependencias (solo la primera vez)...
  %PY% -m pip install --user -r requirements.txt
)

%PY% main.py
if errorlevel 1 pause
