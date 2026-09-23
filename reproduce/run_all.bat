@echo off
setlocal
if "%~1"=="" (
  echo Usage: run_all.bat C:\path\to\CJ9
  exit /b 2
)
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0run_full_reproduction.py" --cj9 "%~1"
  exit /b %errorlevel%
)
python "%~dp0run_full_reproduction.py" --cj9 "%~1"
exit /b %errorlevel%
