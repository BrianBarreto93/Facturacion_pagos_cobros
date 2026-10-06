@echo off
setlocal enabledelayedexpansion

title ETL Factura Pago y Cobro - Mes mas reciente

echo ======================================================================
echo   ETL FACTURA, PAGO Y COBRO - CARGA DEL MES MAS RECIENTE EN ORACLE
echo ======================================================================
echo.

:: Cambiar al directorio donde se encuentra este archivo .bat
cd /d "%~dp0"

:: Detectar el interprete de Python del entorno virtual
set "PYTHON_EXE="

if exist "d:\1. CX\Proyectos\claro_nps_auto\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=d:\1. CX\Proyectos\claro_nps_auto\.venv\Scripts\python.exe"
) else if exist "%~dp0..\claro_nps_auto\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0..\claro_nps_auto\.venv\Scripts\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [INFO] Utilizando Python: "!PYTHON_EXE!"
echo [INFO] Buscando automaticamente el mes mas reciente en OneDrive...
echo.

"!PYTHON_EXE!" main.py
set EXIT_CODE=!ERRORLEVEL!

echo.
echo ======================================================================
if !EXIT_CODE! EQU 0 (
    echo   [EXITO] El proceso ha finalizado correctamente.
) else (
    echo   [ERROR] Ocurrio un fallo durante la ejecucion. Codigo: !EXIT_CODE!
)
echo ======================================================================
echo.
pause
