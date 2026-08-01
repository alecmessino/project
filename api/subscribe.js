// POST /api/subscribe — the ongoing publication.
//
// This is the COMMERCIAL path: a recurring send, so it needs real consent, an unsubscribe link on
// every issue, and a list that honours it. Buttondown holds all three, which is the reason it is
// here rather than a table in this repo: an address Driftwood stores itself is an address Driftwood
// has to be able to delete, export, and prove consent for. Letting the provider own that is fewer
// promises to keep.
//
// DOUBLE OPT-IN IS DELIBERATE. Subscribers are created unactivated, so Buttondown sends its own
// confirmation and nothing goes out until the reader clicks it. A single opt-in list is marginally
// larger and materially worse: it accumulates addresses that never asked, which is exactly the
// complaint that damages a sending domain, and this domain also carries the firm's client mail.

import { env, looksLikeEmail, readJson, tooFast, clientKey, send, fromOurSite, isBot, consentRecord }
  from "./_lib.js";

// The publications a reader may subscribe to. A topic that is not in this map is rejected — the
// endpoint will not create a list for a publication that does not exist, which is the "no
// placeholders ship" rule applied to email. Add a row the day the publication is real.
const TOPICS = {
  "driftwood-review": "The Driftwood Review",
  "research": "Research",
  "commentary": "Commentary",
};

export default async function handler(req, res) {
  if (req.method !== "POST") return send(res, 405, { ok: false, error: "method_not_allowed" });
  if (!fromOurSite(req)) return send(res, 403, { ok: false, error: "forbidden" });

  const key = env("BUTTONDOWN_API_KEY");
  if (!key) return send(res, 503, { ok: false, error: "not_configured" });

  let body;
  try {
    body = await readJson(req);
  } catch {
    return send(res, 400, { ok: false, error: "bad_request" });
  }

  // Answer a bot exactly as we answer a person. Telling it that it was caught only teaches it.
  if (isBot(body)) return send(res, 200, { ok: true });

  const email = String(body.email || "").trim().toLowerCase();
  if (!looksLikeEmail(email)) return send(res, 400, { ok: false, error: "bad_email" });

  const topic = String(body.topic || "driftwood-review");
  if (!TOPICS[topic]) return send(res, 400, { ok: false, error: "unknown_topic" });

  if (tooFast(clientKey(req))) return send(res, 429, { ok: false, error: "slow_down" });

  const r = await fetch("https://api.buttondown.email/v1/subscribers", {
    method: "POST",
    headers: { Authorization: `Token ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      email_address: email,
      type: "unactivated",                 // Buttondown sends the confirmation; see the note above
      tags: [topic],
      metadata: consentRecord(body, req, "subscribe"),
    }),
  }).catch(() => null);

  if (!r) return send(res, 502, { ok: false, error: "upstream_unreachable" });

  // An address already on the list is a success from the reader's point of view. They asked to be
  // subscribed and they are subscribed; surfacing "you already exist" tells a stranger who else is
  // on the list, one address at a time.
  if (r.status === 201 || r.status === 200) return send(res, 200, { ok: true });
  if (r.status === 400 || r.status === 409) {
    const detail = await r.text().catch(() => "");
    if (/already|exists|duplicate/i.test(detail)) return send(res, 200, { ok: true });
    return send(res, 400, { ok: false, error: "rejected" });
  }
  return send(res, 502, { ok: false, error: "upstream_error" });
}
