#!/usr/bin/env python3
"""Build paper1.pdf from paper1.md — SSRN-style working paper.

python-markdown → styled HTML → headless Chromium print-to-PDF. No LaTeX needed.
Deps: `pip install -r the_third_turn/paper/requirements.txt` (the container recycle
wipes them). Self-provisions python-markdown on first run if missing.

    python3 the_third_turn/paper/build_pdf.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    import markdown
except ModuleNotFoundError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "markdown"], check=True)
    import markdown

HERE = Path(__file__).resolve().parent
CHROMIUM = "/opt/pw-browsers/chromium"

CSS = """
@page { size: Letter; margin: 24mm 22mm; }
html { -webkit-print-color-adjust: exact; }
body {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 10.5pt; line-height: 1.55; color: #111; margin: 0;
}
.titleblock { text-align: center; margin: 0 0 18pt; }
.titleblock h1 { font-size: 17pt; line-height: 1.3; margin: 0 0 10pt; }
.epigraph { font-style: italic; color: #444; font-size: 10pt; margin: 0 8% 14pt; }
.author { font-size: 11pt; margin: 0 0 4pt; }
.author .affil { font-size: 9.5pt; color: #444; }
.wp { font-size: 9pt; color: #666; letter-spacing: 0.03em; margin: 0; }
h2 { font-size: 12.5pt; margin: 20pt 0 6pt; border-bottom: 0.5pt solid #bbb; padding-bottom: 2pt; }
h3 { font-size: 11pt; margin: 14pt 0 4pt; }
p { margin: 0 0 8pt; text-align: justify; hyphens: auto; }
blockquote {
  margin: 10pt 0; padding: 8pt 12pt; background: #f6f6f4;
  border-left: 2.5pt solid #888; break-inside: avoid;
}
blockquote p { margin: 0 0 6pt; text-align: left; }
blockquote p:last-child { margin-bottom: 0; }
blockquote h3 { margin-top: 0; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 9pt; background: #f2f2f0; padding: 0 2px; }
hr { border: none; border-top: 0.5pt solid #ccc; margin: 16pt 0; }
p:has(> img) { text-align: center; margin: 12pt 0 4pt; break-inside: avoid; }
img { max-width: 88%; }
p:has(> img) + p { font-size: 9pt; color: #333; text-align: center; margin: 0 6% 16pt; }
table { border-collapse: collapse; font-size: 8.4pt; margin: 10pt auto 14pt; width: 100%; }
th { border-top: 1pt solid #333; border-bottom: 0.5pt solid #333; padding: 3pt 5pt; text-align: left; }
td { border-bottom: 0.25pt solid #ccc; padding: 3pt 5pt; vertical-align: top; }
table { break-inside: auto; }
tr { break-inside: avoid; }
.protocol-box {
  border: 1pt solid #999; background: #fafafa; padding: 8pt 10pt 4pt;
  margin: 14pt auto; max-width: 78%; break-inside: avoid;
}
.protocol-box .pb-title { font-weight: bold; font-size: 9.5pt; margin-bottom: 2pt; }
.protocol-box pre {
  font-family: 'DejaVu Sans Mono', monospace; font-size: 8pt; line-height: 1.35;
  margin: 0; background: none; white-space: pre; text-align: left;
}
"""


def main() -> int:
    src = (HERE / "paper1.md").read_text()
    body = markdown.markdown(src, extensions=["tables"])
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
    out_html = HERE / "paper1.html"
    out_html.write_text(html)
    pdf = HERE / "paper1.pdf"
    subprocess.run([
        CHROMIUM, "--headless=new", "--no-sandbox", "--disable-gpu",
        "--no-pdf-header-footer", f"--print-to-pdf={pdf}", f"file://{out_html}",
    ], check=True, capture_output=True)
    print(f"wrote {pdf} ({pdf.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
