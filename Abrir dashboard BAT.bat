@echo off
setlocal
set "PYTHON_EXE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if not exist "%PYTHON_EXE%" (
  where py >nul 2>nul
  if errorlevel 1 (
    echo No se encontro Python. Instala Python 3 o abre el dashboard desde Codex.
    pause
    exit /b 1
  )
  set "PYTHON_EXE=py -3"
)

start "Servidor local Dashboard BAT" %PYTHON_EXE% "%~dp0dashboard_server.py"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8765/dashboard-bat.html"
endlocal
