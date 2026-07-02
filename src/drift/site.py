"""Single source of truth for the site's public base URL.

Every generated canonical / og:url / og:image / sitemap / JSON-LD URL derives from BASE_URL. The
hand-written literals in src/drift/web/*.html templates mirror it and are kept in sync by
scripts/set_domain.py (guarded by tests/test_site_domain.py) — flip the domain with:

    python scripts/set_domain.py https://www.driftwoodplanning.com

then rebuild (see OPERATIONS.md 'Moving to the custom domain'). Do NOT flip before DNS is live.
"""

BASE_URL = "https://alecmessino.github.io/project"
