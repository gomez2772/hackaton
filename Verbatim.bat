@echo off
rem Verbatim: double-click launcher for Windows. Logic lives in launcher\launch.py.
setlocal
cd /d "%~dp0"
title Verbatim

set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if defined PY goto run
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=python"
if defined PY goto run

echo.
echo Instala Python 3.11 o superior desde python.org (marca "Add Python to PATH")
echo.
pause
exit /b 1

:run
%PY% launcher\launch.py %*
if errorlevel 1 (
    echo.
    echo Verbatim se ha detenido con un error. Lee los mensajes de arriba.
    pause
    exit /b 1
)
endlocal
