"""The Crossing Brief — rendered as an operating document.

Takes the structured brief from `drift.crossing.build_crossing` and lays it out as an institutional
transition memo: a document handed to a decision-maker before a move, whose job is to COORDINATE.
It shares the limestone Atlas system but reads as a prepared brief — a transition band, a one-sentence
executive summary, and operating sections (environment changed · coordination · decisions ·
opportunities · a before/during/after action register · questions worth asking).

    render_crossing_html(brief, edition)      — one directional brief (SSR)
    render_crossing_index_html(edition)       — the routes households make most often
    export_crossings(out_dir, edition)        — the featured briefs + the index

Every Crossing Brief is prepared for a SPECIFIC move; the featured corridors demonstrate the product,
and the Household Record (planned) prepares one bound to a household's own crossing.
"""
from __future__ import annotations

from pathlib import Path

from .leakage import STATE_NAMES
from .statemap import AS_OF_LAW, LAST_REVIEWED, CURRENT_EDITION
from .statepage import (
    _esc, _ABS, NAV_ABS, PLAUSIBLE, DISCLOSURE, _HEAD_CSS, _provenance_block, atlas_url,
    _process_bar, MEETING_URL,
)
from .site import BASE_URL, firm_anchor_html
from . import crossing as _xing

_XING_CSS = _HEAD_CSS + """
  /* ── Crossing Brief — the transition memo ───────────────────────────────────────────────────── */
  .xband{margin:16px 40px 4px;padding:20px 26px;background:var(--navy);color:#eef1f4;display:flex;
    align-items:center;gap:12px 26px;flex-wrap:wrap}
  .xband .leg{display:flex;flex-direction:column;gap:3px}
  .xband .leg .lbl{font-family:var(--sans);font-weight:700;font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--gold)}
  .xband .leg .st{font-family:var(--sans);font-weight:700;font-size:23px;letter-spacing:-.01em;color:#f1ede3;line-height:1}
  .xband .arrow{font-size:24px;color:var(--gold);font-weight:400;line-height:1}
  .xband .prep{margin-left:auto;font-size:11px;color:#aeb7c1;line-height:1.5;text-align:right;max-width:26ch}
  .thesis{font-family:var(--serif);font-size:19px;line-height:1.5;color:var(--ink);margin:0 40px;
    padding:2px 0 2px 18px;border-left:3px solid var(--brass);max-width:none}
  /* Change table (environment that changed) + priority table share a ruled, tabular look. */
  .xtab{width:calc(100% - 80px);margin:2px 40px 0;border-collapse:collapse;font-size:12.5px}
  .xtab th,.xtab td{text-align:left;vertical-align:top;padding:9px 12px;border-bottom:1px solid var(--line2)}
  .xtab thead th{font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:700;font-family:var(--sans)}
  .xtab .dim{font-family:var(--sans);font-weight:700;color:var(--ink);white-space:nowrap}
  .xtab .tag{font-family:var(--sans);font-weight:700;font-size:11px;color:var(--brass);display:block;margin-bottom:1px}
  .xtab .nt{color:var(--body);line-height:1.4}
  .xtab .arr{color:var(--gold);text-align:center;width:26px}
  @media(max-width:820px){.xtab{width:100%;margin:2px 0 0;font-size:12px}.xtab .arr{display:none}}
  /* Coordination priority table */
  .ptab{width:calc(100% - 80px);margin:2px 40px 0;border-collapse:collapse;font-size:12px}
  .ptab th,.ptab td{text-align:left;vertical-align:top;padding:10px 12px;border-bottom:1px solid var(--line2)}
  .ptab thead th{font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:700;font-family:var(--sans)}
  .ptab .p{font-family:var(--sans);font-weight:700;color:var(--ink);white-space:nowrap}
  .ptab .new{display:inline-block;font-family:var(--sans);font-weight:700;font-size:8.5px;letter-spacing:.1em;
    text-transform:uppercase;color:#fff;background:var(--accent-strike);padding:1px 6px;margin-left:6px;vertical-align:middle}
  .ptab .u{font-family:var(--sans);font-weight:700;font-size:10px;letter-spacing:.06em;text-transform:uppercase;white-space:nowrap}
  .ptab .u-immediate{color:var(--neg)} .ptab .u-near-term{color:var(--brass)} .ptab .u-ongoing{color:var(--muted)}
  .ptab .rz{color:var(--body);line-height:1.4} .ptab .dep{color:var(--muted);font-size:11px}
  @media(max-width:820px){.ptab{width:100%;margin:2px 0 0}.ptab .hide-sm{display:none}}
  /* Decisions to reconsider + opportunities — ruled cards */
  .rlist{list-style:none;margin:0;padding:0;display:grid;gap:9px}
  .sec .rlist{margin:2px 0 0}
  .rlist li{border:1px solid var(--line);border-left:3px solid var(--brass);background:#fff;padding:11px 15px}
  .rlist li.opens{border-left-color:var(--teal2)} .rlist li.closes{border-left-color:var(--ghost-line);background:var(--soft)}
  .rlist .rt{font-family:var(--sans);font-weight:700;font-size:12.5px;color:var(--ink)}
  .rlist .rm{font-size:10.5px;font-family:var(--sans);font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-left:8px}
  .rlist p{margin:4px 0 0;font-size:12px;color:var(--body);line-height:1.45}
  /* Action register — before · during · after, the software of the move */
  .phases{display:grid;gap:12px}
  .phase{border:1px solid var(--line);background:var(--soft)}
  .phase h4{font-family:var(--sans);font-weight:700;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;
    color:var(--brass);margin:0;padding:11px 16px;border-bottom:1px solid var(--line);background:#fff}
  .phase ol{margin:0;padding:12px 16px 12px 40px;display:grid;gap:9px}
  .phase li{font-size:12.5px;color:var(--body);line-height:1.5}
  .phase li .at{font-family:var(--sans);font-weight:700;color:var(--ink)}
  .phase li .ao{font-family:var(--sans);font-size:9.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);margin-left:8px}
  .phase .empty{padding:12px 16px;color:var(--muted);font-style:italic;font-size:12px}
  /* Questions worth asking — the closing page */
  .qwrap{margin:2px 40px 0;padding:18px 22px;border:1px solid var(--frame-line);background:var(--soft)}
  .qwrap ol{margin:0;padding-left:20px;display:grid;gap:10px}
  .qwrap li{font-family:var(--serif);font-size:14.5px;line-height:1.5;color:var(--ink)}
  /* Index gallery */
  .xgroup{margin:2px 40px 0}
  .xgroup h3{font-family:var(--sans);font-weight:700;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:16px 0 9px}
  .routes{display:grid;grid-template-columns:repeat(2,1fr);gap:9px}
  @media(max-width:680px){.routes{grid-template-columns:1fr}}
  .routes a{border:1px solid var(--line);background:#fff;padding:12px 15px;text-decoration:none;color:var(--ink);
    display:flex;align-items:center;gap:10px;font-family:var(--sans)}
  .routes a:hover{border-color:var(--brass)}
  .routes a .o{font-weight:500;color:var(--dim)} .routes a .to{color:var(--gold);font-weight:700}
  .routes a .d{font-weight:700}  .routes a .ar{margin-left:auto;color:var(--muted)}
"""


def _changed_table(brief: dict) -> str:
    o, d = brief["origin"]["name"], brief["destination"]["name"]
    rows = []
    for x in brief["environment_changed"]:
        def cell(tag, note):
            t = f'<span class="tag">{_esc(tag)}</span>' if tag else ""
            return f'{t}<span class="nt">{_esc(note)}</span>'
        rows.append(f'<tr><td class="dim">{_esc(x["label"])}</td>'
                    f'<td>{cell(x["a_tag"], x["a_note"])}</td>'
                    f'<td class="arr">→</td>'
                    f'<td>{cell(x["b_tag"], x["b_note"])}</td></tr>')
    if not rows:
        return '<p class="lede" style="margin:2px 40px 0">The move changes nothing across the taxed dimensions — the two environments read alike.</p>'
    return (f'<table class="xtab"><thead><tr><th>What changed</th><th>In {_esc(o)}</th><th></th><th>In {_esc(d)}</th></tr></thead>'
            f'<tbody>{chr(10).join(rows)}</tbody></table>')


def _priority_table(brief: dict) -> str:
    if not brief["coordination"]:
        return '<p class="lede" style="margin:2px 40px 0">No standing coordination priorities are triggered at the destination — the environment is simple.</p>'
    rows = []
    for r in brief["coordination"]:
        newchip = '<span class="new">New</span>' if r["new"] else ""
        uslug = "u-" + r["urgency"].lower().replace(" ", "-")
        rows.append(
            f'<tr><td class="p">{_esc(r["priority"])}{newchip}</td>'
            f'<td class="rz">{_esc(r["reason"])}</td>'
            f'<td class="u {uslug}">{_esc(r["urgency"])}</td>'
            f'<td class="rz hide-sm">{_esc(r["owner"])}</td>'
            f'<td class="dep hide-sm">{_esc(r["dependencies"])}</td></tr>')
    return (f'<table class="ptab"><thead><tr><th>Priority</th><th>Reason</th><th>Urgency</th>'
            f'<th class="hide-sm">Owner</th><th class="hide-sm">Depends on</th></tr></thead>'
            f'<tbody>{chr(10).join(rows)}</tbody></table>')


def _decisions(brief: dict) -> str:
    if not brief["decisions"]:
        return '<p class="lede" style="margin:2px 40px 0">No standing decision is invalidated by the move.</p>'
    items = "\n".join(
        f'<li><span class="rt">{_esc(x["category"])}</span>'
        f'<span class="rm">{_esc(x["signal"])}: {_esc(x["from_level"])} → {_esc(x["to_level"])}</span>'
        f'<p>{_esc(x["note"])}</p></li>' for x in brief["decisions"])
    return f'<ul class="rlist">{items}</ul>'


def _opportunities(brief: dict) -> str:
    if not brief["opportunities"]:
        return '<p class="lede" style="margin:2px 40px 0">The move opens no new review beyond the priorities above.</p>'
    items = []
    for o in brief["opportunities"]:
        verb = "Opportunity opens" if o["kind"] == "opens" else "Stands down"
        items.append(f'<li class="{o["kind"]}"><span class="rt">{_esc(o["opens"])}</span>'
                     f'<span class="rm">{verb}</span><p>{_esc(o["reason"])}.</p></li>')
    return f'<ul class="rlist">{chr(10).join(items)}</ul>'


def _phase(title: str, actions: list[dict]) -> str:
    if not actions:
        return f'<div class="phase"><h4>{_esc(title)}</h4><div class="empty">Nothing required in this phase.</div></div>'
    items = "\n".join(
        f'<li><span class="at">{_esc(a["title"])}</span><span class="ao">{_esc(a["owner"])}</span><br>{_esc(a["step"])}</li>'
        for a in actions)
    return f'<div class="phase"><h4>{_esc(title)}</h4><ol>{items}</ol></div>'


def render_crossing_html(brief: dict, edition: str = CURRENT_EDITION) -> str:
    o, d = brief["origin"], brief["destination"]
    o_name, d_name = o["name"], d["name"]
    title = f"Crossing Brief — moving from {o_name} to {d_name} | Driftwood Atlas"
    desc = (brief["thesis"] + " An operating brief: coordination priorities, standing decisions to "
            "reconsider, and a before/during/after action register. Illustrative, not advice.")[:300]
    url = _xing.crossing_url(o["code"], d["code"], edition)
    ph = brief["actions"]
    questions = "\n".join(f'<li>{_esc(q)}</li>' for q in brief["questions"])
    import json
    jsonld = {"@context": "https://schema.org", "@type": "WebPage",
              "name": f"Crossing Brief — {o_name} to {d_name}", "url": url, "description": desc,
              "isPartOf": {"@type": "WebSite", "name": "Driftwood Capital", "url": f"{BASE_URL}/index.html"}}
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
{PLAUSIBLE}
<title>{_esc(title)}</title>
<meta name="description" content="{_esc(desc)}" />
<link rel="canonical" href="{url}" />
<link rel="icon" href="{_ABS}favicon.svg" />
<link rel="icon" type="image/png" sizes="32x32" href="{_ABS}favicon-32.png" />
<link rel="apple-touch-icon" sizes="180x180" href="{_ABS}apple-touch-icon.png" />
<meta name="theme-color" content="#f1efe9" media="(prefers-color-scheme: light)" />
<meta name="theme-color" content="#1a2330" media="(prefers-color-scheme: dark)" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Driftwood Capital" />
<meta property="og:title" content="{_esc(title)}" />
<meta property="og:description" content="{_esc(desc)}" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{BASE_URL}/og/statemap.png" />
<meta name="twitter:card" content="summary_large_image" />
<script type="application/ld+json">
{json.dumps(jsonld)}
</script>
<link rel="stylesheet" href="{_ABS}driftwood.css">
<script src="{_ABS}dw-context.js"></script>
<style>{_XING_CSS}</style>
</head>
<body>
<div class="sheet">
  <div class="frame">
    {NAV_ABS}
    {_process_bar("plan", edition)}
    <div class="hd">
      <div class="eyebrow">The State Atlas · Crossing Brief</div>
      <h1>What changes when a household crosses state lines.</h1>
      <p class="lede">An operating brief for one move — not an explainer. It reads the reasoning graph
        from origin to destination and returns what the household must coordinate: the priorities that
        change, the standing decisions the move makes stale, and the actions to take before, during, and
        after the crossing.</p>
    </div>
    <div class="xband">
      <div class="leg"><span class="lbl">Origin</span><span class="st">{_esc(o_name)}</span></div>
      <span class="arrow">→</span>
      <div class="leg"><span class="lbl">Destination</span><span class="st">{_esc(d_name)}</span></div>
      <span class="prep">Prepared as an illustrative operating brief · {_esc(edition)} edition</span>
    </div>
    <div class="sec"><div class="sh">Executive summary</div></div>
    <p class="thesis">{_esc(brief["thesis"])}</p>
    <div class="sec"><div class="sh">The operating environment that changed</div>
      <p class="lede" style="margin-bottom:8px">Only the dimensions the move actually changes — origin on the left, destination on the right.</p>
    </div>
    {_changed_table(brief)}
    <div class="sec"><div class="sh">Coordination priorities</div>
      <p class="lede" style="margin-bottom:8px">What the household coordinates in the new environment — who owns it, how soon, and what it depends on. <b>New</b> marks a priority the move opens.</p>
    </div>
    {_priority_table(brief)}
    <div class="sec"><div class="sh">Standing decisions to reconsider</div>
      <p class="lede" style="margin-bottom:8px">Decisions calibrated to the origin's environment that the move makes stale — worth revisiting, not assuming.</p>
    </div>
    {_decisions(brief)}
    <div class="sec"><div class="sh">Opportunities the move opens</div></div>
    {_opportunities(brief)}
    <div class="sec"><div class="sh">The action register</div>
      <p class="lede" style="margin-bottom:8px">Sequenced by the move — what to do before, during, and after the crossing.</p>
      <div class="phases">
        {_phase("Before the move", ph["before"])}
        {_phase("During the move", ph["during"])}
        {_phase("After the move", ph["after"])}
      </div>
    </div>
    <div class="sec"><div class="sh">Questions worth asking</div>
      <p class="lede" style="margin-bottom:8px">Not answers — the questions this move puts on the table, to open the conversation with the household's advisors.</p>
    </div>
    <div class="qwrap"><ol>{questions}</ol></div>
    <div class="cta">
      <div class="ctxt">
        <div class="ch">This brief becomes one entry in a household's operating file.</div>
        <div class="cd">The Household Record binds the move to the family's standing decisions, coordination priorities, and advisors — the place this brief is coordinated, not filed.</div>
      </div>
      <a class="primary" href="{BASE_URL}/atlas/{edition}/household/">Prepare this as your Household Record →</a>
      <a class="ghost" href="{MEETING_URL}">Start a conversation</a>
    </div>
    <div class="rel">Read either environment in full: <a href="{atlas_url(o["code"], edition)}">{_esc(o_name)} Atlas →</a> · <a href="{atlas_url(d["code"], edition)}">{_esc(d_name)} Atlas →</a> · <a href="{BASE_URL}/atlas/{edition}/compare/{_compare_slug(o["code"], d["code"])}/">weigh the two →</a> · <a href="{_xing.crossing_index_url(edition)}">other crossings →</a></div>
    {_provenance_block()}
    {DISCLOSURE}
    {firm_anchor_html()}
    <div class="colophon">Driftwood. State tax law reflects {_esc(AS_OF_LAW)}; last reviewed {_esc(LAST_REVIEWED)}. A Crossing Brief is a view of the reasoning graph — it authors no facts of its own.</div>
  </div>
</div>
</body>
</html>
"""


def _compare_slug(a: str, b: str) -> str:
    from .compare import compare_slug
    return compare_slug(a, b)


# Index gallery — the featured routes grouped by destination magnet.
def render_crossing_index_html(edition: str = CURRENT_EDITION) -> str:
    title = "Crossing Briefs — what changes when you move between states | Driftwood Atlas"
    desc = ("The operating brief for a household changing states: which coordination priorities change, "
            "which standing decisions to reconsider, and the actions to take before, during, and after "
            "the move. The routes households make most often. Illustrative, not advice.")
    url = _xing.crossing_index_url(edition)
    # group featured by destination
    by_dest: dict[str, list[tuple[str, str]]] = {}
    for o, d in _xing.FEATURED_CROSSINGS:
        by_dest.setdefault(d, []).append((o, d))
    groups = []
    for d in sorted(by_dest, key=lambda c: STATE_NAMES[c]):
        links = "\n".join(
            f'<a href="{_xing.crossing_url(o, d, edition)}"><span class="o">{_esc(STATE_NAMES[o])}</span>'
            f'<span class="to">→</span><span class="d">{_esc(STATE_NAMES[d])}</span><span class="ar">brief →</span></a>'
            for o, d in by_dest[d])
        groups.append(f'<div class="xgroup"><h3>Moving to {_esc(STATE_NAMES[d])}</h3><div class="routes">{links}</div></div>')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
{PLAUSIBLE}
<title>{_esc(title)}</title>
<meta name="description" content="{_esc(desc)}" />
<link rel="canonical" href="{url}" />
<link rel="icon" href="{_ABS}favicon.svg" />
<meta name="theme-color" content="#f1efe9" media="(prefers-color-scheme: light)" />
<meta name="theme-color" content="#1a2330" media="(prefers-color-scheme: dark)" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Driftwood Capital" />
<meta property="og:title" content="{_esc(title)}" />
<meta property="og:description" content="{_esc(desc)}" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{BASE_URL}/og/statemap.png" />
<link rel="stylesheet" href="{_ABS}driftwood.css">
<script src="{_ABS}dw-context.js"></script>
<style>{_XING_CSS}</style>
</head>
<body>
<div class="sheet">
  <div class="frame">
    {NAV_ABS}
    {_process_bar("plan", edition)}
    <div class="hd">
      <div class="eyebrow">The State Atlas · Crossing Brief</div>
      <h1>When a household crosses state lines, its operating system changes.</h1>
      <p class="lede">A Crossing Brief is prepared for one move — the memo an institution hands a household
        before a transition. Its job is to coordinate, not to educate: which priorities change, which
        standing decisions to revisit, and what to do before, during, and after. These are the routes
        households make most often; the <a href="{BASE_URL}/atlas/{edition}/household/">Household Record</a>
        prepares one for a household's own crossing.</p>
    </div>
    {chr(10).join(groups)}
    <div class="cta">
      <div class="ctxt">
        <div class="ch">Considering a move that isn't here?</div>
        <div class="cd">Every state pair has a brief in the graph — start a conversation and we'll prepare the one for your household's crossing.</div>
      </div>
      <a class="primary" href="{MEETING_URL}">Start a conversation →</a>
      <a class="ghost" href="{BASE_URL}/atlas/{edition}/compare/">Weigh two states →</a>
    </div>
    {_provenance_block()}
    {DISCLOSURE}
    {firm_anchor_html()}
    <div class="colophon">Driftwood. State tax law reflects {_esc(AS_OF_LAW)}; last reviewed {_esc(LAST_REVIEWED)}. The Crossing Brief renders the reasoning graph as an operating document.</div>
  </div>
</div>
</body>
</html>
"""


def export_crossings(out_dir: str | Path = "docs", edition: str = CURRENT_EDITION) -> list[str]:
    """Publish the Crossing Brief index + a static brief per featured relocation corridor."""
    out_dir = Path(out_dir)
    base = out_dir / "atlas" / edition / "crossing"
    base.mkdir(parents=True, exist_ok=True)
    written = [f"atlas/{edition}/crossing/index.html"]
    (base / "index.html").write_text(render_crossing_index_html(edition))
    for o, d in _xing.FEATURED_CROSSINGS:
        p = out_dir / _xing.crossing_path(o, d, edition)
        p.mkdir(parents=True, exist_ok=True)
        (p / "index.html").write_text(render_crossing_html(_xing.build_crossing(o, d, edition), edition))
        written.append(f"{_xing.crossing_path(o, d, edition)}/index.html")
    return written


def sitemap_entries(edition: str = CURRENT_EDITION) -> list[tuple[str, str, str]]:
    entries = [(f"atlas/{edition}/crossing/", "0.6", "monthly")]
    for o, d in _xing.FEATURED_CROSSINGS:
        entries.append((f"{_xing.crossing_path(o, d, edition)}/", "0.5", "monthly"))
    return entries
