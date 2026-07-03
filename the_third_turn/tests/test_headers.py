"""User-Agent rotation should vary the fingerprint and stay browser-like."""

from shared_piping.headers import USER_AGENTS, HeaderRotator, rotating_headers


def test_rotates_through_pool_round_robin():
    rot = HeaderRotator()
    seen = [rot.random()["User-Agent"] for _ in range(len(USER_AGENTS))]
    # a full cycle hits every distinct agent exactly once.
    assert set(seen) == set(USER_AGENTS)
    # and it wraps around deterministically.
    assert rot.random()["User-Agent"] == seen[0]


def test_headers_look_like_a_browser():
    h = rotating_headers(referer="https://example.com/")
    assert "Mozilla/5.0" in h["User-Agent"]
    assert h["Accept"].startswith("application/json")
    assert h["Referer"] == "https://example.com/"


def test_referer_optional():
    assert "Referer" not in rotating_headers()
