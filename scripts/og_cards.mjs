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
  index:     ['Keep more of what you’ve earned.', 'Private wealth architecture — engineered beta and mechanical tax management.'],
  taxlab:    ['The Tax Lab', 'After-tax return, asset location and tax-loss harvesting — by bracket and state.'],
  leakage:   ['Where your return leaks to tax', 'The Before / After on an identical exposure — your state’s illustrative number.'],
  statemap:  ['Fifty states. One after-tax plan.', 'Capital gains · marriage · estate · step-up · Structural Alpha — by state.'],
  thesis:    ['Own the drift. Refuse the leakage.', 'How Structural Alpha works — and the honest research behind it.'],
  tearsheet: ['Model Portfolio · long history', 'A hypothetical multi-decade backtest — in-sample and out-of-sample.'],
  ledger:    ['An illustrative track record', 'A hypothetical Model Portfolio, marked daily. Not a live client account.'],
  equities:  ['Research dashboard', 'Momentum signals, relative-strength ranking, and per-name backtests.'],
};

const card = (title, sub) => `<!doctype html><html><head><meta charset="utf-8"><style>
  @font-face{font-family:'Erode';font-weight:400;src:url("${FONTS}/erode-400.woff2") format("woff2")}
  @font-face{font-family:'Erode';font-weight:600;src:url("${FONTS}/erode-600.woff2") format("woff2")}
  @font-face{font-family:'Erode';font-weight:700;src:url("${FONTS}/erode-700.woff2") format("woff2")}
  @font-face{font-family:'Inter';font-weight:400;src:url("${FONTS}/inter-400.woff2") format("woff2")}
  @font-face{font-family:'Inter';font-weight:600;src:url("${FONTS}/inter-600.woff2") format("woff2")}
  @font-face{font-family:'Inter';font-weight:700;src:url("${FONTS}/inter-700.woff2") format("woff2")}
  *{margin:0;box-sizing:border-box}
  html,body{width:1200px;height:630px}
  body{background:#f4f0e6;color:#1b1b1f;font-family:'Inter',system-ui,sans-serif;
    padding:74px 80px;display:flex;flex-direction:column;position:relative}
  .rule{position:absolute;top:0;left:0;right:0;height:10px;background:#15806a}
  .brand{font-family:'Inter';font-weight:700;font-size:30px;letter-spacing:-.01em}
  .brand .w{color:#15806a}
  .kicker{margin-top:54px;color:#9a7b3e;font-weight:700;font-size:21px;letter-spacing:.14em;text-transform:uppercase}
  h1{font-family:'Erode','Georgia',serif;font-weight:700;font-size:78px;line-height:1.04;letter-spacing:-.02em;margin-top:18px;max-width:1010px}
  .sub{margin-top:26px;font-family:'Erode','Georgia',serif;font-size:30px;line-height:1.4;color:#41454c;max-width:1000px}
  .foot{margin-top:auto;display:flex;align-items:center;gap:14px;font-size:21px;color:#5f5f68}
  .pill{border:1px solid #c9b27e;color:#9a7b3e;border-radius:999px;padding:6px 16px;font-weight:600;font-size:18px}
</style></head><body>
  <div class="rule"></div>
  <div class="brand">Drift<span class="w">wood</span></div>
  <div class="kicker">Private wealth architecture</div>
  <h1>${title}</h1>
  <div class="sub">${sub}</div>
  <div class="foot"><span class="pill">Illustrative modeling</span>
    <span>CWS Planning · registered investment adviser</span></div>
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
