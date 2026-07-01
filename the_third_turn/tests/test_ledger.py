"""JSONL ledger (Revision 3) — every fired signal, tagged by trigger_type."""

import json

from shared_piping.ledger import Ledger, build_row
from shared_piping.run_expectancy import RunEnvAnchor
from live_engine import Trigger
from sources.base import LiveGameState, Quote


def make_trigger(ttype="WATCH", rule="WATCH-low-scoring", line=6.0, fair=8.0):
    s = LiveGameState(game_pk=777, away="CWS", home="ATL", inning=3, half="top", away_score=0,
                      home_score=1, pitcher_id=42, pitcher_name="Arm", pitch_count=40,
                      batting_slot_due=3, times_through_order=1, status="Live", outs=1,
                      starter_tier="Mid", data_age_seconds=None)
    anchor = RunEnvAnchor(expected_final=fair, base_remaining=5.0, situational=0.0,
                          frac_remaining=0.7, park=1.0)
    return Trigger(ttype, rule, s.game_key, s, Quote(book="sim", home="ATL", away="CWS", line=line),
                   8.5, line, anchor, 4.2, ["r"])


def test_build_row_tags_trigger_type_and_core_fields():
    row = build_row(make_trigger("WATCH"), bullpen_elite_ra9=3.8)
    assert row["trigger_type"] == "WATCH"
    assert row["rule_name"] == "WATCH-low-scoring"
    assert row["game_pk"] == 777
    assert row["live_total"] == 6.0 and row["fair"] == 8.0 and row["edge"] == 2.0
    assert row["pull_risk"] in ("LOW", "MED", "HIGH", "UNKNOWN")


def test_ledger_appends_jsonl(tmp_path):
    path = tmp_path / "ledger.jsonl"
    led = Ledger(path, bullpen_elite_ra9=3.8)
    led.record(make_trigger("CONFIRM", rule="TTO3-Mid/Back"))
    led.record(make_trigger("WATCH"))
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 2
    types = [json.loads(l)["trigger_type"] for l in lines]
    assert types == ["CONFIRM", "WATCH"]


def test_ledger_extra_fields_for_simulation(tmp_path):
    path = tmp_path / "sim.jsonl"
    row = Ledger(path).record(make_trigger("ARM"), ts="2025-04-01",
                              extra={"final_total": 11, "outcome": "Over"})
    assert row["outcome"] == "Over" and row["final_total"] == 11 and row["ts"] == "2025-04-01"
