import sys
from pathlib import Path

# Make the repository root importable so tests can import `backend.*`
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
