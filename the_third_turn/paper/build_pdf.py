#!/usr/bin/env python3
"""Build a PDF from a markdown document — SSRN-style working paper.

Defaults to paper1. Pass a stem in paper/ ("paper2") or a path to any markdown
document ("docs/VISUAL_COMPANION.md").

python-markdown → styled HTML → headless Chromium print-to-PDF. No LaTeX needed.
Deps: `pip install -r the_third_turn/paper/requirements.txt` (the container recycle
wipes them). Self-provisions python-markdown on first run if missing.

    python3 the_third_turn/paper/build_pdf.py
"""

from __future__ import annotations

import html
import re
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
/* max-width keeps a long title clear of both margins; without it a title can be set
   flush to the measure and read as clipped. See paper/check_title_margins.py. */
.titleblock h1 { font-size: 17pt; line-height: 1.3; margin: 0 auto 10pt; max-width: 88%; }
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
p:has(> img) { text-align: center; margin: 14pt 0 4pt; break-inside: avoid; break-after: avoid; }
/* Figures are authored at the full text measure (figstyle.FULL_W), so they display
   at scale 1.0 and a point inside a figure is a point on paper. Narrowing this
   silently shrinks every internal label -- see figstyle's production contract. */
img { max-width: 100%; }
p:has(> img) + p { font-size: 9pt; color: #333; text-align: center; margin: 0 6% 18pt;
                   break-before: avoid; break-inside: avoid; }
table { border-collapse: collapse; font-size: 8.4pt; margin: 10pt auto 14pt; width: 100%; }
th { border-top: 1pt solid #333; border-bottom: 0.5pt solid #333; padding: 3pt 5pt; text-align: left; }
td { border-bottom: 0.25pt solid #ccc; padding: 3pt 5pt; vertical-align: top;
     text-align: left; hyphens: auto; overflow-wrap: break-word; }
table { break-inside: auto; }
tr { break-inside: avoid; }
.protocol-box {
  border: 1pt solid #999; background: #fafafa; padding: 9pt 12pt 6pt;
  margin: 14pt auto; max-width: 82%; break-inside: avoid;
}
.protocol-box .pb-title { font-weight: bold; font-size: 9.5pt; margin-bottom: 4pt; }
.protocol-box p { font-size: 9.5pt; margin: 0 0 3pt; text-align: left; }
.footnote { font-size: 8.5pt; color: #222; margin-top: 14pt; }
.footnote hr { margin: 10pt 0 6pt; width: 30%; margin-left: 0; border-top: 0.5pt solid #666; }
.footnote ol { margin: 0 0 0 14pt; padding: 0; }
.footnote li p { margin: 0 0 5pt; text-align: justify; }
sup { font-size: 7.5pt; }
.footnote-backref { display: none; }
a { color: inherit; text-decoration: none; }
"""


def article_title(src: str) -> str:
    """The <h1> of the title block, as plain text."""
    m = re.search(r"<h1>(.*?)</h1>", src, re.S)
    if not m:
        return ""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).split())


def html_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def use_vector_masters(body: str, base: Path) -> tuple[str, int, int]:
    """Point every figure reference at its vector master, where one exists.

    WHY. The manuscripts reference `figures/<name>.png`, and those references are
    frozen along with the prose. But a PNG placed in a PDF is a raster object: the
    shipped documents embedded their line art at ~200 PPI, which is below what any
    journal will accept for production and visibly soft at print size.

    Every generator now emits an SVG master beside the PNG from the same converged
    canvas (figstyle.save_at_measure). Chromium rasterizes nothing when it prints an
    <img> whose source is SVG -- the geometry lands in the PDF as paths and the
    labels as embedded text -- so swapping the extension here upgrades the figures
    to true vector without touching a single frozen markdown file.

    The PNGs stay in the tree as the markdown/web preview and as the raster
    fallback; they are written at figstyle.PNG_DPI, which clears the 300 PPI floor
    on its own, so a build that cannot use the vector path still ships a
    publishable document. paper/check_figure_output.py enforces one or the other.
    """
    swapped = kept = 0

    def sub(m: "re.Match[str]") -> str:
        nonlocal swapped, kept
        src = m.group(1)
        vec = Path(src).with_suffix(".svg")
        if Path(src).suffix.lower() == ".png" and (base / vec).is_file():
            swapped += 1
            return m.group(0).replace(f'src="{src}"', f'src="{vec}"')
        kept += 1
        return m.group(0)

    return re.sub(r'<img[^>]*\ssrc="([^"]+)"[^>]*>', sub, body), swapped, kept


def normalize(raw: Path, out: Path, title: str, author: str | None) -> None:
    """Stamp document info and rewrite the file structure, preserving page content.

    WHY. Chromium/Skia names the document after its source file, so every PDF
    carried a Title like "paper2_anon.html" and no Author.

    WHY NOT GHOSTSCRIPT. An earlier version of this step re-emitted the pages
    through `gs -sDEVICE=pdfwrite`. A before/after audit showed that cost two
    semantics the Chromium output had: the logical structure tree disappeared
    (tagged: yes -> no, which is what a screen reader uses), and text runs inside
    tables were re-ordered, so extraction and copy/paste read cells in a
    different sequence. No content was lost -- the character and word multisets
    matched exactly -- but both are real losses and neither was worth paying for.

    pikepdf rewrites the cross-reference structure and linearizes without
    touching a single content stream, so tagging, annotations, fonts and text
    order survive byte-for-byte while the document info is corrected.

    No XMP packet is added. Chromium writes none, and an anonymized edition is
    safer with one metadata surface than with two.
    """
    import pikepdf

    with pikepdf.open(raw) as pdf:
        info = pdf.docinfo
        info["/Title"] = title
        if author:
            info["/Author"] = author
        elif "/Author" in info:
            del info["/Author"]
        info["/Creator"] = ""          # drops the Chromium user-agent string
        pdf.save(out, linearize=True)


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else "paper1"
    # Accept either a bare stem in paper/ ("paper2") or a path to any markdown
    # document ("docs/VISUAL_COMPANION.md"), so supplements and companions build
    # by the same documented route as the manuscripts. Output lands next to the
    # source, which keeps relative image paths working.
    cand = Path(arg if arg.endswith(".md") else f"{arg}.md")
    for base in (Path.cwd(), HERE, HERE.parent):
        if (base / cand).is_file():
            srcpath = (base / cand).resolve()
            break
    else:
        raise SystemExit(f"build_pdf: no such markdown document: {arg}")
    outdir, stem = srcpath.parent, srcpath.stem
    src = srcpath.read_text()

    title = article_title(src) or stem
    # A very long title needs a smaller face to keep three lines inside the measure.
    extra = "\n.titleblock h1 { font-size: 15pt; }" if len(title) > 90 else ""

    body = markdown.markdown(src, extensions=["tables", "footnotes"])
    body, vec, raster = use_vector_masters(body, outdir)
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{html_escape(title)}</title>"
        f"<style>{CSS}{extra}</style></head><body>{body}</body></html>"
    )
    out_html = outdir / f"{stem}.html"
    out_html.write_text(html)

    raw = outdir / f"{stem}.raw.pdf"
    pdf = outdir / f"{stem}.pdf"
    subprocess.run([
        CHROMIUM, "--headless=new", "--no-sandbox", "--disable-gpu",
        "--no-pdf-header-footer", f"--print-to-pdf={raw}", f"file://{out_html}",
    ], check=True, capture_output=True)

    # Anonymized editions carry no author. Everything else is Alec Messino.
    author = None if stem.endswith("_anon") else "Alec Messino"
    normalize(raw, pdf, title, author)
    raw.unlink(missing_ok=True)
    print(f"wrote {pdf} ({pdf.stat().st_size // 1024} KB) "
          f"[{vec} vector figure(s), {raster} raster]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
