@echo off
echo Starting YouTube Transcript Processor server...
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.8+ and add to PATH.
    pause
    exit /b 1
)

REM Check for .env file
if not exist .env (
    echo Error: .env file not found. Copy .env.example to .env and set your OPENAI_API_KEY.
    pause
    exit /b 1
)

REM Start Flask server in new window
start "YouTube Transcript Processor" python app.py

REM Wait 3 seconds for server to start
timeout /t 3 /nobreak > nul

REM Open browser
start http://127.0.0.1:5000

echo Server started in new window.
echo Browser opened at http://127.0.0.1:5000
echo.
echo To stop the server, close the command window running the server.
pause