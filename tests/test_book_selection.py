from mrbet.config import EventMeta
from mrbet.odds.theodds import TheOddsProvider


def _provider(books, fallback=True, **kw):
    ev = EventMeta(id="g", away="Oklahoma City Thunder", home="San Antonio Spurs",
                   away_key="OKC", home_key="SAS")
    return TheOddsProvider(event=ev, markets=["total_full"], api_key="x",
                           books=books, fallback_consensus=fallback, **kw)


def _payload(lines_by_book):
    """lines_by_book: {book: (point, over, under)} -> Odds API event payload."""
    bms = []
    for book, (pt, o, u) in lines_by_book.items():
        bms.append({
            "key": book,
            "markets": [{
                "key": "totals",
                "outcomes": [
                    {"name": "Over", "point": pt, "price": o},
                    {"name": "Under", "point": pt, "price": u},
                ],
            }],
        })
    return {"bookmakers": bms}


def test_prefers_bovada_when_present():
    p = _provider(books=["bovada", "betonlineag"])
    payload = _payload({"betonlineag": (218.0, -110, -110), "bovada": (216.5, -105, -115)})
    lines = p._parse_lines(payload)
    assert len(lines) == 1
    assert lines[0].book == "bovada"
    assert lines[0].line == 216.5


def test_falls_back_to_next_preferred_book():
    p = _provider(books=["bovada", "betonlineag"])
    payload = _payload({"betonlineag": (218.0, -110, -110), "lowvig": (217.0, -105, -115)})
    line = p._parse_lines(payload)[0]
    assert line.book == "betonlineag"  # bovada absent, next preferred wins


def test_consensus_when_no_preferred_book():
    p = _provider(books=["bovada"], fallback=True)
    # No bovada; three other books -> pick the one nearest the median line (218.0).
    payload = _payload({
        "betus": (216.0, -110, -110),
        "lowvig": (218.0, -110, -110),
        "betonlineag": (221.0, -110, -110),
    })
    line = p._parse_lines(payload)[0]
    assert line.line == 218.0
    assert line.book == "lowvig"


def test_no_line_when_no_preferred_and_consensus_disabled():
    p = _provider(books=["bovada"], fallback=False)
    payload = _payload({"lowvig": (218.0, -110, -110)})
    assert p._parse_lines(payload) == []
