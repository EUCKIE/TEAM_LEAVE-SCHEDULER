import sys
from pathlib import Path

# Add parent directory to sys.path so tests can import backend modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
