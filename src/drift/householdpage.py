"""The Household Record, rendered as an operating file.

The Record is an INDEX, so its rendering is an index: a short orientation ("begin here"), then the
household's operating system as a set of reference entries, each a one-line summary of one part of the
system and a link to the document that holds it in full. Nothing is authored twice. The visual job is
to make the reference-not-duplicate principle legible: every card points outward to an authoritative
artifact (an Atlas page, the Crossing Brief, the Decision / Opportunity Registers, the Annual Review).

    render_household_html(rec, edition)    , one household's operating file
    render_household_index_html(edition)   , the sample households
    export_households(out_dir, edition)    , the index + one file per sample household
"""
from __future__ import annotations

from pathlib import Path

from .statemap import AS_OF_LAW, LAST_REVIEWED, CURRENT_EDITION
from .statepage import (
    _esc, _ABS, NAV_ABS, PLAUSIBLE, DISCLOSURE, _HEAD_CSS, _provenance_block, _process_bar, MEETING_URL,
)
from .site import BASE_URL, firm_anchor_html
from . import household as _hh

_HH_CSS = _HEAD_CSS + """
  /* ── Household Record, the operating file ──────────────────────────────────────────────────── */
  .hhband{margin:16px 40px 4px;padding:16px 24px;background:var(--navy);color:#eef1f4;display:flex;
    align-items:center;gap:10px 26px;flex-wrap:wrap}
  .hhband .leg{display:flex;flex-direction:column;gap:2px}
  .hhband .leg .lbl{font-family:var(--sans);font-weight:700;font-size:9.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--gold)}
  .hhband .leg .st{font-family:var(--sans);font-weight:700;font-size:19px;color:#f1ede3;line-height:1}
  .hhband .sep{color:var(--gold);font-size:18px}
  .hhband .status{margin-left:auto;font-size:11px;color:#aeb7c1;text-align:right;max-width:28ch;line-height:1.5}
  .begin{font-family:var(--serif);font-size:15.5px;line-height:1.6;color:var(--body);margin:0 40px;max-width:none}
  .begin b{color:var(--ink);font-weight:500}
  /* Reference entries, each points outward to the authoritative artifact */
  .refs{display:grid;gap:10px}
  .ref{border:1px solid var(--line);border-left:3px solid var(--brass);background:#fff;padding:13px 16px}
  .ref .rh{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap}
  .ref .rt{font-family:var(--sans);font-weight:700;font-size:13.5px;color:var(--ink)}
  .ref .go{font-family:var(--sans);font-weight:700;font-size:11px;color:var(--teal2);text-decoration:none;white-space:nowrap}
  .ref .go:hover{text-decoration:underline}
  .ref p{margin:5px 0 0;font-size:12.5px;color:var(--body);line-height:1.5}
  .ref .mini{margin:8px 0 0;padding:0;list-style:none;display:flex;flex-wrap:wrap;gap:5px 14px}
  .ref .mini li{font-size:12px;color:var(--dim)} .ref .mini li b{color:var(--ink);font-weight:500;font-family:var(--sans)}
  .ref.thesis{border-left-color:var(--gold)} .ref.thesis .rt{color:var(--brass)}
  .ref .also{margin:8px 0 0;font-size:11.5px} .ref .also a{color:var(--teal2);text-decoration:none;font-weight:500}
  .docrow{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
  @media(max-width:760px){.docrow{grid-template-columns:1fr}}
  .docrow a{border:1px solid var(--line);background:var(--soft);padding:12px 14px;text-decoration:none;color:var(--ink)}
  .docrow a:hover{border-color:var(--brass)}
  .docrow .dt{display:block;font-family:var(--sans);font-weight:700;font-size:12.5px;color:var(--ink)}
  .docrow .ds{font-size:11.5px;color:var(--muted);margin-top:3px}
  .principle{margin:2px 40px 0;padding:14px 18px;border:1px dashed var(--frame-line);background:var(--soft);
    font-size:12.5px;line-height:1.55;color:var(--dim)}
  .principle b{color:var(--ink);font-weight:500}
  /* Index cards */
  .hhcards{display:grid;grid-template-columns:1fr 1fr;gap:12px}
  @media(max-width:680px){.hhcards{grid-template-columns:1fr}}
  .hhcard{border:1px solid var(--line);border-left:3px solid var(--brass);background:#fff;padding:16px 18px;text-decoration:none;color:var(--ink);display:block}
  .hhcard:hover{border-color:var(--brass)}
  .hhcard .nm{font-family:var(--sans);font-weight:700;font-size:16px;color:var(--ink)}
  .hhcard .wh{font-family:var(--sans);font-weight:700;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--brass);margin:3px 0 8px}
  .hhcard p{margin:0;font-size:12.5px;color:var(--body);line-height:1.5}
  .hhcard .go{display:inline-block;margin-top:9px;font-family:var(--sans);font-weight:700;font-size:11px;color:var(--teal2)}
"""


def _ref(title: str, url: str, summary: str, go: str = "Open →", mini: str = "", also: str = "", cls: str = "") -> str:
    m = f'<ul class="mini">{mini}</ul>' if mini else ""
    a = f'<div class="also">{also}</div>' if also else ""
    return (f'<div class="ref {cls}"><div class="rh"><span class="rt">{title}</span>'
            f'<a class="go" href="{url}">{go}</a></div>'
            f'<p>{summary}</p>{m}{a}</div>')


def render_household_html(rec: dict, edition: str = CURRENT_EDITION) -> str:
    name = rec["name"]
    cur, pot = rec["current"], rec["potential"]
    R = rec["references"]
    title = f"{name}, Household Record | Driftwood Atlas"
    desc = (f"{name}'s operating file: the tax environment in force ({cur['name']}), the coordination "
            f"priorities and standing decisions, {'a move under consideration, ' if pot else ''}and the "
            f"index to every authoritative artifact. Illustrative sample, not advice.")[:300]
    url = _hh.household_url(rec["id"], edition)
    status = (f'Domiciled in {_esc(cur["name"])} · weighing a move to {_esc(pot["name"])}'
              if pot else f'Domiciled in {_esc(cur["name"])} · settled')

    # Coordination priorities in force (summary + reference to the Atlas reasoning).
    if rec["coordination"]:
        mini = "".join(f'<li><b>{_esc(c["title"])}</b> · {_esc(c["coordinate_with"])}</li>' for c in rec["coordination"])
        coord = _ref("Coordination priorities in force", R["atlas_current"]["url"],
                     f"The operating-system domains {name} coordinates in the {_esc(cur['name'])} environment. "
                     f"The full reasoning, how each is read and what opens it, lives in the Atlas.",
                     go=f"{_esc(cur['name'])} Atlas →", mini=mini)
    else:
        coord = _ref("Coordination priorities in force", R["atlas_current"]["url"],
                     f"The {_esc(cur['name'])} environment triggers no standing coordination priority, the file is simple.",
                     go=f"{_esc(cur['name'])} Atlas →")

    # Standing decisions (summary + reference to the Decision Register).
    if rec["standing_decisions"]:
        mini = "".join(f'<li><b>{_esc(s["title"])}</b> ({_esc(s["domain"])})</li>' for s in rec["standing_decisions"])
        standing = _ref("Standing decisions", R["decision_register"]["url"],
                        "The decisions the household holds in force today. Each is a live entry in the Decision "
                        "Register, where it is recorded with its reasoning and never overwritten.",
                        go="Decision Register →", mini=mini)
    else:
        standing = _ref("Standing decisions", R["decision_register"]["url"],
                        "No standing decision is on file yet.", go="Decision Register →")

    # Under consideration, the crossing (only if a potential move).
    considering = ""
    if rec["crossing"]:
        x = rec["crossing"]
        sig_txt = "decision signal changes" if x["changed"] == 1 else "decision signals change"
        open_txt = "priority opens" if x["opened"] == 1 else "priorities open"
        close_txt = "stands down" if x["closed"] == 1 else "stand down"
        considering = (
            '<div class="sec"><div class="sh">Under consideration</div></div>' +
            _ref(f"A move to {_esc(pot['name'])}", R["crossing"]["url"], _esc(x["thesis"]),
                 go="Crossing Brief →", cls="thesis",
                 mini=(f'<li><b>{x["changed"]}</b> {sig_txt}</li>'
                       f'<li><b>{x["opened"]}</b> {open_txt} · <b>{x["closed"]}</b> {close_txt}</li>'),
                 also=(f'Also: <a href="{R["comparison"]["url"]}">weigh {_esc(cur["name"])} against {_esc(pot["name"])} →</a> · '
                       f'<a href="{R["atlas_potential"]["url"]}">{_esc(pot["name"])} Atlas →</a>')))

    # Opportunities (from the crossing) + reference to the Opportunity Register.
    opps = ""
    open_opps = [o for o in rec["opportunities"] if o["kind"] == "opens"]
    if open_opps:
        mini = "".join(f'<li><b>{_esc(o["opens"])}</b></li>' for o in open_opps)
        opps = ('<div class="sec"><div class="sh">Opportunities open</div></div>' +
                _ref("Opportunities the situation opens", R["opportunity_register"]["url"],
                     "Reviews the household's situation invites. They flow into the Opportunity Register, "
                     "where each is tracked from open to closed.", go="Opportunity Register →", mini=mini))

    annual = ""
    if "annual_review" in R:
        annual = ('<div class="sec"><div class="sh">Annual review</div></div>' +
                  _ref("The latest Annual Wealth Operating Review", R["annual_review"]["url"],
                       f"The prepared review of the household's operating system, kept each year, none overwritten.",
                       go="Annual Review →"))

    docs = "".join(
        f'<a href="{g["url"]}"><span class="dt">{_esc(g["label"])}</span><span class="ds">{_esc(g["sub"])}</span></a>'
        for g in R["governing"])

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
<meta property="og:site_name" content="Driftwood Wealth" />
<meta property="og:title" content="{_esc(title)}" />
<meta property="og:description" content="{_esc(desc)}" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{BASE_URL}/og/statemap.png" />
<link rel="stylesheet" href="{_ABS}driftwood.css">
<script src="{_ABS}dw-context.js"></script>
<style>{_HH_CSS}</style>
</head>
<body>
<div class="sheet">
  <div class="frame">
    {NAV_ABS}
    {_process_bar("coordinate", edition)}
    <div class="hd">
      <div class="eyebrow">The State Atlas · Household Record</div>
      <h1>{_esc(name)}.</h1>
      <p class="lede">The operating file for one household, not a folder of documents, but the index to
        how the family's financial life is coordinated. Begin here; each entry summarises one part of the
        system and links to the document that holds it in full.</p>
    </div>
    <div class="hhband">
      <div class="leg"><span class="lbl">In force</span><span class="st">{_esc(cur["name"])}</span></div>
      {'<span class="sep">→</span><div class="leg"><span class="lbl">Under consideration</span><span class="st">' + _esc(pot["name"]) + '</span></div>' if pot else ''}
      <span class="status">Household Record · {_esc(rec["as_of"])} · illustrative sample</span>
    </div>
    <p class="begin">{_esc(rec["sketch"])} Where to begin: the environment in force is <b>{_esc(cur["name"])}</b>; {'a move to <b>' + _esc(pot["name"]) + '</b> is on the table.' if pot else 'the household is settled where it is.'} Each artifact below remains authoritative in its own right, the Record is the standing context, not a copy.</p>
    <div class="sec"><div class="sh">The operating system in force</div></div>
    <div class="refs" style="margin:2px 40px 0">
      {_ref("The tax environment", R["atlas_current"]["url"], f"How {_esc(cur['name'])} taxes the household, capital gains, estate, basis step-up, and the rest. The authoritative reference is the state's Atlas page.", go=f"{_esc(cur['name'])} Atlas →")}
      {coord}
      {standing}
    </div>
    {considering}
    {opps}
    {annual}
    <div class="sec"><div class="sh">Governing documents</div>
      <p class="lede" style="margin-bottom:8px">The standing documents that hold the family's operating rules, authored once, referenced here.</p>
      <div class="docrow">{docs}</div>
    </div>
    <div class="cta">
      <div class="ctxt">
        <div class="ch">This is how one household's system is coordinated.</div>
        <div class="cd">Yours would begin the same way, as a standing record, not a folder. We start with your highest-value coordination opportunities.</div>
      </div>
      <a class="primary" href="{MEETING_URL}">Review your coordination opportunities with Driftwood →</a>
      <a class="ghost" href="{_hh.household_index_url(edition)}">See another record</a>
    </div>
    <div class="principle"><b>Reference, not duplicate.</b> The Household Record is the institutional index and the permanent context for {_esc(name)}. Every summary above is a pointer; the linked artifact, the Atlas reasoning, the Crossing Brief, the Registers, the Annual Review, remains the single authoritative source. The Record never re-authors what those documents hold.</div>
    {_provenance_block()}
    {DISCLOSURE}
    {firm_anchor_html()}
    <div class="colophon">Driftwood. State tax law reflects {_esc(AS_OF_LAW)}; last reviewed {_esc(LAST_REVIEWED)}. The Household Record indexes the reasoning graph for one household, it authors no facts of its own.</div>
  </div>
</div>
</body>
</html>
"""


def render_household_index_html(edition: str = CURRENT_EDITION) -> str:
    title = "Household Record, the operating file for one household | Driftwood Atlas"
    desc = ("The Household Record binds the reasoning graph to a household: the environment in force, the "
            "coordination priorities and standing decisions, any move under consideration, and the index to "
            "every authoritative artifact. Illustrative samples, not advice.")
    url = _hh.household_index_url(edition)
    cards = []
    for h in _hh.SAMPLE_HOUSEHOLDS:
        rec = _hh.build_household_record(h, edition)
        where = (f'{_esc(rec["current"]["name"])} → {_esc(rec["potential"]["name"])}' if rec["potential"]
                 else f'{_esc(rec["current"]["name"])} · settled')
        cards.append(
            f'<a class="hhcard" href="{_hh.household_url(h["id"], edition)}">'
            f'<div class="nm">{_esc(rec["name"])}</div><div class="wh">{where}</div>'
            f'<p>{_esc(rec["sketch"])}</p><span class="go">Open the file →</span></a>')
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
<meta property="og:site_name" content="Driftwood Wealth" />
<meta property="og:title" content="{_esc(title)}" />
<meta property="og:description" content="{_esc(desc)}" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{BASE_URL}/og/statemap.png" />
<link rel="stylesheet" href="{_ABS}driftwood.css">
<script src="{_ABS}dw-context.js"></script>
<style>{_HH_CSS}</style>
</head>
<body>
<div class="sheet">
  <div class="frame">
    {NAV_ABS}
    {_process_bar("coordinate", edition)}
    <div class="hd">
      <div class="eyebrow">The State Atlas · Household Record</div>
      <h1>Where a household's financial operating system lives.</h1>
      <p class="lede">Every other product renders the reasoning; the Household Record binds it to a family.
        It answers one question, if someone needed to understand this household's financial operating
        system, where would they begin?, and indexes every authoritative artifact from there. These are
        illustrative sample households.</p>
    </div>
    <div class="sec"><div class="sh">Sample operating files</div></div>
    <div class="hhcards" style="margin:2px 40px 0">{chr(10).join(cards)}</div>
    <div class="cta">
      <div class="ctxt">
        <div class="ch">If your household spans more than one state, entity, or advisor, this is the file we build first.</div>
        <div class="cd">It is where the reasoning becomes personal, your standing decisions, coordination priorities, and the specialists who hold each.</div>
      </div>
      <a class="primary" href="{MEETING_URL}">Review your coordination opportunities with Driftwood →</a>
    </div>
    <div class="principle" style="margin-top:16px"><b>Reference, not duplicate.</b> A Household Record is an index and standing context, it points to the Atlas reasoning, the Crossing Brief, the Registers, and the Annual Review, each of which remains the single authoritative source.</div>
    {_provenance_block()}
    {DISCLOSURE}
    {firm_anchor_html()}
    <div class="colophon">Driftwood. State tax law reflects {_esc(AS_OF_LAW)}; last reviewed {_esc(LAST_REVIEWED)}. The Household Record is the institutional index over the reasoning graph.</div>
  </div>
</div>
</body>
</html>
"""


def export_households(out_dir: str | Path = "docs", edition: str = CURRENT_EDITION) -> list[str]:
    """Publish the Household Record index + one operating file per sample household."""
    out_dir = Path(out_dir)
    base = out_dir / "atlas" / edition / "household"
    base.mkdir(parents=True, exist_ok=True)
    written = [f"atlas/{edition}/household/index.html"]
    (base / "index.html").write_text(render_household_index_html(edition))
    for h in _hh.SAMPLE_HOUSEHOLDS:
        p = out_dir / _hh.household_path(h["id"], edition)
        p.mkdir(parents=True, exist_ok=True)
        (p / "index.html").write_text(render_household_html(_hh.build_household_record(h, edition), edition))
        written.append(f"{_hh.household_path(h['id'], edition)}/index.html")
    return written


def sitemap_entries(edition: str = CURRENT_EDITION) -> list[tuple[str, str, str]]:
    entries = [(f"atlas/{edition}/household/", "0.5", "monthly")]
    for h in _hh.SAMPLE_HOUSEHOLDS:
        entries.append((f"{_hh.household_path(h['id'], edition)}/", "0.4", "monthly"))
    return entries
