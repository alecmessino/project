// Open-Graph share cards for the long-form essays (1200x630), into docs/og/.
//
//   node scripts/og_essay.mjs
//
// Separate from og_cards.mjs on purpose. That script draws the PRODUCT cards: a full-bleed
// nameplate lockup, an Erode headline, a compliance colophon. An essay card is a different object.
// It carries the piece's own signature figure beside its title, because the figure is what makes
// someone stop scrolling, and the argument of every one of these essays is a shape before it is a
// sentence. docs/og/count-the-pairs.png was built to that pattern months ago and then had no
// generator at all; it is regenerated here so the pattern has one.
//
// Fonts are the self-hosted VARIABLE faces in docs/fonts. og_cards.mjs still points at
// erode-400.woff2 and satoshi-500.woff2, which are not in the tree; a card built from that script
// silently falls back to a system face.
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import path from 'node:path';
import fs from 'node:fs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const FONTS = `file://${ROOT}/docs/fonts`;
const OUT = path.join(ROOT, 'docs', 'og');
const EXE = process.env.CHROME_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
fs.mkdirSync(OUT, { recursive: true });

const INK = '#1e2833', ACCENT = '#2c5878', BODY = '#5c6470', PAPER = '#f1efe9';

// Each essay: kicker, title, standfirst, and the mark that carries its argument.
const ESSAYS = {
  'the-interval-problem': {
    kicker: 'Research · Market structure',
    title: 'The Interval\nProblem',
    sub: 'The same index, the same seven months. One investor had a crisis, the other had an excellent year.',
    // The two endpoints joined twice: once by every close between them, once by a straight line.
    art: `<svg viewBox="0 0 400 400" fill="none" stroke="${ACCENT}" aria-hidden="true">
      <path d="M40 330 L64 268 L88 292 L112 196 L136 226 L160 148 L184 172 L208 74 L232 114 L256 40 L280 196 L304 142 L328 300 L352 244 L376 62"
        stroke-width="2.4" opacity=".34" stroke-linejoin="round" stroke-linecap="round"/>
      <line x1="40" y1="330" x2="376" y2="62" stroke-width="4.5"/>
      <circle cx="40" cy="330" r="9" fill="${ACCENT}" stroke="none"/>
      <circle cx="376" cy="62" r="9" fill="${ACCENT}" stroke="none"/>
    </svg>`,
  },
  'the-shortest-line': {
    kicker: 'Commentary \u00b7 Market structure',
    title: 'The Shortest Line\non the Chart',
    sub: 'Korea\u2019s crash looks like the worst in Asian history because it is the only one still in progress.',
    // Five drawdowns from one peak. The bold short one is the newest, and the reason it looks
    // worst is that the others are still falling past the edge of the frame.
    art: `<svg viewBox="0 0 400 400" fill="none" stroke="${INK}" aria-hidden="true">
      <line x1="40" y1="40" x2="380" y2="40" stroke-width="1.5" stroke-opacity=".45"/>
      <path d="M40 40 L86 92 L132 78 L178 140 L224 126 L270 196 L316 178 L362 246"
        stroke-width="2.2" stroke-opacity=".26" stroke-linejoin="round"/>
      <path d="M40 40 L86 70 L132 118 L178 104 L224 168 L270 214 L316 262 L362 300"
        stroke-width="2.2" stroke-opacity=".2" stroke-linejoin="round"/>
      <path d="M40 40 L86 118 L132 96 L178 158 L224 190 L270 250 L316 300 L362 352"
        stroke-width="2.2" stroke-opacity=".15" stroke-linejoin="round"/>
      <path d="M40 40 L70 104 L100 86 L130 168 L160 150 L190 244" stroke="${ACCENT}"
        stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>
      <circle cx="190" cy="244" r="9" fill="${ACCENT}" stroke="none"/>
    </svg>`,
  },
  'count-the-pairs': {
    kicker: 'Commentary · Portfolio structure',
    title: 'Count the Pairs,\nNot the People',
    sub: 'Your statement reports the diagonal. Your risk lives in the off diagonal.',
    art: (() => {
      const n = 17, cell = 400 / n, gap = 1.6;
      let out = `<svg viewBox="0 0 400 400" aria-hidden="true">`;
      for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) {
        const on = r === c;
        out += `<rect x="${(c * cell + gap).toFixed(2)}" y="${(r * cell + gap).toFixed(2)}" `
          + `width="${(cell - gap * 2).toFixed(2)}" height="${(cell - gap * 2).toFixed(2)}" `
          + `fill="${on ? ACCENT : '#1e2833'}" fill-opacity="${on ? 1 : 0.09}"/>`;
      }
      return out + '</svg>';
    })(),
  },
};

const card = (e) => `<!doctype html><html><head><meta charset="utf-8"><style>
  @font-face{font-family:'Satoshi';font-weight:300 900;font-style:normal;
    src:url("${FONTS}/Satoshi-Variable.woff2") format("woff2")}
  *{margin:0;box-sizing:border-box}
  html,body{width:1200px;height:630px}
  body{background:${PAPER};color:${INK};font-family:'Satoshi',system-ui,sans-serif;
    display:grid;grid-template-columns:1fr 420px;gap:64px;align-items:center;
    padding:72px 76px}
  .kicker{color:${ACCENT};font-weight:700;font-size:19px;letter-spacing:.19em;text-transform:uppercase}
  h1{font-weight:700;font-size:76px;line-height:1.03;letter-spacing:-.028em;margin-top:26px;
    white-space:pre-line}
  .sub{margin-top:28px;font-size:27px;line-height:1.44;color:${BODY};max-width:23ch}
  .wm{margin-top:40px;font-weight:700;font-size:17px;letter-spacing:.19em;text-transform:uppercase;
    color:${BODY}}
  .art{width:420px;height:420px;display:flex;align-items:center;justify-content:center}
  .art svg{width:100%;height:100%}
</style></head><body>
  <div>
    <div class="kicker">${e.kicker}</div>
    <h1>${e.title}</h1>
    <div class="sub">${e.sub}</div>
    <div class="wm">Driftwood Wealth</div>
  </div>
  <div class="art">${e.art}</div>
</body></html>`;

const b = await chromium.launch({ executablePath: EXE });
const ctx = await b.newContext({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
for (const [stem, e] of Object.entries(ESSAYS)) {
  const p = await ctx.newPage();
  await p.setContent(card(e), { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(150);
  await p.screenshot({ path: path.join(OUT, `${stem}.png`) });
  await p.close();
  console.log(`wrote docs/og/${stem}.png`);
}
await b.close();
