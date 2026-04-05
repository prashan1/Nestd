#!/bin/bash
echo "Building FileTrail File Manager..."
pyinstaller --onefile --windowed --name=FileTrail main.py
echo ""
echo "Done! Find FileTrail in the dist/ folder."
