/* dw-capture.js — the browser half of the two capture endpoints.
 *
 * Progressive enhancement over a real <form>. The markup it upgrades posts to /api/subscribe or
 * /api/request on its own if this file never loads, so a reader with a blocked script still gets
 * their document; what this adds is submitting without leaving the page, and honest error states.
 *
 * WHAT IT REPLACED. Until 2026-08-01 the subscribe strip on three essay pages posted straight from
 * the browser to api.web3forms.com with the access key visible in the page source. That meant a
 * third party held every address, the key was public, the reader was told nothing about what they
 * had joined, and there was no record of consent. It also subscribed people to "The Driftwood
 * Letter", which had by then been renamed The Driftwood Review.
 *
 * ONE RULE WORTH KEEPING: the two endpoints are called separately, never chained server-side. A
 * reader who requests a document has consented to that document. If they also tick the box for the
 * publication, that is a second consent and it makes its own request, so each is recorded against
 * the thing it was actually given for.
 */
(function () {
  "use strict";

  var BUSY = "is-busy", DONE = "done", FAIL = "is-error";

  function consentTextFor(form) {
    // The exact words shown next to the control the reader operated. Recorded verbatim, because
    // "they consented" is only meaningful alongside what they were told they were consenting to.
    var fine = form.parentNode.querySelector(".es-fine, .cap-fine");
    return fine ? fine.textContent.replace(/\s+/g, " ").trim().slice(0, 500) : "";
  }

  function post(url, payload) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(function (r) {
      return r.json().catch(function () { return { ok: false, error: "bad_response" }; });
    });
  }

  function message(res) {
    if (!res || res.ok) return "";
    if (res.error === "bad_email") return "That address does not look right. Try again?";
    if (res.error === "slow_down") return "Give that a moment, then try once more.";
    if (res.error === "not_configured") return "Sending is not switched on yet. Write to alec@driftwoodwealth.com.";
    // Anything else is ours, not the reader's, and should not be dressed up as their mistake.
    return "That did not go through. Write to alec@driftwoodwealth.com and it reaches me directly.";
  }

  function wire(form) {
    if (form.getAttribute("data-dw-wired")) return;
    form.setAttribute("data-dw-wired", "1");

    var shell = form.closest(".essay-sub, .dw-capture") || form.parentNode;
    var errEl = shell.querySelector(".es-err, .cap-err");

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (shell.classList.contains(BUSY)) return;

      var data = new FormData(form);
      var email = String(data.get("email") || "").trim();
      var botcheck = String(data.get("botcheck") || "");
      var artifact = form.getAttribute("data-artifact");
      var topic = form.getAttribute("data-topic") || "driftwood-review";

      shell.classList.remove(FAIL);
      shell.classList.add(BUSY);
      if (errEl) errEl.textContent = "";

      var base = {
        email: email,
        botcheck: botcheck,
        source: (location.pathname.split("/").pop() || "index.html"),
        consent_text: consentTextFor(form),
      };

      var first = artifact
        ? post("/api/request", Object.assign({ artifact: artifact }, base))
        : post("/api/subscribe", Object.assign({ topic: topic }, base));

      first.then(function (res) {
        // The second, separate consent. Only fires if the reader ticked it themselves.
        var also = form.querySelector('input[name="also_subscribe"]');
        if (res && res.ok && artifact && also && also.checked) {
          return post("/api/subscribe", Object.assign({ topic: topic }, base)).then(function () {
            return res;
          });
        }
        return res;
      }).then(function (res) {
        shell.classList.remove(BUSY);
        if (res && res.ok) {
          shell.classList.add(DONE);
          var ok = shell.querySelector(".es-ok, .cap-ok");
          if (ok) { ok.setAttribute("role", "status"); ok.focus && ok.focus(); }
        } else {
          shell.classList.add(FAIL);
          if (errEl) errEl.textContent = message(res);
        }
      }).catch(function () {
        shell.classList.remove(BUSY);
        shell.classList.add(FAIL);
        if (errEl) errEl.textContent = message(null);
      });
    });
  }

  function init() {
    var forms = document.querySelectorAll(".es-form, .cap-form");
    for (var i = 0; i < forms.length; i++) wire(forms[i]);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
