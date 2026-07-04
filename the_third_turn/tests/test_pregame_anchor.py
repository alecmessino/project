"""Pregame-anchor correctness (live-vs-pregame comparison audit fixes)."""

from live_engine import load_closing_lines, merge_quotes
from sources.base import Quote


def q(book, line, live=None, home="ATL", away="STL"):
    return Quote(book=book, home=home, away=away, line=line, live_game=live)


def test_merge_prefers_in_play_quote_over_tomorrows_pregame():
    # same matchup listed twice (today in-play + tomorrow pregame) — live must win.
    tomorrow = q("fanduel", 9.5, live=False)
    today_live = q("bovada", 8.0, live=True)
    merged = merge_quotes([tomorrow], [today_live])
    assert merged["STL@ATL"].line == 8.0 and merged["STL@ATL"].live_game


def test_merge_keeps_first_book_when_both_pregame():
    merged = merge_quotes([q("fanduel", 9.0, live=False)], [q("bovada", 9.5, live=False)])
    assert merged["STL@ATL"].book == "fanduel"


def test_merge_live_not_displaced_by_later_pregame():
    merged = merge_quotes([q("bovada", 8.0, live=True)], [q("fanduel", 9.5, live=False)])
    assert merged["STL@ATL"].line == 8.0


def test_load_closing_lines(tmp_path):
    p = tmp_path / "closing_lines.csv"
    p.write_text("game_pk,pregame_total,n_books,commence_time,source\n"
                 "823445,8.0,9,2026-07-01T22:41:00Z,theoddsapi\n"
                 "bad,row,,,\n"
                 "824905,9.0,9,2026-07-01T23:16:00Z,theoddsapi\n")
    lines = load_closing_lines(p)
    assert lines == {823445: 8.0, 824905: 9.0}


def test_load_closing_lines_missing_file(tmp_path):
    assert load_closing_lines(tmp_path / "nope.csv") == {}
