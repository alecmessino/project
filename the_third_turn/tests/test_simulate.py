"""Execution-simulation aggregation + outcome logic (Revision 3) — offline."""

import pandas as pd
import pytest

from simulate_execution import (_final_totals, _matchup_pregame_totals, _pregame_totals,
                                report)


def _pa_frame(away_sp_ra9, home_sp_ra9, home_team="ATL", away_team="CWS"):
    """Tiny 2-starter PA frame: away SP pitches the bottom, home SP the top.
    runs/outs are set so each starter's season RA/9 = the requested value over 30 IP (90 outs)."""
    rows = []
    for topbot, ra9, pid in [("Bot", away_sp_ra9, 100), ("Top", home_sp_ra9, 200)]:
        runs = round(ra9 * 90 / 3 / 9)   # ra9 = 9*runs/(outs/3), outs=90 -> runs = ra9*30/9
        rows.append({"game_pk": 1, "inning_topbot": topbot, "pitcher": pid,
                     "runs": runs, "outs": 90, "home_team": home_team, "away_team": away_team})
    return pd.DataFrame(rows)


def test_matchup_line_lower_for_strong_pitching():
    strong = _matchup_pregame_totals(_pa_frame(2.5, 2.5), {}, bullpen={"ATL": 3.0, "CWS": 3.0})
    weak = _matchup_pregame_totals(_pa_frame(6.0, 6.0), {}, bullpen={"ATL": 5.5, "CWS": 5.5})
    assert strong[1] < weak[1]           # aces ⇒ lower total than batting-practice arms


def test_matchup_park_scales_line():
    coors = _matchup_pregame_totals(_pa_frame(4.3, 4.3, home_team="COL"), {},
                                    bullpen={"COL": 4.3, "CWS": 4.3})
    tmobile = _matchup_pregame_totals(_pa_frame(4.3, 4.3, home_team="SEA"), {},
                                      bullpen={"SEA": 4.3, "CWS": 4.3})
    assert coors[1] > tmobile[1]


def test_matchup_override_wins():
    out = _matchup_pregame_totals(_pa_frame(6.0, 6.0), {1: 6.5}, bullpen={"ATL": 5.5, "CWS": 5.5})
    assert out[1] == 6.5


def test_final_total_is_max_running_sum():
    df = pd.DataFrame({
        "game_pk": [1, 1, 1, 2, 2],
        "post_bat_score": [0, 2, 3, 1, 1],
        "post_fld_score": [0, 1, 4, 0, 5],
    })
    finals = _final_totals(df)
    assert finals[1] == 7      # max(3+4)
    assert finals[2] == 6      # max(1+5)


def test_pregame_proxy_scales_by_park():
    pa = pd.DataFrame({"game_pk": [1, 2], "home_team": ["ATL", "COL"]})
    tot = _pregame_totals(pa, override={})
    assert tot[1] == 8.5       # neutral park ~ league avg
    assert tot[2] > tot[1]     # Coors inflates


def test_pregame_override_wins():
    pa = pd.DataFrame({"game_pk": [1], "home_team": ["ATL"]})
    assert _pregame_totals(pa, override={1: 7.0})[1] == 7.0


def test_report_density_and_conditional_hit_rate():
    rows = [
        {"rule_name": "TTO2", "trigger_type": "CONFIRM", "outcome": "Over"},
        {"rule_name": "TTO2", "trigger_type": "CONFIRM", "outcome": "Under"},
        {"rule_name": "TTO3", "trigger_type": "CONFIRM", "outcome": "Over"},
        {"rule_name": "WATCH", "trigger_type": "WATCH", "outcome": "Push"},
    ]
    rep = report(rows, n_game_days=2, n_games=4)
    overall = rep[rep["rule_name"] == "ALL"].iloc[0]
    assert overall["fires"] == 4
    assert overall["fires_per_game_day"] == 2.0
    assert overall["hit_rate_over_%"] == pytest.approx(66.7, abs=0.1)

    tto2 = rep[rep["rule_name"] == "TTO2"].iloc[0]
    assert tto2["hit_rate_over_%"] == 50.0
    tto3 = rep[rep["rule_name"] == "TTO3"].iloc[0]
    assert tto3["hit_rate_over_%"] == 100.0


def test_report_splits_real_vs_proxy():
    rows = [
        {"rule_name": "TTO2", "trigger_type": "CONFIRM", "outcome": "Over", "line_source": "real"},
        {"rule_name": "TTO2", "trigger_type": "CONFIRM", "outcome": "Under", "line_source": "real"},
        {"rule_name": "TTO3", "trigger_type": "CONFIRM", "outcome": "Over", "line_source": "proxy"},
    ]
    rep = report(rows, n_game_days=1, n_games=3)
    real = rep[rep["rule_name"] == "ALL (real)"].iloc[0]
    proxy = rep[rep["rule_name"] == "ALL (proxy)"].iloc[0]
    assert real["fires"] == 2 and real["hit_rate_over_%"] == 50.0
    assert proxy["fires"] == 1 and proxy["hit_rate_over_%"] == 100.0
