"""The Shortest Line on the Chart: the arithmetic, and the claim it rests on.

The piece asserts something a reader cannot check by eye: that across five Asian drawdowns, which
one is "worst" changes hands repeatedly as the measurement window moves. If a data refresh or an
edit to the sampler ever made that false, the page would still read fluently and would be arguing
nothing. That is the thing pinned hardest here.

The ?stop= URL path is covered in tests/web/test_shortest_line.js, per CLAUDE.md: it is browser
code and it gets exercised through the query string, not through the slider.
"""
import importlib.util
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"
PAGE = "the-shortest-line.html"
CACHE = ROOT / "tests" / "data" / "asia_drawdowns.json"


def _generator():
    spec = importlib.util.spec_from_file_location("asia_drawdowns",
                                                  ROOT / "scripts" / "asia_drawdowns.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


A = _generator()


@pytest.fixture(scope="module")
def data():
    return A.build(json.loads(CACHE.read_text())["raw"])


@pytest.fixture(scope="module")
def built():
    return (DOCS / PAGE).read_text(encoding="utf-8")


def _visible(text: str) -> str:
    for pattern in (r"<!--[\s\S]*?-->", r"<script[\s\S]*?</script>", r"<style[\s\S]*?</style>"):
        text = re.sub(pattern, " ", text)
    return re.sub(r"(?:\s|&nbsp;|&#160;)+", " ", re.sub(r"<[^>]+>", " ", text))


# ── the arithmetic ────────────────────────────────────────────────────────────────────────────

def test_the_peaks_are_the_ones_the_page_names(data):
    """The anchors are found in the series, not asserted, so this is the check that the search
    windows still bracket the right highs. Every number in the piece hangs off them."""
    found = {e["key"]: e["peakDate"] for e in data["events"]}
    assert found == {
        "kospi2026": "2026-06-22", "shanghai2015": "2015-06-12",
        "hangseng2007": "2007-10-30", "kospi1997": "1997-06-17", "nikkei1989": "1989-12-29",
    }, f"an event's peak moved: {found}"


def test_every_path_starts_at_its_own_peak(data):
    for e in data["events"]:
        assert e["path"][0] == 0, f"{e['key']} does not start at zero"
        assert e["troughPct"] < 0, f"{e['key']} never fell"


def test_the_title_of_worst_changes_hands_as_the_window_moves(data):
    """The claim the whole piece rests on. Not 'the numbers differ' but 'the ranking inverts':
    if one event led at every window, the page would be arguing nothing."""
    leaders = []
    for stop in range(5, data["horizon"], 5):
        leader = A.ranking(data, stop)[0]["key"]
        if not leaders or leaders[-1] != leader:
            leaders.append(leader)
    assert len(set(leaders)) >= 4, f"only {len(set(leaders))} events ever lead: {leaders}"
    assert len(leaders) >= 5, f"the lead only changes {len(leaders) - 1} times: {leaders}"
    assert leaders[-1] == "nikkei1989", f"the Nikkei does not end up worst: {leaders}"


def test_the_youngest_crash_leads_early_and_is_shallowest_eventually(data):
    """Both halves of the headline. It really is the fastest, and it really is the mildest."""
    subject = next(e for e in data["events"] if e["key"] == data["subject"])
    assert A.ranking(data, 27)[0]["key"] == "kospi2026", "2026 is no longer worst at session 27"
    floors = sorted(data["events"], key=lambda e: e["troughPct"])
    assert floors[-1]["key"] == "kospi2026", \
        f"2026 is no longer the shallowest of the five: {[(e['key'], e['troughPct']) for e in floors]}"
    assert subject["path"][27] < -35, "the 27-session decline the piece quotes has moved"


def test_the_ranking_never_silently_drops_an_unfinished_event(data):
    """An event with no reading at the chosen session is ranked on its last one and flagged. Drop
    it instead and the title passes to whoever is left, which is the move the piece objects to."""
    order = A.ranking(data, data["horizon"] - 1)
    assert len(order) == len(data["events"])
    subject = next(r for r in order if r["key"] == "kospi2026")
    assert subject["short"] is True and subject["at"] < data["horizon"] - 1


def test_recovery_is_the_first_close_back_at_the_peak(data):
    by = {e["key"]: e for e in data["events"]}
    assert by["nikkei1989"]["recoveryDays"] / A.SESSIONS_PER_YEAR > 30, "the Nikkei recovers too soon"
    assert by["kospi1997"]["recoveryDays"] / A.SESSIONS_PER_YEAR < 3, "Kospi 1997 recovers too late"
    assert by["shanghai2015"]["ongoing"] and by["kospi2026"]["ongoing"]
    assert by["hangseng2007"]["recoveryDays"] is not None


# ── the page against the data ─────────────────────────────────────────────────────────────────

def test_the_prose_quotes_the_computed_floors(built, data):
    prose = _visible(built)
    for e in data["events"]:
        figure = f"{abs(e['troughPct']):.1f} percent"
        assert figure in prose, f"{e['label']} floor of {figure} is not in the copy"


def test_the_rebound_arithmetic_in_the_closing_section_is_right(built, data):
    """The sharpest claim in the piece: the chart it answers ends one session before the largest
    single-day gain in the index's history, and the next point would have been minus 27.6."""
    subject = next(e for e in data["events"] if e["key"] == data["subject"])
    assert len(subject["path"]) > 28, "the 2026 series no longer reaches the rebound session"
    assert subject["path"][28] == pytest.approx(-27.6, abs=0.15), \
        f"session 28 is {subject['path'][28]}, the copy says minus 27.6"
    prose = _visible(built)
    assert "minus 27.6 percent" in prose and "session twenty-seven" in prose


def test_every_generated_block_is_filled():
    src = (WEB / PAGE).read_text(encoding="utf-8")
    for name in A.BLOCKS:
        m = re.search(r"<!--%s-->([\s\S]*?)<!--/%s-->" % (re.escape(name), re.escape(name)), src)
        assert m and len(m.group(1).strip()) > 40, f"the {name} block is missing or empty"
    assert 'data-paths-figure=' in src, "the figure has no static default state"


def test_docs_matches_src():
    src = (WEB / PAGE).read_text(encoding="utf-8")
    built = (DOCS / PAGE).read_text(encoding="utf-8")
    assert "<!--FIRM_ANCHOR-->" in src and "<!--FIRM_ANCHOR-->" not in built
    norm = lambda t: re.sub(r"<!--FIRM_ANCHOR-->|<div class=\"firm-anchor\"[\s\S]*?</div>", "", t)
    assert norm(src) == norm(built), f"docs/{PAGE} is stale, run scripts/sync_docs.py"


def test_the_page_is_registered_everywhere_a_page_has_to_be():
    from drift.statepage import _CORE_SITEMAP
    assert PAGE in [loc for loc, _, _ in _CORE_SITEMAP]
    assert PAGE in (ROOT / "scripts" / "sync_docs.py").read_text()
    # See the sibling note in test_interval_problem.py: the masthead spec lives in drift.nav now,
    # and the mapping is a truer assertion than a grep of the injector script.
    from drift.nav import CURRENT
    assert PAGE in CURRENT
    assert PAGE in (DOCS / "sitemap.xml").read_text()
    for name in ("commentary.html", "insights.html"):
        for tree in (WEB, DOCS):
            assert PAGE in (tree / name).read_text(encoding="utf-8"), f"{tree.name}/{name}"


def test_the_two_market_structure_pieces_point_at_each_other():
    """A note answering a chart is worth more next to the essay it extends than alone."""
    note = (DOCS / PAGE).read_text(encoding="utf-8")
    essay = (DOCS / "the-interval-problem.html").read_text(encoding="utf-8")
    assert "the-interval-problem.html" in note, "the note does not link the essay"
    assert PAGE in essay, "the essay does not link the note"


def test_the_share_card_exists():
    card = DOCS / "og" / "the-shortest-line.png"
    assert card.exists() and card.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert "og/the-shortest-line.png" in (WEB / PAGE).read_text(encoding="utf-8")


def test_the_house_punctuation_rule_holds():
    prose = _visible((WEB / PAGE).read_text(encoding="utf-8"))
    assert "—" not in prose and "--" not in prose


def test_the_disclosure_survives(built):
    prose = _visible(built)
    for phrase in ("Park Avenue Securities", "Past performance does not indicate future results",
                   "price returns in local currency", "does not adjust for inflation"):
        assert phrase in prose, f"the disclosure lost: {phrase!r}"


def test_the_where_korea_is_now_preset_tracks_the_live_series(data):
    """The jump buttons are generated, not typed.

    "Where Korea is now" was hardcoded to session 29 and was wrong by the next close. It is
    written from data["stopsAt"] now, so it moves with the series it names.
    """
    src = (WEB / PAGE).read_text(encoding="utf-8")
    m = re.search(r'<button type="button" data-stop="(\d+)">Where Korea is now</button>', src)
    assert m, "the live preset button is missing"
    assert int(m.group(1)) == data["stopsAt"], (
        f"the preset points at session {m.group(1)} but the 2026 series now ends at "
        f"{data['stopsAt']}")
    assert f'value="{data["stopsAt"]}"' in src or 'id="stop"' in src


def test_the_live_event_reaches_the_most_recent_settled_session(data):
    """Same stale-tail guard as the essay. Four of these five events are decades old; the fifth is
    the one the piece is about, and it is the one that can silently fall a session behind."""
    subject = next(e for e in data["events"] if e["key"] == data["subject"])
    kospi = json.loads(CACHE.read_text())["raw"]["kospi2026"]
    assert subject["path"] and len(subject["path"]) - 1 == data["stopsAt"]
    assert kospi[-1][0] >= "2026-08-04", f"the live series ends at {kospi[-1][0]}"


def test_no_stored_path_point_is_pre_rounded_to_a_display_precision(data):
    """Same contract as the essay. 238 of these points were stored at two decimals and displayed
    at one, which is the precision that re-rounds wrong at a .x5 boundary."""
    exact_2dp = [round(v, 2) == v and round(v, 4) == v and abs(v * 100 % 1) < 1e-9
                 for e in data["events"] for v in e["path"] if v != 0]
    assert not all(exact_2dp), "every path point lands on two decimals, which cannot be data"
    assert sum(exact_2dp) < len(exact_2dp) * 0.5, (
        "most path points are stored at exactly two decimals, one digit beyond the display: "
        "store full precision and let _mag() round once")


def test_the_python_and_javascript_rounding_agree():
    src = (WEB / PAGE).read_text(encoding="utf-8")
    assert "Math.round(Math.abs(v) * q) / q" in src
    assert "math.floor(abs(v) * q + 0.5) / q" in (
        ROOT / "scripts" / "asia_drawdowns.py").read_text(encoding="utf-8")
