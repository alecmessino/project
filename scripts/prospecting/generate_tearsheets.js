#!/usr/bin/env node
'use strict';
/*
 * Visual Prospecting Automation — personalized Driftwood tearsheet generator.
 *
 * Reads a CSV of leads (Name, State, Portfolio_Size), and for each one renders a
 * personalized "After-Tax Review" and screenshots it to outputs/.
 *
 * ── WHICH PAGE THIS DRIVES (important) ────────────────────────────────────────
 * The brief named `docs/taxlab.html`, but that page is the *static public exhibit*
 * — one fixed hero chart ("Coordinated versus isolated, over thirty years"). It has
 * NO state dropdown, NO portfolio slider, and NO "Asset Location" / "Tax Drag" /
 * "Alpha-Turnover Frontier" widgets, so per-lead params do not change what it renders.
 *
 * The interactive tool that actually has those controls is `docs/workspace.html`
 * (the Advisor Workspace, data-page="taxlab"): `#state`, `#bracket`, the portfolio
 * sliders (`#taxbal` / `#leadport`), the Asset-Location result (`#locresult`), the
 * "Tax drag" metric, and the Alpha-Turnover Frontier (`<details id="frontier">` →
 * `#ftchart`). workspace.html is *explicitly built for personalized cold-outreach
 * deep-links* — see its own source comment:
 *     //   ?view=lead&state=IL&port=2000000
 * So this script targets workspace.html by default. Override with PAGE=taxlab.html
 * to screenshot the static exhibit instead (it will just render the same hero).
 *
 * Personalization is applied two ways for robustness:
 *   1. URL query params (?state=..&port=..&bracket=..) — the page's designed path
 *      (dw-context.js hydrates the controls from these; URL always wins).
 *   2. Direct DOM interaction (select the state, move the sliders, open the frontier)
 *      — satisfies the "programmatically interact with the DOM" requirement and
 *      guarantees a repaint even if the URL path ever changes.
 *
 * No core files are modified. We only read docs/ and mutate the live DOM at runtime.
 *
 * Usage:
 *   npm install                 # installs playwright-core (already in package.json)
 *   node scripts/prospecting/generate_tearsheets.js
 *
 * Config via env:
 *   LEADS_CSV, OUT_DIR, DOCS_DIR, PAGE (default workspace.html),
 *   CHROMIUM_EXE, VW, VH, DSF (device scale factor, default 2), BRACKET (default 37)
 */

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright-core');

// ── Paths & config ────────────────────────────────────────────────────────────
const HERE = __dirname;
const ROOT = path.resolve(HERE, '..', '..');
const DOCS = process.env.DOCS_DIR || path.join(ROOT, 'docs');
const OUT = process.env.OUT_DIR || path.join(HERE, 'outputs');
const CSV = process.env.LEADS_CSV || path.join(HERE, 'austin_leads.csv');
const PAGE = process.env.PAGE || 'workspace.html';
const EXE = process.env.CHROMIUM_EXE || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const VIEWPORT = { width: Number(process.env.VW) || 1440, height: Number(process.env.VH) || 1024 };
const DSF = Number(process.env.DSF) || 2;
const DEFAULT_BRACKET = Number(process.env.BRACKET) || 37; // top federal ordinary rate, a sane HNW default

// ── US state name → USPS code (so a CSV can say "Texas" or "TX") ────────────────
const STATE_CODES = {
  alabama: 'AL', alaska: 'AK', arizona: 'AZ', arkansas: 'AR', california: 'CA',
  colorado: 'CO', connecticut: 'CT', delaware: 'DE', florida: 'FL', georgia: 'GA',
  hawaii: 'HI', idaho: 'ID', illinois: 'IL', indiana: 'IN', iowa: 'IA', kansas: 'KS',
  kentucky: 'KY', louisiana: 'LA', maine: 'ME', maryland: 'MD', massachusetts: 'MA',
  michigan: 'MI', minnesota: 'MN', mississippi: 'MS', missouri: 'MO', montana: 'MT',
  nebraska: 'NE', nevada: 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ',
  'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND',
  ohio: 'OH', oklahoma: 'OK', oregon: 'OR', pennsylvania: 'PA', 'rhode island': 'RI',
  'south carolina': 'SC', 'south dakota': 'SD', tennessee: 'TN', texas: 'TX', utah: 'UT',
  vermont: 'VT', virginia: 'VA', washington: 'WA', 'west virginia': 'WV',
  wisconsin: 'WI', wyoming: 'WY', 'district of columbia': 'DC', 'washington dc': 'DC',
};

function normState(raw) {
  const s = String(raw || '').trim();
  if (!s) return 'TX'; // brief default
  if (/^[A-Za-z]{2}$/.test(s)) return s.toUpperCase();
  const code = STATE_CODES[s.toLowerCase()];
  return code || s.toUpperCase();
}

// "$2,000,000" | "2000000" | "2M" | "1.5m" | "750k" → number
function parseMoney(raw) {
  let s = String(raw || '').trim().toLowerCase().replace(/[$,\s]/g, '');
  if (!s) return 0;
  let mult = 1;
  if (s.endsWith('k')) { mult = 1e3; s = s.slice(0, -1); }
  else if (s.endsWith('m')) { mult = 1e6; s = s.slice(0, -1); }
  else if (s.endsWith('b')) { mult = 1e9; s = s.slice(0, -1); }
  const n = parseFloat(s);
  return Number.isFinite(n) ? Math.round(n * mult) : 0;
}

// ── Minimal CSV parser (handles quoted fields with embedded commas) ─────────────
function parseCSV(text) {
  const rows = [];
  let row = [], field = '', inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; } else inQ = false;
      } else field += c;
    } else if (c === '"') inQ = true;
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(field); field = '';
      if (row.some(v => v.trim() !== '')) rows.push(row);
      row = [];
    } else field += c;
  }
  if (field !== '' || row.length) { row.push(field); if (row.some(v => v.trim() !== '')) rows.push(row); }
  if (!rows.length) return [];
  const header = rows[0].map(h => h.trim().toLowerCase());
  return rows.slice(1).map(r => {
    const o = {};
    header.forEach((h, i) => { o[h] = (r[i] || '').trim(); });
    return o;
  });
}

function sanitizeName(name) {
  return String(name || 'lead').trim().replace(/[^A-Za-z0-9]+/g, '_').replace(/^_+|_+$/g, '') || 'lead';
}

// ── A tiny static file server rooted at docs/ (serves relative CSS/JS/fonts and
//    lets URL query params work over a real http origin, avoiding file:// quirks) ─
const MIME = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.ico': 'image/x-icon',
};

function startServer(root) {
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      let p = decodeURIComponent((req.url || '/').split('?')[0]);
      if (p.endsWith('/')) p += 'index.html';
      const fp = path.normalize(path.join(root, p));
      if (!fp.startsWith(root)) { res.statusCode = 403; return res.end('forbidden'); }
      fs.readFile(fp, (err, buf) => {
        if (err) { res.statusCode = 404; return res.end('not found'); }
        res.setHeader('Content-Type', MIME[path.extname(fp).toLowerCase()] || 'application/octet-stream');
        res.end(buf);
      });
    });
    srv.listen(0, '127.0.0.1', () => resolve({ srv, port: srv.address().port }));
  });
}

// ── Per-lead DOM personalization (runs inside the page) ─────────────────────────
// Feature-detected throughout so it degrades gracefully on the static taxlab.html.
function personalizeInPage({ state, port, bracket }) {
  const $ = (id) => document.getElementById(id);
  const out = { state: false, portfolio: false, frontier: false, sections: false };

  // 1 · State dropdown
  try {
    const s = $('state');
    if (s) {
      s.value = state;
      if (typeof selectState === 'function') selectState(state);
      else s.dispatchEvent(new Event('change', { bubbles: true }));
      out.state = (s.value === state);
    }
  } catch (e) { /* ignore */ }

  // 2 · Portfolio Size slider(s) — clamp into each slider's own [min,max]
  try {
    let moved = false;
    ['leadport', 'taxbal'].forEach((id) => {
      const el = $(id);
      if (!el) return;
      const mn = parseFloat(el.min) || 0;
      const mx = parseFloat(el.max) || port;
      el.value = String(Math.min(Math.max(port, mn), mx));
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      moved = true;
    });
    if (window.dwTaxContext) dwTaxContext.save({ portfolio: port, state, bracket });
    out.portfolio = moved;
  } catch (e) { /* ignore */ }

  // 3 · Force a full recompute so Asset Location + Tax Drag reflect the new inputs
  try { if (typeof render === 'function') render(); } catch (e) { /* ignore */ }
  try { if (typeof reviewLead === 'function') reviewLead(); } catch (e) { /* ignore */ }

  // 4 · Reveal every section (the tool normally shows one at a time via body.on-*),
  //     so a single screenshot holds Portfolio (asset location), Taxes (tax drag)
  //     and Holdings (the Alpha-Turnover Frontier).
  try {
    ['portfolio', 'taxes', 'state', 'holdings', 'estate', 'implementation']
      .forEach((s) => document.body.classList.add('on-' + s));
    out.sections = true;
  } catch (e) { /* ignore */ }

  // 5 · Open the Alpha-Turnover Frontier <details> so the chart is visible
  try {
    const f = $('frontier');
    if (f) { f.open = true; out.frontier = true; }
  } catch (e) { /* ignore */ }

  return out;
}

// ── Main ────────────────────────────────────────────────────────────────────────
(async () => {
  if (!fs.existsSync(CSV)) { console.error(`No leads CSV at ${CSV}`); process.exit(1); }
  if (!fs.existsSync(path.join(DOCS, PAGE))) { console.error(`No page at ${path.join(DOCS, PAGE)}`); process.exit(1); }
  if (!fs.existsSync(EXE)) { console.error(`Chromium not found at ${EXE} (set CHROMIUM_EXE).`); process.exit(1); }

  const leads = parseCSV(fs.readFileSync(CSV, 'utf8'))
    .map((r) => ({
      name: r.name || r.prospect || r['prospect_name'] || 'Lead',
      state: normState(r.state || 'TX'),
      portfolio: parseMoney(r.portfolio_size || r.portfolio || r['portfolio size']),
      bracket: Number(r.bracket || r['federal_bracket']) || DEFAULT_BRACKET,
    }))
    .filter((l) => l.name);

  if (!leads.length) { console.error('CSV parsed but no lead rows found.'); process.exit(1); }

  fs.mkdirSync(OUT, { recursive: true });
  const { srv, port: httpPort } = await startServer(DOCS);
  const base = `http://127.0.0.1:${httpPort}`;
  console.log(`Serving ${DOCS} at ${base}`);
  console.log(`Driving /${PAGE} for ${leads.length} lead(s) → ${OUT}\n`);

  const browser = await chromium.launch({
    executablePath: EXE,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });

  const results = [];
  for (const lead of leads) {
    const stem = sanitizeName(lead.name);
    const params = new URLSearchParams({
      state: lead.state,
      port: String(lead.portfolio),
      bracket: String(lead.bracket),
      utm_source: 'prospecting', utm_medium: 'tearsheet',
    });
    const url = `${base}/${PAGE}?${params.toString()}`;

    // Fresh context per lead → no localStorage bleed between prospects.
    const context = await browser.newContext({ viewport: VIEWPORT, deviceScaleFactor: DSF });
    // Keep it hermetic: drop any non-local request (analytics, Calendly, etc.).
    await context.route('**/*', (route) => {
      try {
        const h = new URL(route.request().url()).hostname;
        return (h === '127.0.0.1' || h === 'localhost') ? route.continue() : route.abort();
      } catch (e) { return route.abort(); }
    });

    const pg = await context.newPage();
    try {
      await pg.goto(url, { waitUntil: 'load', timeout: 30000 });
      await pg.evaluate(() => document.fonts && document.fonts.ready);
      const applied = await pg.evaluate(personalizeInPage, lead);

      // Best-effort wait for the Asset-Location result to populate (workspace.html only).
      await pg.waitForFunction(() => {
        const el = document.getElementById('locresult');
        return !el || el.textContent.trim().length > 0;
      }, { timeout: 5000 }).catch(() => {});
      await pg.waitForTimeout(400); // let SVG paths settle

      const analysisPath = path.join(OUT, `${stem}_Driftwood_Analysis.png`);
      await pg.screenshot({ path: analysisPath, fullPage: true });

      // Focused close-up of the Alpha-Turnover Frontier chart, if present.
      let frontierPath = null;
      const fr = await pg.$('#frontier');
      if (fr && await fr.isVisible()) {
        frontierPath = path.join(OUT, `${stem}_Driftwood_Frontier.png`);
        await fr.screenshot({ path: frontierPath });
      }

      console.log(`✓ ${lead.name}  [${lead.state} · $${lead.portfolio.toLocaleString('en-US')} · ${lead.bracket}%]`);
      console.log(`    controls → state:${applied.state} portfolio:${applied.portfolio} frontier:${applied.frontier}`);
      console.log(`    ${path.relative(ROOT, analysisPath)}${frontierPath ? '  +  ' + path.relative(ROOT, frontierPath) : ''}`);
      results.push({ lead: lead.name, analysisPath, frontierPath, applied });
    } catch (err) {
      console.error(`✗ ${lead.name}: ${err.message}`);
      results.push({ lead: lead.name, error: err.message });
    } finally {
      await context.close();
    }
  }

  await browser.close();
  await new Promise((r) => srv.close(r));

  const ok = results.filter((r) => !r.error).length;
  console.log(`\nDone. ${ok}/${results.length} tearsheet(s) written to ${path.relative(ROOT, OUT)}/`);
  if (ok < results.length) process.exitCode = 1;
})().catch((e) => { console.error(e); process.exit(1); });
