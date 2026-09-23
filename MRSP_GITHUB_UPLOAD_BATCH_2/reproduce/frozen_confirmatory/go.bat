@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYEXE="
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -c "import sys" >nul 2>nul
  if %errorlevel%==0 goto :use_py
)
where python >nul 2>nul
if %errorlevel%==0 (
  python -c "import sys" >nul 2>nul
  if %errorlevel%==0 (
    set "PYEXE=python"
    goto :use_exe
  )
)
set "CAND=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%CAND%" (
  set "PYEXE=%CAND%"
  goto :use_exe
)
for /d %%D in ("%USERPROFILE%\.cache\codex-runtimes\*") do (
  if not defined PYEXE if exist "%%~fD\dependencies\python\python.exe" set "PYEXE=%%~fD\dependencies\python\python.exe"
)
if defined PYEXE goto :use_exe
echo PYTHON_NOT_FOUND
exit /b 2
:use_py
py -3 tools\deps.py || goto :fail
py -3 tools\run_pipeline.py || goto :fail
goto :ok
:use_exe
"%PYEXE%" tools\deps.py || goto :fail
"%PYEXE%" tools\run_pipeline.py || goto :fail
goto :ok
:fail
echo.
echo CONFIRMATORY RUN FAILED. Return the newest MRSP_PREDICTABILITY_CONFIRMATORY_FAILURE_*.zip.
exit /b 1
:ok
echo.
echo COMPLETE. Return only MRSP_PREDICTABILITY_CONFIRMATORY_AUDIT_*.zip to ChatGPT.
exit /b 0
