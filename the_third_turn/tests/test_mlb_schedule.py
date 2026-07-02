"""Date-aware game_pk matching — the series-mislabel fix. Pure, no network."""

from shared_piping.mlb_schedule import et_date, match_game_pk

# a 3-game STL@ATL series: same pair, three schedule dates, three game_pks.
PAIR = frozenset(("STL", "ATL"))
SCHED = {(PAIR, "2026-06-30"): 111, (PAIR, "2026-07-01"): 222, (PAIR, "2026-07-02"): 333}


def test_et_date_rolls_late_utc_back_a_day():
    # 01:41 UTC on July 2 is a July 1 (ET) game.
    assert et_date("2026-07-02T01:41:00Z") == "2026-07-01"
    assert et_date("2026-07-01T23:16:00.000Z") == "2026-07-01"
    assert et_date(None) is None


def test_series_games_match_their_own_night():
    # evening game (23:16Z) -> July 1's pk, NOT June 30's or July 2's.
    assert match_game_pk(SCHED, "St. Louis Cardinals", "Atlanta Braves",
                         "2026-07-01T23:16:00Z") == 222
    # late game past UTC midnight -> still the July 1 game.
    assert match_game_pk(SCHED, "Cardinals", "Braves", "2026-07-02T01:41:00Z") == 222
    # next night's game -> July 2's pk.
    assert match_game_pk(SCHED, "STL", "ATL", "2026-07-02T23:16:00Z") == 333


def test_unknown_teams_return_none():
    assert match_game_pk(SCHED, "Manchester United", "ATL", "2026-07-01T23:00:00Z") is None
