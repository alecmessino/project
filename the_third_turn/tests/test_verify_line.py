"""Fire-time line verification (stale-feed fix) — pure, no network."""

from datetime import datetime, timedelta, timezone

from live_engine import LineVerifier, verification_verdict
from shared_piping.notify import build_embed
from tests.test_notify import make_trigger


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _event(away, home, commence, books):
    return {"away_team": away, "home_team": home, "commence_time": commence,
            "bookmakers": [{"key": k, "markets": [{"key": "totals", "outcomes": [
                {"name": "Over", "point": v}, {"name": "Under", "point": v}]}]}
                for k, v in books.items()]}


def test_parse_board_excludes_tomorrows_series_game():
    now = datetime.now(timezone.utc)
    data = [
        _event("Cincinnati Reds", "Milwaukee Brewers", _iso(now - timedelta(hours=1)),
               {"draftkings": 9.5, "fanduel": 9.5, "betrivers": 9.0}),      # live game
        _event("Cincinnati Reds", "Milwaukee Brewers", _iso(now + timedelta(hours=17)),
               {"draftkings": 7.0, "fanduel": 7.0}),                        # TOMORROW
    ]
    board = LineVerifier.parse_board(data)
    assert board["CIN@MIL"]["median"] == 9.5          # live game wins, 7.0 excluded
    assert board["CIN@MIL"]["books"]["draftkings"] == 9.5


def test_verdict_suppresses_when_real_line_kills_edge():
    # the CIN@MIL case: fair 10.58, feed said 8.5 but real books sat 10.5.
    v_edge, suppress = verification_verdict(fair=10.58, verified_line=10.5, min_edge=0.5)
    assert suppress and v_edge == 0.08


def test_verdict_passes_when_edge_holds():
    v_edge, suppress = verification_verdict(fair=10.58, verified_line=9.5, min_edge=0.5)
    assert not suppress and v_edge == 1.08


def test_embed_gains_verified_field():
    verified = {"median": 9.5, "books": {"draftkings": 9.5, "fanduel": 9.5}}
    e = build_embed(make_trigger(fair=10.5), bullpen_elite_ra9=3.8, max_data_age=30,
                    verified=verified)
    names = [f["name"] for f in e["fields"]]
    assert names[-1] == "Betable line (verified)"
    assert "DK 9.5" in e["fields"][-1]["value"]
    # without verification the embed is unchanged (6 fields)
    e2 = build_embed(make_trigger(), bullpen_elite_ra9=3.8, max_data_age=30)
    assert len(e2["fields"]) == 6
