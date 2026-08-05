"""The Interval Problem: the arithmetic, and the ways it can silently stop being true.

The essay is a numerical argument. Its prose quotes about twenty figures, its four exhibits are
drawn from one series, and both instruments recompute from that same series in the browser. That
is three places one number can live, so this file exists to keep them from disagreeing.

Three kinds of guard, in order of how quietly they would fail:

  1. THE ARITHMETIC. Pure functions in scripts/kospi_interval.py against the committed cache. If
     the sampler or the ladder changes meaning, these fail before anything ships.
  2. THE PAGE AGAINST THE DATA. Every figure quoted in the prose is re-derived here and looked for
     in the published HTML. A hand-edit to the copy that rounds 53.0 to 53 fails here, which is the
     point: the sources note tells the reader no number on the page was typed by hand.
  3. THE PAGE AGAINST ITSELF. src/ and docs/ must match, the markers must be filled, and the
     figures the reader gets with JavaScript disabled must be the same figures.

The URL-parameter paths (?cadence=, ?missed=) are covered in tests/web/test_interval_instruments.js
rather than here: they are browser code, and per CLAUDE.md they get exercised through the query
string rather than through the controls.
"""
import datetime as dt
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"
PAGE = "the-interval-problem.html"
CACHE = ROOT / "tests" / "data" / "ks11_2026.json"


def _generator():
    spec = importlib.util.spec_from_file_location("kospi_interval",
                                                  ROOT / "scripts" / "kospi_interval.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


K = _generator()


@pytest.fixture(scope="module")
def data():
    """Recomputed from the committed cache, never from the network. The suite has to run offline,
    and a test that fetches would also be testing the market rather than the code."""
    rows, quote = K.load_cache()
    return K.compute(rows, quote)


@pytest.fixture(scope="module")
def src_page():
    return (WEB / PAGE).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def built(data):
    return (DOCS / PAGE).read_text(encoding="utf-8")


# ── 1. the arithmetic ─────────────────────────────────────────────────────────────────────────

def test_the_period_return_is_the_same_on_every_cadence(data):
    """The claim the whole essay rests on. How often someone looks changes what they saw; it does
    not change what the position was worth. If this ever fails, the page is arguing the opposite of
    its own thesis and must not ship."""
    totals = {c: s["total"] for c, s in data["cadences"].items()}
    assert len(set(totals.values())) == 1, f"cadences disagree about the period return: {totals}"


def test_the_deepest_observed_fall_shrinks_as_the_interval_lengthens(data):
    """The second half of the claim, and the half a reader would call a trick if it were only
    asserted in prose."""
    falls = [abs(data["cadences"][c]["maxDrawdown"])
             for c in ("daily", "weekly", "monthly", "quarterly")]
    assert falls == sorted(falls, reverse=True), f"not monotone in the interval: {falls}"
    assert falls[0] > falls[-1], "every cadence saw the same fall, which cannot be right"


def test_the_worst_single_reading_does_not_shrink_with_the_interval(data):
    """Deliberately the other way round, and the page says so in prose. A wider interval bundles
    more into one reading: the monthly observer opened a statement worse than anything the weekly
    observer ever received. This is what stops the instrument being a "check less, feel better"
    toy, so it is pinned rather than left as an accident of this particular July."""
    weekly = abs(data["cadences"]["weekly"]["worstStep"])
    monthly = abs(data["cadences"]["monthly"]["worstStep"])
    assert monthly > weekly, (
        "the monthly observer's worst single reading is no longer worse than the weekly "
        f"observer's ({monthly} vs {weekly}); the prose making that point is now wrong")


def test_every_cadence_starts_and_ends_on_the_same_close(data):
    """Otherwise the equal-return result above is an artifact of sampling different endpoints
    rather than a fact about the interval."""
    first = data["series"][0]
    last = data["series"][-1]
    for cadence, stats in data["cadences"].items():
        readings = stats["readings"]
        assert readings[0] == first, f"{cadence} does not start at the first close"
        assert readings[-1] == last, f"{cadence} does not end at the most recent close"
        assert len(readings) == len(set(d for d, _ in readings)), f"{cadence} repeats a session"


def test_sampling_only_ever_removes_readings(data):
    """A slower cadence is a subset of a faster one. If sampling ever invented a level the index
    never printed, every number in the instrument would be fiction."""
    closes = {tuple(r) for r in data["series"]}
    for cadence, stats in data["cadences"].items():
        for reading in stats["readings"]:
            assert tuple(reading) in closes, f"{cadence} shows a level the index never printed"
    counts = [data["cadences"][c]["count"] for c in ("daily", "weekly", "monthly", "quarterly")]
    assert counts == sorted(counts, reverse=True), f"cadences are not ordered by frequency: {counts}"


def test_the_ladder_falls_monotonically_and_removes_the_right_sessions(data):
    """Removing the best session cannot help, and removing n+1 cannot beat removing n."""
    lad = data["ladder"]
    assert len(lad) == 11
    assert lad == sorted(lad, reverse=True), f"the ladder is not monotone: {lad}"
    assert lad[0] > 0 > lad[-1], "the ladder no longer crosses zero, which is the exhibit"


def test_missing_one_session_costs_what_the_prose_says(data):
    """23.2 points of a 53.0 percent year, from a single session out of a hundred and forty-one."""
    assert data["facts"]["missOneCost"] == pytest.approx(
        data["ladder"][0] - data["ladder"][1], abs=0.02)


def test_the_ladder_is_a_hold_calculation_not_a_zeroed_return(data):
    """Setting a day's return to zero and never holding through it are different numbers, and the
    difference compounds. The page describes the second, so it has to compute the second."""
    rows = [r for r in data["series"] if r[0] <= data["essayEnd"]]
    rets = K.daily_returns(rows)
    best = max(r for _, r in rets)
    zeroed = 1.0
    for _, r in rets:
        zeroed *= 1 + (0 if r == best else r) / 100
    assert data["ladder"][1] == pytest.approx((zeroed - 1) * 100, abs=0.02), (
        "the one-missed-session figure no longer matches a genuine hold calculation")


def test_the_cache_covers_the_period_the_essay_argues_over(data):
    facts = data["facts"]
    assert data["series"][0][0] == "2026-01-02"
    assert data["series"][-1][0] >= data["essayEnd"]
    assert facts["sessions"] == 142, f"the essay's session count moved: {facts['sessions']}"
    assert facts["julySessions"] == 22


# ── 2. the page against the data ──────────────────────────────────────────────────────────────

def _quoted(built: str) -> str:
    """The article's prose, with markup and whitespace flattened so a figure split across a line
    break or wrapped in <b> still matches."""
    body = re.sub(r"<script[\s\S]*?</script>", " ", built)
    body = re.sub(r"<style[\s\S]*?</style>", " ", body)
    body = re.sub(r"<[^>]+>", " ", body)
    return re.sub(r"(?:\s|&nbsp;|&#160;)+", " ", body)


def test_every_headline_figure_in_the_prose_is_the_computed_one(built, data):
    """The figures the essay's argument turns on, re-derived and looked for in the published copy.

    This is the test that catches the ordinary failure: someone improves a sentence, retypes a
    number from memory, and the page quietly starts disagreeing with its own chart.
    """
    f, lad = data["facts"], data["ladder"]
    prose = _quoted(built)
    expected = {
        "July return": f"{abs(f['julyReturn']):.1f} percent",
        "year through July": f"{f['ytdThroughEssay']:.1f} percent",
        "best session": f"{f['bestSession']:.1f} percent",
        "peak to trough": f"{abs(f['peakToTrough']):.1f} percent",
        "peak level": f"{f['peak']:,.2f}",
        "trough level": f"{f['trough']:,.2f}",
        "June 30 level": f"{f['juneEnd']:,.2f}",
        "missing one session": f"{lad[1]:.1f} percent",
        "cost of one session": f"{f['missOneCost']:.1f} percentage points",
        "missing three": f"{lad[3]:.1f} percent",
        "missing ten": f"{abs(lad[10]):.1f} percent",
    }
    missing = {k: v for k, v in expected.items() if v not in prose}
    assert not missing, f"the prose no longer quotes the computed figure for: {missing}"


def test_the_negative_five_percent_figure_is_stated_as_a_minus(built, data):
    """Missing the five best sessions turns a 53 percent year negative. The essay writes it out as
    "minus 6.9 percent" rather than with a glyph, which is the house style and also the only form
    that survives being read aloud."""
    assert f"minus {abs(data['ladder'][5]):.1f} percent" in _quoted(built)


def test_the_session_counts_in_the_prose_are_spelled_and_correct(built, data):
    f = data["facts"]
    prose = _quoted(built)
    assert f["julyBigMoves"] == 10 and "Ten of the month's twenty-two sessions" in prose
    assert f["bigMoves"] == 32 and "thirty-two of one hundred forty-two" in prose
    assert f["peakToTroughSessions"] == 27 and "twenty-seven trading sessions" in prose
    by_month = f["bigMovesByMonth"]
    assert (by_month["2026-03"], by_month["2026-06"], by_month["2026-07"]) == (7, 7, 10)
    assert "seven in March, seven in June, ten in July" in prose


def test_the_dated_update_carries_the_most_recent_close(built, data):
    latest = data["latest"]
    prose = _quoted(built)
    assert f"{latest['level']:,.2f}" in prose, "the update box is not on the latest close"
    assert f"{abs(latest['change']):.2f} percent" in prose
    assert "written on Saturday" in prose, "the update no longer dates the essay beneath it"


# ── 3. the page against itself ────────────────────────────────────────────────────────────────

def test_every_generated_block_is_filled(src_page):
    """An empty marker pair ships a blank figure and a blank caption, and nothing else on the page
    would look wrong."""
    for name in K.BLOCKS:
        m = re.search(r"<!--%s-->([\s\S]*?)<!--/%s-->" % (re.escape(name), re.escape(name)),
                      src_page)
        assert m, f"the {name} markers are gone from the page"
        assert len(m.group(1).strip()) > 40, f"the {name} block is empty"


def test_the_four_figures_render_without_javascript(src_page):
    """Both instruments claim in their own comments to be enhancements over a correct static state.
    Four <svg> roots in the markup is what makes that claim true."""
    svgs = re.findall(r"<svg\b", src_page)
    assert len(svgs) >= 5, f"expected the four figures plus the brand mark, found {len(svgs)}"
    assert 'data-cadence-figure="daily"' in src_page
    assert 'data-ladder-figure="0"' in src_page


def test_the_static_and_scripted_figures_share_one_geometry(src_page):
    """The instruments redraw into the same viewBox the generator wrote. If the two drift, the
    figure jumps the moment the script runs, which reads as a bug even though both are correct."""
    py = (ROOT / "scripts" / "kospi_interval.py").read_text(encoding="utf-8")
    body = py[py.index("def fig_cadence("):py.index("def fig_ladder(")]
    _, _, pad_l, pad_r, top, bot = [
        x.strip() for x in
        re.search(r"pad_l, pad_r, top, bot = ([\d, ]+)", body).group(1).split(",")]
    js = re.search(r"var W = (\d+), H = (\d+), PL = (\d+), PR = (\d+), TOP = (\d+), BOT = (\d+);",
                   src_page)
    assert js, "the instrument script no longer declares its plotting geometry"
    assert (js.group(3), js.group(4), js.group(5), js.group(6)) == (pad_l, pad_r, top, bot), (
        "the generated figure and the scripted one use different padding")


def test_docs_matches_src(src_page, built):
    """docs/ is the deploy artifact and is copied by sync_docs.py. The one legitimate difference is
    the firm anchor, which the build expands from a token."""
    assert "<!--FIRM_ANCHOR-->" in src_page, "the page no longer carries the firm-anchor token"
    assert "<!--FIRM_ANCHOR-->" not in built, "docs/ still has an unexpanded token, run sync_docs.py"
    assert 'class="firm-anchor"' in built
    normalize = lambda t: re.sub(r"<!--FIRM_ANCHOR-->|<div class=\"firm-anchor\"[\s\S]*?</div>",
                                 "", t)
    assert normalize(src_page) == normalize(built), \
        "docs/the-interval-problem.html is out of sync with src, run scripts/sync_docs.py"


def test_the_page_is_registered_everywhere_a_page_has_to_be():
    """Four registries, and the repo has shipped a page missing one of them twice."""
    from drift.statepage import _CORE_SITEMAP
    assert PAGE in [loc for loc, _, _ in _CORE_SITEMAP], "not announced in the sitemap"
    assert PAGE in (ROOT / "scripts" / "sync_docs.py").read_text(), "not copied into docs/ by the build"
    assert PAGE in (ROOT / "scripts" / "phase2_nav.py").read_text(), "no masthead family assigned"
    assert PAGE in (DOCS / "sitemap.xml").read_text(), "the built sitemap has not been regenerated"


def test_the_essay_is_reachable_from_the_pages_that_index_essays():
    """A published essay nothing links to is an unpublished essay with a URL."""
    for name in ("research.html", "insights.html"):
        for tree in (WEB, DOCS):
            assert PAGE in (tree / name).read_text(encoding="utf-8"), \
                f"{tree.name}/{name} does not link the essay"


def test_the_share_card_exists_and_is_a_png():
    card = DOCS / "og" / "the-interval-problem.png"
    assert card.exists(), "no Open Graph card, so every share of this link renders as bare text"
    assert card.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert "og/the-interval-problem.png" in (WEB / PAGE).read_text(encoding="utf-8")


def test_the_house_punctuation_rule_holds(src_page):
    """No em dashes. The site's editorial standard, and the single most reliable tell that a page
    was pasted in from somewhere else."""
    prose = _quoted(src_page)
    assert "—" not in prose and "--" not in prose, "an em dash reached the copy"


def test_the_disclosure_survives(built):
    """The page makes hypothetical return claims, so the illustration language is load-bearing."""
    for phrase in ("Park Avenue Securities", "Past performance does not indicate future results",
                   "not investment advice or a recommendation",
                   "no one could have known in advance which sessions to miss"):
        assert phrase in _quoted(built), f"the disclosure lost: {phrase!r}"
    assert "adviserinfo.sec.gov" not in built and "Form ADV" not in built


def test_the_cache_is_committed_and_reproducible():
    """The point of committing it is that a reader, and the suite, can rebuild every figure in the
    piece from the repo alone."""
    assert CACHE.exists(), "the series the whole page is built from is not in the repo"
    blob = json.loads(CACHE.read_text())
    assert blob["symbol"] == "^KS11"
    assert len(blob["rows"]) > 200
    assert all(len(r) == 2 and isinstance(r[1], (int, float)) for r in blob["rows"])


# ── the two failures this page had on 2026-08-04 ──────────────────────────────────────────────

def test_the_series_reaches_the_most_recent_settled_session(data):
    """No stale tail.

    Yahoo's multi-day arrays lag. Hours after the Seoul close on 2026-08-04 the two-year array
    still ended at August 3 (6,257.45) while the quote already read 6,358.95, so a generator that
    trusted only the array published a page a full session behind while printing its own as-of
    date. fetch() now fills the tail from the single-day endpoint; this fails if that stops
    working, or if a cache is committed with a settled session missing from it.
    """
    stamp = dt.datetime.fromisoformat(data["asOf"])
    if stamp.time() < dt.time(15, 0):
        pytest.skip("the session in the cache had not settled when it was taken")
    assert data["series"][-1][0] == stamp.strftime("%Y-%m-%d"), (
        f"the series ends at {data['series'][-1][0]} but the quote is stamped "
        f"{stamp.strftime('%Y-%m-%d')} after the close: a settled session is missing")


def test_the_dated_reporting_stays_welded_to_its_own_session(built, data):
    """Reporting is dated; a quote is live; the two cannot share a sentence.

    The update box carries press about ONE session: a sidecar, and the two chipmakers. It used to
    be attached to "the latest session" instead, which held for exactly one day. When August 4
    closed UP 1.62 percent the generator produced "opened sharply lower and triggered a five-minute
    program trading suspension" over that session's figures, and would have published it.
    """
    prose = _quoted(built)
    by_day = {d: c for d, c in data["series"]}
    i = [d for d, _ in data["series"]].index(K.SIDECAR_SESSION)
    level = by_day[K.SIDECAR_SESSION]
    move = abs(K.pct(data["series"][i - 1][1], level))
    assert "On Monday, August 3" in prose, "the sidecar report no longer names its own date"
    assert f"It closed at {level:,.2f}" in prose, "the sidecar report is not on its own close"
    assert f"down {move:.2f} percent" in prose, "the sidecar report is not on its own move"
    # And the live line is a separate sentence carrying the separate session.
    latest = data["latest"]
    assert f"{latest['level']:,.2f}" in prose and f"{abs(latest['change']):.2f} percent" in prose
    if latest["date"] != K.SIDECAR_SESSION:
        assert f"on the {_day(latest['date'])} session" in prose, \
            "the live close does not name the session it belongs to"


def _day(iso: str) -> str:
    return dt.date.fromisoformat(iso).strftime("%B %-d")


# ── the rounding contract ─────────────────────────────────────────────────────────────────────

def test_no_stored_figure_is_pre_rounded_to_a_display_precision(data):
    """Values are stored at full precision and rounded exactly once, at display time.

    The bug this pins shipped on 2026-08-04. The year-to-date return was 47.5521. The update box
    formatted the raw value and printed 47.6. The instruments read a value the generator had
    already rounded to two places, and round(47.5521, 2) is a float sitting just BELOW 47.55, so
    formatting it again at one place gave 47.5. The page said 47.6 in one place and 47.5 in
    another, from one series, directly under a colophon promising they cannot disagree.

    Two places is the dangerous precision precisely because it is one digit beyond what is shown.
    Anything stored at four or more is safe, because a second rounding can no longer cross a
    boundary the first one moved.
    """
    suspect = []
    for cadence, s in data["cadences"].items():
        for k in ("total", "worstStep", "maxDrawdown"):
            suspect.append((f"cadences.{cadence}.{k}", s[k]))
    for n, v in enumerate(data["ladder"]):
        suspect.append((f"ladder[{n}]", v))
    pre_rounded = [(name, v) for name, v in suspect
                   if v != 0 and round(v, 2) == v and round(v, 4) == v and abs(v * 100 % 1) < 1e-9]
    assert not pre_rounded, (
        f"stored at exactly two decimals, one digit beyond the display: {pre_rounded[:6]}. "
        "Store full precision and let _mag() round once.")


def test_the_update_box_and_the_instrument_state_the_same_year_to_date(built, data):
    """The reader's version of the test above, and the one that actually caught it.

    Two places on this page report the return over the whole period: the dated stamp at the top
    and the instrument's fourth readout. They are the same quantity from the same series and they
    must render the same string.
    """
    ytd = K.pct(data["series"][0][1], data["latest"]["level"])
    prose = _quoted(built)
    assert f"{K._mag(ytd)} percent higher than it began the year" in prose, \
        f"the update box does not state {K._mag(ytd)} percent"
    for cadence, s in data["cadences"].items():
        assert K._pc(s["total"]) == f"+{K._mag(ytd)}%", (
            f"the {cadence} instrument reports {K._pc(s['total'])} while the update box reports "
            f"+{K._mag(ytd)}%")
    assert f'id="c-total">{K._pc(data["cadences"]["daily"]["total"])}<' in built


def test_the_python_and_javascript_rounding_agree():
    """The static figure and the scripted one are rounded by two different implementations. They
    have to be the same rule, or the page changes its numbers the moment the script runs."""
    src = (WEB / PAGE).read_text(encoding="utf-8")
    assert "Math.round(Math.abs(v) * q) / q" in src, \
        "the page's pct() no longer rounds half up the way _mag() does"
    assert "math.floor(abs(v) * q + 0.5) / q" in (
        ROOT / "scripts" / "kospi_interval.py").read_text(encoding="utf-8")
