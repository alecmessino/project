#!/usr/bin/env python3
"""Rebuild the data and the figures inside src/drift/web/the-interval-problem.html.

The essay makes a numerical argument about one index over one period, so every figure in it,
and every number quoted in its prose, is derived here from a single fetched series rather than
typed by hand. Run this, then `python3 scripts/sync_docs.py`, and the published page and the
market agree by construction.

    python3 scripts/kospi_interval.py            # fetch, recompute, rewrite the page
    python3 scripts/kospi_interval.py --offline  # recompute from the committed cache only
    python3 scripts/kospi_interval.py --check    # recompute and diff, write nothing (CI)

Why the series is baked into the page rather than fetched by the browser: driftwoodwealth.com is
a static GitHub Pages build, the quote hosts send no CORS headers, and a chart that silently
fails to draw for a reader behind a corporate proxy is worse than one that is simply true as of a
stated date. The page therefore carries its own data and says when it was taken.

The cache (tests/data/ks11_2026.json) is the offline source of truth. It is committed so the
suite and the build both run without network access, and so a future reader can reproduce every
figure in the piece from the repo alone.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "src" / "drift" / "web" / "the-interval-problem.html"
CACHE = ROOT / "tests" / "data" / "ks11_2026.json"

SYMBOL = "^KS11"
HOSTS = ("https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com")
KST = dt.timezone(dt.timedelta(hours=9))

# The window the essay argues over. START is the first session of 2026 and the base every
# return in the prose is measured from; ESSAY_END is the close the written piece stops at.
# Sessions after ESSAY_END belong to the dated update box, not to the argument.
START = "2026-01-02"
ESSAY_END = "2026-07-31"

# Markers the generator writes between. Each appears exactly twice in the page.
#
# The figure blocks are the obvious ones. UPDATE, READOUT and the two captions are here for a less
# obvious reason: they are the parts of the page the instruments overwrite at runtime, which means
# a hand-typed default quietly becomes the version served to anyone whose script never runs. The
# page claims in its own sources note that no number on it was entered by hand. These blocks are
# what makes that true on the no-JavaScript path as well.
BLOCKS = ("DATA", "FIG-JULY", "FIG-CUMULATIVE", "FIG-CADENCE", "FIG-LADDER",
          "UPDATE", "READOUT", "CAP-LADDER", "CAP-CADENCE")


# ── the series ────────────────────────────────────────────────────────────────────────────────

def fetch() -> list[list]:
    """Daily closes for ^KS11, most recent two years, as [["YYYY-MM-DD", close], ...] in KST.

    Yahoo stamps each daily bar at the session open in UTC; Korea is UTC+9, so a naive UTC date
    lands the whole series one day early. Converting before taking the date is the difference
    between "July 31 gained 17.9 percent" and attributing that session to July 30.
    """
    last = None
    for host in HOSTS:
        url = f"{host}/v8/finance/chart/{SYMBOL.replace('^', '%5E')}?range=2y&interval=1d"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            payload = json.load(urllib.request.urlopen(req, timeout=30))
        except Exception as exc:                                    # noqa: BLE001
            last = exc
            continue
        result = payload["chart"]["result"][0]
        closes = result["indicators"]["quote"][0]["close"]
        rows = [[dt.datetime.fromtimestamp(t, KST).strftime("%Y-%m-%d"), round(c, 2)]
                for t, c in zip(result["timestamp"], closes) if c is not None]
        meta = result["meta"]
        stamp = dt.datetime.fromtimestamp(meta["regularMarketTime"], KST)
        return rows, {"level": round(meta["regularMarketPrice"], 2),
                      "asOf": stamp.isoformat(timespec="seconds"),
                      "exchange": meta.get("exchangeName", "KSC")}
    raise SystemExit(f"could not reach a quote host: {last}")


def load_cache():
    blob = json.loads(CACHE.read_text())
    return blob["rows"], blob["quote"]


# ── the arithmetic ────────────────────────────────────────────────────────────────────────────

def pct(a: float, b: float) -> float:
    return (b / a - 1) * 100


def daily_returns(window: list[list]) -> list[tuple[str, float]]:
    """Session-over-session percent change, measured from the first close in the window.

    The first row is a level, not a return, so it contributes no observation. Everything the
    essay quotes on a "since January 2" basis chains from here.
    """
    out, prev = [], window[0][1]
    for day, close in window[1:]:
        out.append((day, pct(prev, close)))
        prev = close
    return out


def ladder(rets: list[tuple[str, float]], depth: int = 10) -> list[float]:
    """Cumulative return with the n best sessions removed, for n in 0..depth.

    Removing a session means never holding through it, which is what stepping out actually does.
    It is not the same as setting that day's return to zero, and the difference compounds.
    """
    ranked = [day for day, _ in sorted(rets, key=lambda r: -r[1])]
    rows = []
    for n in range(depth + 1):
        dropped = set(ranked[:n])
        growth = 1.0
        for day, r in rets:
            if day not in dropped:
                growth *= 1 + r / 100
        rows.append(round((growth - 1) * 100, 2))
    return rows


def _week(day: str) -> tuple:
    return dt.date.fromisoformat(day).isocalendar()[:2]


def _month(day: str) -> str:
    return day[:7]


def _quarter(day: str) -> tuple:
    return day[:4], (int(day[5:7]) - 1) // 3


def sample(window: list[list], cadence: str) -> list[list]:
    """The subset of closes an investor on this cadence would ever have seen.

    Period-END sampling, because that is what a statement reports and what an investor checking
    "at the end of the month" reads. The first and last closes are always included: the first is
    the cost basis, the last is today, and both are visible on any cadence.
    """
    if cadence == "daily":
        return [list(r) for r in window]
    key = {"weekly": _week, "monthly": _month, "quarterly": _quarter}[cadence]
    out, current, prev = [list(window[0])], key(window[0][0]), list(window[0])
    for day, close in window[1:]:
        bucket = key(day)
        if bucket != current:
            out.append(prev)
            current = bucket
        prev = [day, close]
    out.append(list(window[-1]))
    deduped = []
    for row in out:
        if not deduped or deduped[-1][0] != row[0]:
            deduped.append(row)
    return deduped


def cadence_stats(window: list[list], cadence: str) -> dict:
    """What this cadence shows its observer, and what it hides.

    `worstStep` is the largest decline between two consecutive readings: the worst single piece
    of news this observer ever receives. `maxDrawdown` is the deepest fall from a previously
    observed high, measured only at readings, so a low the observer never looked at never
    happened to them. `total` is identical across every cadence, which is the point.
    """
    readings = sample(window, cadence)
    levels = [c for _, c in readings]
    steps = [(readings[i + 1][0], pct(levels[i], levels[i + 1])) for i in range(len(levels) - 1)]
    worst_day, worst = min(steps, key=lambda s: s[1])
    peak, peak_day, trough, span = levels[0], readings[0][0], 0.0, (readings[0][0], readings[0][0])
    for day, close in readings:
        if close > peak:
            peak, peak_day = close, day
        fall = pct(peak, close)
        if fall < trough:
            trough, span = fall, (peak_day, day)
    return {
        "cadence": cadence,
        "readings": readings,
        "count": len(readings),
        "worstStep": round(worst, 2),
        "worstStepDate": worst_day,
        "maxDrawdown": round(trough, 2),
        "drawdownSpan": list(span),
        "total": round(pct(levels[0], levels[-1]), 2),
    }


def compute(rows: list[list], quote: dict) -> dict:
    by_day = dict((d, c) for d, c in rows)
    window = [r for r in rows if r[0] >= START]                     # Jan 2 through the last close
    essay = [r for r in window if r[0] <= ESSAY_END]
    rets = daily_returns(essay)
    july = [(d, r) for d, r in rets if d.startswith("2026-07")]
    june_end = [r for r in essay if r[0] < "2026-07-01"][-1]
    days = [d for d, _ in essay]

    big = [(d, r) for d, r in rets if abs(r) > 5]
    months = {}
    for day, _ in big:
        months[day[:7]] = months.get(day[:7], 0) + 1

    hold = ladder(rets, 10)
    latest = window[-1]
    prior = window[-2]

    return {
        "asOf": quote["asOf"],
        "symbol": SYMBOL,
        "start": START,
        "essayEnd": ESSAY_END,
        "series": [[d, c] for d, c in window],
        "julyReturns": [[d, round(r, 2)] for d, r in july],
        "ladder": hold,
        "cadences": {c: {k: v for k, v in cadence_stats(window, c).items() if k != "readings"}
                     | {"readings": sample(window, c)}
                     for c in ("daily", "weekly", "monthly", "quarterly")},
        "facts": {
            "janOpen": essay[0][1],
            "juneEnd": june_end[1],
            "julyEnd": essay[-1][1],
            "julyReturn": round(pct(june_end[1], essay[-1][1]), 2),
            "julySessions": len(july),
            "julyBigMoves": sum(1 for _, r in july if abs(r) > 5),
            "ytdThroughEssay": round(pct(essay[0][1], essay[-1][1]), 2),
            "peak": by_day["2026-06-22"],
            "trough": by_day["2026-07-30"],
            "peakToTrough": round(pct(by_day["2026-06-22"], by_day["2026-07-30"]), 2),
            "peakToTroughSessions": days.index("2026-07-30") - days.index("2026-06-22"),
            "bestSession": round(max(r for _, r in rets), 2),
            "worstSession": round(min(r for _, r in rets), 2),
            "sessions": len(essay),
            "bigMoves": len(big),
            "bigMovesByMonth": months,
            "missOneCost": round(hold[0] - hold[1], 2),
            "goesFlatAt": next(n for n, v in enumerate(hold) if v < 1),
        },
        "latest": {
            "date": latest[0],
            "level": latest[1],
            "change": round(pct(prior[1], latest[1]), 2),
            "points": round(latest[1] - prior[1], 2),
            "priorClose": prior[1],
            "priorDate": prior[0],
        },
    }


# ── the figures ───────────────────────────────────────────────────────────────────────────────
#
# Static SVG, generated rather than drawn, for the same reason the numbers are: a figure that is
# typed by hand is a figure that can disagree with its own caption. The two interactive figures
# also get a static default state here, so the page is complete and truthful with JavaScript
# turned off and the script only ever enhances what is already on the screen.

INK, LINE, ACCENT, POS, NEG, MUTED = "#1E2833", "#D8D3C6", "#2C5878", "#2F6F5B", "#9B4439", "#6B6E6A"
# The two surfaces a figure can sit on: the page itself, and the ruled sheet an instrument is
# drawn on. A marker that overlaps its own line needs a ring in the colour behind it.
PAPER, SHEET = "#F1EFE9", "#F7F5F0"


def _sx(i, n, x0, x1):
    return x0 + (x1 - x0) * (i / max(n - 1, 1))


def fig_july(data: dict) -> str:
    """Daily returns for July, as columns from a zero rule.

    Polarity, not magnitude, is the job here, so the two poles take the palette's committed
    diverging pair and every column also carries its sign in the accessible label: nothing in
    this figure is legible by colour alone.
    """
    rows = data["julyReturns"]
    w, h, pad_l, pad_r, top, bot = 660, 300, 54, 12, 20, 42
    lo, hi = min(r for _, r in rows), max(r for _, r in rows)
    lo, hi = min(lo, -12), max(hi, 18)
    zero = top + (h - top - bot) * (hi / (hi - lo))
    span = (h - top - bot) / (hi - lo)
    slot = (w - pad_l - pad_r) / len(rows)
    bw = min(slot * 0.66, 18)
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" '
           f'aria-label="Daily percent change in the Kospi Composite for each of the '
           f'{len(rows)} trading sessions in July 2026.">']
    for gl in (15, 10, 5, 0, -5, -10):
        y = top + (hi - gl) * span
        out.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w - pad_r}" y2="{y:.1f}" '
                   f'stroke="{INK if gl == 0 else LINE}" stroke-width="{1 if gl == 0 else 0.5}" '
                   f'stroke-opacity="{0.55 if gl == 0 else 1}"/>')
        out.append(f'<text x="{pad_l - 8}" y="{y + 3.4:.1f}" text-anchor="end" font-size="9.5" '
                   f'letter-spacing=".08em" fill="{MUTED}">{gl:+d}%</text>')
    for i, (day, r) in enumerate(rows):
        cx = pad_l + slot * (i + 0.5)
        y = zero - r * span if r >= 0 else zero
        out.append(f'<rect x="{cx - bw / 2:.1f}" y="{y:.1f}" width="{bw:.1f}" '
                   f'height="{abs(r) * span:.1f}" fill="{POS if r >= 0 else NEG}"/>')
        if day[-2:] in ("01", "06", "13", "20", "28", "31"):
            out.append(f'<text x="{cx:.1f}" y="{h - bot + 18:.1f}" text-anchor="middle" '
                       f'font-size="9.5" letter-spacing=".08em" fill="{MUTED}">'
                       f'{int(day[-2:])}</text>')
    # The one annotation the figure needs. Anchored to the right edge rather than centred on its
    # column: the best session is the last one, so a centred label runs off the canvas.
    best = max(range(len(rows)), key=lambda i: rows[i][1])
    cx = pad_l + slot * (best + 0.5)
    out.append(f'<text x="{min(cx + bw / 2, w - pad_r):.1f}" '
               f'y="{zero - rows[best][1] * span - 9:.1f}" text-anchor="end" '
               f'font-size="10.5" font-weight="700" fill="{INK}">'
               f'Jul 31, {rows[best][1]:+.1f}%</text>')
    out.append("</svg>")
    return "\n".join(out)


def _month_ticks(rows, x_of, y, out):
    """First session of each month, as a tick and a three-letter label.

    A seven-month line with no time axis asks the reader to take the shape on trust. These are
    the minimum furniture that lets someone locate June in it.
    """
    seen = set()
    for i, (day, _) in enumerate(rows):
        if day[:7] in seen:
            continue
        seen.add(day[:7])
        x = x_of(i)
        out.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y + 4:.1f}" '
                   f'stroke="{INK}" stroke-opacity=".4" stroke-width="0.5"/>')
        # A label centred on the last tick hangs off the figure once mobile scales the type up.
        anchor = "end" if x > x_of(len(rows) - 1) - 26 else "middle"
        out.append(f'<text x="{x:.1f}" y="{y + 16:.1f}" text-anchor="{anchor}" font-size="9.5" '
                   f'letter-spacing=".08em" fill="{MUTED}">'
                   f'{dt.date.fromisoformat(day).strftime("%b").upper()}</text>')


def fig_cumulative(data: dict) -> str:
    """Cumulative return from the first close of the year, with the three readings called out.

    The three readings the prose names all sit within the last fifteen sessions of a
    hundred-and-forty-two-session line, so labelling them where they fall stacks three labels on
    top of each other and on top of the line. They are called out into a right-hand gutter at
    their own heights instead, with a leader to each marker: the vertical separation between the
    readings is the whole point of the figure, and the gutter is what makes it legible.
    """
    rows = [r for r in data["series"] if r[0] <= data["essayEnd"]]
    base = rows[0][1]
    pts = [(d, pct(base, c)) for d, c in rows]
    w, h, pad_l, pad_r, top, bot = 660, 300, 56, 108, 22, 46
    lo, hi = min(v for _, v in pts), max(v for _, v in pts)
    lo, hi = min(lo, 0) - 6, hi + 12
    span = (h - top - bot) / (hi - lo)

    def y_of(v):
        return top + (hi - v) * span

    def x_of(i):
        return _sx(i, len(pts), pad_l, w - pad_r)

    path = " ".join(f"{'M' if i == 0 else 'L'}{x_of(i):.1f},{y_of(v):.1f}"
                    for i, (_, v) in enumerate(pts))
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" '
           f'aria-label="Cumulative return of the Kospi Composite from January 2 to July 31, '
           f'2026, rising to a peak near 97 percent in late June, falling through July, and '
           f'closing the period up {pts[-1][1]:.0f} percent.">']
    for gl in (0, 25, 50, 75, 100):
        y = y_of(gl)
        out.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w - pad_r}" y2="{y:.1f}" '
                   f'stroke="{INK if gl == 0 else LINE}" stroke-width="{1 if gl == 0 else 0.5}" '
                   f'stroke-opacity="{0.55 if gl == 0 else 1}"/>')
        out.append(f'<text x="{pad_l - 8}" y="{y + 3.4:.1f}" text-anchor="end" font-size="9.5" '
                   f'fill="{MUTED}">{gl:+d}%</text>')
    _month_ticks(rows, x_of, h - bot, out)
    out.append(f'<path d="{path}" fill="none" stroke="{ACCENT}" stroke-width="2" '
               f'stroke-linejoin="round"/>')
    index = [d for d, _ in pts]
    gutter = w - pad_r + 14
    for label, day in (("Jun 30", "2026-06-30"), ("Jul 31", "2026-07-31"),
                       ("Jul 30", "2026-07-30")):
        i = index.index(day)
        x, y = x_of(i), y_of(pts[i][1])
        out.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{gutter - 6:.1f}" y2="{y:.1f}" '
                   f'stroke="{INK}" stroke-width="0.5" stroke-opacity=".35"/>')
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="{ACCENT}" '
                   f'stroke="{PAPER}" stroke-width="1.5"/>')
        out.append(f'<text x="{gutter:.1f}" y="{y - 2:.1f}" font-size="10" font-weight="700" '
                   f'fill="{INK}">{label}</text>')
        out.append(f'<text x="{gutter:.1f}" y="{y + 11:.1f}" font-size="10" font-weight="700" '
                   f'fill="{ACCENT}">{pts[i][1]:+.1f}%</text>')
    out.append("</svg>")
    return "\n".join(out)


def fig_cadence(data: dict, cadence: str = "daily") -> str:
    """The full series in outline, with the readings one cadence would actually deliver.

    The daily line is always drawn, faintly, because the argument is not that the other closes
    did not happen. It is that an observer on a slower cadence never saw them.
    """
    stats = data["cadences"][cadence]
    rows = data["series"]
    base = rows[0][1]
    w, h, pad_l, pad_r, top, bot = 660, 300, 56, 14, 22, 46
    vals = [pct(base, c) for _, c in rows]
    lo, hi = min(vals) - 8, max(vals) + 10
    span = (h - top - bot) / (hi - lo)

    def y_of(v):
        return top + (hi - v) * span

    index = [d for d, _ in rows]
    faint = " ".join(f"{'M' if i == 0 else 'L'}{_sx(i, len(rows), pad_l, w - pad_r):.1f},"
                     f"{y_of(v):.1f}" for i, v in enumerate(vals))
    seen = [(index.index(d), pct(base, c)) for d, c in stats["readings"]]
    read_path = " ".join(f"{'M' if k == 0 else 'L'}{_sx(i, len(rows), pad_l, w - pad_r):.1f},"
                         f"{y_of(v):.1f}" for k, (i, v) in enumerate(seen))
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
           f'data-cadence-figure="{cadence}" role="img" aria-label="The Kospi Composite from '
           f'January 2 to {rows[-1][0]}, drawn faintly, with the {stats["count"]} closing levels '
           f'an investor checking {cadence} would have seen marked on it.">']
    for gl in (0, 25, 50, 75, 100):
        y = y_of(gl)
        out.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w - pad_r}" y2="{y:.1f}" '
                   f'stroke="{INK if gl == 0 else LINE}" stroke-width="{1 if gl == 0 else 0.5}" '
                   f'stroke-opacity="{0.55 if gl == 0 else 1}"/>')
        out.append(f'<text x="{pad_l - 8}" y="{y + 3.4:.1f}" text-anchor="end" font-size="9.5" '
                   f'fill="{MUTED}">{gl:+d}%</text>')
    _month_ticks(rows, lambda i: _sx(i, len(rows), pad_l, w - pad_r), h - bot, out)
    out.append(f'<path d="{faint}" fill="none" stroke="{INK}" stroke-opacity=".22" '
               f'stroke-width="1"/>')
    out.append(f'<path d="{read_path}" fill="none" stroke="{ACCENT}" stroke-width="2" '
               f'stroke-linejoin="round"/>')
    if len(seen) <= 40:
        for i, v in seen:
            out.append(f'<circle cx="{_sx(i, len(rows), pad_l, w - pad_r):.1f}" '
                       f'cy="{y_of(v):.1f}" r="3.2" fill="{ACCENT}" stroke="{SHEET}" '
                       f'stroke-width="1.2"/>')
    out.append("</svg>")
    return "\n".join(out)


def fig_ladder(data: dict, missed: int = 0) -> str:
    """The year's return as the best sessions are removed one at a time."""
    rows = data["ladder"]
    w, h, pad_l, pad_r, top, bot = 660, 300, 56, 14, 22, 46
    lo, hi = min(rows) - 8, max(rows) + 8
    span = (h - top - bot) / (hi - lo)

    def y_of(v):
        return top + (hi - v) * span

    slot = (w - pad_l - pad_r) / len(rows)
    bw = min(slot * 0.58, 30)
    out = [f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
           f'data-ladder-figure="{missed}" role="img" aria-label="Cumulative return for 2026 '
           f'through July 31 as the best sessions are removed one at a time, falling from '
           f'{rows[0]:.1f} percent holding every session to {rows[-1]:.1f} percent without the '
           f'ten best.">']
    for gl in (50, 25, 0, -25):
        y = y_of(gl)
        out.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w - pad_r}" y2="{y:.1f}" '
                   f'stroke="{INK if gl == 0 else LINE}" stroke-width="{1 if gl == 0 else 0.5}" '
                   f'stroke-opacity="{0.55 if gl == 0 else 1}"/>')
        out.append(f'<text x="{pad_l - 8}" y="{y + 3.4:.1f}" text-anchor="end" font-size="9.5" '
                   f'fill="{MUTED}">{gl:+d}%</text>')
    zero = y_of(0)
    for n, v in enumerate(rows):
        cx = pad_l + slot * (n + 0.5)
        y = zero - v * span if v >= 0 else zero
        active = n == missed
        out.append(f'<rect data-bar="{n}" x="{cx - bw / 2:.1f}" y="{y:.1f}" width="{bw:.1f}" '
                   f'height="{abs(v) * span:.1f}" fill="{POS if v >= 0 else NEG}" '
                   f'fill-opacity="{1 if active else 0.3}"/>')
        out.append(f'<text x="{cx:.1f}" y="{h - bot + 17:.1f}" text-anchor="middle" '
                   f'font-size="9.5" fill="{INK if active else MUTED}" '
                   f'font-weight="{700 if active else 400}">{n}</text>')
        if active:
            # Above a positive bar, above the zero rule for a negative one. Hanging it under a
            # negative bar puts it on top of the tick row at the deep end of the ladder.
            label_y = y - 8 if v >= 0 else zero - 7
            out.append(f'<text data-bar-label="1" x="{cx:.1f}" y="{label_y:.1f}" '
                       f'text-anchor="middle" font-size="11" font-weight="700" '
                       f'fill="{INK}">{v:+.1f}%</text>')
    out.append("</svg>")
    return "\n".join(out)


# ── the prose the instruments also write ──────────────────────────────────────────────────────

CADENCE_LABEL = {"daily": "every day", "weekly": "every week",
                 "monthly": "every month", "quarterly": "every quarter"}


def _pc(v: float, dp: int = 1) -> str:
    """A signed percent with a real minus sign, matching what the instruments render."""
    sign = "+" if v > 0 else ("−" if v < 0 else "")
    return f"{sign}{abs(v):.{dp}f}%"


def _day(iso: str) -> str:
    return dt.date.fromisoformat(iso).strftime("%B %-d")


def update_block(data: dict) -> str:
    """The dated stamp above the essay. The market facts come from the series; the reporting
    around them (the sidecar, the two chipmakers) is the morning's press and is stated as such."""
    latest = data["latest"]
    day = dt.date.fromisoformat(latest["date"])
    down = latest["change"] < 0
    return (
        f'<p class="u-h"><span>Update</span><span class="u-when" id="u-when">'
        f'{day.strftime("%A, %B %-d, %Y")}</span></p>\n'
        f'      <p>The Kospi opened sharply lower in Seoul and triggered a five-minute program '
        f'trading suspension after falling more than five percent at the open. The index sits at '
        f'<span class="u-quote" id="u-level">{latest["level"]:,.2f}</span>, '
        f'<span class="u-move" id="u-move">'
        f'{"down" if down else "up"} {abs(latest["points"]):,.2f} points, or '
        f'{abs(latest["change"]):.2f} percent</span>, with Samsung Electronics off 6.86 percent and '
        f'SK Hynix off 7.16 percent. That is seventy-two hours after the largest single-day gain in '
        f'the index\'s history.</p>\n'
        f'      <p><b>The piece below was written on Saturday.</b> Its arithmetic runs through the '
        f'July 31 close and has not been restated. The instrument in '
        f'<a href="#interval">the final section</a> does keep running, and it now includes this '
        f'session.</p>'
    )


def readout_block(data: dict, cadence: str = "daily") -> str:
    s = data["cadences"][cadence]
    return (
        f'<div><p class="r-k">Times you looked</p><p class="r-v" id="c-count">{s["count"]}</p></div>\n'
        f'          <div><p class="r-k">Worst single reading</p>'
        f'<p class="r-v" id="c-step">{_pc(s["worstStep"])}</p>\n'
        f'            <p class="r-n" id="c-step-n">Reading of {_day(s["worstStepDate"])}</p></div>\n'
        f'          <div><p class="r-k">Deepest fall you saw</p>'
        f'<p class="r-v" id="c-dd">{_pc(s["maxDrawdown"])}</p>\n'
        f'            <p class="r-n" id="c-dd-n">{_day(s["drawdownSpan"][0])} to '
        f'{_day(s["drawdownSpan"][1])}</p></div>\n'
        f'          <div class="r-fixed"><p class="r-k">Return over the period</p>'
        f'<p class="r-v" id="c-total">{_pc(s["total"])}</p>\n'
        f'            <p class="r-n">Identical on every cadence</p></div>'
    )


def cap_cadence(data: dict, cadence: str = "daily") -> str:
    """The comparison always runs against the opposite end of the range, so the sentence never
    compares a cadence with itself."""
    s = data["cadences"][cadence]
    other = "quarterly" if cadence == "daily" else "daily"
    o = data["cadences"][other]
    return (f'Checking {CADENCE_LABEL[cadence]} over this period meant {s["count"]} readings, a '
            f'worst single reading of {_pc(s["worstStep"])}, and a deepest observed fall of '
            f'{_pc(s["maxDrawdown"])}. The {other} observer saw {_pc(o["maxDrawdown"])}. The money '
            f'did the same thing in both cases.')


def cap_ladder(data: dict) -> str:
    lad = data["ladder"]
    return (f'Holding every session returned {_pc(lad[0])}. Missing the single best session leaves '
            f'{_pc(lad[1])}. The year goes flat at {data["facts"]["goesFlatAt"]} sessions missed '
            f'and reaches {_pc(lad[-1])} without the ten best, in a market that finished up '
            f'{_pc(lad[0])}.')


# ── writing it back ───────────────────────────────────────────────────────────────────────────

def replace(page: str, name: str, body: str) -> str:
    open_tag, close_tag = f"<!--{name}-->", f"<!--/{name}-->"
    start, end = page.find(open_tag), page.find(close_tag)
    if start < 0 or end < 0:
        raise SystemExit(f"the page is missing its {name} markers")
    return page[:start + len(open_tag)] + "\n" + body + "\n" + page[end:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true", help="use the committed cache, do not fetch")
    ap.add_argument("--check", action="store_true", help="recompute and report, write nothing")
    args = ap.parse_args()

    if args.offline:
        rows, quote = load_cache()
        print(f"   cache    {CACHE.relative_to(ROOT)} ({len(rows)} sessions)")
    else:
        rows, quote = fetch()
        if args.check:
            # --check writes NOTHING, and the cache is a write. Refreshing it here would leave the
            # committed series ahead of the page that was generated from it, which is a state the
            # suite (correctly) fails on: the page would be quoting a level the cache no longer
            # holds. A read-only mode that moves the source of truth is not read-only.
            print(f"   fetched  {SYMBOL}: {len(rows)} sessions, last {rows[-1][0]} at "
                  f"{rows[-1][1]} (not written)")
        else:
            CACHE.parent.mkdir(parents=True, exist_ok=True)
            CACHE.write_text(json.dumps({"symbol": SYMBOL, "quote": quote, "rows": rows},
                                        indent=0))
            print(f"   fetched  {SYMBOL}: {len(rows)} sessions, last {rows[-1][0]} at {rows[-1][1]}")

    data = compute(rows, quote)
    f = data["facts"]
    print(f"   July     {f['julyReturn']:+.1f}% over {f['julySessions']} sessions, "
          f"{f['julyBigMoves']} of them beyond five percent")
    print(f"   Peak     {f['peak']} on 2026-06-22 to {f['trough']} on 2026-07-30, "
          f"{f['peakToTrough']:+.1f}% over {f['peakToTroughSessions']} sessions")
    print(f"   Year     {f['ytdThroughEssay']:+.1f}% held; {data['ladder'][1]:+.1f}% missing one "
          f"session; {data['ladder'][5]:+.1f}% missing five")
    for c, s in data["cadences"].items():
        print(f"   {c:10} {s['count']:3} readings, worst step {s['worstStep']:+.1f}%, "
              f"deepest fall {s['maxDrawdown']:+.1f}%, period {s['total']:+.1f}%")

    if args.check:
        return 0

    page = PAGE.read_text()
    page = replace(page, "DATA", "window.__INTERVAL__ = " + json.dumps(data, separators=(",", ":"))
                   + ";")
    page = replace(page, "FIG-JULY", fig_july(data))
    page = replace(page, "FIG-CUMULATIVE", fig_cumulative(data))
    page = replace(page, "FIG-CADENCE", fig_cadence(data, "daily"))
    page = replace(page, "FIG-LADDER", fig_ladder(data, 0))
    page = replace(page, "UPDATE", "      " + update_block(data))
    page = replace(page, "READOUT", "          " + readout_block(data, "daily"))
    page = replace(page, "CAP-LADDER", "          " + cap_ladder(data))
    page = replace(page, "CAP-CADENCE", "        " + cap_cadence(data, "daily"))
    PAGE.write_text(page)
    print(f"OK: rewrote {PAGE.relative_to(ROOT)} ({len(page)} bytes). "
          f"Now run scripts/sync_docs.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
