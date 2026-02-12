@echo off
echo ======================================================================
echo           VoiceMind Meeting System - Automated Setup
echo ======================================================================
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo X Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)
echo + Python found
echo.

REM Check MySQL installation
echo Checking MySQL installation...
mysql --version >nul 2>&1
if errorlevel 1 (
    echo X MySQL is not installed. Please install MySQL 8.0 or higher.
    pause
    exit /b 1
)
echo + MySQL found
echo.

REM Create virtual environment
echo Creating Python virtual environment...
python -m venv venv
call venv\Scripts\activate
echo + Virtual environment created
echo.

REM Install Python dependencies
echo Installing Python dependencies...
pip install --upgrade pip
pip install -r backend\requirements.txt
echo + Dependencies installed
echo.

REM Initialize database
echo Initializing MySQL database...
python database\init_db.py
echo + Database initialized
echo.

REM Create .env file if not exists
if not exist .env (
    echo Creating .env configuration file...
    copy .env.example .env
    echo ! Please edit .env file and add your configuration
)
echo.

echo ======================================================================
echo + Setup completed successfully!
echo ======================================================================
echo.
echo Next steps:
echo 1. Edit .env file with your MySQL password and OpenAI API key
echo 2. Upload ESP32 Arduino code to your device
echo 3. Start the server: python backend\server.py
echo 4. Run the client: python client\meeting_client.py
echo.
pause