/* Driftwood: Layer 1 of the operating system — the shared household context (privacy-first,
 * cross-page).
 *
 * The site is one system, not a shelf of calculators. Layers 1-3 are the platform; the tools
 * (Assessment, Atlas, Diagnostic, Labs) are applications that plug into it:
 *
 *   Layer 1 · shared household context   this IIFE            window.dwTaxContext
 *   Layer 2 · recommendation engine      the 5th IIFE below   window.dwNextBest
 *   Layer 3 · journey rail               renderJourney()      + scripts/phase2_nav.py
 *   Layer 4 · decision applications      the tool pages
 *
 * A module declares itself to the platform; it does not wire itself into it. Adding one means a
 * MODULES entry below, a CURRENT entry in phase2_nav.py, a row on the Decision Tools shelf, and a
 * <div id="dw-next"> mount — no new plumbing.
 *
 * Five pieces of state, in-browser only (localStorage; nothing is ever transmitted):
 *
 *   household   state, bracket, portfolio   what the visitor told us about their situation
 *   drivers     string[]                    the situation factors from the Coordination Assessment
 *   steps       number[]                    journey steps visited
 *   done        string[]                    modules actually completed, not merely opened
 *   (recommendations are DERIVED per page load by Layer 2, never stored)
 *
 * It renders as an editable "Your household" bar at the top of each tool: set it anywhere and every
 * tool follows.
 *
 * Precedence guardrail: URL search params ALWAYS win. A personalized link
 * (?state=IL&bracket=37&port=2000000&drivers=concentration) overrides, and refreshes, whatever this
 * browser had stored.
 */
(function () {
  var KEY = "dw_tax_context";
  var subs = [];

  // Canonical option lists for the editable bar. Tools map the chosen code onto their own data.
  var STATES = [["", "Select…"], ["—", "No state / federal only"],
    ["AL","Alabama"],["AK","Alaska"],["AZ","Arizona"],["AR","Arkansas"],["CA","California"],
    ["CO","Colorado"],["CT","Connecticut"],["DE","Delaware"],["FL","Florida"],["GA","Georgia"],
    ["HI","Hawaii"],["ID","Idaho"],["IL","Illinois"],["IN","Indiana"],["IA","Iowa"],["KS","Kansas"],
    ["KY","Kentucky"],["LA","Louisiana"],["ME","Maine"],["MD","Maryland"],["MA","Massachusetts"],
    ["MI","Michigan"],["MN","Minnesota"],["MS","Mississippi"],["MO","Missouri"],["MT","Montana"],
    ["NE","Nebraska"],["NV","Nevada"],["NH","New Hampshire"],["NJ","New Jersey"],["NM","New Mexico"],
    ["NY","New York"],["NC","North Carolina"],["ND","North Dakota"],["OH","Ohio"],["OK","Oklahoma"],
    ["OR","Oregon"],["PA","Pennsylvania"],["RI","Rhode Island"],["SC","South Carolina"],
    ["SD","South Dakota"],["TN","Tennessee"],["TX","Texas"],["UT","Utah"],["VT","Vermont"],
    ["VA","Virginia"],["WA","Washington"],["WV","West Virginia"],["WI","Wisconsin"],["WY","Wyoming"],
    ["DC","Washington, DC"]];
  var BRACKETS = [["", "Select…"], ["37","37% (top)"], ["35","35%"], ["32","32%"], ["24","24%"], ["22","22%"], ["12","12%"]];
  var PORTS = [["", "Select…"], ["250000","$250k"], ["500000","$500k"], ["1000000","$1.0M"],
    ["2000000","$2.0M"], ["3000000","$3.0M"], ["5000000","$5.0M"], ["10000000","$10M"]];

  // Canonical situation drivers, in the Coordination Assessment's checklist order. The SLUG is the
  // contract: score.html's buttons carry it as data-key, a personalized link carries it as
  // ?drivers=a,b, and Layer 2's rules table keys off it. Adding a driver means adding it in all
  // three places — never derive a slug from display copy, which is edited freely.
  var DRIVER_KEYS = ["business", "entities", "trusts", "equity-comp", "concentration",
    "multi-state", "private", "real-estate", "charity", "estate-tax"];

  // Modules that can be recorded as completed. Kept separate from DRIVER_KEYS so a stray value
  // from an older build can never masquerade as a finished module.
  var MODULE_KEYS = ["score", "leakage", "statemap", "taxlab", "concentration"];

  function read() {
    try { var v = JSON.parse(localStorage.getItem(KEY) || "null"); return v && typeof v === "object" ? v : {}; }
    catch (e) { return {}; }
  }
  function write(ctx) { try { localStorage.setItem(KEY, JSON.stringify(ctx)); } catch (e) {} }
  function notify(c) { subs.forEach(function (fn) { try { fn(c); } catch (e) {} }); }

  // Accepts a raw dollar number (the household dropdown's own values, e.g. "2000000") or a hand-typed
  // cold-outreach shorthand ("2M", "500k") — an explicit suffix scales the number; anything else,
  // including a plain small number, passes through unscaled so a real raw-dollar value is never
  // silently reinterpreted as millions. Mirrors leakage.html's parsePortfolio for the same convention
  // everywhere a portfolio value can enter the site.
  function parsePortfolioLike(raw) {
    var m = String(raw).trim().match(/^(-?[\d.]+)\s*([km])?$/i);
    if (!m) return NaN;
    var n = parseFloat(m[1]); if (!isFinite(n)) return NaN;
    var suf = (m[2] || "").toLowerCase();
    return suf === "m" ? n * 1e6 : suf === "k" ? n * 1e3 : n;
  }

  // Accepts either an array or a comma-separated string (the URL form), keeps only known slugs,
  // dedupes, and returns them in canonical order so two visitors who checked the same boxes in a
  // different sequence store byte-identical context.
  function cleanKeys(raw, allowed) {
    var given = Array.isArray(raw) ? raw : String(raw).split(",");
    var want = {};
    given.forEach(function (k) { want[String(k).trim()] = true; });
    return allowed.filter(function (k) { return want[k] === true; });
  }

  function clean(patch, c) {
    if (patch && patch.state != null) {
      var s = String(patch.state).toUpperCase();
      if (s === "—" || /^[A-Z]{2,3}$/.test(s)) c.state = s;
    }
    if (patch && patch.bracket != null && patch.bracket !== "") {
      var b = parseInt(patch.bracket, 10); if (b >= 10 && b <= 60) c.bracket = b;
    }
    if (patch && patch.portfolio != null && patch.portfolio !== "") {
      var p = Math.round(parsePortfolioLike(patch.portfolio)); if (isFinite(p) && p >= 0 && p <= 1e11) c.portfolio = p;
    }
    // `!= null` and NOT the `!== ""` guard the scalars use: clearing every checkbox is a real
    // state that must be storable, so an empty list has to survive down to [] rather than being
    // treated as "no opinion" and leaving a stale set in place.
    if (patch && patch.drivers != null) c.drivers = cleanKeys(patch.drivers, DRIVER_KEYS);
    if (patch && patch.done != null) c.done = cleanKeys(patch.done, MODULE_KEYS);
    return c;
  }

  // 1 · Merge URL params into storage (URL wins).
  //
  // `visited` -> `steps` migration (2026-07-31): the journey rail went from four linear steps to
  // three, so a returning visitor's stored visited:[1,2,3,4] would mark every step of the NEW rail
  // done on first load. The field is renamed rather than reinterpreted, and the legacy key is
  // dropped on first write — stale data is then simply ignored instead of silently mis-read.
  var qp, ctx = read(), dirty = false;
  if (ctx.visited != null) { delete ctx.visited; dirty = true; }
  try { qp = new URLSearchParams(location.search); } catch (e) { qp = null; }
  if (qp) {
    var before = JSON.stringify(ctx);
    ctx = clean({ state: qp.get("state"), bracket: qp.get("bracket"),
      portfolio: qp.get("port") || qp.get("portfolio"),
      drivers: qp.get("drivers"), done: qp.get("done") }, ctx);
    dirty = dirty || JSON.stringify(ctx) !== before;
  }
  if (dirty) write(ctx);

  // 2 · Decorate same-directory links to the consuming tools so the household follows the visitor.
  var CONSUMERS = [
    { prefix: "taxlab.html", params: ["state", "bracket", "port"] },
    { prefix: "leakage.html", params: ["state", "port"] },
    { prefix: "statemap.html", params: ["state"] },
    // The production pages read the same household, so a link from any of them carries it.
    // (tax-atlas.html retired 2026-07 — consolidated into statemap.html; no entry needed, same as
    // the other redirect stubs.)
    { prefix: "the-record.html", params: ["state", "bracket", "port"] },
    { prefix: "the-practice.html", params: ["state", "bracket", "port"] },
    // coordination-review.html is deliberately NOT decorated. It is the booking page, and it reads
    // none of these params — there is not a single qp.get() on it — so they were pure noise on the
    // one URL a visitor is most likely to copy, share, or hand to Calendly as a referrer. Putting a
    // household's tax bracket and portfolio size in a query string is a habit worth not having:
    // it travels into analytics, referrer headers, and anyone's clipboard. The page loads
    // dw-context.js like every other, so if it ever needs the household it reads dwTaxContext.get()
    // in the browser, where the data already lives and never leaves.
    // The Coordination Assessment is the front of the funnel: a link into it carries the household
    // so the visitor is not asked twice, and carries drivers so a shared link restores the boxes.
    // (concentration.html reads nothing from the context, so it is deliberately NOT decorated —
    // appending params a page ignores is noise in a URL a visitor may well share.)
    { prefix: "score.html", params: ["state", "bracket", "port", "drivers"] }
  ];
  function paramVal(k, c) {
    if (k === "port") return c.portfolio;
    // Lists travel as a comma-joined string; an empty list is not worth a param.
    if (k === "drivers" || k === "done") return c[k] && c[k].length ? c[k].join(",") : null;
    return c[k];
  }
  function withContext(href, keys, c) {
    try {
      var u = new URL(href, location.href), changed = false;
      keys.forEach(function (k) { var v = paramVal(k, c); if (v != null && !u.searchParams.has(k)) { u.searchParams.set(k, v); changed = true; } });
      if (!changed) return href;
      return u.pathname.split("/").pop() + u.search + u.hash;
    } catch (e) { return href; }
  }
  function decorate() {
    var c = read();
    if (c.state == null && c.bracket == null && c.portfolio == null && c.drivers == null) return;
    CONSUMERS.forEach(function (t) {
      var links = document.querySelectorAll('a[href^="' + t.prefix + '"]');
      for (var i = 0; i < links.length; i++) links[i].setAttribute("href", withContext(links[i].getAttribute("href"), t.params, c));
    });
  }

  // 3 · The editable "Your household" bar. A module mounts it by placing
  //     <div id="dw-household" data-page="score|leakage|statemap|taxlab|concentration"></div>
  //     after its nav.
  var CSS = ""
    + ".dw-household{font-family:var(--sans);background:var(--soft);border-bottom:1px solid var(--line);"
    + "padding:9px 24px;display:flex;align-items:center;gap:8px 16px;flex-wrap:wrap;font-size:12px;color:var(--dim)}"
    + ".dw-household .lbl{font-weight:700;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent-strike)}"
    + ".dw-household .fields{display:flex;gap:6px 12px;flex-wrap:wrap;align-items:center}"
    + ".dw-household .f{display:inline-flex;align-items:center;gap:6px}"
    + ".dw-household .f .k{color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-size:9.5px;font-weight:700}"
    + ".dw-household select{font-family:var(--sans);font-size:12px;color:var(--ink);background:#fff;"
    + "border:1px solid var(--line);border-radius:0;padding:4px 20px 4px 8px;font-variant-numeric:tabular-nums;cursor:pointer;"
    + "-webkit-appearance:none;appearance:none;"
    + "background-image:url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='9' height='6'><path fill='%235c6470' d='M0 0h9L4.5 6z'/></svg>\");"
    + "background-repeat:no-repeat;background-position:right 7px center}"
    + ".dw-household select:hover{border-color:var(--ghost-line)}"
    + ".dw-household select:focus-visible{outline:2px solid var(--accent-strike);outline-offset:1px}"
    + ".dw-household .right{margin-left:auto;display:flex;gap:14px;align-items:center;flex-wrap:wrap}"
    + ".dw-household .reset{background:none;border:0;color:var(--muted);font:inherit;font-size:11.5px;cursor:pointer;padding:2px 0;text-decoration:underline;text-underline-offset:3px}"
    + ".dw-household .reset:hover{color:var(--ink)}"
    + ".dw-household .links{display:inline-flex;gap:14px;flex-wrap:wrap}"
    + ".dw-household .links a{color:var(--teal2);text-decoration:none;font-weight:600;font-size:11.5px}"
    + ".dw-household .links a:hover{color:var(--ink)}"
    + ".dw-household .note{width:100%;color:var(--muted);font-size:10.5px;letter-spacing:.01em;margin-top:1px}"
    + "@media(max-width:640px){.dw-household{padding:9px 16px}.dw-household .right{margin-left:0;width:100%}}";
  var styled = false;
  function injectCss() {
    if (styled || typeof document === "undefined") return;
    styled = true;
    var s = document.createElement("style"); s.dataset.dw = "household"; s.textContent = CSS; document.head.appendChild(s);
  }
  function opts(list, sel) {
    return list.map(function (o) {
      return '<option value="' + o[0] + '"' + (String(sel) === o[0] ? " selected" : "") + ">" + o[1] + "</option>";
    }).join("");
  }
  // Sibling links in the household bar. Labels must match the shipped product names exactly. The
  // retired name for taxlab.html survived here for months, in five places, against a page the rest
  // of the site calls the After-Tax Lab — because tests/test_naming_convention.py globbed only
  // *.html and never opened this file. It scans this file now, by literal substring, which is why
  // the retired string cannot appear even in a comment explaining it.
  // "Review" belongs to the engagement (OPERATIONS.md); nothing else may borrow it.
  var SIBLINGS = {
    taxlab: [{ href: "leakage.html", label: "Tax Diagnostic →" }, { href: "statemap.html", label: "State Tax Atlas →" }],
    statemap: [{ href: "leakage.html", label: "Tax Diagnostic →" }, { href: "taxlab.html", label: "After-Tax Lab →" }],
    leakage: [{ href: "taxlab.html", label: "After-Tax Lab →" }, { href: "statemap.html", label: "State Tax Atlas →" }],
    score: [{ href: "leakage.html", label: "Tax Diagnostic →" }, { href: "statemap.html", label: "State Tax Atlas →" }],
    concentration: [{ href: "taxlab.html", label: "After-Tax Lab →" }, { href: "leakage.html", label: "Tax Diagnostic →" }],
    // (the standalone "atlas" key retired 2026-07 with tax-atlas.html — consolidated into statemap.html,
    // which keeps its own siblings entry above)
    record: [{ href: "statemap.html", label: "State Tax Atlas →" }, { href: "the-practice.html", label: "The Practice →" }],
    practice: [{ href: "statemap.html", label: "State Tax Atlas →" }, { href: "the-record.html", label: "The Record →" }],
    home: [{ href: "statemap.html", label: "State Tax Atlas →" }, { href: "the-record.html", label: "The Record →" }]
  };
  function renderBars() {
    var hosts = document.querySelectorAll("#dw-household");
    if (!hosts.length) return;
    injectCss();
    var c = read();
    hosts.forEach(function (el) {
      var page = el.getAttribute("data-page") || "taxlab";
      var sibs = (SIBLINGS[page] || []).map(function (s) { return '<a href="' + s.href + '">' + s.label + "</a>"; }).join("");
      el.className = "dw-household";
      el.innerHTML =
        '<span class="lbl">Your household</span>' +
        '<div class="fields">' +
          '<label class="f"><span class="k">State</span><select data-k="state" aria-label="Your state">' + opts(STATES, c.state == null ? "" : c.state) + "</select></label>" +
          '<label class="f"><span class="k">Federal</span><select data-k="bracket" aria-label="Your federal bracket">' + opts(BRACKETS, c.bracket == null ? "" : c.bracket) + "</select></label>" +
          '<label class="f"><span class="k">Portfolio</span><select data-k="portfolio" aria-label="Your taxable portfolio">' + opts(PORTS, c.portfolio == null ? "" : c.portfolio) + "</select></label>" +
        "</div>" +
        '<div class="right"><span class="links">' + sibs + "</span>" +
          '<button type="button" class="reset">Reset</button></div>' +
        '<span class="note">Set once, carried across every Driftwood analysis. Saved in this browser only, never transmitted.</span>';
      el.querySelectorAll("select").forEach(function (s) {
        s.addEventListener("change", function () {
          var patch = {}; patch[s.getAttribute("data-k")] = s.value;
          api.save(patch);
        });
      });
      var rb = el.querySelector(".reset");
      if (rb) rb.addEventListener("click", function () { api.reset(); });
    });
  }

  // 3b · Layer 3 — the journey progress rail. Each tool page carries a .journey-rail, emitted by
  //      scripts/phase2_nav.py so the three steps are written in exactly one place (Assess →
  //      Analyze → Coordination Review). The middle step is deliberately not a sequence: the four
  //      analyses are parallel, and which one a visitor should run is Layer 2's job, not the rail's.
  //      Mark steps prior to the current one (and any previously visited step, persisted in the
  //      shared context) as done, and show a household-readiness pip so the visitor sees how far
  //      their setup has progressed. Pure enhancement: with the script absent the static rail still
  //      reads correctly.
  function markVisited(step) {
    var c = read(), v = Array.isArray(c.steps) ? c.steps.slice() : [];
    if (v.indexOf(step) === -1) { v.push(step); c.steps = v; write(c); }
  }
  function renderJourney() {
    var rail = document.querySelector(".journey-rail");
    if (!rail) return;
    var step = parseInt(rail.getAttribute("data-step"), 10);
    if (!step) { var cur = rail.querySelector('li[aria-current="step"]'); step = cur ? parseInt(cur.querySelector(".num").textContent, 10) : 0; }
    if (!step) return;
    markVisited(step);
    var c = read(), visited = Array.isArray(c.steps) ? c.steps : [];
    var items = rail.querySelectorAll("ol > li:not(.sep)");
    for (var i = 0; i < items.length; i++) {
      var n = parseInt(items[i].querySelector(".num").textContent, 10);
      // The step you are standing on is CURRENT, never done. markVisited() records it a few lines
      // above, so without this guard every page marked itself complete on arrival — and because
      // `li.done .num` is declared after `li[aria-current] .num`, the teal "finished" pip won the
      // cascade over the blue "you are here" pip. The rail told every visitor they had finished the
      // page they were still reading.
      if (n !== step && (n < step || visited.indexOf(n) !== -1)) items[i].classList.add("done");
      else items[i].classList.remove("done");
    }
    // Household-readiness pip: all three facts set = ready.
    var ready = c.state != null && c.state !== "" && c.bracket != null && c.portfolio != null;
    var pip = rail.querySelector(".jr-house");
    if (!pip) {
      pip = document.createElement("span");
      pip.className = "jr-house";
      var cta = rail.querySelector(".jr-cta");
      (cta ? rail.querySelector(".jr-in") : rail).insertBefore(pip, cta || null);
    }
    pip.textContent = ready ? "Household set" : "Set your household →";
    pip.className = "jr-house" + (ready ? " set" : "");
  }

  // 4 · Public API. The four production pages consume this rather than re-deriving the household,
  //     so a state name, a dollar format, and an as-of stamp read identically everywhere.
  var NAME_BY_CODE = {};
  STATES.forEach(function (s) { if (s[0] && s[0] !== "—") NAME_BY_CODE[s[0]] = s[1]; });

  var api = window.dwTaxContext = {
    get: read,
    save: function (patch) { var c = clean(patch, read()); write(c); decorate(); renderBars(); renderJourney(); notify(c); },
    reset: function () { try { localStorage.removeItem(KEY); } catch (e) {} decorate(); renderBars(); renderJourney(); notify({}); },
    subscribe: function (fn) { if (typeof fn === "function") subs.push(fn); },
    decorate: decorate, mountBar: renderBars,
    // Record a module as actually completed (not merely opened, which is what `steps` tracks).
    markDone: function (mod) {
      var c = read(), d = Array.isArray(c.done) ? c.done.slice() : [];
      if (MODULE_KEYS.indexOf(mod) === -1 || d.indexOf(mod) !== -1) return;
      d.push(mod); api.save({ done: d });
    },
    states: STATES,
    driverKeys: DRIVER_KEYS,
    moduleKeys: MODULE_KEYS,
    stateName: function (code) { return NAME_BY_CODE[String(code || "").toUpperCase()] || ""; },
    // Dollars, never percentages, on family-facing pages; tabular numerals are applied in CSS.
    usd: function (n) {
      if (n == null || !isFinite(n)) return "–";
      return "$" + Math.round(n).toLocaleString("en-US");
    },
    // Every computed figure carries where it came from and when. Showing the work is the point.
    asOf: function (c) {
      c = c || read();
      var where = c.state && c.state !== "—" ? api.stateName(c.state) : "Federal only";
      return where + " · 2025 law · computed in this browser, never transmitted";
    }
  };

  // Cross-tab sync.
  try { window.addEventListener("storage", function (e) { if (e.key === KEY) { decorate(); renderBars(); renderJourney(); notify(read()); } }); } catch (e) {}

  function ready() { decorate(); renderBars(); renderJourney(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ready); else ready();
})();

/* Driftwood: Layer 2 of the operating system — the recommendation engine ("Your Next Decision").
 *
 * Every module ends by recommending the ONE analysis this household should run next, and says why.
 * Before this existed each tool simply stopped, which is the Journey defect the category audit
 * scored 3.6/5 across the site: competing co-equal CTAs, so no single next step dominates.
 *
 *   candidates  ->  requirements filter  ->  ranking  ->  one recommendation
 *
 * The rules are DECLARATIVE on purpose. A destination is a record with a priority, its
 * requirements, a confidence, a reason, and the outcomes it promises — never an `if` buried in a
 * branch. Ranking can then get smarter (weighting by confidence, by recency, by completion) without
 * anyone rewriting the engine, and a new module is a MODULES entry rather than a new code path.
 *
 * Two platform rules this file must keep:
 *
 *   1. No score, no grade. The platform surfaces constraints, opportunities, and a recommended next
 *      decision. It never tells a household it scored 72.
 *   2. No dollar or percent figure renders here — enforced by tests/web/test_next_decision.js. That
 *      is what keeps this feature outside FIGURE_PROVENANCE.md's standing mandate and outside the
 *      single-numeric-lineage guarantee in tests/test_drift_tool_consistency.py. If a figure ever
 *      belongs here, it needs a provenance row first.
 *
 * A module mounts it with <div id="dw-next" data-page="score|leakage|statemap|taxlab|concentration">
 * placed after the page's own static CTA, which stays as the JS-off fallback.
 */
(function () {
  if (typeof document === "undefined") return;
  var ctx = window.dwTaxContext;
  if (!ctx) return;

  // Each destination declares what it is, what it promises, and how strongly it wants to be
  // recommended when nothing else distinguishes it. `outcomes` is the "you'll leave with" list and
  // must stay qualitative — see platform rule 2 above.
  var MODULES = {
    score: {
      href: "score.html", name: "Coordination Assessment", priority: 1,
      lead: "Start with the Coordination Assessment",
      why: "Two minutes of check-boxes tells the rest of this site what to show you.",
      outcomes: ["the systems your situation actually touches",
                 "the matters each one implies",
                 "a register of opportunities to work through"]
    },
    statemap: {
      href: "statemap.html", name: "State Tax Atlas", priority: 2,
      lead: "Continue with the State Tax Atlas",
      why: "Where you live changes which decisions are worth making.",
      outcomes: ["how your state treats income, gains, and estates",
                 "the dimensions where your state is an outlier",
                 "what crossing a state line would and would not change"]
    },
    leakage: {
      href: "leakage.html", name: "Tax Diagnostic", priority: 2,
      lead: "Continue with the Tax Diagnostic",
      why: "Tax is the most measurable expression of coordination.",
      outcomes: ["where return is lost before it reaches the household",
                 "what is recoverable by structure alone",
                 "the levers that recover it"]
    },
    taxlab: {
      href: "taxlab.html", name: "After-Tax Lab", priority: 2,
      lead: "Continue with the After-Tax Lab",
      why: "The return you keep is not the return you earn.",
      outcomes: ["the same portfolio measured after tax",
                 "where the drag is concentrated",
                 "what coordination is worth over a full horizon"]
    },
    concentration: {
      href: "concentration.html", name: "Concentrated Position Lab", priority: 3,
      lead: "Continue with the Concentrated Position Lab",
      why: "A single position is a risk decision and a tax decision at the same time.",
      outcomes: ["tax-aware routes out of a single position",
                 "what each route costs in tax, time, and liquidity",
                 "the order they run in"]
    },
    review: {
      href: "coordination-review.html", name: "Coordination Review", priority: 0,
      lead: "Request a Coordination Review",
      why: "Some decisions cannot be run from a browser. This is the one that reads them together.",
      outcomes: ["every system read together, once",
                 "the sequence your decisions should run in",
                 "a written plan you keep"]
    }
  };

  // Driver -> which analysis it argues for, and how strongly. Integers, not a model:
  //   3 = the driver IS that tool's subject   2 = the tool answers it directly   1 = adjacent
  var DRIVER_VOTES = {
    "business":      { leakage: 2, taxlab: 1 },
    "entities":      { leakage: 1 },
    "trusts":        {},                          // no shipped tool answers this — see REVIEW_ONLY
    "equity-comp":   { concentration: 3, taxlab: 1 },
    "concentration": { concentration: 3, leakage: 1 },
    "multi-state":   { statemap: 3, leakage: 1 },
    "private":       { taxlab: 2 },
    "real-estate":   { statemap: 2, taxlab: 1 },
    "charity":       { concentration: 1, taxlab: 1 },
    "estate-tax":    {}                           // no shipped tool answers this — see REVIEW_ONLY
  };

  // Be honest about the gap rather than routing these somewhere that only half answers them.
  // They score nothing, and instead strengthen the Review's reason.
  var REVIEW_ONLY = ["trusts", "estate-tax"];

  var DRIVER_PHRASE = {
    "business":      "you own an operating business",
    "entities":      "you hold more than one legal entity",
    "trusts":        "trusts are already part of your structure",
    "equity-comp":   "a meaningful part of your pay arrives as equity",
    "concentration": "a large share of your wealth sits in one position",
    "multi-state":   "your financial life crosses a state line",
    "private":       "you hold private or alternative investments",
    "real-estate":   "you hold investment real estate",
    "charity":       "giving is part of your plan",
    "estate-tax":    "your estate may be large enough to be taxed"
  };

  // With no drivers to go on, fall back to the path the static rail already walked, so behaviour
  // with an empty context is exactly what shipped before this engine existed.
  var DEFAULT_NEXT = {
    score: "leakage", leakage: "statemap", statemap: "taxlab",
    taxlab: "review", concentration: "leakage"
  };

  function recommend(page) {
    var c = ctx.get() || {};
    var drivers = Array.isArray(c.drivers) ? c.drivers : [];
    var done = Array.isArray(c.done) ? c.done : [];
    var hasHousehold = c.state != null || c.bracket != null || c.portfolio != null;

    var scores = {};
    function bump(k, n) { scores[k] = (scores[k] || 0) + n; }

    drivers.forEach(function (d) {
      var votes = DRIVER_VOTES[d] || {};
      Object.keys(votes).forEach(function (k) { bump(k, votes[k]); });
    });

    // Household signals nudge, they do not decide.
    if (c.portfolio != null) bump("leakage", 1);
    if (c.bracket != null && c.bracket >= 32) bump("taxlab", 1);
    if (c.state != null && c.state !== "" && c.state !== "—") bump("statemap", 1);

    // Never recommend the page the visitor is standing on, and demote what they already finished.
    delete scores[page];
    done.forEach(function (m) { if (scores[m] != null) scores[m] -= 5; });

    var ranked = Object.keys(scores)
      .filter(function (k) { return MODULES[k] && scores[k] > 0; })
      .sort(function (a, b) {
        return (scores[b] - scores[a]) || (MODULES[b].priority - MODULES[a].priority) || (a < b ? -1 : 1);
      });

    // Drivers that no shipped tool answers. Tracked separately so they can never be quietly mapped
    // onto a calculator that only half addresses them.
    var unanswered = drivers.filter(function (d) { return REVIEW_ONLY.indexOf(d) !== -1; });

    var pick = null, why = null;
    if (ranked.length) {
      pick = ranked[0];
      // Name the driver that actually argued for this tool, not merely the first one checked.
      var top = null, best = 0;
      drivers.forEach(function (d) {
        var v = (DRIVER_VOTES[d] || {})[pick] || 0;
        if (v > best) { best = v; top = d; }
      });
      why = top ? "Because " + DRIVER_PHRASE[top] + "." : MODULES[pick].why;
    } else if (!drivers.length && !hasHousehold && page !== "score") {
      pick = "score";                              // cold visitor: teach the system to know them
      why = MODULES.score.why;
    } else if (unanswered.length) {
      // They told us something real and nothing self-serve addresses it. Sending them to whatever
      // tool happens to be next in the default order would be answering a question they did not
      // ask; the honest recommendation is the Review.
      pick = "review";
    } else {
      pick = DEFAULT_NEXT[page] || "review";
      if (pick === page) pick = "review";
      why = MODULES[pick] ? MODULES[pick].why : MODULES.review.why;
    }

    if (pick === "review" && unanswered.length) {
      why = "You flagged " + unanswered.map(function (d) { return DRIVER_PHRASE[d]; }).join(" and ")
          + " — no self-serve analysis covers that. It is a Review conversation.";
    }

    if (!MODULES[pick]) pick = "review";           // never render empty
    var m = MODULES[pick];
    return { key: pick, href: m.href, name: m.name, lead: m.lead, why: why, outcomes: m.outcomes };
  }

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function render() {
    var hosts = document.querySelectorAll("#dw-next");
    if (!hosts.length) return;
    Array.prototype.forEach.call(hosts, function (el) {
      var page = el.getAttribute("data-page") || "";
      var r = recommend(page);
      el.className = "dw-next";
      el.innerHTML =
        '<p class="dwn-k">Your next decision</p>' +
        '<h2 class="dwn-h">' + esc(r.lead) + "</h2>" +
        '<p class="dwn-why">' + esc(r.why) + "</p>" +
        '<p class="dwn-lede">You&rsquo;ll leave with</p>' +
        '<ul class="dwn-out">' + r.outcomes.map(function (o) { return "<li>" + esc(o) + "</li>"; }).join("") + "</ul>" +
        // The action row names the destination once. The headline above already says which module
        // this is, so repeating it here read as a stutter in the rendered card.
        '<div class="onward"><a class="ow-cta" href="' + esc(r.href) + '">Open the ' +
        esc(r.name) + " &rarr;</a></div>";
      var a = el.querySelector(".ow-cta");
      if (a) a.addEventListener("click", function () {
        try { if (window.plausible) plausible("next_decision_click", { props: { from: page || "unknown", to: r.key } }); } catch (e) {}
      });
      // The household may have been set on this very page; re-decorate so the new link carries it.
      try { ctx.decorate(); } catch (e) {}
    });
  }

  window.dwNextBest = { recommend: recommend, render: render, modules: MODULES, driverVotes: DRIVER_VOTES };

  ctx.subscribe(render);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", render);
  else render();
})();

/* Mobile navigation disclosure: progressive enhancement.
 *
 * The shared chrome carries a two-family running index (Understand · Discover). On a phone it wraps
 * to seven rows and pushes the hero and its CTA below the fold. This wires a single disclosure control
 * so the first screen leads with content; the collapse itself is CSS (scoped to .dwnav--menu). It lives
 * here (one file every page already loads) so no per-template markup changes are needed, and it
 * degrades cleanly: with the script absent the full index simply stays visible. */
(function () {
  if (typeof document === "undefined") return;
  function enhance() {
    var navs = document.querySelectorAll("nav.dwnav");
    for (var i = 0; i < navs.length; i++) {
      (function (nav, idx) {
        if (nav.querySelector(".dwnav-toggle")) return;              // already wired
        // The Waterline masthead carries its five Primary words at every width (they wrap to two
        // lines of tracked caps under 860px), so it must never grow a hamburger. 2026 header port.
        // The Phase 2 dropdown masthead (.dwnav--phase2) intentionally keeps the hamburger on phones.
        if (nav.classList.contains("dwnav--waterline")) return;
        var links = nav.querySelector(".dwnav-links");
        if (!links) return;
        if (!links.id) links.id = "dwnav-links-" + (idx + 1);

        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "dwnav-toggle";
        btn.setAttribute("aria-expanded", "false");
        btn.setAttribute("aria-controls", links.id);
        btn.innerHTML = '<span class="bars" aria-hidden="true"></span>' +
                        '<span class="dwnav-toggle-txt">Menu</span>';

        var brand = nav.querySelector(".brand");
        if (brand && brand.nextSibling) nav.insertBefore(btn, brand.nextSibling);
        else nav.insertBefore(btn, nav.firstChild);
        nav.classList.add("dwnav--menu");

        function setOpen(open) {
          nav.classList.toggle("dwnav--open", open);
          btn.setAttribute("aria-expanded", open ? "true" : "false");
          var txt = btn.querySelector(".dwnav-toggle-txt");
          if (txt) txt.textContent = open ? "Close" : "Menu";
        }
        btn.addEventListener("click", function () {
          setOpen(!nav.classList.contains("dwnav--open"));
        });
        // Dismiss on selection, on Escape, and when the viewport grows back to desktop.
        links.addEventListener("click", function (e) { if (e.target.closest && e.target.closest("a")) setOpen(false); });
        document.addEventListener("keydown", function (e) { if (e.key === "Escape" || e.keyCode === 27) setOpen(false); });
        try {
          var mq = window.matchMedia("(min-width:1200px)");
          var onChange = function () { if (mq.matches) setOpen(false); };
          if (mq.addEventListener) mq.addEventListener("change", onChange);
          else if (mq.addListener) mq.addListener(onChange);
        } catch (e) {}
      })(navs[i], i);
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", enhance);
  else enhance();
})();

/* Primary-nav dropdowns (desktop): each .dwnav-drop opens its panel on hover, focus, or click, keeping
 * aria-expanded in sync; one family open at a time; Escape and outside-click close. Progressive
 * enhancement, with JS off the panels are still reachable, and on a phone or tablet the shared hamburger
 * shows every link stacked, so this desktop layer stays out of the way (open() is a no-op below 1200px). */
(function () {
  if (typeof document === "undefined") return;
  function desktop() { try { return window.matchMedia("(min-width:1200px)").matches; } catch (e) { return true; } }
  function enhance() {
    var drops = [].slice.call(document.querySelectorAll(".dwnav-drop"));
    if (!drops.length) return;
    var wired = [];
    drops.forEach(function (drop, i) {
      var trigger = drop.querySelector(".dwnav-trigger");
      var panel = drop.querySelector(".dwnav-panel");
      if (!trigger || !panel) return;
      if (!panel.id) panel.id = "dwnav-panel-" + (i + 1);
      trigger.setAttribute("aria-haspopup", "true");
      trigger.setAttribute("aria-expanded", "false");
      trigger.setAttribute("aria-controls", panel.id);
      function open() { if (!desktop()) return; closeOthers(drop); drop.classList.add("dwnav-drop--open"); trigger.setAttribute("aria-expanded", "true"); }
      function close() { drop.classList.remove("dwnav-drop--open"); trigger.setAttribute("aria-expanded", "false"); }
      drop._close = close;
      trigger.addEventListener("click", function (e) { if (!desktop()) return; e.preventDefault(); if (drop.classList.contains("dwnav-drop--open")) close(); else open(); });
      drop.addEventListener("mouseenter", open);
      drop.addEventListener("mouseleave", function () { if (!drop.contains(document.activeElement)) close(); });
      trigger.addEventListener("keydown", function (e) {
        if (e.key === "Escape" || e.keyCode === 27) { close(); trigger.focus(); }
        else if (e.key === "ArrowDown" || e.key === "Down") { e.preventDefault(); open(); var a = panel.querySelector("a"); if (a) a.focus(); }
      });
      drop.addEventListener("focusout", function (e) { if (!drop.contains(e.relatedTarget)) close(); });
      panel.addEventListener("keydown", function (e) { if (e.key === "Escape" || e.keyCode === 27) { close(); trigger.focus(); } });
      wired.push(drop);
    });
    function closeOthers(except) { wired.forEach(function (d) { if (d !== except && d._close) d._close(); }); }
    document.addEventListener("click", function (e) { if (!(e.target.closest && e.target.closest(".dwnav-drop"))) closeOthers(null); });
    try {
      var mq = window.matchMedia("(max-width:1199px)");
      var onMob = function () { if (mq.matches) closeOthers(null); };
      if (mq.addEventListener) mq.addEventListener("change", onMob); else if (mq.addListener) mq.addListener(onMob);
    } catch (e) {}
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", enhance);
  else enhance();
})();

/* Inline Letter subscribe strip (foot of each essay): post to Web3Forms with no backend, then swap
 * the form for the quiet confirmation. Mirrors the /letter page behaviour; scoped to .essay-sub so it
 * never touches any other form. Progressive enhancement, with JS off the form still submits normally. */
(function () {
  if (typeof document === "undefined") return;
  function enhance() {
    var forms = [].slice.call(document.querySelectorAll(".essay-sub .es-form"));
    forms.forEach(function (f) {
      f.addEventListener("submit", function (e) {
        e.preventDefault();
        var strip = f.closest(".essay-sub");
        var data = new FormData(f);
        fetch("https://api.web3forms.com/submit", { method: "POST", body: data })
          .then(function () { if (strip) strip.classList.add("done"); if (window.plausible) plausible("letter_subscribe"); })
          .catch(function () { if (strip) strip.classList.add("done"); });
      });
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", enhance);
  else enhance();
})();
