"""Execution-simulation aggregation + outcome logic (Revision 3) — offline."""

import pandas as pd
import pytest

from simulate_execution import _final_totals, _pregame_totals, report


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
    real = rep[rep["rule_name"] == "ALL [real]"].iloc[0]
    proxy = rep[rep["rule_name"] == "ALL [proxy]"].iloc[0]
    assert real["fires"] == 2 and real["hit_rate_over_%"] == 50.0
    assert proxy["fires"] == 1 and proxy["hit_rate_over_%"] == 100.0
