// Per-state Open-Graph share cards (1200x630) for the state landing pages.
// Reads a JSON array of {code,name,alpha,rate} (arg or default scratch path) and writes
// docs/og/states/<code>.png. Re-run after a brand/copy change:  node scripts/og_states.mjs <data.json>
import pkg from '/home/user/project/node_modules/playwright-core/index.js';
const { chromium } = pkg;
import path from 'node:path';
import fs from 'node:fs';

const ROOT = '/home/user/project';
const FONTS = `file://${ROOT}/docs/fonts`;
const OUT = path.join(ROOT, 'docs', 'og', 'states');
const EXE = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const DATA = process.argv[2] || '/tmp/claude-0/-home-user-project/66a39e90-7a01-53b5-9f3a-ee763ef29077/scratchpad/og_states.json';
fs.mkdirSync(OUT, { recursive: true });
const rows = JSON.parse(fs.readFileSync(DATA, 'utf8'));

const card = (r) => `<!doctype html><html><head><meta charset="utf-8"><style>
  @font-face{font-family:'Moret';font-weight:700;src:url("${FONTS}/moret-700.woff2") format("woff2")}
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
  .kicker{margin-top:50px;color:#9a7b3e;font-weight:700;font-size:21px;letter-spacing:.14em;text-transform:uppercase}
  h1{font-family:'Moret','Georgia',serif;font-weight:700;font-size:70px;line-height:1.03;letter-spacing:-.02em;margin-top:16px;max-width:1010px}
  .stat{margin-top:26px;display:flex;align-items:baseline;gap:16px}
  .stat .n{font-family:'Inter';font-weight:700;font-size:60px;color:#15806a;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
  .stat .l{font-size:23px;color:#41454c;max-width:560px;line-height:1.3}
  .foot{margin-top:auto;display:flex;align-items:center;gap:14px;font-size:21px;color:#5f5f68}
  .pill{border:1px solid #c9b27e;color:#9a7b3e;border-radius:999px;padding:6px 16px;font-weight:600;font-size:18px}
</style></head><body>
  <div class="rule"></div>
  <div class="brand">Drift<span class="w">wood</span></div>
  <div class="kicker">${r.name} · tax-leakage diagnostic</div>
  <h1>Where your ${r.name} portfolio leaks to tax</h1>
  <div class="stat"><div class="n">+${Number(r.alpha).toFixed(1)}%/yr</div>
    <div class="l">illustrative after-tax Structural Alpha a tax-managed book can recover</div></div>
  <div class="foot"><span class="pill">Illustrative modeling</span>
    <span>CWS Planning · registered investment adviser</span></div>
</body></html>`;

const b = await chromium.launch({ executablePath: EXE });
const ctx = await b.newContext({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
for (const r of rows) {
  const p = await ctx.newPage();
  await p.setContent(card(r), { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(60);
  await p.screenshot({ path: path.join(OUT, `${r.code.toLowerCase()}.png`) });
  await p.close();
}
await b.close();
console.log(`wrote ${rows.length} state OG cards -> docs/og/states/`);
