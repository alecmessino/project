from drift import universes as u


def test_equities_spans_regions_and_factors_without_dupes():
    assert len(u.EQUITIES) == len(set(u.EQUITIES))          # no duplicate tickers
    # all three regions represented
    assert {"SPY"} <= set(u.US)
    assert {"EFA"} <= set(u.DEV_INTL)
    assert {"EEM"} <= set(u.EM)
    # regional×factor sleeves present (e.g. international small-cap value)
    assert "DLS" in u.DEV_INTL          # intl small value
    assert "DGS" in u.EM                # EM small value
    assert "VBR" in u.US                # US small value


def test_groups_cover_the_full_equities_universe():
    grouped = [t for syms in u.GROUPS.values() for t in syms]
    assert sorted(grouped) == sorted(u.EQUITIES)


def test_every_ticker_has_a_label():
    for t in u.EQUITIES + u.CRYPTO:
        assert t in u.LABELS and u.LABELS[t]


def test_csv_helper():
    assert u.csv(["A", "B", "C"]) == "A,B,C"
