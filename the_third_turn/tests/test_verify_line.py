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


def test_probe_quote_reveals_state_match():
    """The rescue pass probes with line=0 — a fire proves the STATE gates pass,
    then the verified median decides. Stale-HIGH scrape lines can't block fires."""
    from config import Constraints, TriggerRule
    from live_engine import evaluate_rule
    from tests.test_trigger import state, q as make_q

    rule = TriggerRule(name="TTO3-Mid/Back", times_through_order=3,
                       top_of_order_slots=[1, 2, 3, 4], starter_tier_filter=["Mid", "Back"],
                       min_inning=5, ttop_run_multiplier=1.15)
    c = Constraints()
    st = state(inning=6, times_through_order=3, batting_slot_due=2)

    # stale-HIGH scrape (12.0) blocks the fire...
    assert evaluate_rule(rule, st, make_q(12.0), 9.0, c, 4.5) == []
    # ...but the probe shows the state gates match...
    from sources.base import Quote
    probe = Quote(book="probe", home=st.home, away=st.away, line=0.0, live_game=True)
    assert evaluate_rule(rule, st, probe, 9.0, c, 4.5) != []
    # ...and the verified median (5.0, below fair) rescues the fire.
    vq = Quote(book="market-verified", home=st.home, away=st.away, line=5.0, live_game=True)
    rescued = evaluate_rule(rule, st, vq, 9.0, c, 4.5)
    assert rescued and rescued[0].quote.book == "market-verified"


def test_verifier_daily_budget_cap():
    from live_engine import LineVerifier
    v = LineVerifier("k", daily_cap=2)
    assert v._budget_ok() and v._budget_ok()   # counter resets/init per day
    v.fetches_today = 2
    assert not v._budget_ok()                  # cap reached -> no more spends today


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
