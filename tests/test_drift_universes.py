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
    # Every proxied fund is either a traded cell or the VT global-market reference.
    for fund in u.PROXY:
        assert fund in u.EQUITIES or fund == "VT"
    assert u.PROXY["AVEE"] == "EEMS"
    assert u.PROXY["VT"] == "VTI"


def test_every_ticker_has_a_label():
    for t in u.EQUITIES + u.CRYPTO + u.BASELINES:
        assert t in u.LABELS and u.LABELS[t]


def test_groups_cover_the_universe():
    grouped = [t for syms in u.GROUPS.values() for t in syms]
    assert sorted(grouped) == sorted(u.EQUITIES)
