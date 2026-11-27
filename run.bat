@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Uruchamiam program Moto Shorts PL...
python moto.py
if errorlevel 9009 (
  echo.
  echo Nie widze Pythona. Zainstaluj go z python.org i uruchom ponownie.
)
echo.
echo Nacisnij dowolny klawisz, aby zamknac...
pause >nul
