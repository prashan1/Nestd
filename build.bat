@echo off
echo Building CA File Manager for Windows...
echo.

echo Installing / checking dependencies...
pip install customtkinter pyinstaller --quiet
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Make sure Python is installed and on PATH.
    pause
    exit /b 1
)

echo.
echo Running PyInstaller...
pyinstaller --onefile --windowed --name=NestDFileManager main.py
if %errorlevel% neq 0 (
    echo ERROR: Build failed. See output above.
    pause
    exit /b 1
)

echo.
echo Done! Find NestDFileManager.exe in the dist\ folder.
pause
