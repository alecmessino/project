"""Entry point: python -m launch_skew.web"""

import sys
from pathlib import Path

# Allow running without install: python -m launch_skew.web
_ROOT = Path(__file__).parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from launch_skew.config import Settings
from launch_skew.web.server import DEFAULT_CONFIG, DemoProvider, serve

if __name__ == "__main__":
    cfg_path = DEFAULT_CONFIG if DEFAULT_CONFIG.exists() else None
    settings = Settings.load(cfg_path) if cfg_path else Settings()
    provider = DemoProvider(settings.skew)
    serve(settings, provider,
          host=settings.skew.server.host,
          port=settings.skew.server.port)
