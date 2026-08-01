# Outbound email

Two endpoints, two providers, two kinds of consent. Nothing sends until the steps in
**Switching it on** are done; until then both endpoints answer `503 not_configured` and the forms
tell the reader to write to `alec@driftwoodwealth.com` instead. That is the intended failure mode.

## The two paths, and why they are not one

| | `/api/request` | `/api/subscribe` |
|---|---|---|
| Kind | Transactional | Commercial, recurring |
| Sends | One artifact, once | The publication, quarterly |
| Provider | Postmark (`outbound` stream) | Buttondown |
| Consent | The request itself | Double opt-in, confirmed by the reader |
| Unsubscribe | Not applicable | Required on every issue |

They are separate on purpose. A reader who asks for a specimen memorandum has consented to that
memorandum and nothing else, and `tests/test_capture_endpoints.py` fails if `request.js` ever gains
the ability to add someone to the list. When a form offers both, the browser makes two calls, so
each consent is recorded against the thing it was actually given for.

## What replaced what

Until 2026-08-01 the site had a **live** capture on 55 built pages — three essay strips and all 51
Atlas pages — posting from the browser to `api.web3forms.com` with its access key inline in the
HTML. A third party held every address, the key was readable in page source, nothing recorded what
anyone agreed to, and the essay handler in `dw-context.js` added its success class inside its own
`.catch`, so a reader whose subscription failed was still shown the confirmation. The forms also
subscribed people to *The Driftwood Letter*, a publication that had been renamed The Driftwood
Review. Two test files asserted parts of that arrangement were correct, which is why it survived.

## The blocker, before any of the rest

**`driftwoodwealth.com` is served by GitHub Pages, so `/api/subscribe` and `/api/request` cannot
run.** Verified 2026-08-01: the apex A records are `185.199.108-111.153` (GitHub's anycast range)
and the response carries `server: GitHub.com`. A POST to `/api/subscribe` returns 405 because Pages
answers GET and HEAD only. That 405 is Pages refusing the method, not the function replying.

The repo already deploys to Vercel (`vercel.json`, `outputDirectory: docs`), so Vercel can serve the
same static build **and** the functions. Pick one:

**A. Point the domain at Vercel.** Add the domain in the Vercel project, then replace the four
GitHub A records in Cloudflare with the record Vercel shows for an apex (currently an A to
`76.76.21.21` — confirm in the dashboard rather than trusting this line). One platform, one origin,
no CORS. Recommended.

**B. Keep Pages, put the API on a subdomain.** `api.driftwoodwealth.com` CNAME to Vercel. The forms
then post cross-origin, so `_lib.js` needs CORS preflight handling and `ALLOWED` needs the subdomain.
More moving parts for no benefit unless Pages is doing something Vercel is not.

**C. Cloudflare Workers.** A Worker route on `driftwoodwealth.com/api/*` would intercept before
Pages, and Workers Routes is already in the sidebar. It requires turning the orange-cloud proxy on
(the records resolve to GitHub's real IPs today, so the zone is DNS-only and no Worker route fires)
and rewriting both handlers to the Workers runtime. Only worth it to consolidate on Cloudflare.

Nothing below matters until this is settled, because the forms have nowhere to post.

## Switching it on

### 1. What is already correct

| Record | Current value | Verdict |
|---|---|---|
| NS | `clark.ns.cloudflare.com`, `erin.ns.cloudflare.com` | Cloudflare is authoritative |
| MX | `route1/2/3.mx.cloudflare.net` | Cloudflare Email Routing, inbound forwarding only |
| DMARC | `v=DMARC1; p=none; rua=mailto:dmarc@driftwoodwealth.com` | Right starting posture |

Two notes on what is there. Cloudflare Email Routing **forwards** inbound mail; it does not send,
so it authorises nothing outbound. And the DMARC `rua` points at `dmarc@driftwoodwealth.com` — add
a routing rule for that address or the aggregate reports go nowhere, which is the only thing that
tells you whether alignment is working before you tighten the policy.

### 2. SPF, which is the one that can break inbound mail

There must be exactly **one** SPF TXT record on the apex. Two is a permanent fail, so this is an
edit, never an addition.

```
current   v=spf1 include:_spf.mx.cloudflare.net ~all
becomes   v=spf1 include:_spf.mx.cloudflare.net include:spf.mtasv.net ~all
```

Keep the Cloudflare include: removing it breaks forwarding. `spf.mtasv.net` is Postmark. If
Buttondown sends from the domain rather than its own, its include goes in the same record. SPF
permits ten DNS lookups total; three includes is comfortable, ten is a cliff.

### 3. Records the providers generate

Do not invent these. Copy what each dashboard shows, verbatim.

| Provider | Record | Notes |
|---|---|---|
| Postmark | DKIM `TXT` at `<selector>._domainkey` | Per-server selector |
| Postmark | Return-Path `CNAME` → `pm.mtasv.net` | Postmark names the hostname; this is what makes SPF align |
| Buttondown | DKIM `CNAME`s | Only if sending from the domain |

**Every one of these must be DNS-only (grey cloud).** Proxying a mail record breaks it. This is
automatic today because the zone is unproxied, but it matters the moment option A or C turns the
orange cloud on.

DNSSEC is off. It is good hygiene and has nothing to do with deliverability — do it after mail works,
not before, since it needs a DS record at the registrar and adds one more thing to have gotten wrong.

### 4. Sender identity

`POSTMARK_FROM` is `alec@driftwoodwealth.com`, which is a Cloudflare **forwarding** address, not a
mailbox. Postmark verifies a Sender Signature by emailing it; the forward delivers that to the
Gmail account, so it works. Replies to a sent artifact follow the same path.

### 5. Vercel environment variables

Project → Settings → Environment Variables, all environments:

```
POSTMARK_SERVER_TOKEN   Server API Token
POSTMARK_FROM           alec@driftwoodwealth.com
BUTTONDOWN_API_KEY      Settings → Programming
```

### 6. The CAN-SPAM postal address

```
1 Westbrook Corporate Center, Suite 306
Westchester, IL 60154
```

Set it once in Buttondown so it renders in every issue's footer beside the unsubscribe link. It is
required in **commercial** mail only; the transactional sends in `api/request.js` do not carry it.

**This disagrees with the site.** `site.py` sets `FIRM_LOCATION = "Chicago, Illinois"`; the office is
in Westchester, a western suburb. A metro descriptor is ordinary marketing practice and defensible,
but a CPA who reads the newsletter footer and then the site footer sees two different places. Either
is fine. Deciding is not optional, because the pages carrying the mismatch also carry the regulatory
disclosure.

### 7. Compliance

Every message either endpoint sends is an advertising communication by a registered representative.
Route the artifact body in `api/request.js`, the Buttondown confirmation, and the issue footer
through PAS/OSJ before the keys go in.

## Adding a document, or a publication

Both maps refuse anything that does not exist, which is the "no placeholders ship" rule applied to
email:

- **A document** → add a row to `ARTIFACTS` in `api/request.js`. `test_every_offered_artifact_resolves_to_a_page_that_exists`
  fails if the page is not real.
- **A publication** → add a row to `TOPICS` in `api/subscribe.js` **and** the map in
  `test_only_real_publications_can_be_subscribed_to`. A publication with no page behind it cannot
  be subscribed to.

**Tax Intelligence is deliberately absent from `TOPICS`, and not because it does not exist.**

Two documents were reviewed on 2026-08-01, and they are in different categories:

- **Exhibit A, the Illinois Estate Tax Register** (`EXHIBIT A | LEGISLATIVE REGISTER`, prepared
  31 July 2026) carries no internal marking. It is sponsor composition and committee mechanics, it
  states its source (LegiScan status), and it answers a question a client actually asks. It is
  distributable to a CPA or an estate attorney today, subject to OSJ review of the covering note.

- **Driftwood Tax Intelligence Q2 2026** is stamped `INTERNAL WORKING QOCUMENT` in its masthead and
  `Internal · 1 of 4` on every page footer. It also carries the argument in the firm's own voice
  rather than the reader's: a section headed *the stalled moat*, and the line *"this is the
  strongest version of the argument yet."* That is positioning, written for the practice, and
  sending it to a referral source distributes an internal document with the sales reasoning still
  in it.

So the wiring is ready and the subscription is not. To open it, three things in one commit: publish a
client-facing edition with the internal marking and the positioning language removed, give it a page
on the site, then add its row to `TOPICS` here and to the map in
`test_only_real_publications_can_be_subscribed_to`. The test refuses a topic with no page behind it,
which is the whole point.

Until then, the professional briefs go out through `api/request.js` as named artifacts — a specific
document, to someone who asked for it, once — which is the right shape for a referral relationship
anyway. A CPA does not want a subscription. They want the Illinois register when Illinois matters.

## Where capture appears, and where it does not

Only where the reader has already done work and wants the output: the Atlas state pages, the
Commentary index, and the foot of each long essay. Not the homepage, not inside a piece, not on the
Coordination Review — that page has one ask and it is the introduction. One action per page.

## Testing it locally

`vercel dev` runs the functions against `docs/`. Without keys both endpoints return
`503 not_configured`, which is the correct answer and is what the forms are written to handle.
