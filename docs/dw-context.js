/* Driftwood — the shared household profile (privacy-first, cross-page).
 *
 * One household — state, federal bracket, and taxable portfolio — remembered in THIS browser only
 * (localStorage; nothing is ever transmitted) and carried across the three tools that consume it:
 * the After-Tax Review, the State Tax Atlas, and the Tax Diagnostic. Set it once in any tool and it
 * follows you to the others, so the site reads as one coordinated plan rather than three separate
 * calculators.
 *
 * Precedence guardrail: URL search params ALWAYS win. A personalized link (?state=IL&bracket=37&port=2000000)
 * overrides — and refreshes — whatever this browser had stored, so a custom link a prospect was sent
 * never loses to a stale local context.
 */
(function () {
  var KEY = "dw_tax_context";
  var subs = [];

  function read() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY) || "null");
      return v && typeof v === "object" ? v : {};
    } catch (e) { return {}; }
  }
  function write(ctx) {
    try { localStorage.setItem(KEY, JSON.stringify(ctx)); } catch (e) { /* private mode */ }
  }
  function notify(c) { subs.forEach(function (fn) { try { fn(c); } catch (e) {} }); }

  // Field validators — keep the store clean regardless of who writes to it.
  function clean(patch, c) {
    if (patch && patch.state != null) {
      var s = String(patch.state).toUpperCase();
      if (/^[A-Z]{2,3}$/.test(s)) c.state = s;
    }
    if (patch && patch.bracket != null) {
      var b = parseInt(patch.bracket, 10);
      if (b >= 10 && b <= 60) c.bracket = b;
    }
    if (patch && patch.portfolio != null) {
      var p = Math.round(Number(patch.portfolio));
      if (isFinite(p) && p >= 0 && p <= 1e11) c.portfolio = p;
    }
    return c;
  }

  // 1 · Merge URL params into storage (URL wins — see guardrail above).
  var qp, ctx = read(), dirty = false;
  try { qp = new URLSearchParams(location.search); } catch (e) { qp = null; }
  if (qp) {
    var before = JSON.stringify(ctx);
    ctx = clean({
      state: qp.get("state"),
      bracket: qp.get("bracket"),
      portfolio: qp.get("port") || qp.get("portfolio")
    }, ctx);
    dirty = JSON.stringify(ctx) !== before;
  }
  if (dirty) write(ctx);

  // 2 · Decorate same-directory links to the consuming tools, so the household follows the visitor
  //     around the site. Never override a param a link already carries explicitly.
  var CONSUMERS = [
    { prefix: "taxlab.html",  params: ["state", "bracket", "port"] },
    { prefix: "leakage.html", params: ["state", "port"] },
    { prefix: "statemap.html", params: ["state"] }
  ];
  function paramVal(k, c) { return k === "port" ? c.portfolio : c[k]; }
  function withContext(href, keys, c) {
    try {
      var u = new URL(href, location.href), changed = false;
      keys.forEach(function (k) {
        var v = paramVal(k, c);
        if (v != null && !u.searchParams.has(k)) { u.searchParams.set(k, v); changed = true; }
      });
      if (!changed) return href;
      return u.pathname.split("/").pop() + u.search + u.hash;
    } catch (e) { return href; }
  }
  function decorate() {
    var c = read();
    if (c.state == null && c.bracket == null && c.portfolio == null) return;
    CONSUMERS.forEach(function (t) {
      var links = document.querySelectorAll('a[href^="' + t.prefix + '"]');
      for (var i = 0; i < links.length; i++) {
        links[i].setAttribute("href", withContext(links[i].getAttribute("href"), t.params, c));
      }
    });
  }

  // 3 · The visible "Your household" bar — a slim, hairline strip a tool mounts by placing
  //     <div id="dw-household" data-page="taxlab|statemap|leakage"></div> after its nav. It makes the
  //     shared context legible ("CA · 37% · $2.0M, carried across the Review, Atlas & Diagnostic") and
  //     links to the sibling tools, each carrying the household forward.
  var CSS = ""
    + ".dw-household{font-family:var(--sans);background:var(--soft);border-bottom:1px solid var(--line);"
    + "padding:9px 24px;display:flex;align-items:center;gap:8px 18px;flex-wrap:wrap;font-size:12px;color:var(--dim)}"
    + ".dw-household .lbl{font-weight:700;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent-strike)}"
    + ".dw-household .facts{display:flex;gap:7px 16px;flex-wrap:wrap;align-items:baseline}"
    + ".dw-household .f b{color:var(--ink);font-weight:700;font-variant-numeric:tabular-nums}"
    + ".dw-household .f .k{color:var(--muted);text-transform:uppercase;letter-spacing:.08em;font-size:10px;margin-right:5px}"
    + ".dw-household .sep{color:var(--line)}"
    + ".dw-household .links{margin-left:auto;display:flex;gap:14px;flex-wrap:wrap}"
    + ".dw-household .links a{color:var(--teal2);text-decoration:none;font-weight:600}"
    + ".dw-household .links a:hover{color:var(--ink)}"
    + ".dw-household .note{width:100%;color:var(--muted);font-size:10.5px;letter-spacing:.01em}"
    + ".dw-household.empty .facts{color:var(--muted)}"
    + "@media(max-width:620px){.dw-household{padding:9px 16px}.dw-household .links{margin-left:0;width:100%}}";
  var styled = false;
  function injectCss() {
    if (styled || typeof document === "undefined") return;
    styled = true;
    var s = document.createElement("style"); s.dataset.dw = "household"; s.textContent = CSS;
    document.head.appendChild(s);
  }
  function fmtMoney(n) {
    if (n == null) return null;
    if (n >= 1e6) return "$" + (n / 1e6).toFixed(n % 1e6 === 0 ? 0 : 2).replace(/\.?0+$/, "") + "M";
    if (n >= 1e3) return "$" + Math.round(n / 1e3) + "k";
    return "$" + n;
  }
  var SIBLINGS = {
    taxlab:   [{ href: "statemap.html", label: "State Atlas →" }, { href: "leakage.html", label: "Tax Diagnostic →" }],
    statemap: [{ href: "taxlab.html", label: "After-Tax Review →" }, { href: "leakage.html", label: "Tax Diagnostic →" }],
    leakage:  [{ href: "taxlab.html", label: "After-Tax Review →" }, { href: "statemap.html", label: "State Atlas →" }]
  };
  function esc(s) { return String(s).replace(/[&<>"]/g, function (m) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[m]; }); }
  function renderBars() {
    var hosts = document.querySelectorAll("#dw-household");
    if (!hosts.length) return;
    injectCss();
    var c = read();
    var has = c.state != null || c.bracket != null || c.portfolio != null;
    hosts.forEach(function (el) {
      var page = el.getAttribute("data-page") || "taxlab";
      var facts = "";
      if (has) {
        var parts = [];
        if (c.state != null) parts.push('<span class="f"><span class="k">State</span><b>' + esc(c.state) + "</b></span>");
        if (c.bracket != null) parts.push('<span class="f"><span class="k">Federal</span><b>' + esc(c.bracket) + "%</b></span>");
        if (c.portfolio != null) parts.push('<span class="f"><span class="k">Portfolio</span><b>' + esc(fmtMoney(c.portfolio)) + "</b></span>");
        facts = parts.join('<span class="sep">·</span>');
      } else {
        facts = "Set your state, bracket, and portfolio in any tool — it will follow you here.";
      }
      var sibs = (SIBLINGS[page] || []).map(function (s) {
        return '<a href="' + s.href + '">' + s.label + "</a>";
      }).join("");
      el.className = "dw-household" + (has ? "" : " empty");
      el.innerHTML =
        '<span class="lbl">Your household</span>' +
        '<span class="facts">' + facts + "</span>" +
        '<span class="links">' + sibs + "</span>" +
        (has ? '<span class="note">Carried across the After-Tax Review, State Atlas, and Tax Diagnostic — saved in this browser only, never transmitted.</span>' : "");
      // decorate the freshly-written sibling links with the current context
      decorate();
    });
  }

  // 4 · Public API for page scripts.
  window.dwTaxContext = {
    get: read,
    save: function (patch) {
      var c = clean(patch, read());
      write(c);
      decorate();
      renderBars();
      notify(c);
    },
    subscribe: function (fn) { if (typeof fn === "function") subs.push(fn); },
    decorate: decorate,
    mountBar: renderBars,
    fmtMoney: fmtMoney
  };

  // Cross-tab: if another tab changes the household, refresh links + bar here.
  try {
    window.addEventListener("storage", function (e) { if (e.key === KEY) { decorate(); renderBars(); notify(read()); } });
  } catch (e) {}

  // This file loads synchronously in <head> so page scripts can call save()/get() during parse; link
  // decoration and the household bar wait for the DOM.
  function ready() { decorate(); renderBars(); }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ready);
  } else {
    ready();
  }
})();
