# Disclosure documents (drop-in location)

The site footer links to the firm's Form ADV Part 2A and Form CRS at **stable, relative paths**
so they can be hosted directly on the site instead of routing visitors to the general SEC homepage.

| Link in footer            | File served here                     |
|---------------------------|--------------------------------------|
| **Form ADV Part 2A**      | `disclosures/adv-part-2a.pdf`        |
| **Form CRS**              | `disclosures/form-crs.pdf`           |

## How to publish the real filings

**Option A — host the PDFs here (recommended).**
Replace the two placeholder PDFs in this directory with the firm's current filings, keeping the
**exact same filenames**. Commit them to `master`; the Pages deploy publishes `docs/` as-is, so the
footer links resolve immediately with no markup change.

```
docs/disclosures/adv-part-2a.pdf   <- current Form ADV Part 2A (Brochure)
docs/disclosures/form-crs.pdf      <- current Form CRS (Client Relationship Summary)
```

**Option B — point at an external URL instead.**
If the filings are hosted elsewhere (e.g. the SEC's IAPD PDF), repoint the footer links. The link
text and targets live in the page templates under `src/drift/web/` — search for
`disclosures/adv-part-2a.pdf` and `disclosures/form-crs.pdf`, change the `href`, then rebuild docs
with `python scripts/sync_docs.py` (and `drift states --out-dir docs` for the atlas pages).

> The two PDFs currently in this folder are **placeholders** — they clearly say so on their single
> page. They exist only so the links (and the HTTPS padlock check) resolve cleanly before the real
> filings are posted. Do not treat them as filed documents.

The internal Advisor Workspace uses the same paths via its `CONFIG.formAdvUrl` / `CONFIG.formCrsUrl`
hooks (in `src/drift/web/workspace.html`) — repoint those too if you choose Option B.
