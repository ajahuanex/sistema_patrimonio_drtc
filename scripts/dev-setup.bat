@echo off
echo 🚀 Setting up development environment...

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 18 or higher.
    pause
    exit /b 1
)

echo ✅ Node.js version: 
node --version

REM Install frontend dependencies
echo 📦 Installing frontend dependencies...
cd frontend
call npm install

if %errorlevel% neq 0 (
    echo ❌ Failed to install frontend dependencies
    pause
    exit /b 1
)

echo ✅ Frontend dependencies installed successfully

REM Go back to root directory
cd ..

REM Install Python dependencies (if requirements.txt exists)
if exist requirements.txt (
    echo 📦 Installing Python dependencies...
    pip install -r requirements.txt
    
    if %errorlevel% neq 0 (
        echo ❌ Failed to install Python dependencies
        pause
        exit /b 1
    )
    
    echo ✅ Python dependencies installed successfully
)

echo 🎉 Development environment setup complete!
echo.
echo To start development:
echo 1. Start Django backend: python manage.py runserver
echo 2. Start React frontend: cd frontend ^&^& npm run dev
echo.
echo Frontend will be available at: http://localhost:3000
echo Backend will be available at: http://localhost:8000

pause