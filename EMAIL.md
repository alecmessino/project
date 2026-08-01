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

## Switching it on

Nothing below is in the repo, and none of it can be done from here.

**1. Postmark.** Create a server. Copy its Server API Token.

**2. Buttondown.** Create the newsletter. Copy the API key from Settings → Programming.

**3. DNS on `driftwoodwealth.com`.** Both providers give you records; add all of them.

| Record | Why |
|---|---|
| SPF (`TXT`) | Names the hosts allowed to send as the domain |
| DKIM (`TXT` or `CNAME`) | Signs each message so it cannot be forged in transit |
| DMARC (`TXT`) | Tells receivers what to do when the first two fail. Start at `p=none` and read the reports for two weeks before tightening |
| Return-Path (`CNAME`) | Aligns the bounce domain, which is what makes SPF pass |

Sending before these exist will land in spam and will damage the domain that also carries client
mail. This is the step to do first and to verify before anything else.

**4. Vercel environment variables** (Project → Settings → Environment Variables, all environments):

```
POSTMARK_SERVER_TOKEN   the Server API Token from step 1
POSTMARK_FROM           alec@driftwoodwealth.com   (must be a verified Sender Signature)
BUTTONDOWN_API_KEY      the key from step 2
```

**5. A physical postal address.** CAN-SPAM requires a valid one in every *commercial* message, so
it belongs in the Buttondown footer. A PO box qualifies. This applies to the publication only, not
to the transactional sends, and it is the one place a mailing address is required despite the
site's own rule against putting a street address in marketing.

**6. Compliance.** Every message either endpoint sends is an advertising communication by a
registered representative. Route the artifact email body in `api/request.js` and the Buttondown
confirmation and footer through PAS/OSJ before the keys go in. The disclosure in `request.js`
matches the site's and is test-guarded, but matching the site is not the same as being approved.

## Adding a document, or a publication

Both maps refuse anything that does not exist, which is the "no placeholders ship" rule applied to
email:

- **A document** → add a row to `ARTIFACTS` in `api/request.js`. `test_every_offered_artifact_resolves_to_a_page_that_exists`
  fails if the page is not real.
- **A publication** → add a row to `TOPICS` in `api/subscribe.js` **and** the map in
  `test_only_real_publications_can_be_subscribed_to`. A publication with no page behind it cannot
  be subscribed to.

*Tax Intelligence* is deliberately absent from `TOPICS`. There is no such publication on the site
today, and offering a subscription to one would be a placeholder with an email address attached.

## Where capture appears, and where it does not

Only where the reader has already done work and wants the output: the Atlas state pages, the
Commentary index, and the foot of each long essay. Not the homepage, not inside a piece, not on the
Coordination Review — that page has one ask and it is the introduction. One action per page.

## Testing it locally

`vercel dev` runs the functions against `docs/`. Without keys both endpoints return
`503 not_configured`, which is the correct answer and is what the forms are written to handle.
