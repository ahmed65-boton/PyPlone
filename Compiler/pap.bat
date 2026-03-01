@echo off
setlocal

set "ROOT=%~dp0.."
set "PY=%ROOT%\python\python.exe"

if not exist "%PY%" (
  echo [pap] ERROR: embedded python not found:
  echo %PY%
  exit /b 1
)

if "%~1"=="" goto :help

if /I "%~1"=="get" goto :get
if /I "%~1"=="remove" goto :remove
if /I "%~1"=="list" goto :list
if /I "%~1"=="upgrade" goto :upgrade

goto :help


:get
if "%~2"=="" (
  echo [pap] Please specify a package.
  exit /b 1
)
echo Installing %~2 ...
"%PY%" -m pip install %~2
exit /b %errorlevel%


:remove
if "%~2"=="" (
  echo [pap] Please specify a package.
  exit /b 1
)
echo Removing %~2 ...
"%PY%" -m pip uninstall -y %~2
exit /b %errorlevel%


:list
"%PY%" -m pip list
exit /b 0


:upgrade
echo Upgrading pip...
"%PY%" -m pip install --upgrade pip
exit /b %errorlevel%


:help
echo PyPlone Package Manager (pap)
echo.
echo Usage:
echo   pap get [package]
echo   pap remove [package]
echo   pap list
echo   pap upgrade
exit /b 0