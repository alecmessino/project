// Shared guts for the two capture endpoints. Kept deliberately small: this is the only server-side
// code in an otherwise static site, and every line of it handles a stranger's email address.
//
// WHY THERE IS A SERVER AT ALL. driftwoodwealth.com is a static build (docs/ on Pages, mirrored on
// Vercel). Until now the one capture form on the site posted straight from the browser to
// api.web3forms.com with its access key in plain sight in the HTML — which meant a third party
// held the addresses, the key was public, and there was no record of what anyone consented to.
// These two functions exist so the address goes to a provider Driftwood controls, under a key that
// never reaches the browser, with the consent written down.

const MAX_BODY = 4096; // an email address and a topic; anything larger is not a real submission.

/** Providers are read at call time, never at import time, so a missing key fails one request
 *  rather than crashing the whole function on cold start. */
export function env(name) {
  const v = process.env[name];
  return typeof v === "string" && v.trim() ? v.trim() : null;
}

/** Deliberately permissive. Address validation by regex is a losing game — the provider does the
 *  real check, and the only job here is to reject obvious junk before spending an API call. */
export function looksLikeEmail(s) {
  if (typeof s !== "string") return false;
  const v = s.trim();
  return v.length >= 6 && v.length <= 254 && /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v);
}

/** Read and size-cap the JSON body. Vercel parses JSON for us when the content-type is right, but
 *  a hand-rolled POST may not set it, and an unbounded read is a free denial-of-service. */
export async function readJson(req) {
  if (req.body && typeof req.body === "object") return req.body;
  let raw = "";
  for await (const chunk of req) {
    raw += chunk;
    if (raw.length > MAX_BODY) throw new Error("body too large");
  }
  try {
    return raw ? JSON.parse(raw) : {};
  } catch {
    throw new Error("body is not JSON");
  }
}

/** One shared in-memory bucket per warm instance. This is NOT a real rate limiter — serverless
 *  instances are ephemeral and there may be many at once — it is a cheap brake on a single client
 *  hammering one instance. Real abuse protection is the provider's and Vercel's job; saying so
 *  here so nobody mistakes this for the thing it resembles. */
const seen = new Map();
export function tooFast(key, windowMs = 60_000, limit = 5) {
  const now = Date.now();
  const hits = (seen.get(key) || []).filter((t) => now - t < windowMs);
  hits.push(now);
  seen.set(key, hits);
  if (seen.size > 5000) seen.clear(); // bound the map; correctness does not depend on its contents
  return hits.length > limit;
}

export function clientKey(req) {
  const fwd = req.headers["x-forwarded-for"];
  return (Array.isArray(fwd) ? fwd[0] : fwd || "").split(",")[0].trim() || "unknown";
}

/** Same shape for every response so the browser handler has exactly one contract to code against. */
export function send(res, status, body) {
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  res.status(status).json(body);
}

/**
 * The one guard that must never regress: a submission is only accepted from the site itself.
 *
 * Without this the endpoint is an open relay for sending Driftwood-branded mail to any address
 * anyone chooses, which is both an abuse vector and a compliance problem, because every message it
 * sends is an advertising communication by a registered representative.
 */
const ALLOWED = [
  "https://driftwoodwealth.com",
  "https://www.driftwoodwealth.com",
];

export function fromOurSite(req) {
  const origin = req.headers.origin || "";
  if (ALLOWED.includes(origin)) return true;
  // Vercel preview deployments are legitimate and have generated hostnames.
  if (/^https:\/\/[a-z0-9-]+\.vercel\.app$/.test(origin)) return true;
  // Some browsers omit Origin on same-origin POSTs; fall back to the referer's origin.
  try {
    const ref = new URL(req.headers.referer || "");
    return ALLOWED.includes(ref.origin) || /\.vercel\.app$/.test(ref.hostname);
  } catch {
    return false;
  }
}

/** A honeypot field the CSS hides and a human never fills. Bots fill everything. */
export function isBot(body) {
  return Boolean(body && typeof body.botcheck === "string" && body.botcheck.trim());
}

/**
 * The consent record.
 *
 * This is the part that exists for the compliance file rather than for the feature. Whenever
 * Driftwood is asked to show that a given address asked to hear from it, the answer has to be a
 * record made at the time, not a recollection. Provider metadata is where it lives, because the
 * provider is also what holds the address.
 */
export function consentRecord(body, req, kind) {
  return {
    consent_kind: kind,                          // "subscribe" (ongoing) or "request" (one artifact)
    consent_text: String(body.consent_text || "").slice(0, 500),
    source_page: String(body.source || "").slice(0, 120),
    submitted_at: new Date().toISOString(),
    ip_country: String(req.headers["x-vercel-ip-country"] || ""),
    user_agent: String(req.headers["user-agent"] || "").slice(0, 200),
  };
}
