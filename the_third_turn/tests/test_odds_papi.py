"""Odds Papi closing-line extraction (Revision 6) — pure, no network."""

from datetime import datetime, timezone

from odds_papi_history import _last_pre, _parse_ts, closing_total, closing_total_for_book

START = datetime(2026, 6, 20, 23, 0, tzinfo=timezone.utc)

# marketId -> (handicap, Over outcomeId, Under outcomeId)
MMAP = {100: {"hc": 8.5, "over": 1001, "under": 1002},
        200: {"hc": 7.0, "over": 2001, "under": 2002}}


def _snap(mins_before, price, extra_after=False):
    hh = 22 if not extra_after else 23  # 22:xx is pre-start, 23:30 is post-start
    mm = 60 - mins_before if not extra_after else 30
    return {"createdAt": f"2026-06-20T{hh:02d}:{mm:02d}:00.000Z", "price": price, "active": True}


def _market(over_id, under_id, over_price, under_price, post_over=None):
    over_snaps = [_snap(20, 2.5), _snap(5, over_price)]
    if post_over:  # a post-first-pitch snapshot that must be ignored
        over_snaps.append(_snap(0, post_over, extra_after=True))
    return {"outcomes": {
        str(over_id): {"players": {"0": over_snaps}},
        str(under_id): {"players": {"0": [_snap(20, 2.5), _snap(5, under_price)]}},
    }}


def test_picks_balanced_main_line():
    markets = {
        "100": _market(1001, 1002, 1.91, 1.91),   # hc 8.5, balanced -> main line
        "200": _market(2001, 2002, 1.40, 3.10),   # hc 7.0, lopsided alt line
    }
    assert closing_total_for_book(markets, MMAP, START) == 8.5


def test_ignores_post_first_pitch_snapshots():
    # if the balanced price only appears AFTER first pitch, it must not be used.
    markets = {"100": _market(1001, 1002, 1.91, 1.91, post_over=1.05)}
    line = closing_total_for_book(markets, MMAP, START)
    assert line == 8.5   # uses the pre-start snapshot, not the post-start 1.05


def test_last_pre_filters_and_orders():
    snaps = [{"createdAt": "2026-06-20T22:00:00Z", "price": 1.8},
             {"createdAt": "2026-06-20T22:50:00Z", "price": 1.9},
             {"createdAt": "2026-06-20T23:30:00Z", "price": 9.9}]  # post-start
    assert _last_pre(snaps, START)["price"] == 1.9


def test_median_across_books():
    # both books' balanced line is the hc-8.5 market -> median 8.5.
    hist = {"bookmakers": {
        "pinnacle": {"markets": {"100": _market(1001, 1002, 1.91, 1.91),
                                 "200": _market(2001, 2002, 1.40, 3.10)}},
        "fanduel": {"markets": {"100": _market(1001, 1002, 1.95, 1.88),
                                "200": _market(2001, 2002, 1.35, 3.20)}},
    }}
    total, n = closing_total(hist, MMAP, START)
    assert n == 2 and total == 8.5


def test_no_lines_returns_none():
    assert closing_total({"bookmakers": {}}, MMAP, START) == (None, 0)


def test_parse_ts_handles_z():
    assert _parse_ts("2026-06-20T23:00:00.000Z") == START
