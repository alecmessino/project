"""Fuzzy team resolution must unify how MLB/FanDuel/Bovada spell the same club."""

import pytest

from shared_piping.team_map import canonical_keys, resolve


@pytest.mark.parametrize("name,expected", [
    ("Arizona Diamondbacks", "ARI"),
    ("D-Backs", "ARI"),
    ("d backs", "ARI"),
    ("Arizona", "ARI"),
    ("Chicago White Sox", "CWS"),
    ("Chicago Cubs", "CHC"),
    ("White Sox", "CWS"),
    ("Cubs", "CHC"),
    ("Athletics", "OAK"),
    ("A's", "OAK"),
    ("St. Louis Cardinals", "STL"),
    ("Cards", "STL"),
    ("Tampa Bay Rays", "TB"),
    ("New York Yankees", "NYY"),
    ("New York Mets", "NYM"),
    ("Washington Nationals", "WSH"),
    ("Nats", "WSH"),
])
def test_resolves_known_aliases(name, expected):
    assert resolve(name) == expected


def test_disambiguates_chicago_and_new_york():
    # the two-team cities must never collide.
    assert resolve("Chicago White Sox") != resolve("Chicago Cubs")
    assert resolve("New York Yankees") != resolve("New York Mets")


def test_handles_book_descriptor_wrapping():
    # FanDuel-style "(Pitcher)" and Bovada-style descriptors should still resolve.
    assert resolve("San Diego Padres (W Buehler)") == "SD"
    assert resolve("Over 8.5 - Arizona Diamondbacks") == "ARI"


def test_unknown_returns_none():
    # a city token that IS an MLB team (e.g. "Toronto") intentionally resolves; use
    # strings with no baseball token at all.
    assert resolve("Manchester United") is None
    assert resolve("zzzzzzzz") is None
    assert resolve("") is None
    assert resolve("   ") is None


def test_all_30_teams_present():
    assert len(canonical_keys()) == 30
