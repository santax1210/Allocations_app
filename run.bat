@echo off
if "%1"=="app" goto run_app
if "%1"=="test" goto run_test
if "%1"=="clean" goto clean_port
echo Uso: 
echo   run app   - Ejecutar aplicacion (Home.py con multi-page)
echo   run clean - Limpiar puerto 8501 y procesos
echo   run test  - Ejecutar pruebas del procesador
pause
exit /b 1

:clean_port
echo Limpiando procesos de Streamlit...
call cleanup.bat
echo Listo!
pause
exit /b 0

:run_app
echo Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error al activar el entorno virtual. Verifica que exista venv\Scripts\activate.bat
    pause
    exit /b 1
)
echo Ejecutando Refinitiv Automation...
echo.
echo Paginas disponibles:
echo   - Home (inicio)
echo   - Carga de Archivos
echo   - Validacion de Monedas
echo.
echo Presiona Ctrl+C para detener el servidor
echo.
python -m streamlit run Home.py
pause
exit /b 0

:run_test
echo Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error al activar el entorno virtual. Verifica que exista venv\Scripts\activate.bat
    pause
    exit /b 1
)
echo Ejecutando pruebas del procesador...
python tests\test_processor.py
pause