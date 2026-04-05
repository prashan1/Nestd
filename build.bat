@echo off
echo Building CA File Manager for Windows...
pyinstaller --onefile --windowed --icon=assets/icon.ico --name=CAFileManager main.py
echo.
echo Done! Find CAFileManager.exe in the dist/ folder.
pause
