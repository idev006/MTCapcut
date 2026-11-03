@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
if not exist ".venv\Scripts\python.exe" (
  echo Python environment is missing at %~dp0.venv
  echo Prepare the project virtual environment before running MTCapcut.
  exit /b 1
)
".venv\Scripts\python.exe" -m mtcapcut --config "%~dp0config.toml" %*
exit /b %errorlevel%
