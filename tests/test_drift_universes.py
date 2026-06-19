from drift import universes as u


def test_matrix_spans_regions_sizes_styles_without_dupes():
    assert len(u.EQUITIES) == len(set(u.EQUITIES))          # no duplicate tickers
    assert set(u.REGION_OF.values()) == {"US", "DEV", "EM"}
    assert {"value", "blend", "growth"} <= set(u.STYLE_OF.values())
    assert {"large", "mid", "small"} <= set(u.SIZE_OF.values())
    # the full US 3x3 size x style box is present
    us = [t for t in u.EQUITIES if u.REGION_OF[t] == "US"]
    assert len(us) == 9
    assert {(u.SIZE_OF[t], u.STYLE_OF[t]) for t in us} == {
        (sz, st) for sz in ("large", "mid", "small") for st in ("value", "blend", "growth")}


def test_known_cells_mapped_correctly():
    assert u.MATRIX["IWN"] == ("US", "small", "value")
    assert u.MATRIX["EFG"] == ("DEV", "largemid", "growth")
    assert u.MATRIX["AVEE"] == ("EM", "small", "value")


def test_group_map_dimensions():
    assert u.group_map("region")["IVV"] == "US"
    assert u.group_map("size")["IWN"] == "small"
    assert u.group_map("style")["IVE"] == "value"
    assert u.group_map("factor")["IVE"] == "value"     # alias for style
    assert u.group_map("none") == {}


def test_proxies_point_to_longer_history_funds():
    # Every proxied fund is either a traded cell or the VT global-market reference,
    # and every proxy is a non-empty, distinct legacy ticker (no self-proxy).
    for fund, proxy in u.PROXY.items():
        assert fund in u.EQUITIES or fund == "VT"
        assert isinstance(proxy, str) and proxy and proxy != fund
    # A few load-bearing legacy splices that give the tearsheet its deep history.
    assert u.PROXY["IVV"] == "VFINX"     # US large blend  <- Vanguard 500 (1986)
    assert u.PROXY["AVEE"] == "DGS"      # EM small value  <- WisdomTree EM small (2007)
    assert u.PROXY["VT"] == "VFINX"      # global reference back to 1986


def test_every_ticker_has_a_label():
    for t in u.EQUITIES + u.BASELINES:
        assert t in u.LABELS and u.LABELS[t]


def test_groups_cover_the_universe():
    grouped = [t for syms in u.GROUPS.values() for t in syms]
    assert sorted(grouped) == sorted(u.EQUITIES)


def test_tlh_substitutes_are_distinct_and_cover_the_matrix():
    for tkr in u.EQUITIES:
        sub = u.tlh_substitute(tkr)
        assert sub, f"{tkr} has no TLH substitute"
        assert sub != tkr                       # a real alternative, not itself
    # IVV's substitute must NOT be VOO (same S&P 500 index = substantially identical).
    assert u.TLH_SUBSTITUTE["IVV"] not in ("VOO", "SPY", "IVV")
    assert u.tlh_substitute("IWN") == "VBR"     # Russell 2000 Value -> CRSP small value
    assert u.tlh_substitute("ZZZZ") is None     # unmapped ticker
