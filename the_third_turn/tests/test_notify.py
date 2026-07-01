"""Discord embed builder (Revision 3) — pure payload, no network."""

from shared_piping.notify import (ARM_COLOR, CONFIRM_COLOR, DiscordNotifier, build_embed,
                                  game_script_tag, pull_risk_label)
from shared_piping.run_expectancy import RunEnvAnchor
from live_engine import Trigger
from sources.base import LiveGameState, Quote


def make_trigger(ttype="CONFIRM", rule="TTO3-Mid/Back", line=7.0, fair=8.5, bullpen=4.5):
    s = LiveGameState(game_pk=1, away="CWS", home="ATL", inning=6, half="top", away_score=2,
                      home_score=1, pitcher_id=99, pitcher_name="Test Guy", pitch_count=85,
                      batting_slot_due=2, times_through_order=3, status="Live", outs=0,
                      starter_tier="Back", data_age_seconds=12.0)
    anchor = RunEnvAnchor(expected_final=fair, base_remaining=4.0, situational=0.1,
                          frac_remaining=0.5, park=1.0)
    quote = Quote(book="fanduel", home="ATL", away="CWS", line=line)
    return Trigger(ttype, rule, s.game_key, s, quote, 9.0, line, anchor, bullpen, ["r"])


def test_embed_has_all_required_fields():
    e = build_embed(make_trigger(), bullpen_elite_ra9=3.8, max_data_age=30)
    names = [f["name"] for f in e["fields"]]
    assert names == ["Why (rule)", "Gap (Over value)", "Pull Risk", "Score", "Pitcher", "Latency"]


def test_embed_shows_gap_score_latency_and_rule():
    e = build_embed(make_trigger(line=7.0, fair=8.5), bullpen_elite_ra9=3.8, max_data_age=30)
    body = {f["name"]: f["value"] for f in e["fields"]}
    assert "TTO3-Mid/Back" in e["title"] and "CWS @ ATL" in e["title"]
    assert "+1.5" in body["Gap (Over value)"]         # fair 8.5 - line 7.0
    assert "2 – 1" in body["Score"]
    assert "12s" in body["Latency"]


def test_embed_color_per_type():
    assert build_embed(make_trigger("CONFIRM"), bullpen_elite_ra9=3.8, max_data_age=30)["color"] == CONFIRM_COLOR
    assert build_embed(make_trigger("ARM"), bullpen_elite_ra9=3.8, max_data_age=30)["color"] == ARM_COLOR


def test_latency_flags_stale():
    t = make_trigger()
    t.state.data_age_seconds = 45.0
    e = build_embed(t, bullpen_elite_ra9=3.8, max_data_age=30)
    assert "STALE" in {f["name"]: f["value"] for f in e["fields"]}["Latency"]


def test_pull_risk_labels():
    assert pull_risk_label(None, 3.8).startswith("UNKNOWN")
    assert pull_risk_label(3.0, 3.8).startswith("HIGH")
    assert pull_risk_label(5.5, 3.8).startswith("LOW")


def test_game_script_tag():
    assert game_script_tag(2, 2) == "tie"
    assert game_script_tag(5, 1).startswith("blowout")


def test_notifier_disabled_without_url():
    assert DiscordNotifier(webhook_url="").enabled is False


def test_confirm_ping_payload():
    n = DiscordNotifier(webhook_url="https://x", ping="everyone")
    payload = n._payload(make_trigger("CONFIRM"))
    assert payload["content"].startswith("@everyone")
    # ARM never pings.
    assert "content" not in n._payload(make_trigger("ARM"))
