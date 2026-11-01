@echo off
REM Inicia la app Flet del Optimizador de Inventario y Pedidos
cd /d "%~dp0"
where uv >nul 2>nul
if %errorlevel%==0 (
  uv run python main.py
) else (
  python main.py
)
pause
