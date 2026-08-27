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
img { max-width: 88%; }
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


def _pdfmark_str(s: str) -> str:
    """Docinfo value as hex UTF-16BE, so em-dashes and the like survive."""
    return "<FEFF" + s.encode("utf-16-be").hex().upper() + ">"


def normalize(raw: Path, out: Path, title: str, author: str | None) -> None:
    """Re-emit through Ghostscript and stamp document info.

    WHY. Two problems, one fix. Chromium/Skia names the document after the source
    file, so every PDF carried a Title like "paper2_anon.html" and no Author. And
    Skia's content streams have been observed to render inconsistently across
    readers -- text near a following background box masked under Poppler while
    Ghostscript drew it correctly. Re-emitting through pdfwrite produces one
    conventional content stream per page and removes that class of difference.

    Images are kept lossless and un-downsampled, so figures are byte-for-byte the
    same pixels; only the container changes.
    """
    marks = [f"/Title {_pdfmark_str(title)}"]
    if author:
        marks.append(f"/Author {_pdfmark_str(author)}")
    marks.append("/Creator ()")          # drops the Chromium user-agent string
    pdfmark = raw.with_suffix(".pdfmark")
    pdfmark.write_text("[ " + " ".join(marks) + " /DOCINFO pdfmark\n")
    subprocess.run([
        "gs", "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.7", "-dEmbedAllFonts=true", "-dSubsetFonts=true",
        "-dDownsampleColorImages=false", "-dDownsampleGrayImages=false",
        "-dDownsampleMonoImages=false", "-dAutoFilterColorImages=false",
        "-dAutoFilterGrayImages=false", "-dColorImageFilter=/FlateEncode",
        "-dGrayImageFilter=/FlateEncode", "-dPreserveMarkedContent=true",
        f"-sOutputFile={out}", str(raw), str(pdfmark),
    ], check=True, capture_output=True)
    pdfmark.unlink(missing_ok=True)


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
    print(f"wrote {pdf} ({pdf.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
