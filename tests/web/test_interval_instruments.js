// The two instruments on the-interval-problem.html, driven through their URL parameters.
//
// The repo rule (CLAUDE.md) is that a page reading the same field from a URL param and from a
// control gets tested through the URL, because those are two code paths for one value and they
// diverge silently. The 2026-07-26 leakage.html incident is the precedent: the dropdown path was
// fine for months while the hand-typed link rendered "$0/yr".
//
// This page has the same shape twice. `?cadence=` and `?missed=` are the shareable form of a
// reading of the essay ("look at the quarterly line", "look at five sessions missed"), so they are
// what a link in a thread or an email will carry, and nobody clicking a control will ever exercise
// them.
//
// The last assertion is the important one, and it is not about parameters at all: the period
// return must be IDENTICAL across all four cadences. That equality is the argument the essay
// makes. If a future edit to the sampler breaks it, the page starts claiming that checking your
// portfolio less often changes what it is worth, which is the opposite of the piece.
'use strict';
const fs = require('fs');
const path = require('path');

const TEMPLATE = path.join(__dirname, '..', '..', 'src', 'drift', 'web', 'the-interval-problem.html');

function scripts() {
  const html = fs.readFileSync(TEMPLATE, 'utf8');
  return [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
}

function dataScript() {
  const s = scripts().find((x) => x.includes('window.__INTERVAL__'));
  if (!s) throw new Error('the generated __INTERVAL__ data block is missing from the page');
  return s;
}

function instrumentScript() {
  const s = scripts().find((x) => x.includes('function parseCadence'));
  if (!s) throw new Error('the instrument script is missing from the page');
  return s;
}

// ── a DOM the instruments can be driven through ──────────────────────────────────────────────
// Ids auto-vivify so a stray lookup never throws, and elements record what was set on them so the
// assertions can read the rendered state back out.
function makeEl(tag, attrs) {
  const a = Object.assign({}, attrs);
  const el = {
    tagName: tag, textContent: '', value: '', className: '', children: [],
    dataset: {}, style: {},
    setAttribute(k, v) { a[k] = String(v); if (k.startsWith('data-')) this.dataset[k.slice(5)] = String(v); },
    getAttribute(k) { return k in a ? a[k] : null; },
    appendChild(c) { this.children.push(c); this.firstChild = this.children[0]; return c; },
    removeChild(c) {
      this.children = this.children.filter((x) => x !== c);
      this.firstChild = this.children[0];
      return c;
    },
    addEventListener() {},
    querySelector() { return null; },
    querySelectorAll() { return []; },
  };
  Object.defineProperty(el, 'firstChild', {
    get() { return el.children.length ? el.children[0] : null; },
    set() {}, configurable: true,
  });
  // A real DOM stringifies whatever you assign to textContent. Without this the shim reports a
  // number where the browser would report "9", and an assertion written against the browser's
  // behaviour fails for a reason that does not exist on the page.
  let text = '';
  Object.defineProperty(el, 'textContent', {
    get() { return text; },
    set(v) { text = v === null || v === undefined ? '' : String(v); },
    configurable: true, enumerable: true,
  });
  for (const k of Object.keys(a)) if (k.startsWith('data-')) el.dataset[k.slice(5)] = a[k];
  return el;
}

function drive(search) {
  const byId = {};
  const get = (id) => byId[id] || (byId[id] = makeEl('div'));

  const cadFig = makeEl('svg', { 'data-cadence-figure': 'daily' });
  const ladFig = makeEl('svg', { 'data-ladder-figure': '0' });
  const buttons = ['daily', 'weekly', 'monthly', 'quarterly'].map((c) => {
    const b = makeEl('button', { 'data-cadence': c, 'aria-pressed': String(c === 'daily') });
    return b;
  });
  const tbodies = { '#cadence-table tbody': makeEl('tbody'), '#ladder-table tbody': makeEl('tbody') };

  byId.missed = makeEl('input');
  byId.missed.value = '0';

  global.document = {
    getElementById: get,
    createElement: (t) => makeEl(t),
    createElementNS: (_ns, t) => makeEl(t),
    querySelector(sel) {
      if (sel === '[data-cadence-figure]') return cadFig;
      if (sel === '[data-ladder-figure]') return ladFig;
      return tbodies[sel] || null;
    },
    querySelectorAll(sel) { return sel === '[data-cadence]' ? buttons : []; },
  };
  const location = { search };
  global.window = { location };
  global.location = location;
  global.URLSearchParams = require('url').URLSearchParams;

  // eslint-disable-next-line no-eval
  eval(dataScript() + '\n' + instrumentScript());

  return {
    cadence: cadFig.getAttribute('data-cadence-figure'),
    pressed: buttons.filter((b) => b.getAttribute('aria-pressed') === 'true')
      .map((b) => b.getAttribute('data-cadence')),
    missed: ladFig.getAttribute('data-ladder-figure'),
    slider: byId.missed.value,
    count: get('c-count').textContent,
    total: get('c-total').textContent,
    worstStep: get('c-step').textContent,
    drawdown: get('c-dd').textContent,
    missedNote: get('missed-note').textContent,
    ladderCap: get('ladder-cap').textContent,
    cadenceCap: get('cadence-cap').textContent,
    level: get('u-level').textContent,
    data: global.window.__INTERVAL__,
  };
}

// ── assertions ───────────────────────────────────────────────────────────────────────────────
const out = {};
const eq = (name, got, want) => { out[name] = got === want ? true : `got ${JSON.stringify(got)}, want ${JSON.stringify(want)}`; };
const ok = (name, cond, why) => { out[name] = cond ? true : why; };

// No parameters: the essay's own reading.
const bare = drive('');
eq('default-cadence', bare.cadence, 'daily');
eq('default-missed', bare.missed, '0');
eq('default-pressed-one', bare.pressed.length, 1);
eq('default-pressed-daily', bare.pressed[0], 'daily');

// The cadence parameter, including the alias and the legacy spelling.
eq('cadence-monthly', drive('?cadence=monthly').cadence, 'monthly');
eq('cadence-quarterly', drive('?cadence=quarterly').cadence, 'quarterly');
eq('cadence-alias-q', drive('?cadence=q').cadence, 'quarterly');
eq('cadence-alias-week', drive('?cadence=Week').cadence, 'weekly');
eq('cadence-legacy-frame', drive('?frame=weekly').cadence, 'weekly');
eq('cadence-garbage-falls-back', drive('?cadence=yearly').cadence, 'daily');
eq('cadence-empty-falls-back', drive('?cadence=').cadence, 'daily');

// A cadence from the URL must also move the control, or the reader who arrives by link sees a
// chart and a button row that disagree about what is selected.
const monthly = drive('?cadence=monthly');
eq('cadence-url-presses-button', monthly.pressed.join(), 'monthly');
eq('cadence-url-readout-count', monthly.count, String(monthly.data.cadences.monthly.readings.length));

// The missed parameter, with the clamping a hand-typed link needs.
eq('missed-five', drive('?missed=5').missed, '5');
eq('missed-five-slider', drive('?missed=5').slider, '5');
eq('missed-clamped-high', drive('?missed=99').missed, '10');
eq('missed-clamped-low', drive('?missed=-4').missed, '0');
eq('missed-garbage', drive('?missed=abc').missed, '0');
eq('missed-rounded', drive('?missed=3.7').missed, '4');
eq('missed-empty', drive('?missed=').missed, '0');

// Both parameters at once, which is what a real shared link looks like.
const both = drive('?cadence=quarterly&missed=5');
eq('both-cadence', both.cadence, 'quarterly');
eq('both-missed', both.missed, '5');

// THE ARGUMENT. Every cadence must report the same period return: the interval changes what the
// investor saw, never what the money did.
const totals = ['daily', 'weekly', 'monthly', 'quarterly'].map((c) => drive('?cadence=' + c).total);
ok('period-return-identical-across-cadences', new Set(totals).size === 1,
  `cadences disagree about the period return: ${JSON.stringify(totals)}`);

// And the deepest observed fall must shrink as the interval lengthens, which is the other half of
// the claim. (The worst SINGLE reading does not, deliberately; the essay says so in prose.)
const dd = ['daily', 'weekly', 'monthly', 'quarterly']
  .map((c) => Math.abs(parseFloat(bare.data.cadences[c].maxDrawdown)));
ok('deepest-fall-shrinks-with-the-interval',
  dd[0] >= dd[1] && dd[1] >= dd[2] && dd[2] >= dd[3],
  `deepest observed falls are not monotone in the interval: ${JSON.stringify(dd)}`);

// The captions have to restate the state, not a build-time constant: they are what a screen reader
// and a no-mouse reader get instead of the chart.
ok('ladder-caption-is-rendered', /Holding every session returned/.test(bare.ladderCap),
  `ladder caption not rendered: ${bare.ladderCap}`);
ok('missed-note-tracks-the-value', /5 sessions missed/.test(drive('?missed=5').missedNote),
  `missed note did not follow the parameter: ${drive('?missed=5').missedNote}`);
ok('cadence-caption-names-the-cadence', /every quarter/.test(drive('?cadence=quarterly').cadenceCap),
  `cadence caption did not follow the parameter: ${drive('?cadence=quarterly').cadenceCap}`);

// The dated update reads its level from the same series as the figures.
eq('update-level-matches-series', bare.level.replace(/,/g, ''),
  bare.data.latest.level.toFixed(2));

let failed = 0, total = 0;
for (const k of Object.keys(out)) {
  total++;
  const good = out[k] === true;
  if (!good) failed++;
  console.log(`${good ? 'PASS' : 'FAIL'}  interval-instruments.${k}` + (good ? '' : ` => ${out[k]}`));
}
console.log(`\n${total - failed}/${total} assertions passed`);
process.exit(failed ? 1 : 0);
