import sys
from pathlib import Path

# Ensure the app directory is importable when running tests from repo root or app/
APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
