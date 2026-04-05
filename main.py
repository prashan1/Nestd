import sys
import os

# Ensure project root is on the path (needed when running as a bundled .exe)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
