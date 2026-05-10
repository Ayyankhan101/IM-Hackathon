@echo off
REM GitMind launcher — Windows
REM Starts FastAPI backend (port 8000) + React dev server (port 3000)
REM Each runs in its own console window. Close windows to stop.

setlocal
cd /d "%~dp0"

REM ── Setup checks ──────────────────────────────────────────────────────────

if not exist "backend\.env" (
    echo ERROR: backend\.env missing. Create it with: OPENAI_API_KEY=sk-...
    pause
    exit /b 1
)

if not exist "backend\venv" (
    echo Setting up Python venv...
    python -m venv backend\venv
    if errorlevel 1 (
        echo ERROR: python not found. Install Python 3.11+.
        pause
        exit /b 1
    )
    call backend\venv\Scripts\activate.bat
    python -m pip install --upgrade pip --quiet
    pip install --quiet "fastapi[standard]" uvicorn langgraph langchain langchain-openai ^
        langchain-text-splitters chromadb gitpython tiktoken python-dotenv diskcache ^
        websockets semgrep
    deactivate
)

if not exist "frontend\node_modules" (
    echo Installing npm packages...
    pushd frontend
    call npm install
    if errorlevel 1 (
        echo ERROR: npm install failed. Install Node.js 18+.
        popd
        pause
        exit /b 1
    )
    popd
)

REM ── Backend ───────────────────────────────────────────────────────────────

echo Starting backend on http://127.0.0.1:8000 ...
start "GitMind Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

REM Wait briefly for backend to come up
timeout /t 5 /nobreak >nul

REM ── Frontend ──────────────────────────────────────────────────────────────

echo Starting frontend on http://localhost:3000 ...
start "GitMind Frontend" cmd /k "cd /d %~dp0frontend && set BROWSER=none && npm start"

echo.
echo ──────────────────────────────────────────────
echo   GitMind running
echo   Backend:  http://127.0.0.1:8000
echo   Frontend: http://localhost:3000
echo   Close the two console windows to stop.
echo ──────────────────────────────────────────────
echo.
pause
endlocal
