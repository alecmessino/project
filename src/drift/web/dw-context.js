/* Driftwood — privacy-first cross-page tax context.
 *
 * Remembers the visitor's state + federal bracket in THIS browser only (localStorage; nothing is
 * ever transmitted) so their personalization follows them between the Tax Lab, the Leakage
 * Diagnostic, and the rest of the site via decorated nav links.
 *
 * Precedence guardrail: URL search params ALWAYS win. A personalized link (?state=IL&bracket=37)
 * overrides — and refreshes — whatever this browser had stored, so a custom link a prospect was
 * sent never loses to a stale local context.
 */
(function () {
  var KEY = "dw_tax_context";

  function read() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY) || "null");
      return v && typeof v === "object" ? v : {};
    } catch (e) { return {}; }
  }
  function write(ctx) {
    try { localStorage.setItem(KEY, JSON.stringify(ctx)); } catch (e) { /* private mode */ }
  }

  // 1 · Merge URL params into storage (URL wins — see guardrail above).
  var qp, ctx = read(), dirty = false;
  try { qp = new URLSearchParams(location.search); } catch (e) { qp = null; }
  if (qp) {
    var uState = (qp.get("state") || "").toUpperCase();
    if (/^[A-Z]{2,3}$/.test(uState) && uState !== ctx.state) { ctx.state = uState; dirty = true; }
    var uBracket = parseInt(qp.get("bracket"), 10);
    if (uBracket >= 10 && uBracket <= 60 && uBracket !== ctx.bracket) { ctx.bracket = uBracket; dirty = true; }
  }
  if (dirty) write(ctx);

  // 2 · Decorate same-directory links to the pages that consume the context, so it follows the
  //     visitor around the site. Never override a param a link already carries explicitly.
  var CONSUMERS = [
    { prefix: "taxlab.html",  params: ["state", "bracket"] },
    { prefix: "leakage.html", params: ["state"] }
  ];
  function withContext(href, keys, c) {
    try {
      var u = new URL(href, location.href), changed = false;
      keys.forEach(function (k) {
        if (c[k] != null && !u.searchParams.has(k)) { u.searchParams.set(k, c[k]); changed = true; }
      });
      if (!changed) return href;
      return u.pathname.split("/").pop() + u.search + u.hash;
    } catch (e) { return href; }
  }
  function decorate() {
    var c = read();
    if (c.state == null && c.bracket == null) return;
    CONSUMERS.forEach(function (t) {
      var links = document.querySelectorAll('a[href^="' + t.prefix + '"]');
      for (var i = 0; i < links.length; i++) {
        links[i].setAttribute("href", withContext(links[i].getAttribute("href"), t.params, c));
      }
    });
  }

  // 3 · Small API for page scripts (the Tax Lab saves on every state/bracket selection).
  //     save() sanitizes: state must look like a code (IL / NYC), bracket a plausible federal %.
  window.dwTaxContext = {
    get: read,
    save: function (patch) {
      var c = read();
      if (patch && patch.state != null) {
        var s = String(patch.state).toUpperCase();
        if (/^[A-Z]{2,3}$/.test(s)) c.state = s;
      }
      if (patch && patch.bracket != null) {
        var b = parseInt(patch.bracket, 10);
        if (b >= 10 && b <= 60) c.bracket = b;
      }
      write(c);
      decorate();
    },
    decorate: decorate
  };

  // This file loads synchronously in <head> so page scripts can call save()/get() during parse;
  // link decoration waits for the DOM (which also catches the hub's inline-rendered exhibit links).
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", decorate);
  } else {
    decorate();
  }
})();
