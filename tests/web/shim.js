// Zero-dependency DOM/window/fetch shim for the Tax Lab inline script.
// It is a LOGIC harness (asserts on produced HTML + state), not a visual/layout test.
// Covers exactly the browser API surface src/drift/web/taxlab.html uses.
'use strict';
const fs = require('fs');
const path = require('path');

// The estate/lead/statemap flows this harness drives moved from the public TaxLab into the
// Advisor Workspace when TaxLab became a public exhibit (commit 7035c86). Point at their home.
const TEMPLATE = path.join(__dirname, '..', '..', 'src', 'drift', 'web', 'workspace.html');

function templateText() { return fs.readFileSync(TEMPLATE, 'utf8'); }
function cssText() { return fs.readFileSync(path.join(__dirname, '..', '..', 'src', 'drift', 'web', 'driftwood.css'), 'utf8'); }

// The main inline <script> (the one with the app), with the trailing init() call stripped so
// flows can seed S/CONFIG and drive specific functions deterministically.
function extractInline() {
  const html = templateText();
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
  const main = scripts.find(s => s.includes('function renderEstate'));
  if (!main) throw new Error('main inline script not found');
  return main.replace(/\ninit\(\);\s*$/, '\n');
}

let _n = 0;
function makeEl(store, id) {
  if (store[id]) return store[id];
  const o = { id, value: '', textContent: '', innerHTML: '', disabled: false,
    min: '', max: '', step: '', style: {}, dataset: {}, _cls: new Set(), _attr: {} };
  o.classList = {
    add: c => o._cls.add(c), remove: c => o._cls.delete(c),
    toggle: (c, f) => { const on = f === undefined ? !o._cls.has(c) : f; on ? o._cls.add(c) : o._cls.delete(c); return on; },
    contains: c => o._cls.has(c),
  };
  o.setAttribute = (k, v) => { o._attr[k] = String(v); };
  o.getAttribute = k => (k in o._attr ? o._attr[k] : null);
  o.removeAttribute = k => { delete o._attr[k]; };
  o.addEventListener = () => {}; o.focus = () => {}; o.reportValidity = () => true;
  o.querySelector = () => makeEl(store, '__q' + (_n++));
  o.querySelectorAll = () => []; o.insertAdjacentHTML = () => {};
  store[id] = o; return o;
}

// Install global document/window/fetch. Returns handles for assertions.
function installEnv(search) {
  const store = {};
  const events = [];      // track() events: [name, props]
  const fetchLog = [];    // {url, body}
  let fetchResp = { ok: true, status: 200 };
  let fetchThrows = false;

  global.document = {
    getElementById: id => makeEl(store, id),
    querySelector: () => makeEl(store, '__q' + (_n++)),
    querySelectorAll: () => [],
    createElement: () => makeEl(store, '__c' + (_n++)),
    body: makeEl(store, '__body'),
    addEventListener: () => {},
  };
  const location = { search: search || '', href: 'http://test/' + (search || '') };
  global.window = {
    __STATE__: null, location, history: { replaceState: () => {} },
    matchMedia: () => ({ matches: false, addEventListener: () => {} }),
    print: () => {}, addEventListener: () => {},
    plausible: (n, o) => events.push([n, o && o.props]),
  };
  global.location = location;
  global.history = global.window.history;
  global.URL = require('url').URL;
  global.URLSearchParams = require('url').URLSearchParams;
  global.setTimeout = () => {}; global.requestAnimationFrame = () => {};
  global.fetch = (url, opts) => {
    fetchLog.push({ url, body: opts && opts.body ? JSON.parse(opts.body) : null });
    return fetchThrows ? Promise.reject(new Error('network'))
      : Promise.resolve({ ok: fetchResp.ok, status: fetchResp.status });
  };

  return {
    events, fetchLog,
    el: id => makeEl(store, id),
    setFetch: r => { fetchResp = r; fetchThrows = false; },
    setFetchThrows: () => { fetchThrows = true; },
  };
}

// Synthetic __STATE__ shaped like build_taxlab() output — enough for the estate/lead flows.
const FIXTURE = {
  header: { short_term_share: 0.95, avg_holding_days: 63, annual_turnover: 4.0, generated: 'test' },
  profile: { years: 9, pretax_return: 0.5 },
  states: { '—': [0, 0], IL: [0.0495, 0.0495], TX: [0, 0], NY: [0.0882, 0.0882], PA: [0.0307, 0.0307] },
  // Mirrors FED_BRACKETS in src/drift/taxlab.py — rates() does S.brackets[+$("bracket").value],
  // so this must be a populated ARRAY (an empty {} made b undefined -> b.lt threw in renderDecisionTree).
  brackets: [
    { label: '22% ordinary · 15% LT', ord: 0.22, lt: 0.15, niit: 0.0 },
    { label: '24% ordinary · 15% LT', ord: 0.24, lt: 0.15, niit: 0.0 },
    { label: '32% ordinary · 15% LT · NIIT', ord: 0.32, lt: 0.15, niit: 0.038 },
    { label: '35% ordinary · 20% LT · NIIT', ord: 0.35, lt: 0.20, niit: 0.038 },
    { label: '37% ordinary · 20% LT · NIIT (top)', ord: 0.37, lt: 0.20, niit: 0.038 },
  ],
  assumptions: {
    growth_rate: 0.07, horizon_years: 30,
    estate: {
      fed_exemption_indiv: 15000000, fed_exemption_couple: 30000000, fed_rate: 0.40,
      il_exclusion: 4000000, il_hb2601_exclusion: 8000000, il_top_rate: 0.16,
      default_individual: 3000000, default_joint: 0, default_trust: 1000000,
      estate_max: 30000000, estate_step: 100000, trust_compression_top_threshold: 15650,
      state_estate: { WA: 'estate', NY: 'estate', MA: 'estate', MD: 'both', PA: 'inheritance', NJ: 'inheritance' },
      // Mirrors build_taxlab's injected drift.state_facts.IL_AG_CURVE so the estate calc can run.
      il_ag_curve: [[0, 0, 0.285], [1000000, 285000, 0.135], [4000000, 690000, 0.145], [6000000, 980000, 0.160], [10000000, 1620000, 0.160]],
    },
    strategy: {},
  },
  // Minimal embed of the State Tax Map dataset (build_taxlab attaches the full version) so the harness
  // can exercise the in-place dimension tabs over the cartogram.
  statemap: {
    dimensions: [
      { key: 'cg', label: 'Income & gains', title: 'Where a harvested loss lands',
        legend: [['notax', '#d8cfbc', 'No tax on gains'], ['conforming', '#7faa97', 'Conforming'],
                 ['nonconforming', '#9b4439', 'Non-conforming'], ['expiring', '#c1a35b', 'Expiring'],
                 ['lt_only', '#15806a', 'Long-term only']] },
      { key: 'estate', label: 'Estate', title: 'Estate & inheritance tax at death',
        legend: [['none', '#d8cfbc', 'None'], ['estate', '#15806a', 'Estate tax'],
                 ['inheritance', '#c1a35b', 'Inheritance tax'], ['both', '#9b4439', 'Both']] },
      { key: 'alpha', label: 'Tax Management Impact', title: "How much a state's tax rules can affect a tax-managed portfolio",
        legend: [['a', '#cfe0d6', 'lower'], ['b', '#9ec9b6', ''], ['c', '#5ea98c', ''],
                 ['d', '#2f8467', ''], ['e', '#15604a', 'higher impact']] },
    ],
    states: {
      IL: { estate: { regime: 'estate', tag: 'estate', note: 'Illinois estate tax — confirm with counsel.', source: 's' },
            alpha: { regime: 'c', tag: '+4.0', note: 'Illustrative tax-management impact.', deeplink: 'leakage.html?state=IL', source: 's' } },
      TX: { estate: { regime: 'none', tag: '', note: 'No state estate or inheritance tax.', source: 's' } },
      NY: { estate: { regime: 'estate', tag: 'estate', note: 'State estate tax.', source: 's' } },
      PA: { estate: { regime: 'inheritance', tag: 'inher.', note: 'State inheritance tax.', source: 's' } },
    },
  },
};

module.exports = { templateText, cssText, extractInline, installEnv, FIXTURE, TEMPLATE };
