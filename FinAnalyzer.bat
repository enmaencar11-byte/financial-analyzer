@echo off
REM ---------------------------------------------------------------
REM  FinAnalyzer Pro - lanzador
REM
REM  Abre el panel en el navegador. Cierre esta ventana para
REM  detenerlo. Debe permanecer abierta mientras use el programa:
REM  es el programa.
REM ---------------------------------------------------------------

title FinAnalyzer Pro
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  No se encontro Python en este equipo.
    echo.
    echo  Instalelo desde https://www.python.org/downloads/
    echo  y marque la casilla "Add Python to PATH" durante la
    echo  instalacion.
    echo.
    pause
    exit /b 1
)

python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  Faltan dependencias. Instalandolas, espere un momento...
    echo.
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo  No se pudieron instalar las dependencias.
        pause
        exit /b 1
    )
)

echo.
echo  Iniciando FinAnalyzer Pro...
echo  Se abrira en el navegador. Para cerrarlo, cierre esta ventana.
echo.

python -m streamlit run app.py

echo.
echo  FinAnalyzer Pro se ha detenido.
pause
