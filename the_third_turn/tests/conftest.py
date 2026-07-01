"""Put the_third_turn/ on sys.path so `import sources...`, `config`, etc. resolve
when tests run from the repo root (pytest the_third_turn)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
