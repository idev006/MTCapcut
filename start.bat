@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"

if not exist ".venv\Scripts\python.exe" (
  echo Python environment is missing at %~dp0.venv
  echo Create or restore the project environment before starting MTCapcut.
  exit /b 1
)
if not exist "config.toml" (
  echo config.toml is missing. Copy config.example.toml and edit the paths.
  exit /b 1
)

:menu
cls
echo ========================================
echo             MTCapcut Engines
echo ========================================
echo 1. Check environment
echo 2. List project assets
echo 3. Show command help
echo 0. Exit
echo.
set "MT_MENU_CHOICE="
set /p MT_MENU_CHOICE=Select: 
if not defined MT_MENU_CHOICE exit /b 0

if "%MT_MENU_CHOICE%"=="1" (
  call "%~dp0doctor.bat"
  pause
  goto menu
)
if "%MT_MENU_CHOICE%"=="2" (
  set /p MT_PROJECT_ID=Project ID: 
  call "%~dp0mtcapcut.bat" assets "%MT_PROJECT_ID%"
  pause
  goto menu
)
if "%MT_MENU_CHOICE%"=="3" (
  ".venv\Scripts\python.exe" -m mtcapcut --help
  pause
  goto menu
)
if "%MT_MENU_CHOICE%"=="0" exit /b 0

echo Invalid selection.
pause
goto menu
