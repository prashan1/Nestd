#!/bin/bash
echo "Building Nestd File Manager..."
pyinstaller --onefile --windowed --name=Nestd main.py
echo ""
echo "Done! Find Nestd in the dist/ folder."
