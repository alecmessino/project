// The social graphic for "The Interval Problem": the same index, drawn at two checking cadences,
// side by side. 1600x900, into docs/og/.
//
//   node scripts/og_interval_share.mjs
//
// This is not the Open Graph card (that is og_essay.mjs). It is the image you attach to a post,
// where the picture has to make the whole argument before anyone clicks: two panels, one series,
// identical period return, and a deepest observed fall that differs by twelve points purely
// because of how often the observer looked.
//
// It renders the published page twice rather than redrawing the charts, so the graphic cannot
// disagree with the essay. Run scripts/kospi_interval.py first if the data is stale.
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import path from 'node:path';
import fs from 'node:fs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const PAGE = `file://${ROOT}/docs/the-interval-problem.html`;
const OUT = path.join(ROOT, 'docs', 'og');
const EXE = process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
fs.mkdirSync(OUT, { recursive: true });

const b = await chromium.launch({ executablePath: EXE });
const ctx = await b.newContext({ viewport: { width: 1000, height: 700 }, deviceScaleFactor: 2 });

// Pull the two figures and their numbers straight out of the rendered page.
async function panel(cadence) {
  const p = await ctx.newPage();
  await p.goto(`${PAGE}?cadence=${cadence}`, { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(250);
  const out = await p.evaluate(() => {
    var s = window.__INTERVAL__.series;
    return {
      svg: document.querySelector('[data-cadence-figure]').outerHTML,
      count: document.getElementById('c-count').textContent,
      dd: document.getElementById('c-dd').textContent,
      total: document.getElementById('c-total').textContent,
      // The period, read off the series rather than typed into this file. It was hardcoded to
      // "January 2 to August 3, 2026" and went stale the next time the market closed.
      span: [s[0][0], s[s.length - 1][0]].map(function (d) {
        return new Date(d + 'T00:00:00').toLocaleDateString('en-US',
          { month: 'long', day: 'numeric' }); }).join(' to ') + ', ' + s[0][0].slice(0, 4),
    };
  });
  await p.close();
  return out;
}

const daily = await panel('daily');
const quarterly = await panel('quarterly');

const LABEL = { daily: 'Checked every day', quarterly: 'Checked every quarter' };
const cell = (title, d) => `
  <section>
    <h2>${title}</h2>
    <div class="fig">${d.svg}</div>
    <dl>
      <div><dt>Times you looked</dt><dd>${d.count}</dd></div>
      <div><dt>Deepest fall you saw</dt><dd class="hot">${d.dd}</dd></div>
      <div><dt>Return over the period</dt><dd class="same">${d.total}</dd></div>
    </dl>
  </section>`;

const html = `<!doctype html><html><head><meta charset="utf-8"><style>
  @font-face{font-family:'Satoshi';font-weight:300 900;font-style:normal;
    src:url("file://${ROOT}/docs/fonts/Satoshi-Variable.woff2") format("woff2")}
  *{margin:0;box-sizing:border-box}
  html,body{width:1600px;height:900px}
  body{background:#f1efe9;color:#1e2833;font-family:'Satoshi',system-ui,sans-serif;
    padding:52px 60px 44px;display:flex;flex-direction:column}
  .kicker{color:#2c5878;font-weight:700;font-size:16px;letter-spacing:.2em;text-transform:uppercase}
  h1{font-weight:700;font-size:44px;letter-spacing:-.024em;margin-top:14px;line-height:1.1}
  .stand{margin-top:12px;font-size:22px;color:#5c6470;max-width:96ch}
  .grid{flex:1;display:grid;grid-template-columns:1fr 1fr;gap:52px;margin-top:30px;align-items:stretch}
  /* The stats sit on the bottom rule of each panel rather than tucked under the chart, so the
     two panels read as one ruled sheet instead of leaving a dead band above the colophon. */
  section{border-top:1px solid #1e2833;padding-top:16px;display:flex;flex-direction:column}
  h2{font-weight:700;font-size:21px;letter-spacing:-.01em}
  .fig{margin-top:14px;margin-bottom:22px}
  .fig svg{width:100%;height:auto;display:block;font-family:'Satoshi',sans-serif}
  dl{display:grid;grid-template-columns:repeat(3,1fr);margin-top:auto;border-top:1px solid #d8d3c6;
    padding-top:16px}
  dt{font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:#6b6e6a;
    line-height:1.4;min-height:32px}
  dd{font-size:29px;font-weight:700;letter-spacing:-.02em;margin-top:6px;font-variant-numeric:tabular-nums}
  dd.same{color:#2c5878}
  .foot{margin-top:26px;padding-top:16px;border-top:1px solid #d8d3c6;display:flex;
    justify-content:space-between;align-items:baseline;font-size:16px;color:#5c6470}
  .wm{font-weight:700;font-size:14px;letter-spacing:.19em;text-transform:uppercase;color:#1e2833}
</style></head><body>
  <div class="kicker">Kospi Composite · ${daily.span}</div>
  <h1>The same index. The same money. Two different years.</h1>
  <div class="stand">The faint line is every closing level. The marked line is what an investor on that
    checking habit would ever have seen.</div>
  <div class="grid">${cell(LABEL.daily, daily)}${cell(LABEL.quarterly, quarterly)}</div>
  <div class="foot">
    <span>The interval changed what the investor saw. It never touched what the position was worth.</span>
    <span class="wm">Driftwood Wealth</span>
  </div>
</body></html>`;

const p = await ctx.newPage();
await p.setViewportSize({ width: 1600, height: 900 });
await p.setContent(html, { waitUntil: 'load' });
await p.evaluate(() => document.fonts.ready);
await p.waitForTimeout(200);
await p.screenshot({ path: path.join(OUT, 'the-interval-problem-share.png') });
await p.close();
await b.close();
console.log('wrote docs/og/the-interval-problem-share.png');
