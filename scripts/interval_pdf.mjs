// Cut the PDF of "The Interval Problem" from the published page.
//
//   node scripts/interval_pdf.mjs
//
// Printed from docs/the-interval-problem.html rather than typeset separately, so the PDF and the
// site cannot say different things. The page's own @media print rules drop the masthead, the
// controls and the subscribe form; what is left is the essay, the four exhibits, and the full
// disclosure.
//
// The two instruments are printed in the state that carries the argument rather than in their
// default state: the cadence figure at QUARTERLY, because paper cannot offer the comparison
// interactively and the quarterly line against the faint daily one is the whole point; the ladder
// at five sessions missed, which is where the year goes negative. Both states are reachable from
// the URL, which is why the parameters exist.
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import path from 'node:path';
import fs from 'node:fs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const OUT = path.join(ROOT, 'docs', 'The-Interval-Problem-Driftwood-Wealth.pdf');
const EXE = process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';

const b = await chromium.launch({ executablePath: EXE });
const ctx = await b.newContext({ viewport: { width: 1100, height: 1400 } });
const p = await ctx.newPage();
await p.goto(`file://${ROOT}/docs/the-interval-problem.html?cadence=quarterly&missed=5`,
  { waitUntil: 'load' });
await p.evaluate(() => document.fonts.ready);
await p.waitForTimeout(500);
await p.emulateMedia({ media: 'print' });
await p.pdf({
  path: OUT,
  format: 'Letter',
  printBackground: true,
  displayHeaderFooter: true,
  headerTemplate: '<div></div>',
  footerTemplate: `<div style="width:100%;padding:0 15mm;font-family:system-ui,sans-serif;
    font-size:7.5pt;color:#6b6e6a;display:flex;justify-content:space-between">
    <span>Driftwood Wealth &nbsp;·&nbsp; The Interval Problem</span>
    <span class="pageNumber"></span></div>`,
  margin: { top: '16mm', bottom: '18mm', left: '15mm', right: '15mm' },
});
await b.close();
console.log(`wrote ${path.relative(ROOT, OUT)} (${(fs.statSync(OUT).size / 1024).toFixed(0)} KB)`);
