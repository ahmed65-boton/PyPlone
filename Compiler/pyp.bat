@echo off
setlocal

REM Project root = one folder above Compiler
set "ROOT=%~dp0.."
set "PY=%ROOT%\python\python.exe"
set "COMPILER=%~dp0pyplone.py"

if not exist "%PY%" (
  echo [pyp] ERROR: embedded python not found:
  echo %PY%
  exit /b 1
)

if not exist "%COMPILER%" (
  echo [pyp] ERROR: compiler script not found:
  echo %COMPILER%
  exit /b 1
)

"%PY%" "%COMPILER%" %*
exit /b %errorlevel%