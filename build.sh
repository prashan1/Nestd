#!/bin/bash
echo "Building CA File Manager..."
pyinstaller --onefile --windowed --name=CAFileManager main.py
echo ""
echo "Done! Find CAFileManager in the dist/ folder."
