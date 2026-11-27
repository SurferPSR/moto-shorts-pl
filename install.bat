@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Uruchamiam instalator...
python moto.py install
if errorlevel 1 (
  echo.
  echo Cos poszlo nie tak. Sprawdz, czy Python jest zainstalowany.
)
echo.
echo Nacisnij dowolny klawisz, aby zamknac...
pause >nul
