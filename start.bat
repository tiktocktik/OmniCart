@echo off
setlocal EnableExtensions
title OmniCart Launcher

REM OmniCart launcher for Windows.
REM Usage: start.bat        -> development server (hot reload)
REM        start.bat prod   -> production build + server
REM
REM The backend uses 127.0.0.1:8000 and the frontend uses localhost:3000.

cd /d "%~dp0"
set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%omnicart-backend"
set "FRONTEND_DIR=%ROOT%omnicart-app"

echo ============================================
echo   OmniCart - local launcher
echo ============================================
echo.

REM ---------- Pick the Python interpreter ----------
set "PYTHON=python"
if exist "%BACKEND_DIR%\.venv\Scripts\python.exe" (
  set "PYTHON=%BACKEND_DIR%\.venv\Scripts\python.exe"
)

"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python was not found.
  echo Install Python 3.10+ and make sure "python" is on PATH.
  goto :fail
)

REM ---------- Backend dependencies ----------
"%PYTHON%" -c "import fastapi, uvicorn, pydantic, bs4, requests, cryptography" >nul 2>&1
if errorlevel 1 (
  echo [WARN] Backend dependencies are missing.
  echo.
  echo Install them with:
  echo   "%PYTHON%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
  echo.
  choice /C YN /N /M "Install them now? [Y/N] "
  if errorlevel 2 goto :no_backend_deps

  echo Installing backend dependencies...
  "%PYTHON%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
  if errorlevel 1 (
    echo [ERROR] pip install failed.
    goto :fail
  )

  "%PYTHON%" -c "import fastapi, uvicorn, pydantic, bs4, requests, cryptography" >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] Backend dependencies are still missing.
    goto :fail
  )
)

REM ---------- Node.js ----------
where npm >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js / npm was not found.
  echo Install Node.js 20+ from https://nodejs.org and run this file again.
  goto :fail
)

if not exist "%FRONTEND_DIR%\node_modules" (
  echo Installing frontend dependencies...
  pushd "%FRONTEND_DIR%"
  if exist "package-lock.json" (
    call npm ci
  ) else (
    call npm install
  )
  if errorlevel 1 (
    popd
    echo [ERROR] npm install failed.
    goto :fail
  )
  popd
)

REM ---------- Frontend config ----------
if not exist "%FRONTEND_DIR%\.env.local" (
  if exist "%FRONTEND_DIR%\.env.example" (
    copy /Y "%FRONTEND_DIR%\.env.example" "%FRONTEND_DIR%\.env.local" >nul
    echo Created %FRONTEND_DIR%\.env.local
  )
)

REM ---------- Reuse anything already running ----------
set "BACKEND_UP="
netstat -ano | findstr /C:":8000" | findstr /C:"LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo Backend already listening on port 8000 - reusing it.
  set "BACKEND_UP=1"
)

set "FRONTEND_UP="
netstat -ano | findstr /C:":3000" | findstr /C:"LISTENING" >nul 2>&1
if not errorlevel 1 (
  echo Frontend already listening on port 3000 - reusing it.
  set "FRONTEND_UP=1"
)

REM ---------- Start the backend ----------
if not defined BACKEND_UP (
  echo Starting backend on http://127.0.0.1:8000 ...
  start "OmniCart Backend" /D "%BACKEND_DIR%" cmd /k ""%PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
)

REM ---------- Start the frontend ----------
if not defined FRONTEND_UP (
  if /I "%~1"=="prod" (
    if not exist "%FRONTEND_DIR%\.next\BUILD_ID" (
      echo Building frontend for production...
      pushd "%FRONTEND_DIR%"
      call npm run build
      if errorlevel 1 (
        popd
        echo [ERROR] Frontend build failed.
        goto :fail
      )
      popd
    )
    echo Starting frontend on http://localhost:3000 ...
    start "OmniCart Frontend" /D "%FRONTEND_DIR%" cmd /k "npm run start"
  ) else (
    echo Starting frontend on http://localhost:3000 ...
    start "OmniCart Frontend" /D "%FRONTEND_DIR%" cmd /k "npm run dev"
  )
)

REM ---------- Wait for the backend ----------
echo.
echo Waiting for the backend...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline=(Get-Date).AddSeconds(60); while((Get-Date) -lt $deadline){ try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2; if($r.StatusCode -eq 200){ exit 0 } } catch {}; Start-Sleep -Milliseconds 500 }; exit 1"
if errorlevel 1 (
  echo [ERROR] The backend did not become ready within 60 seconds.
  echo Check the "OmniCart Backend" window for the error.
  goto :fail
)
echo Backend is ready.

REM ---------- Wait for the frontend ----------
echo Waiting for the frontend...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$deadline=(Get-Date).AddSeconds(90); while((Get-Date) -lt $deadline){ try { $r=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:3000' -TimeoutSec 3; if($r.StatusCode -eq 200){ exit 0 } } catch {}; Start-Sleep -Milliseconds 500 }; exit 1"
if errorlevel 1 (
  echo [ERROR] The frontend did not become ready within 90 seconds.
  echo Check the "OmniCart Frontend" window for the error.
  goto :fail
)
echo Frontend is ready.

echo.
echo ============================================
echo   OmniCart is running
echo   App:  http://localhost:3000
echo   API:  http://127.0.0.1:8000/docs
echo.
echo   Close the "OmniCart Backend" and
echo   "OmniCart Frontend" windows to stop.
echo ============================================
echo.

start "" "http://localhost:3000"
ping -n 4 127.0.0.1 >nul
exit /b 0

:no_backend_deps
echo.
echo Install the dependencies and run this file again:
echo   "%PYTHON%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
goto :fail

:fail
echo.
pause
exit /b 1
