#!/usr/bin/env python3
"""Rebuild the data and figure inside src/drift/web/the-shortest-line.html.

Five Asian equity drawdowns, each anchored at its own pre-event peak and then followed forward
for as long as the record allows. Same discipline as scripts/kospi_interval.py: every number in
the piece is computed here from fetched closes, written into the page between markers, and cached
so the suite and the build run offline.

    python3 scripts/asia_drawdowns.py            # fetch, recompute, rewrite the page
    python3 scripts/asia_drawdowns.py --offline  # recompute from the committed cache only

The peaks are FOUND, not asserted. Each event names a window in which its pre-crash high sits and
the generator takes the maximum close inside it, so the anchor is a fact about the series rather
than a date someone remembered. Getting this wrong by a few sessions would change every number
downstream, and an anchor typed from memory is exactly the failure the page's own argument is
about.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "src" / "drift" / "web" / "the-shortest-line.html"
CACHE = ROOT / "tests" / "data" / "asia_drawdowns.json"

BLOCKS = ("DATA", "FIG-PATHS", "TABLE", "CAP-PATHS", "MARKS")

# How far forward the instrument tracks. Roughly five years of sessions, which covers every change
# of hands in the ranking. What happens past it (the Nikkei's eventual floor nineteen years out) is
# in the table, because a slider nobody would drag that far is not how you state a fact.
HORIZON = 1300
SESSIONS_PER_YEAR = 246
KST = dt.timezone(dt.timedelta(hours=9))

# (key, label, index name, symbol, window the pre-event peak sits inside)
EVENTS = (
    ("kospi2026", "Kospi, 2026", "Kospi Composite", "%5EKS11", "2026-05-01", "2026-07-01"),
    ("shanghai2015", "Shanghai, 2015", "Shanghai Composite", "000001.SS", "2015-04-01", "2015-07-01"),
    ("hangseng2007", "Hang Seng, 2007", "Hang Seng", "%5EHSI", "2007-06-01", "2007-12-01"),
    ("kospi1997", "Kospi, 1997", "Kospi Composite", "%5EKS11", "1997-01-01", "1997-12-01"),
    ("nikkei1989", "Nikkei, 1989", "Nikkei 225", "%5EN225", "1989-01-01", "1990-01-05"),
)


def _chart(symbol: str, query: str) -> dict:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req, timeout=45))["chart"]["result"][0]


def _rows(result: dict) -> list[list]:
    closes = result["indicators"]["quote"][0]["close"]
    return [[dt.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"), round(c, 2)]
            for t, c in zip(result["timestamp"], closes) if c is not None]


def fetch(symbol: str) -> list[list]:
    """The full history, with the most recent session filled in if the long array is missing it.

    Yahoo's multi-day arrays lag: hours after the Seoul close on 2026-08-04 the full history still
    ended at August 3 while the single-day endpoint already had the new bar. Four of the five
    events here are decades old and unaffected, but the fifth is live, and it is the one the whole
    piece is about. Only appended once the session has settled, so an intraday print never enters
    a series of closes.
    """
    rows = _rows(_chart(symbol, "period1=-2208988800&period2=9999999999&interval=1d"))
    try:
        tail = _chart(symbol, "range=1d&interval=1d")
    except Exception:                                               # noqa: BLE001
        return rows
    tail_rows = _rows(tail)
    stamp = dt.datetime.fromtimestamp(tail["meta"]["regularMarketTime"], KST)
    if (tail_rows and tail_rows[-1][0] > rows[-1][0]
            and tail_rows[-1][0] == stamp.strftime("%Y-%m-%d")
            and stamp.time() >= dt.time(15, 0)):
        rows.append(tail_rows[-1])
    return rows


def build(raw: dict) -> dict:
    events = []
    for key, label, index, symbol, lo, hi in EVENTS:
        rows = raw[key]
        window = [r for r in rows if lo <= r[0] <= hi]
        peak_date, peak = max(window, key=lambda r: r[1])
        forward = [r for r in rows if r[0] >= peak_date]
        # Four places, not two. Two is one digit beyond what the page displays, which is exactly
        # the precision that re-rounds wrong at a .x5 boundary: 238 of these points did. See _mag.
        path = [round((c / peak - 1) * 100, 4) for _, c in forward[:HORIZON]]

        trough_i = min(range(len(forward)), key=lambda i: forward[i][1])
        recovered = next((i for i, (_, c) in enumerate(forward) if i > 0 and c >= peak), None)
        events.append({
            "key": key, "label": label, "index": index,
            "peakDate": peak_date, "peak": peak,
            "path": path,
            "dates": [forward[0][0], forward[min(len(forward), HORIZON) - 1][0]],
            "troughPct": round((forward[trough_i][1] / peak - 1) * 100, 6),
            "troughDate": forward[trough_i][0],
            "troughDays": trough_i,
            "recoveryDays": recovered,
            "recoveryDate": forward[recovered][0] if recovered is not None else None,
            "ongoing": recovered is None,
            "sessions": len(forward),
        })
    subject = next(e for e in events if e["key"] == "kospi2026")
    return {
        "asOf": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "horizon": HORIZON,
        "events": events,
        "stopsAt": len(subject["path"]) - 1,      # the last session the youngest crash has printed
        "subject": subject["key"],
    }


# ── the figure ────────────────────────────────────────────────────────────────────────────────
#
# One hue, not five. Five categorical colours drawn from a two-family palette cannot be separated
# under colour-vision deficiency without inventing hues the site does not own, and the argument
# does not need them: the subject is one series and the other four are context. The 2026 line
# takes the editorial blue, the historical four are ink at graded opacity, and every line is named
# at its own end, so identity never depends on colour at all.

INK, LINE, ACCENT, MUTED, PAPER = "#1E2833", "#D8D3C6", "#2C5878", "#6B6E6A", "#F7F5F0"
W, H, PAD_L, PAD_R, TOP, BOT = 660, 330, 46, 104, 20, 42
GHOST = (0.55, 0.42, 0.32, 0.24)          # oldest event faintest, so the eye lands on 2026 first


def fig_paths(data: dict, stop: int) -> str:
    events = data["events"]
    visible = [(e, e["path"][:stop + 1]) for e in events]
    lo = min(min(p) for _, p in visible if p)
    lo = min(lo - 5, -10)
    # Zero is NOT the ceiling. Kospi 1997 regained its pre-crisis peak inside two years and kept
    # going, so a domain that stops at zero draws that recovery outside the frame and on top of the
    # paragraph above it. The recovery is the most interesting thing in the exhibit; it has to fit.
    hi = max(0.0, max(max(p) for _, p in visible if p) + 4)
    span = (H - TOP - BOT) / (hi - lo)

    def y_of(v):
        return TOP + (hi - v) * span

    def x_of(i):
        return PAD_L + (W - PAD_L - PAD_R) * (i / max(stop, 1))

    out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" '
           f'data-paths-figure="{stop}" role="img" aria-label="Five Asian equity drawdowns from '
           f'their own pre-event peaks, followed for {stop} trading sessions.">']
    step = 10 if lo > -45 else 20
    # Bounded at both ends: a gridline outside [lo, hi] is drawn off the plot, and its label lands
    # on the axis title or in the paragraph above.
    grid = [g for g in range(int(hi // step) * step, int(lo) - 1, -step) if lo <= g <= hi]
    for g in grid:
        y = y_of(g)
        out.append(f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{W - PAD_R}" y2="{y:.1f}" '
                   f'stroke="{INK if g == 0 else LINE}" stroke-width="{1 if g == 0 else 0.5}" '
                   f'stroke-opacity="{0.55 if g == 0 else 1}"/>')
        out.append(f'<text x="{PAD_L - 8}" y="{y + 3.4:.1f}" text-anchor="end" font-size="9.5" '
                   f'fill="{MUTED}">{g}%</text>')
    for n in (0, stop // 4, stop // 2, stop * 3 // 4, stop):
        x = x_of(n)
        out.append(f'<text x="{x:.1f}" y="{H - BOT + 16:.1f}" '
                   f'text-anchor="{"end" if n == stop else "middle"}" font-size="9.5" '
                   f'fill="{MUTED}">{n}</text>')
    out.append(f'<text x="{PAD_L}" y="{H - 6}" font-size="9.5" letter-spacing=".16em" '
               f'fill="{MUTED}">TRADING SESSIONS SINCE THAT EVENT\'S PEAK</text>')

    # historical first, subject last, so the line that matters is drawn on top of the others
    ordered = [e for e in visible if e[0]["key"] != data["subject"]] + \
              [e for e in visible if e[0]["key"] == data["subject"]]
    ends = []
    for idx, (event, path) in enumerate(ordered):
        if not path:
            continue
        subject = event["key"] == data["subject"]
        d = " ".join(f"{'M' if i == 0 else 'L'}{x_of(i):.1f},{y_of(v):.1f}"
                     for i, v in enumerate(path))
        colour = ACCENT if subject else INK
        opacity = 1 if subject else GHOST[min(idx, len(GHOST) - 1)]
        out.append(f'<path d="{d}" fill="none" stroke="{colour}" stroke-opacity="{opacity}" '
                   f'stroke-width="{2 if subject else 1.4}" stroke-linejoin="round"/>')
        ex, ey = x_of(len(path) - 1), y_of(path[-1])
        out.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{3.2 if subject else 2.4}" '
                   f'fill="{colour}" fill-opacity="{opacity}" stroke="{PAPER}" '
                   f'stroke-width="1.2"/>')
        ends.append([ey, ex, event["label"], colour, opacity, subject])
    # Early in an event's life the five lines sit within a few percent of each other, so their end
    # labels stack on top of one another exactly when the reader most needs to tell them apart.
    # Nudged apart vertically, in order, and each keeps a leader to its own line.
    for i, e in enumerate(sorted(ends, key=lambda r: r[0])):
        e[0] = max(e[0], TOP + 6 + i * 12)
    for ey, ex, label, colour, opacity, subject in ends:
        out.append(f'<text x="{ex + 8:.1f}" y="{ey + 3.4:.1f}" font-size="10" '
                   f'font-weight="{700 if subject else 500}" fill="{colour}" '
                   f'fill-opacity="{1 if subject else 0.8}">{label}</text>')
    out.append("</svg>")
    return "\n".join(out)


def ranking(data: dict, stop: int) -> list[dict]:
    """Who is worst if you stop the clock at session `stop`.

    An event that has not printed that many sessions is ranked on its last available reading and
    flagged, rather than dropped. Dropping it would quietly hand the title to whoever is left,
    which is the move the piece is objecting to.
    """
    rows = []
    for e in data["events"]:
        path = e["path"]
        i = min(stop, len(path) - 1)
        rows.append({"key": e["key"], "label": e["label"], "value": path[i],
                     "short": i < stop, "at": i})
    return sorted(rows, key=lambda r: r["value"])


def _mag(v: float, dp: int = 1) -> str:
    """Half up, exactly once. Same contract as scripts/kospi_interval.py::_mag, and the same
    reason: a value pre-rounded to a display precision arrives at the formatter as a float just
    below the .x5 boundary and loses a digit."""
    q = 10 ** dp
    return f"{math.floor(abs(v) * q + 0.5) / q:.{dp}f}"


def _pc(v: float, dp: int = 1) -> str:
    sign = "" if v >= 0 else "\u2212"
    return f"{sign}{_mag(v, dp)}%"


def _yrs(sessions: int) -> str:
    years = sessions / SESSIONS_PER_YEAR
    return f"{years:.0f} years" if years >= 2 else f"{years * 12:.0f} months"


def table_block(data: dict) -> str:
    stop = data["stopsAt"]
    rows = []
    for e in data["events"]:
        at_stop = e["path"][min(stop, len(e["path"]) - 1)]
        if e["ongoing"]:
            back = "Not yet" + (", still" if e["key"] != data["subject"] else "")
        else:
            back = _yrs(e["recoveryDays"])
        cls = ' class="hi"' if e["key"] == data["subject"] else ''
        rows.append(
            f'<tr{cls}>'
            f'<td>{e["label"]}</td>'
            f'<td>{_pc(at_stop)}</td>'
            f'<td>{_pc(e["troughPct"])}</td>'
            f'<td>{_yrs(e["troughDays"]) if e["troughDays"] else "0"}</td>'
            f'<td>{back}</td></tr>')
    return (f'<thead><tr><th>Event</th><th>At session {stop}</th><th>Eventually</th>'
            f'<th>Time to the floor</th><th>Back to the peak</th></tr></thead>\n'
            f'        <tbody>\n          ' + "\n          ".join(rows) + '\n        </tbody>')


def cap_paths(data: dict, stop: int) -> str:
    order = ranking(data, stop)
    worst, second = order[0], order[1]
    return (f'Stopped at session {stop}, the worst of the five is {worst["label"]} at '
            f'{_mag(worst["value"])} percent, ahead of {second["label"]} at '
            f'{_mag(second["value"])} percent. Move the window and the order changes, because each '
            f'line is still falling somewhere to the right of where it has been cut.')


def marks_block(data: dict) -> str:
    """The jump buttons. The first one tracks the live series rather than a number typed once:
    "where Korea is now" moves every session, and a hardcoded 29 is wrong by the next close."""
    stop = data["stopsAt"]
    marks = [(stop, "Where Korea is now"), (50, "50 sessions"),
             (SESSIONS_PER_YEAR, "One year"), (SESSIONS_PER_YEAR * 3, "Three years"),
             (data["horizon"] - 1, "Five years")]
    return "\n          ".join(
        f'<button type="button" data-stop="{n}">{label}</button>' for n, label in marks)


def replace(page: str, name: str, body: str) -> str:
    open_tag, close_tag = f"<!--{name}-->", f"<!--/{name}-->"
    start, end = page.find(open_tag), page.find(close_tag)
    if start < 0 or end < 0:
        raise SystemExit(f"the page is missing its {name} markers")
    return page[:start + len(open_tag)] + "\n" + body + "\n" + page[end:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true", help="use the committed cache, do not fetch")
    args = ap.parse_args()

    if args.offline:
        raw = json.loads(CACHE.read_text())["raw"]
        print(f"   cache    {CACHE.relative_to(ROOT)}")
    else:
        raw = {}
        for key, label, _index, symbol, _lo, _hi in EVENTS:
            raw[key] = fetch(symbol)
            print(f"   fetched  {label:16} {len(raw[key]):>6} sessions")

    data = build(raw)
    for e in data["events"]:
        back = "not yet" if e["ongoing"] else _yrs(e["recoveryDays"])
        print(f"   {e['label']:16} peak {e['peakDate']} {e['peak']:>10,.2f}  "
              f"floor {_pc(e['troughPct']):>7} after {e['troughDays']:>4} sessions, "
              f"back to peak: {back}")
    for day in (data["stopsAt"], 50, 120, 300, 900):
        order = ranking(data, day)
        print(f"   worst at session {day:>4}: {order[0]['label']} ({_pc(order[0]['value'])})")

    if not args.offline:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps({"raw": raw}, separators=(",", ":")))

    page = PAGE.read_text()
    page = replace(page, "DATA", "window.__ASIA__ = " + json.dumps(data, separators=(",", ":")) + ";")
    page = replace(page, "FIG-PATHS", fig_paths(data, data["stopsAt"]))
    page = replace(page, "TABLE", "        " + table_block(data))
    page = replace(page, "CAP-PATHS", "          " + cap_paths(data, data["stopsAt"]))
    page = replace(page, "MARKS", "          " + marks_block(data))
    PAGE.write_text(page)
    print(f"OK: rewrote {PAGE.relative_to(ROOT)}. Now run scripts/sync_docs.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
