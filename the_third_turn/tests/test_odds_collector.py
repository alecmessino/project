"""Odds collector consensus/sanity logic (Revision 4) — pure, no network."""

from odds_collector import consensus_total


def mk_event(over_points):
    return {"bookmakers": [
        {"markets": [{"key": "totals", "outcomes": [
            {"name": "Over", "point": p}, {"name": "Under", "point": p}]}]}
        for p in over_points
    ]}


def test_median_consensus():
    total, n = consensus_total(mk_event([8.5, 9.0, 8.5, 9.0, 9.0]), min_books=2)
    assert total == 9.0 and n == 5


def test_sanity_filter_drops_garbage():
    # a stray 26.5 (alt/team-total line) must not poison the median.
    total, n = consensus_total(mk_event([8.0, 8.5, 26.5, 8.0]), min_books=2)
    assert total == 8.0 and n == 3          # 26.5 filtered out


def test_min_books_enforced():
    total, n = consensus_total(mk_event([9.0]), min_books=2)
    assert total is None and n == 1


def test_rounds_to_half():
    total, _ = consensus_total(mk_event([8.5, 9.0]), min_books=2)   # median 8.75
    assert total == 8.5 or total == 9.0     # snapped to nearest 0.5
