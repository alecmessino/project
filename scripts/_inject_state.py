#!/usr/bin/env python3
"""One-off: rebuild the embedded window.__STATE__ JSON in docs/statemap.html from the
live build_statemap() model (which now carries the 'Coordination Impact' label fix) and
overwrite the stale blob. Does NOT touch HTML/CSS — only the JSON data blob."""
import json, re, sys, pathlib
sys.path.insert(0, "src")
from drift.statemap import build_statemap

DOCS = pathlib.Path("docs/statemap.html")
fresh = json.dumps(build_statemap())
assert '"label": "Coordination Impact"' in fresh, "label not updated in built JSON!"

html = DOCS.read_text()
m = re.search(r"window\.__STATE__ = (.*?);\s*\n", html)
if not m:
    print("!! could not find window.__STATE__ blob"); sys.exit(1)
old_blob = m.group(1)
new_html = html[:m.start(1)] + fresh + html[m.end(1):]
DOCS.write_text(new_html)
print(f"replaced blob {len(old_blob)} -> {len(fresh)} bytes")
print("new label present:", '"label": "Coordination Impact"' in new_html)
print("old label gone:", '"label": "Coordination Opportunity"' not in new_html)
