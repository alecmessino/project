// Generate Driftwood Open-Graph share cards (1200x630) with the self-hosted Erode/Inter fonts.
// Erode is the brand display face (headline + prose); Inter is retained for dense UI (wordmark, kicker, pill).
// Usage: node scripts/og_cards.mjs   (needs playwright-core + the bundled Chromium)
// Renders one PNG per page into docs/og/. Re-run after a brand/copy change.
import pkg from '/home/user/project/node_modules/playwright-core/index.js';
const { chromium } = pkg;
import path from 'node:path';
import fs from 'node:fs';

const ROOT = '/home/user/project';
const FONTS = `file://${ROOT}/docs/fonts`;
const OUT = path.join(ROOT, 'docs', 'og');
const EXE = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
fs.mkdirSync(OUT, { recursive: true });

const CARDS = {
  index:     ['Keep more of what you’ve earned.', 'Your portfolio, taxes, estate, and cash flow — coordinated as one after-tax system.'],
  taxlab:    ['After-Tax Review', 'After-tax return, asset location and tax-loss harvesting — by bracket and state.'],
  leakage:   ['Where your return leaks to tax', 'The Before / After on an identical exposure — your state’s illustrative number.'],
  statemap:  ['Fifty states, fifty tax personalities', 'Gains · marriage · death · munis · QSBS · losses · step-up — by state.'],
  concentration: ['How to de-risk a concentrated position', 'Selling · harvesting · hedging · deferring · giving — scored on the tradeoffs.'],
  thesis:    ['Own the drift. Refuse the leakage.', 'How Structural Alpha works — and the honest research behind it.'],
  tearsheet: ['Model Portfolio · long history', 'A hypothetical multi-decade backtest — in-sample and out-of-sample.'],
  ledger:    ['An illustrative track record', 'A hypothetical Model Portfolio, marked daily. Not a live client account.'],
  equities:  ['Research dashboard', 'Momentum signals, relative-strength ranking, and per-name backtests.'],
};

// The confluence mark — the same nameplate lockup the site nav uses, so the share card is unmistakably
// the brand rather than a text slab. Editorial-blue on warm paper, tracked-caps wordmark, one hairline
// accent, a serif headline, and a quiet compliance colophon.
const MARK = `<svg class="mark" viewBox="6 13 90 74" fill="none" stroke="currentColor" stroke-linecap="square" stroke-linejoin="miter" aria-hidden="true">
    <polyline points="10,18 24.35,18 62,50" stroke-width="3.2"/><polyline points="10,34 43.18,34 62,50" stroke-width="3.2"/><line x1="10" y1="50" x2="62" y2="50" stroke-width="3.2"/><polyline points="10,66 43.18,66 62,50" stroke-width="3.2"/><polyline points="10,82 24.35,82 62,50" stroke-width="3.2"/><line x1="62" y1="50" x2="90" y2="50" stroke-width="5.2"/></svg>`;
const card = (title, sub) => `<!doctype html><html><head><meta charset="utf-8"><style>
  @font-face{font-family:'Erode';font-weight:400;src:url("${FONTS}/erode-400.woff2") format("woff2")}
  @font-face{font-family:'Erode';font-weight:600;src:url("${FONTS}/erode-600.woff2") format("woff2")}
  @font-face{font-family:'Erode';font-weight:700;src:url("${FONTS}/erode-700.woff2") format("woff2")}
  @font-face{font-family:'Satoshi';font-weight:400;src:url("${FONTS}/satoshi-400.woff2") format("woff2")}
  @font-face{font-family:'Satoshi';font-weight:500;src:url("${FONTS}/satoshi-500.woff2") format("woff2")}
  @font-face{font-family:'Satoshi';font-weight:700;src:url("${FONTS}/satoshi-700.woff2") format("woff2")}
  *{margin:0;box-sizing:border-box}
  html,body{width:1200px;height:630px}
  body{background:#f1efe9;color:#1e2833;font-family:'Satoshi',system-ui,sans-serif;
    padding:60px 72px 54px;display:flex;flex-direction:column;position:relative;
    background-image:radial-gradient(120% 140% at 100% 0%, #f7f5f0 0%, #f1efe9 46%, #eceae2 100%)}
  .accent{position:absolute;top:0;left:0;right:0;height:6px;background:#2c5878}
  .lockup{display:flex;align-items:center;gap:15px}
  .lockup .mark{height:38px;width:auto;color:#2c5878;overflow:visible}
  .lockup .rule{width:1px;height:30px;background:#c3bcab}
  .lockup .wm{font-family:'Satoshi';font-weight:600;font-size:25px;letter-spacing:.16em;text-transform:uppercase;color:#1e2833}
  .body{flex:1;display:flex;flex-direction:column;justify-content:center}
  .kicker{color:#2c5878;font-weight:700;font-size:18px;letter-spacing:.2em;text-transform:uppercase}
  h1{font-family:'Erode','Georgia',serif;font-weight:700;font-size:74px;line-height:1.045;letter-spacing:-.021em;color:#1e2833;margin-top:20px;max-width:1010px}
  .sub{margin-top:24px;font-family:'Erode','Georgia',serif;font-size:29px;line-height:1.42;color:#48525e;max-width:960px}
  .foot{display:flex;align-items:center;gap:16px;padding-top:22px;border-top:1px solid #d8d3c6;
    font-size:18.5px;letter-spacing:.01em;color:#5c6470}
  .pill{border:1px solid #c3bcab;color:#6b6e6a;border-radius:999px;padding:7px 17px;font-weight:600;font-size:15.5px;letter-spacing:.06em;text-transform:uppercase}
</style></head><body>
  <div class="accent"></div>
  <div class="lockup">${MARK}<span class="rule"></span><span class="wm">Driftwood&nbsp;Wealth</span></div>
  <div class="body">
    <div class="kicker">Private Wealth Architecture</div>
    <h1>${title}</h1>
    <div class="sub">${sub}</div>
  </div>
  <div class="foot"><span class="pill">Illustrative modeling</span>
    <span>Registered Investment Adviser</span></div>
</body></html>`;

const b = await chromium.launch({ executablePath: EXE });
const ctx = await b.newContext({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
for (const [stem, [title, sub]] of Object.entries(CARDS)) {
  const p = await ctx.newPage();
  await p.setContent(card(title, sub), { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(120);
  await p.screenshot({ path: path.join(OUT, `${stem}.png`) });
  await p.close();
  console.log(`wrote docs/og/${stem}.png`);
}
await b.close();
console.log('OG cards done.');
