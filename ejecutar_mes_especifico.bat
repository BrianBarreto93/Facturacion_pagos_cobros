@echo off
setlocal enabledelayedexpansion

title ETL Factura Pago y Cobro - Mes Especifico

echo ======================================================================
echo   ETL FACTURA, PAGO Y COBRO - CARGA DE MES ESPECIFICO EN ORACLE
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

:: Parametros opcionales pasados por linea de comandos (%1 = Anio, %2 = Mes)
set "PARAM_YEAR=%~1"
set "PARAM_MONTH=%~2"

if "%PARAM_YEAR%"=="" (
    set /p "PARAM_YEAR=>> Ingresa el ANIO a procesar (ej. 2026): "
)

if "%PARAM_MONTH%"=="" (
    set /p "PARAM_MONTH=>> Ingresa el MES a procesar (1 al 12, ej. 8 para Agosto): "
)

echo.
echo [INFO] Utilizando Python: "!PYTHON_EXE!"
echo [INFO] Procesando Anio: %PARAM_YEAR% ^| Mes: %PARAM_MONTH%
echo.

"!PYTHON_EXE!" main.py --year %PARAM_YEAR% --month %PARAM_MONTH%
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
