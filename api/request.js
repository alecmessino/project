// POST /api/request — one artifact, once.
//
// This is the TRANSACTIONAL path and it is deliberately not the subscription path. A reader who
// asks for a specimen memorandum has consented to receive that memorandum and nothing else.
// Keeping the two endpoints apart is what makes that promise keepable: there is no code here that
// can add anyone to a list. If a reader also wants the publication, the form asks separately and
// the browser calls /api/subscribe, so each consent is recorded against the thing it was given for.
//
// Postmark rather than Buttondown for this leg because the two message classes should not share a
// reputation or a stream: a confirmation someone is waiting for must not queue behind a broadcast,
// and a compliance review reads better when advertising and transactional mail are separable.

import { env, looksLikeEmail, readJson, tooFast, clientKey, send, fromOurSite, isBot, consentRecord }
  from "./_lib.js";

const SITE = "https://driftwoodwealth.com";

// Every artifact a reader may ask for, and the page it actually lives on.
//
// The URL is verified against the built site by tests/test_capture_endpoints.py, so this map cannot
// name a document that does not exist. A link in a Driftwood email that 404s costs more than the
// document was worth.
const ARTIFACTS = {
  "coordination-report": {
    name: "The Coordination Report",
    href: `${SITE}/ic-memo.html`,
    line: "A specimen memorandum: what was observed in each system, the consequence of each, and who owns its resolution.",
  },
  "opportunity-register": {
    name: "The Opportunity Register",
    href: `${SITE}/opportunity-register.html`,
    line: "A specimen register: every open matter with a status, an owner, and its dependency.",
  },
  "operating-manual": {
    name: "The Wealth Operating Manual",
    href: `${SITE}/manual.html`,
    line: "The written operating system for a household: every decision, its rationale, and the conditions that would reopen it.",
  },
  "transition-plan": {
    name: "A 90-Day Transition Plan",
    href: `${SITE}/transition-plan.html`,
    line: "A specimen plan: the first owned decisions, sequenced, each with a date it closes.",
  },
};

/**
 * The Atlas pages ask for something none of the fixed artifacts above can be: a brief about the
 * reader's own state. The honest state-specific thing Driftwood can send automatically, today, is
 * the Tax Diagnostic already pointed at that state — so that is what this sends, rather than
 * promising a bespoke document that a person would have to write by hand for each of fifty-one
 * states. The follow-up is still promised, because a person really does follow up; what changed is
 * that the reader now gets something in the meantime instead of only a promise.
 */
function stateBrief(code) {
  if (!/^[A-Z]{2}$/.test(code)) return null;
  return {
    name: `Your ${code} tax picture`,
    href: `${SITE}/leakage.html?state=${code}`,
    line: `The Tax Diagnostic, set to ${code}: where return is lost to tax in your state, on your own bracket and holdings. It runs in your browser and nothing is sent anywhere.`,
  };
}

/** Plain text, deliberately. A one-link note from a person reads as a person; a designed template
 *  with a hero image reads as a campaign, and this message is neither. */
function bodyText(a) {
  return [
    `Here is ${a.name}, as requested.`,
    "",
    a.line,
    "",
    a.href,
    "",
    "This is a specimen prepared on an illustrative household, not advice, and not a recommendation.",
    "If it raises a question about your own situation, reply to this message and it reaches me directly.",
    "",
    "Alec Messino",
    "Driftwood Wealth",
    "Chicago, Illinois",
    "(708) 548-7600",
    "",
    "Educational and illustrative, not investment, tax, or legal advice. Securities products and",
    "advisory services offered through Park Avenue Securities LLC (PAS), member FINRA, SIPC.",
    "Alec Messino is a Registered Representative and Financial Advisor of PAS and a Financial",
    "Representative of The Guardian Life Insurance Company of America (Guardian), New York, NY.",
    "PAS is a wholly owned subsidiary of Guardian. Driftwood Wealth is not an affiliate or",
    "subsidiary of PAS or Guardian.",
    "",
    "You received this message because you requested this document at driftwoodwealth.com.",
    "It is a one-time send and does not subscribe you to anything.",
  ].join("\n");
}

async function postmark(payload) {
  const token = env("POSTMARK_SERVER_TOKEN");
  if (!token) return { ok: false, status: 503 };
  const r = await fetch("https://api.postmarkapp.com/email", {
    method: "POST",
    headers: {
      "X-Postmark-Server-Token": token,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  }).catch(() => null);
  return { ok: Boolean(r && r.ok), status: r ? r.status : 502 };
}

export default async function handler(req, res) {
  if (req.method !== "POST") return send(res, 405, { ok: false, error: "method_not_allowed" });
  if (!fromOurSite(req)) return send(res, 403, { ok: false, error: "forbidden" });

  const from = env("POSTMARK_FROM");
  if (!from) return send(res, 503, { ok: false, error: "not_configured" });

  let body;
  try {
    body = await readJson(req);
  } catch {
    return send(res, 400, { ok: false, error: "bad_request" });
  }

  if (isBot(body)) return send(res, 200, { ok: true });

  const email = String(body.email || "").trim().toLowerCase();
  if (!looksLikeEmail(email)) return send(res, 400, { ok: false, error: "bad_email" });

  const slug = String(body.artifact || "");
  const artifact = slug === "state-brief"
    ? stateBrief(String(body.state || "").toUpperCase())
    : ARTIFACTS[slug];
  if (!artifact) return send(res, 400, { ok: false, error: "unknown_artifact" });

  if (tooFast(clientKey(req))) return send(res, 429, { ok: false, error: "slow_down" });

  const sent = await postmark({
    From: from,
    To: email,
    ReplyTo: "alec@driftwoodwealth.com",
    Subject: `${artifact.name}, as requested`,
    TextBody: bodyText(artifact),
    MessageStream: "outbound",             // transactional stream, never the broadcast stream
    Tag: "artifact-request",
    Metadata: consentRecord(body, req, "request"),
  });

  if (!sent.ok) return send(res, 502, { ok: false, error: "send_failed" });

  // Tell the principal, and do not let that failing cost the reader their document. A solo practice
  // wants to know a stranger asked for a specimen memorandum; the reader's copy is what matters.
  await postmark({
    From: from,
    To: "alec@driftwoodwealth.com",
    Subject: `Requested: ${artifact.name}`,
    TextBody: `${email} requested ${artifact.name} from ${String(body.source || "the site")}.`,
    MessageStream: "outbound",
    Tag: "artifact-request-notice",
  }).catch(() => null);

  return send(res, 200, { ok: true });
}
