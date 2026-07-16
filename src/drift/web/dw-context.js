/* Driftwood: the shared household profile (privacy-first, cross-page).
 *
 * One household (state, federal bracket, and taxable portfolio) set once, in-browser only
 * (localStorage; nothing is ever transmitted), and carried across the three tools that consume it:
 * the Tax Diagnostic, the State Tax Atlas, and the After-Tax Review. It renders as an editable
 * "Your household" bar at the top of each tool: set it anywhere and every tool follows, so the site
 * behaves like one coordinated system rather than three separate calculators.
 *
 * Precedence guardrail: URL search params ALWAYS win. A personalized link
 * (?state=IL&bracket=37&port=2000000) overrides, and refreshes, whatever this browser had stored.
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

  function read() {
    try { var v = JSON.parse(localStorage.getItem(KEY) || "null"); return v && typeof v === "object" ? v : {}; }
    catch (e) { return {}; }
  }
  function write(ctx) { try { localStorage.setItem(KEY, JSON.stringify(ctx)); } catch (e) {} }
  function notify(c) { subs.forEach(function (fn) { try { fn(c); } catch (e) {} }); }

  function clean(patch, c) {
    if (patch && patch.state != null) {
      var s = String(patch.state).toUpperCase();
      if (s === "—" || /^[A-Z]{2,3}$/.test(s)) c.state = s;
    }
    if (patch && patch.bracket != null && patch.bracket !== "") {
      var b = parseInt(patch.bracket, 10); if (b >= 10 && b <= 60) c.bracket = b;
    }
    if (patch && patch.portfolio != null && patch.portfolio !== "") {
      var p = Math.round(Number(patch.portfolio)); if (isFinite(p) && p >= 0 && p <= 1e11) c.portfolio = p;
    }
    return c;
  }

  // 1 · Merge URL params into storage (URL wins).
  var qp, ctx = read(), dirty = false;
  try { qp = new URLSearchParams(location.search); } catch (e) { qp = null; }
  if (qp) {
    var before = JSON.stringify(ctx);
    ctx = clean({ state: qp.get("state"), bracket: qp.get("bracket"), portfolio: qp.get("port") || qp.get("portfolio") }, ctx);
    dirty = JSON.stringify(ctx) !== before;
  }
  if (dirty) write(ctx);

  // 2 · Decorate same-directory links to the consuming tools so the household follows the visitor.
  var CONSUMERS = [
    { prefix: "taxlab.html", params: ["state", "bracket", "port"] },
    { prefix: "leakage.html", params: ["state", "port"] },
    { prefix: "statemap.html", params: ["state"] }
  ];
  function paramVal(k, c) { return k === "port" ? c.portfolio : c[k]; }
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
    if (c.state == null && c.bracket == null && c.portfolio == null) return;
    CONSUMERS.forEach(function (t) {
      var links = document.querySelectorAll('a[href^="' + t.prefix + '"]');
      for (var i = 0; i < links.length; i++) links[i].setAttribute("href", withContext(links[i].getAttribute("href"), t.params, c));
    });
  }

  // 3 · The editable "Your household" bar. A tool mounts it by placing
  //     <div id="dw-household" data-page="taxlab|statemap|leakage"></div> after its nav.
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
  var SIBLINGS = {
    taxlab: [{ href: "leakage.html", label: "Tax Diagnostic →" }, { href: "statemap.html", label: "State Atlas →" }],
    statemap: [{ href: "leakage.html", label: "Tax Diagnostic →" }, { href: "taxlab.html", label: "After-Tax Review →" }],
    leakage: [{ href: "taxlab.html", label: "After-Tax Review →" }, { href: "statemap.html", label: "State Atlas →" }]
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
        '<span class="note">Set once, carried across the Tax Diagnostic, State Atlas, and After-Tax Review. Saved in this browser only, never transmitted.</span>';
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

  // 4 · Public API.
  var api = window.dwTaxContext = {
    get: read,
    save: function (patch) { var c = clean(patch, read()); write(c); decorate(); renderBars(); notify(c); },
    reset: function () { try { localStorage.removeItem(KEY); } catch (e) {} decorate(); renderBars(); notify({}); },
    subscribe: function (fn) { if (typeof fn === "function") subs.push(fn); },
    decorate: decorate, mountBar: renderBars
  };

  // Cross-tab sync.
  try { window.addEventListener("storage", function (e) { if (e.key === KEY) { decorate(); renderBars(); notify(read()); } }); } catch (e) {}

  function ready() { decorate(); renderBars(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", ready); else ready();
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
          var mq = window.matchMedia("(min-width:621px)");
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
