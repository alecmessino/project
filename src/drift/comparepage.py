"""The Comparison instrument — rendered.

A product renders a query over the graph; it authors nothing. This module takes the structured diff
from `drift.compare.build_comparison` and lays it out as an instrument for weighing two operating
environments — the Decision Framework read side by side on identical lenses, the Coordination
Priorities that change, and the facts underneath. It reuses the state-page visual system verbatim
(nav, frame, eyebrow, dot-meters, disclosure, firm-anchor) so a Comparison is unmistakably the same
Atlas, one level up.

    render_comparison_html(cmp, edition)   — one canonical pair page (SSR)
    render_compare_index_html(edition)     — the picker: weigh any two, plus the featured corridors
    export_comparisons(out_dir, edition)   — write the index + featured pages + reverse-slug redirects

The page is SYMMETRIC (it does not say which environment is "better"); the directional transition memo
is the Crossing Brief.
"""
from __future__ import annotations

from pathlib import Path

from .leakage import STATE_NAMES
from .statemap import AS_OF_LAW, LAST_REVIEWED, CURRENT_EDITION
from .statepage import (
    _esc, _ABS, NAV_ABS, PLAUSIBLE, DISCLOSURE, _HEAD_CSS, _provenance_block,
    _LEVEL_DOTS, atlas_url,
)
from .site import BASE_URL, firm_anchor_html
from . import compare as _cmp

# Comparison-specific styles layered on the shared state-page foundation, so the two never diverge.
_CMP_CSS = _HEAD_CSS + """
  /* ── Comparison instrument ─────────────────────────────────────────────────────────────────── */
  .cmp-band{margin:16px 40px 2px;padding:16px 22px;background:var(--navy);color:#eef1f4;
    display:flex;align-items:center;gap:10px 20px;flex-wrap:wrap}
  .cmp-band .side{font-family:var(--sans);font-weight:700;font-size:20px;letter-spacing:-.01em;color:#f1ede3}
  .cmp-band .vs{font-family:var(--sans);font-weight:700;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--gold)}
  .cmp-band .cmp-tally{margin-left:auto;font-size:12px;color:#c3ccd6;line-height:1.5;text-align:right}
  .cmp-band .cmp-tally b{color:#f1ede3;font-variant-numeric:tabular-nums}
  /* The five lenses, weighed. A meter each side of the lens; changed rows carry a hairline accent. */
  .weigh{display:grid;gap:9px}
  .wrow{border:1px solid var(--line);background:#fff;padding:12px 16px}
  .wrow.same{background:var(--soft);border-style:dashed}
  .wtop{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:14px}
  .wtop .lens{text-align:center}
  .wtop .lens .ll{font-family:var(--sans);font-weight:700;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink)}
  .wtop .lens .ld{display:block;font-size:10.5px;color:var(--muted);margin-top:3px;line-height:1.35;font-family:var(--sans);font-weight:400;letter-spacing:0;text-transform:none}
  .wtop .end{display:flex;align-items:center;gap:9px}
  .wtop .end.a{justify-content:flex-end} .wtop .end.b{justify-content:flex-start}
  .wtop .lvl{font-family:var(--sans);font-weight:700;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
  .fm{display:inline-flex;gap:3px;align-items:center}
  .fm i{width:6px;height:6px;border-radius:50%;background:var(--line);display:inline-block}
  .fm i.on{background:var(--brass)} .fm.sev i.on{background:var(--neg)} .fm.zero i.on{background:var(--muted)}
  .wread{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:11px;border-top:1px solid var(--line2);padding-top:10px}
  .wread .r{font-size:12px;color:var(--body);line-height:1.5}
  .wread .r .who{font-family:var(--sans);font-weight:700;font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--brass);display:block;margin-bottom:3px}
  .wrow.chg .wtop .lens .ll{color:var(--accent-strike)}
  @media(max-width:640px){.wtop{grid-template-columns:1fr}.wtop .end.a,.wtop .end.b{justify-content:flex-start}.wread{grid-template-columns:1fr}}
  /* Coordination priorities that change — three columns: only-A, shared, only-B. */
  .cmp-cols{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}
  @media(max-width:760px){.cmp-cols{grid-template-columns:1fr}}
  .cmp-col{border:1px solid var(--line);background:var(--soft);padding:13px 15px}
  .cmp-col.only{border-left:3px solid var(--accent-strike)} .cmp-col.both{border-left:3px solid var(--muted)}
  .cmp-col h4{font-family:var(--sans);font-weight:700;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:0 0 10px}
  .cmp-col h4 b{color:var(--accent-strike)}
  .cmp-col ul{list-style:none;margin:0;padding:0;display:grid;gap:9px}
  .cmp-col li .pt{font-family:var(--sans);font-weight:500;font-size:12.5px;color:var(--ink)}
  .cmp-col li .pw{font-size:10.5px;color:var(--brass);font-weight:500}
  .cmp-col li p{margin:3px 0 0;font-size:11.5px;color:var(--body);line-height:1.45}
  .cmp-col .none{font-size:12px;color:var(--muted);font-style:italic}
  /* The facts underneath — a compact two-environment table of the dimensions that differ. */
  .facts{width:calc(100% - 80px);margin:4px 40px 0;border-collapse:collapse;font-size:12.5px}
  .facts th,.facts td{text-align:left;vertical-align:top;padding:9px 12px;border-bottom:1px solid var(--line2)}
  .facts thead th{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:700;font-family:var(--sans)}
  .facts .dim{font-family:var(--sans);font-weight:700;color:var(--ink);white-space:nowrap}
  .facts .tag{font-family:var(--sans);font-weight:700;font-size:11px;color:var(--brass);display:block;margin-bottom:2px}
  .facts .nt{color:var(--body);line-height:1.45} .facts .cite a{color:var(--teal2);font-size:10.5px}
  @media(max-width:760px){.facts{width:100%;margin:4px 0 0;font-size:12px}.facts th:nth-child(1){display:none}}
  /* The picker (index) */
  .picker{margin:16px 40px 4px;padding:18px 22px;background:var(--soft);border:1px solid var(--line);
    display:flex;align-items:end;gap:14px;flex-wrap:wrap}
  .picker .pf{display:flex;flex-direction:column;gap:5px}
  .picker label{font-family:var(--sans);font-weight:700;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
  .picker select{font:inherit;font-size:14px;padding:10px 12px;border:1px solid var(--line);background:#fff;border-radius:0;min-width:190px}
  .picker .vs{font-family:var(--sans);font-weight:700;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);padding-bottom:11px}
  .picker button{background:var(--teal);color:#f1ede3;border:0;border-radius:0;font:inherit;font-weight:500;font-size:14px;padding:11px 20px;cursor:pointer;margin-left:auto}
  .picker button:disabled{opacity:.55;cursor:default}
  .corridors{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}
  @media(max-width:760px){.corridors{grid-template-columns:1fr 1fr}}
  @media(max-width:480px){.corridors{grid-template-columns:1fr}}
  .corridors a{border:1px solid var(--line);background:#fff;padding:11px 14px;text-decoration:none;color:var(--ink);
    font-family:var(--sans);font-weight:500;font-size:13px;display:flex;align-items:center;gap:8px}
  .corridors a:hover{border-color:var(--brass)} .corridors a .ar{color:var(--muted);margin-left:auto}
"""


def _meter(level: str, tone: str = "") -> str:
    """A four-dot intensity meter for a signal level (reuses the state-page dot language)."""
    n = _LEVEL_DOTS.get(level, 0)
    cls = "sev" if level == "severe" else "zero" if level == "none" else ""
    dots = "".join(f'<i class="{"on" if i < n else ""}"></i>' for i in range(4))
    return f'<span class="fm {cls}" role="img" aria-label="{_esc(level)}">{dots}</span>'


def _weigh_row(sig: dict, a_name: str, b_name: str) -> str:
    changed = sig["changed"]
    rowcls = "wrow chg" if changed else "wrow same"
    return (
        f'<div class="{rowcls}">'
        f'<div class="wtop">'
        f'<div class="end a"><span class="lvl">{_esc(sig["a_level"])}</span>{_meter(sig["a_level"])}</div>'
        f'<div class="lens"><span class="ll">{_esc(sig["title"])}</span>'
        f'<span class="ld">{_esc(sig["question"])}</span></div>'
        f'<div class="end b">{_meter(sig["b_level"])}<span class="lvl">{_esc(sig["b_level"])}</span></div>'
        f'</div>'
        f'<div class="wread">'
        f'<div class="r"><span class="who">{_esc(a_name)}</span>{_esc(sig["a_reading"])}</div>'
        f'<div class="r"><span class="who">{_esc(b_name)}</span>{_esc(sig["b_reading"])}</div>'
        f'</div></div>'
    )


def _pri_items(items: list[dict]) -> str:
    if not items:
        return '<li class="none">None triggered.</li>'
    return "\n".join(
        f'<li><span class="pt">{_esc(p["title"])}</span> <span class="pw">· {_esc(p["coordinate_with"])}</span>'
        f'<p>{_esc(p["rationale"])}</p></li>' for p in items)


def _facts_table(cmp: dict) -> str:
    a_name, b_name = cmp["a"]["name"], cmp["b"]["name"]
    rows = []
    for d in cmp["environment_diffs"]:
        def cell(tag, note, cites):
            c = ""
            if cites:
                c = ' <span class="cite">· ' + " · ".join(
                    f'<a href="{_esc(x["url"])}" target="_blank" rel="noopener">{_esc(x["label"])}</a>' for x in cites) + '</span>'
            tagh = f'<span class="tag">{_esc(tag)}</span>' if tag else ""
            return f'{tagh}<span class="nt">{_esc(note)}{c}</span>'
        rows.append(
            f'<tr><td class="dim">{_esc(d["label"])}</td>'
            f'<td>{cell(d["a_tag"], d["a_note"], d["a_citations"])}</td>'
            f'<td>{cell(d["b_tag"], d["b_note"], d["b_citations"])}</td></tr>')
    if not rows:
        return '<p class="lede" style="margin:2px 40px 0">These two environments are identical across every tax dimension.</p>'
    return (f'<table class="facts"><thead><tr><th>Dimension</th><th>{_esc(a_name)}</th><th>{_esc(b_name)}</th></tr></thead>'
            f'<tbody>{chr(10).join(rows)}</tbody></table>')


def _impact_line(cmp: dict) -> str:
    ia = cmp["impact"]
    if ia["a_alpha"] is None or ia["b_alpha"] is None:
        return ""
    a_name, b_name = cmp["a"]["name"], cmp["b"]["name"]
    return (
        f'<p class="lede" style="margin:2px 40px 0;max-width:none">On an illustrative 30-year path, coordinated tax '
        f'management recovers about <b>+{ia["a_alpha"]:.1f}%/yr</b> of after-tax return in {_esc(a_name)} versus '
        f'<b>+{ia["b_alpha"]:.1f}%/yr</b> in {_esc(b_name)} — a hypothetical, illustrative figure; the household\'s '
        f'own depends on bracket, holdings, and residency (see the full basis of the estimate below).</p>')


def render_comparison_html(cmp: dict, edition: str = CURRENT_EDITION) -> str:
    a, b = cmp["a"], cmp["b"]
    a_name, b_name = a["name"], b["name"]
    title = f"{a_name} vs {b_name} — Capital Gains, Estate & Coordination | Driftwood Atlas"
    desc = (f"{a_name} vs {b_name}, weighed as two operating environments: {cmp['signals_changed']} of "
            f"{cmp['signals_total']} decision signals read differently and {cmp['priorities_changed']} "
            f"coordination priorities change. Capital-gains rate, estate tax, basis step-up, and more. "
            f"Illustrative, not advice.")[:300]
    url = _cmp.compare_url(a["code"], b["code"], edition)
    weigh = "\n".join(_weigh_row(s, a_name, b_name) for s in cmp["signals"])
    co = cmp["coordination"]
    tally = (f'<b>{cmp["signals_changed"]}</b> of {cmp["signals_total"]} decision signals read differently<br>'
             f'<b>{cmp["priorities_changed"]}</b> coordination priorit{"y" if cmp["priorities_changed"]==1 else "ies"} change')
    jsonld = {
        "@context": "https://schema.org", "@type": "WebPage", "name": f"{a_name} vs {b_name} — Driftwood Atlas",
        "url": url, "description": desc,
        "isPartOf": {"@type": "WebSite", "name": "Driftwood Capital", "url": f"{BASE_URL}/index.html"},
    }
    import json
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
<meta name="twitter:title" content="{_esc(title)}" />
<meta name="twitter:description" content="{_esc(desc)}" />
<meta name="twitter:image" content="{BASE_URL}/og/statemap.png" />
<script type="application/ld+json">
{json.dumps(jsonld)}
</script>
<link rel="stylesheet" href="{_ABS}driftwood.css">
<script src="{_ABS}dw-context.js"></script>
<style>{_CMP_CSS}</style>
</head>
<body>
<div class="sheet">
  <div class="frame">
    {NAV_ABS}
    <div class="hd">
      <div class="eyebrow">The State Atlas · Comparison</div>
      <h1>{_esc(a_name)} and {_esc(b_name)}, weighed as two operating environments.</h1>
      <p class="lede">Not which state is better — the wrong question. This instrument weighs both environments
        on the same five decision lenses and shows <b>which coordination priorities change</b> when the
        environment does. Same reasoning every state is read through; here, side by side.</p>
    </div>
    <div class="cmp-band">
      <span class="side">{_esc(a_name)}</span><span class="vs">weighed against</span><span class="side">{_esc(b_name)}</span>
      <span class="cmp-tally">{tally}</span>
    </div>
    <div class="sec"><div class="sh">The Decision Framework, side by side</div>
      <p class="lede" style="margin-bottom:12px">Each lens turns a tax environment into a household decision.
        A dashed row means the two environments read the same on that lens; a solid row means they differ.</p>
      <div class="weigh">{weigh}</div>
    </div>
    <div class="sec"><div class="sh">Which coordination priorities change</div>
      <p class="lede" style="margin-bottom:12px">The household's operating-system domains each environment opens.
        The middle column holds where they agree; the outer columns are what is unique to each.</p>
      <div class="cmp-cols">
        <div class="cmp-col only"><h4>Only <b>{_esc(a_name)}</b></h4><ul>{_pri_items(co["only_a"])}</ul></div>
        <div class="cmp-col both"><h4>Shared</h4><ul>{_pri_items(co["shared"])}</ul></div>
        <div class="cmp-col only"><h4>Only <b>{_esc(b_name)}</b></h4><ul>{_pri_items(co["only_b"])}</ul></div>
      </div>
    </div>
    <div class="sec"><div class="sh">The facts underneath</div></div>
    {_facts_table(cmp)}
    <div class="sec"><div class="sh">Illustrative impact</div></div>
    {_impact_line(cmp)}
    <div class="cta">
      <div class="ctxt">
        <div class="ch">Read either environment in full.</div>
        <div class="cd">Each state's complete Atlas page carries every dimension, the reasoning chain, and a personalized diagnostic.</div>
      </div>
      <a class="primary" href="{atlas_url(a["code"], edition)}">{_esc(a_name)} Atlas →</a>
      <a class="ghost" href="{atlas_url(b["code"], edition)}">{_esc(b_name)} Atlas →</a>
    </div>
    <div class="rel">Weigh another pair: <a href="{_cmp.compare_index_url(edition)}">the Comparison instrument →</a></div>
    {_provenance_block()}
    {DISCLOSURE}
    {firm_anchor_html()}
    <div class="colophon">Driftwood. State tax law reflects {_esc(AS_OF_LAW)}; last reviewed {_esc(LAST_REVIEWED)}. A comparison is a view of the reasoning graph — it authors no facts of its own.</div>
  </div>
</div>
</body>
</html>
"""


# The browser presenter — it LAYS OUT the already-decided reasoning embedded as window.__CMP__; it does
# not reason (every level/reading was decided in Python). Kept deliberately parallel to _weigh_row /
# _pri_items above so the live instrument and the static corridor pages render the identical graph.
_INDEX_JS = r"""
(function(){
  var D = window.__CMP__, C = window.__CFG__;
  if(!D) return;
  var DOTS = {none:0, low:1, moderate:2, high:3, severe:4};
  var selA = document.getElementById("cmpA"), selB = document.getElementById("cmpB");
  var out = document.getElementById("cmpOut");
  function opt(sel, code){ var s=D.states[code]; var o=document.createElement("option"); o.value=code; o.textContent=s.name; sel.appendChild(o); }
  D.order.forEach(function(c){ opt(selA,c); opt(selB,c); });
  function esc(t){ var d=document.createElement("div"); d.textContent=(t==null?"":String(t)); return d.innerHTML; }
  function canon(a,b){ return D.states[a].slug <= D.states[b].slug ? [a,b] : [b,a]; }
  function meter(level){
    var n=DOTS[level]||0, cls = level==="severe"?"sev":(level==="none"?"zero":"");
    var s='<span class="fm '+cls+'" role="img" aria-label="'+esc(level)+'">';
    for(var i=0;i<4;i++) s+='<i class="'+(i<n?"on":"")+'"></i>';
    return s+"</span>";
  }
  function weighRow(sig, A, B){
    var a=A.signals[sig.id], b=B.signals[sig.id], changed=a.level!==b.level;
    var s='<div class="'+(changed?"wrow chg":"wrow same")+'">';
    s+='<div class="wtop">';
    s+='<div class="end a"><span class="lvl">'+esc(a.level)+'</span>'+meter(a.level)+'</div>';
    s+='<div class="lens"><span class="ll">'+esc(sig.title)+'</span><span class="ld">'+esc(sig.question)+'</span></div>';
    s+='<div class="end b">'+meter(b.level)+'<span class="lvl">'+esc(b.level)+'</span></div>';
    s+='</div><div class="wread">';
    s+='<div class="r"><span class="who">'+esc(A.name)+'</span>'+esc(a.reading)+'</div>';
    s+='<div class="r"><span class="who">'+esc(B.name)+'</span>'+esc(b.reading)+'</div>';
    s+='</div></div>';
    return s;
  }
  function priList(ids){
    if(!ids.length) return '<li class="none">None triggered.</li>';
    return ids.map(function(id){ var p=D.priorities[id];
      return '<li><span class="pt">'+esc(p.title)+'</span> <span class="pw">· '+esc(p.coordinate_with)+'</span><p>'+esc(p.rationale)+'</p></li>';
    }).join("");
  }
  function render(ca, cb){
    var pair=canon(ca,cb), A=D.states[pair[0]], B=D.states[pair[1]];
    var changed=D.signals.filter(function(s){ return A.signals[s.id].level!==B.signals[s.id].level; }).length;
    var pa=A.priorities, pb=B.priorities;
    var onlyA=pa.filter(function(i){return pb.indexOf(i)<0;});
    var onlyB=pb.filter(function(i){return pa.indexOf(i)<0;});
    var shared=pa.filter(function(i){return pb.indexOf(i)>=0;});
    var priCh=onlyA.length+onlyB.length;
    var featured = D.featured.some(function(f){ return f[0]===pair[0] && f[1]===pair[1]; });
    var h='';
    h+='<div class="cmp-band"><span class="side">'+esc(A.name)+'</span><span class="vs">weighed against</span><span class="side">'+esc(B.name)+'</span>';
    h+='<span class="cmp-tally"><b>'+changed+'</b> of '+D.signals.length+' decision signals read differently<br><b>'+priCh+'</b> coordination priorit'+(priCh===1?"y":"ies")+' change</span></div>';
    h+='<div class="sec"><div class="sh">The Decision Framework, side by side</div><div class="weigh">';
    h+=D.signals.map(function(s){ return weighRow(s,A,B); }).join("");
    h+='</div></div>';
    h+='<div class="sec"><div class="sh">Which coordination priorities change</div><div class="cmp-cols">';
    h+='<div class="cmp-col only"><h4>Only <b>'+esc(A.name)+'</b></h4><ul>'+priList(onlyA)+'</ul></div>';
    h+='<div class="cmp-col both"><h4>Shared</h4><ul>'+priList(shared)+'</ul></div>';
    h+='<div class="cmp-col only"><h4>Only <b>'+esc(B.name)+'</b></h4><ul>'+priList(onlyB)+'</ul></div>';
    h+='</div></div>';
    var url=C.base+"/atlas/"+C.edition+"/compare/"+pair.map(function(c){return D.states[c].slug;}).join("-vs-")+"/";
    if(featured) h+='<div class="rel" style="padding-top:12px">Full comparison with the facts underneath: <a href="'+url+'">'+esc(A.name)+' vs '+esc(B.name)+' →</a></div>';
    out.innerHTML=h;
    if(window.history&&history.replaceState) history.replaceState(null,"","?a="+pair[0]+"&b="+pair[1]);
    if(window.plausible) plausible("comparison",{props:{pair:pair[0]+"-"+pair[1]}});
  }
  function go(){ if(selA.value&&selB.value&&selA.value!==selB.value) render(selA.value, selB.value); }
  selA.addEventListener("change", go); selB.addEventListener("change", go);
  var btn=document.getElementById("cmpGo"); if(btn) btn.addEventListener("click", go);
  // Seed from ?a=&b= or the defaults, and render on load.
  var qp; try{ qp=new URLSearchParams(location.search); }catch(e){ qp=null; }
  var a0=(qp&&qp.get("a"))||C.defaultA, b0=(qp&&qp.get("b"))||C.defaultB;
  if(!D.states[a0]) a0=C.defaultA; if(!D.states[b0]||b0===a0) b0=C.defaultB;
  selA.value=a0; selB.value=b0; render(a0,b0);
})();
"""


def render_compare_index_html(edition: str = CURRENT_EDITION) -> str:
    """The Comparison instrument's home: weigh ANY two operating environments live (the browser lays
    out the embedded, already-decided reasoning), with the high-intent corridors as one-click routes
    into the full static comparisons."""
    import json
    data = _cmp.index_dataset(edition)
    title = "Compare Any Two States — Capital Gains, Estate & Coordination | Driftwood Atlas"
    desc = ("Weigh any two states as operating environments: which of five decision signals read "
            "differently, and which coordination priorities change. Capital-gains rate, estate tax, "
            "basis step-up, harvesting, and residency — side by side. Illustrative, not advice.")
    url = _cmp.compare_index_url(edition)
    cfg = {"base": BASE_URL, "edition": edition, "defaultA": "CA", "defaultB": "TX"}
    corridors = "\n".join(
        f'<a href="{_cmp.compare_url(a, b, edition)}">{_esc(STATE_NAMES[a])} &amp; {_esc(STATE_NAMES[b])}<span class="ar">→</span></a>'
        for a, b in _cmp.FEATURED_CORRIDORS)
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
<link rel="stylesheet" href="{_ABS}driftwood.css">
<script src="{_ABS}dw-context.js"></script>
<style>{_CMP_CSS}</style>
</head>
<body>
<div class="sheet">
  <div class="frame">
    {NAV_ABS}
    <div class="hd">
      <div class="eyebrow">The State Atlas · Comparison</div>
      <h1>Weigh any two operating environments.</h1>
      <p class="lede">Pick two states. This instrument reads both through the same five decision lenses and
        shows <b>which coordination priorities change</b> when the environment does — not which state is
        "better," but what a household would coordinate differently. Every reading is the same reasoning
        the state pages render.</p>
    </div>
    <div class="picker">
      <div class="pf"><label for="cmpA">Environment A</label><select id="cmpA" aria-label="First state"></select></div>
      <span class="vs">vs</span>
      <div class="pf"><label for="cmpB">Environment B</label><select id="cmpB" aria-label="Second state"></select></div>
      <button id="cmpGo" type="button">Weigh them →</button>
    </div>
    <div id="cmpOut" aria-live="polite"></div>
    <div class="sec"><div class="sh">High-intent corridors</div>
      <p class="lede" style="margin-bottom:12px">The routes households weigh most often — each a full comparison
        with the facts underneath.</p>
      <div class="corridors">{corridors}</div>
    </div>
    {_provenance_block()}
    {DISCLOSURE}
    {firm_anchor_html()}
    <div class="colophon">Driftwood. State tax law reflects {_esc(AS_OF_LAW)}; last reviewed {_esc(LAST_REVIEWED)}. The instrument lays out the reasoning graph; it authors no facts of its own.</div>
  </div>
</div>
<script>window.__CFG__={json.dumps(cfg)};window.__CMP__={json.dumps(data)};</script>
<script>{_INDEX_JS}</script>
</body>
</html>
"""


def export_comparisons(out_dir: str | Path = "docs", edition: str = CURRENT_EDITION) -> list[str]:
    """Publish the Comparison instrument: the index (weigh any pair, live) + a canonical static page
    for each high-intent corridor (the facts-underneath render, for SEO + citability). Returns written
    paths relative to out_dir."""
    out_dir = Path(out_dir)
    base = out_dir / "atlas" / edition / "compare"
    base.mkdir(parents=True, exist_ok=True)
    written = []
    (base / "index.html").write_text(render_compare_index_html(edition))
    written.append(f"atlas/{edition}/compare/index.html")
    seen = set()
    for a, b in _cmp.FEATURED_CORRIDORS:
        slug = _cmp.compare_slug(a, b)
        if slug in seen:
            continue
        seen.add(slug)
        d = out_dir / _cmp.compare_path(a, b, edition)
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render_comparison_html(_cmp.build_comparison(a, b, edition), edition))
        written.append(f"{_cmp.compare_path(a, b, edition)}/index.html")
    return written


# The corridors that belong in the sitemap (canonical, deduped) — the instrument index + featured pages.
def sitemap_entries(edition: str = CURRENT_EDITION) -> list[tuple[str, str, str]]:
    entries = [(f"atlas/{edition}/compare/", "0.6", "monthly")]
    seen = set()
    for a, b in _cmp.FEATURED_CORRIDORS:
        slug = _cmp.compare_slug(a, b)
        if slug in seen:
            continue
        seen.add(slug)
        entries.append((f"{_cmp.compare_path(a, b, edition)}/", "0.5", "monthly"))
    return entries
