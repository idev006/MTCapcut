@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
if not exist ".venv\Scripts\python.exe" (
  echo Python environment is missing at %~dp0.venv
  echo Prepare the project virtual environment before running MTCapcut tests.
  exit /b 1
)
".venv\Scripts\python.exe" -m unittest discover -s tests -v
exit /b %errorlevel%
