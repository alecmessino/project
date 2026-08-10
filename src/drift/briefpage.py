"""The COI-ready state brief: one printable page a CPA or an estate attorney can send a client.

WHAT IT IS. `/atlas/{edition}/{state}/brief/`, one per state, generated from the same reasoning
graph the Atlas page renders. It carries the state's severity reading, the coordination agenda with
an owner against each row, the action register with the artifact each request needs, the
illustrative per-$1M figure with its hypothetical-performance disclosure, and Driftwood's
non-competitive framing lifted from partners.html and estate-attorneys.html.

It exists because the Atlas's primary reader is a centre of influence, and the one thing a partner
could not do with it was hand it to a client. A state page is a reference; this is a document.

WHAT IT DELIBERATELY IS NOT:

  * NOT a new set of claims. Every sentence here is already published on the state page or on the
    two For Professionals pages. The brief is an arrangement, not an assertion. In particular it
    carries no collision block: that layer is staged and unpublished (see reasoning.py), and a
    document designed to be forwarded is the last place to debut an unverified tax claim.
  * NOT per-partner tracked. The ask was to know which briefs partners open and forward. That needs
    a partner registry, a backend, and a privacy-policy amendment, and OPERATIONS.md records the
    interactive referral workflow as DEFERRED pending exactly those. A forward-tracking beacon also
    points at the partner's client, who never agreed to anything. The honest maximum, and what is
    built, is aggregate: the page is a plain URL, the booking link carries its placement, and
    Plausible counts pageviews. No cookie, no identifier, no registry.
  * NOT co-branded. Putting a third party's firm name on a Driftwood-generated, PAS-disclosed
    document is a compliance decision for the principal and counsel, not a template feature. In
    place of it the brief carries a talk track the partner pastes into their OWN email, where the
    co-branding is theirs and needs no approval from us.
  * NOT collecting anything. No form, no input, no dw-context.js, no URL personalization. The only
    figure is scale-free per $1M, so the page never needs to know a household's numbers.

noindex, deliberately: it restates the state page's substance for a different reader, and two URLs
competing on the same facts is the duplicate-content problem the editioned canonical exists to
avoid. It is a tool a partner is handed, not a search destination.
"""

from __future__ import annotations

from pathlib import Path

from .site import BASE_URL, CONTACT_EMAIL, booking_link, firm_anchor_html
from .statemap import AS_OF_LAW, CURRENT_EDITION, LAST_REVIEWED
from .statepage import (DISCLOSURE, PLAUSIBLE, STATE_PAGE_CODES, _ABS, _esc, _severity_line,
                        atlas_url, build_state_pages, state_slug)

__all__ = ["brief_path", "brief_url", "render_brief", "export_briefs"]


def brief_path(code: str, edition: str = CURRENT_EDITION) -> str:
    return f"atlas/{edition}/{state_slug(code)}/brief"


def brief_url(code: str, edition: str = CURRENT_EDITION) -> str:
    return f"{BASE_URL}/{brief_path(code, edition)}/"


_CSS = """
  :root{--bg:#f1efe9;--soft:#f7f5f0;--line:#d8d3c6;--line2:#e9e5db;--frame-line:#c3bcab;
    --ink:#1d242d;--body:#3a414b;--dim:#5f5d68;--muted:#6f675b;
    --brass:#2c5878;--gold:#a9c2d6;--teal2:#15806a;--navy:#1a2330;--accent-strike:#2c5878;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--body);font:14.5px/1.6 var(--serif);
    -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
  .sheet{max-width:820px;margin:30px auto;padding:0 20px 50px}
  .frame{background:#fff;border:1px solid var(--line);padding:38px 40px 30px}
  .eyebrow{font-family:var(--sans);font-weight:700;font-size:10px;letter-spacing:.2em;
    text-transform:uppercase;color:var(--brass);margin-bottom:10px}
  h1{font-family:var(--sans);font-weight:700;font-size:28px;line-height:1.1;letter-spacing:-.02em;
    color:var(--ink);margin:0 0 12px}
  .sev{font-family:var(--sans);font-weight:500;font-size:15px;line-height:1.45;color:var(--ink);
    margin:0 0 16px;max-width:64ch}
  .fig{border-top:2px solid var(--brass);border-bottom:1px solid var(--line);padding:12px 0;
    margin:0 0 6px;display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
  .fig .n{font-family:var(--sans);font-weight:700;font-size:30px;color:var(--ink);
    font-variant-numeric:tabular-nums;letter-spacing:-.02em}
  .fig .u{font-family:var(--sans);font-size:12.5px;color:var(--dim);flex:1;min-width:210px}
  .fine{font-size:10.5px;line-height:1.5;color:var(--muted);margin:0 0 22px}
  h2{font-family:var(--sans);font-weight:700;font-size:10px;letter-spacing:.16em;
    text-transform:uppercase;color:var(--muted);margin:22px 0 10px}
  table{width:100%;border-collapse:collapse;font-family:var(--sans)}
  th{text-align:left;font-size:9px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);
    font-weight:700;padding:0 12px 7px 0;border-bottom:1px solid var(--ink)}
  td{font-size:12.5px;line-height:1.5;color:var(--body);padding:10px 12px 10px 0;
    border-bottom:1px solid var(--line2);vertical-align:top}
  td.who{font-weight:600;color:var(--brass);white-space:nowrap;font-size:11.5px}
  td .bring{display:block;margin-top:3px;font-size:11px;color:var(--muted)}
  .seat{border:1px solid var(--ink);padding:14px 16px;margin:20px 0 0}
  .seat p{margin:0;font-family:var(--sans);font-size:12.5px;line-height:1.55;color:var(--body)}
  .seat p+p{margin-top:8px}
  .seat b{color:var(--ink)}
  .close{margin:22px 0 0;padding-top:16px;border-top:1px solid var(--line)}
  .close .cn{font-family:var(--sans);font-weight:700;font-size:14px;color:var(--ink)}
  .close .cr{font-family:var(--sans);font-size:11.5px;color:var(--dim);margin-bottom:8px}
  .close a{font-family:var(--sans);font-size:12.5px;color:var(--brass);text-decoration:none;
    border-bottom:1px solid var(--gold)}
  .disc{margin-top:20px;padding-top:12px;border-top:1px solid var(--line);
    font-size:9.5px;line-height:1.5;color:var(--muted)}
  .disc a{color:var(--teal2)}
  /* The partner strip. Instructions to the SENDER, never to the recipient, so it is the one thing
     on the page that must not survive printing: the client's copy carries no talk track. */
  .strip{max-width:820px;margin:0 auto 14px;padding:0 20px}
  .strip .in{background:var(--navy);padding:16px 20px}
  .strip .sk{font-family:var(--sans);font-weight:700;font-size:9.5px;letter-spacing:.16em;
    text-transform:uppercase;color:var(--gold);margin-bottom:8px}
  .strip p{font-family:var(--sans);font-size:12.5px;line-height:1.6;color:#dfe4ea;margin:0 0 10px}
  .strip textarea{width:100%;min-height:96px;font:12.5px/1.55 var(--sans);color:var(--ink);
    background:#fff;border:1px solid var(--frame-line);padding:10px 12px;resize:vertical}
  .strip .row{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px}
  .strip button{font:inherit;font-family:var(--sans);font-size:12.5px;font-weight:700;
    background:var(--brass);color:#f1ede3;border:0;padding:11px 18px;cursor:pointer;min-height:44px}
  .strip .ok{font-family:var(--sans);font-size:11.5px;color:var(--gold);align-self:center}
  @media print{
    body{background:#fff}
    .sheet{margin:0;max-width:none;padding:0}
    .frame{border:0;padding:0}
    .strip{display:none}
    h2{margin-top:14px}
    tr{break-inside:avoid}
    .seat{break-inside:avoid}
  }
  @media(max-width:620px){.frame{padding:24px 18px}}
"""


def _agenda_rows(r: dict) -> str:
    rows = []
    for c in r.get("coordination") or []:
        rows.append(f'<tr><td class="who">{_esc(c["coordinate_with"])}</td>'
                    f'<td><b>{_esc(c["title"])}</b><br>{_esc(c["rationale"])}</td></tr>')
    return "".join(rows)


def _action_rows(r: dict) -> str:
    rows = []
    for a in r.get("actions") or []:
        rows.append(f'<tr><td class="who">{_esc(a["owner"])}</td>'
                    f'<td>{_esc(a["step"])}<span class="bring">Bring: {_esc(a["bring"])}</span></td></tr>')
    return "".join(rows)


def _talk_track(name: str, url: str) -> str:
    """What the partner pastes into their own email. Written in the partner's voice, not ours, and
    it promises only what the referral page already promises: fifteen minutes, and no proposal."""
    return (f"I came across a plain-language reference on how {name} taxes investment and estate "
            f"decisions, and it lines up with a few things we have discussed. It is free and there "
            f"is nothing to sign up for.\n\n{url}\n\nThe firm behind it, Driftwood, coordinates "
            f"across the CPA, the attorney and the portfolio rather than replacing any of them. If "
            f"it is useful, they offer a fifteen-minute introduction and it produces no proposal. "
            f"I would stay involved either way.")


def render_brief(data: dict, edition: str = CURRENT_EDITION) -> str:
    code, name = data["code"], data["name"]
    r = data.get("reasoning") or {}
    impact = r.get("impact") or {}
    a = data.get("alpha")
    url = brief_url(code, edition)
    sev = _severity_line(r.get("framework") or [], name)
    from .leakage import coordination_opportunity_per_m, fmt_usd
    figure = f"~{fmt_usd(coordination_opportunity_per_m(a['value']))}" if a else ""
    talk = _talk_track(name, url)
    agenda, actions = _agenda_rows(r), _action_rows(r)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
{PLAUSIBLE}
<title>{_esc(name)} coordination brief | Driftwood Wealth</title>
<meta name="description" content="A one-page {_esc(name)} coordination brief for a CPA, attorney, or advisor to share with a client. Illustrative, not advice." />
<!-- noindex: this restates the state page's substance for a different reader, and two URLs
     competing on the same facts is the duplicate-content problem the editioned canonical exists to
     avoid. It is a document a partner is handed, not a search destination. -->
<meta name="robots" content="noindex,follow" />
<link rel="canonical" href="{atlas_url(code, edition)}" />
<link rel="icon" href="{_ABS}favicon.svg" />
<meta name="theme-color" content="#f1efe9" />
<link rel="stylesheet" href="{_ABS}driftwood.css">
<style>{_CSS}</style>
</head>
<body>
<!-- Addressed to the sender, and print:none. The client's copy must not arrive carrying the note
     the professional was supposed to write themselves. -->
<div class="strip"><div class="in">
  <div class="sk">For the professional sending this</div>
  <p>This page is written to be forwarded as it stands. Nothing on it asks your client for
    information, and Driftwood is not introduced as a replacement for you.</p>
  <label class="sk" for="btalk">A note you can paste into your own email</label>
  <textarea id="btalk" readonly aria-label="A note you can paste into your own email">{_esc(talk)}</textarea>
  <div class="row"><button type="button" id="bcopy">Copy the note</button>
    <span class="ok" id="bok" role="status" aria-live="polite"></span></div>
</div></div>

<div class="sheet">
  <div class="frame">
    <div class="eyebrow">Coordination brief &middot; {_esc(name)}</div>
    <h1>What {_esc(name)} changes about a household's decisions.</h1>
    {f'<p class="sev">{_esc(sev)}</p>' if sev else ''}
    {f'''<div class="fig"><span class="n">{figure}</span>
      <span class="u">per $1M of taxable assets each year, illustrative: what tax-aware portfolio
      management alone is worth in {_esc(name)}. Treat it as the floor. It counts the portfolio
      only, and leaves the estate, gifting, and residency coordination at zero.</span></div>
    <p class="fine">Illustrative and hypothetical, not a track record: a tax-management model
      applied retroactively to roughly 30 years of proxy-spliced market data on a single path, with
      no client capital invested. A household's own figure depends on its holdings, basis, and
      bracket. Full disclosure below.</p>''' if figure else ''}

    {f'<h2>The agenda, and whose desk each item is on</h2><table><thead><tr><th>Owner</th><th>Matter</th></tr></thead><tbody>{agenda}</tbody></table>' if agenda else ''}

    {f'<h2>What can be answered this week</h2><table><thead><tr><th>Ask</th><th>The request, and what it needs</th></tr></thead><tbody>{actions}</tbody></table>' if actions else ''}

    <div class="seat">
      <p><b>Where Driftwood sits.</b> Driftwood is the coordination seat. It does not file returns,
        draft or amend documents, or offer a second opinion on the work of the professionals a
        household already has. It makes that work coordinate with everything else.</p>
      <p>You are a permanent seat, not a relationship being routed around. Your engagement, and your
        client relationship, remain yours. Driftwood does not pay or receive compensation for
        professional referrals.</p>
    </div>

    <div class="close">
      <div class="cn">Alec Messino</div>
      <div class="cr">Founder &amp; Financial Advisor, Driftwood Wealth</div>
      <a href="{booking_link(f'brief-{code.lower()}', campaign='cpa_referral')}" target="_blank" rel="noopener">Book a 15-minute professional introduction &rarr;</a>
      &nbsp;&nbsp;<a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
      &nbsp;&nbsp;<a href="{atlas_url(code, edition)}">The full {_esc(name)} Atlas entry &rarr;</a>
    </div>

    {DISCLOSURE.replace('<div class="disc">', '<div class="disc">')}
    <div class="disc">State law reflects {_esc(AS_OF_LAW)}; last reviewed {_esc(LAST_REVIEWED)}.
      Nothing here is a statement about any particular household.</div>
    {firm_anchor_html()}
  </div>
</div>
<script>
(function(){{
  var b=document.getElementById("bcopy"), t=document.getElementById("btalk"), k=document.getElementById("bok");
  if(!b||!t) return;
  b.addEventListener("click", function(){{
    t.select(); t.setSelectionRange(0, 99999);
    var done=function(){{ k.textContent="Copied."; if(window.plausible) plausible("brief_note_copied",{{props:{{state:"{code}"}}}}); }};
    if(navigator.clipboard&&navigator.clipboard.writeText){{ navigator.clipboard.writeText(t.value).then(done, done); }}
    else {{ try{{ document.execCommand("copy"); }}catch(e){{}} done(); }}
  }});
}})();
</script>
</body>
</html>
"""


def export_briefs(out_dir: str | Path = "docs", edition: str = CURRENT_EDITION) -> list[str]:
    """Publish one brief per state. Returns the written paths, relative to out_dir."""
    out_dir = Path(out_dir)
    pages = build_state_pages()
    written = []
    for code in STATE_PAGE_CODES:
        d = out_dir / brief_path(code, edition)
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render_brief(pages[code], edition))
        written.append(f"{brief_path(code, edition)}/index.html")
    return written
