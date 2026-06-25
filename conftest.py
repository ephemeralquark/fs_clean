"""Configure pytest to find the src package."""

import sys
from pathlib import Path

# Add the src directory to the Python path so `import src` works.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
