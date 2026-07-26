// Regression guard for leakage.html's personalized hero (2026-07-26 review fix): the dollarized
// alpha ("+X%/yr recovered (~$Y/yr on this portfolio)") must be correct on the documented
// cold-outreach URL format (?state=IL&port=2000000, raw dollars — see the comment in leakage.html's
// own render()), and the "2M"/"500k" hand-typed shorthand a human is likely to type must resolve to
// the same number rather than silently mis-rendering as "$0/yr" (parseFloat("2M") === 2, not
// 2000000 — the bug an independent review caught on 57b6c1d2).
//
// Self-contained: does NOT depend on tests/web/shim.js, which is wired to workspace.html (deleted
// earlier this session) and currently fails to load — see run.js's try/catch around the legacy flows.
'use strict';
const fs = require('fs');
const path = require('path');

const TEMPLATE = path.join(__dirname, '..', '..', 'src', 'drift', 'web', 'leakage.html');

function extractInline() {
  const html = fs.readFileSync(TEMPLATE, 'utf8');
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  const main = scripts.find((s) => s.includes('function render('));
  if (!main) throw new Error('leakage.html render() script not found');
  return main.replace(/\nload\(\);\s*$/, '\n'); // strip the auto-fetch/render kickoff
}

// Minimal DOM shim: everything render() touches (id lookups auto-vivify so a stray one never
// throws), including href/getAttribute/setAttribute for the CTA links it decorates.
function makeEl() {
  const attrs = {};
  const o = { textContent: '', innerHTML: '', style: {}, id: '', href: '' };
  o.getAttribute = (k) => (k in attrs ? attrs[k] : null);
  o.setAttribute = (k, v) => { attrs[k] = String(v); };
  o.removeAttribute = (k) => { delete attrs[k]; };
  o.querySelectorAll = () => [];
  o.insertAdjacentHTML = () => {};
  o.addEventListener = () => {};
  return o;
}

function driveLeakage(search, state) {
  const store = {};
  global.document = {
    getElementById: (id) => (store[id] || (store[id] = makeEl())),
    querySelectorAll: () => [],
  };
  const location = { search };
  global.window = { dwTaxContext: null, location };
  global.location = location;
  global.URLSearchParams = require('url').URLSearchParams;
  const scriptBody = extractInline();
  // eslint-disable-next-line no-eval
  eval(scriptBody + '\nrender(state);');
  return store;
}

// Mirrors drift.leakage.build_leakage()'s shape for California (verified against the real engine:
// state_alpha.CA = {before: 0.4, after: 5.1, alpha: 4.7}).
const STATE = {
  header: { horizon_years: 30 },
  headline: { alpha_low: 3.7, alpha_high: 4.7, pretax_before: 9.4, pretax_after: 9.1 },
  before: { atc_low: 0.4, atc_high: 2.7, keep_pct: 9 },
  after: { atc_low: 5.1, atc_high: 6.3, keep_pct: 41 },
  index: { atc_low: 6.18, atc_high: 6.89 },
  levers: [],
  states: [],
  state_alpha: { CA: { before: 0.4, after: 5.1, alpha: 4.7 } },
  state_names: { CA: 'California' },
};

function main() {
  const out = {};

  // Documented format (the code's own inline comment: "?state=IL&port=2000000") — the URL path an
  // independent review flagged as untested; must show the correct dollarized recovery.
  const raw = driveLeakage('?state=CA&port=2000000', STATE);
  out.raw_dollars_headline = raw['h-alpha'].textContent === '0.4%';
  out.raw_dollars_dollarized = raw['h-note'].innerHTML.includes('$94,000');

  // Hand-typed shorthand a cold-outreach link is likely to use — must resolve to the SAME number,
  // not silently render "$0/yr" (the exact defect the review caught: parseFloat("2M") === 2).
  const shorthandM = driveLeakage('?state=CA&port=2M', STATE);
  out.shorthand_m_dollarized = shorthandM['h-note'].innerHTML.includes('$94,000');
  out.shorthand_m_not_zero = !shorthandM['h-note'].innerHTML.includes('$0/yr');

  const shorthandK = driveLeakage('?state=CA&port=500k', STATE);
  out.shorthand_k_dollarized = shorthandK['h-note'].innerHTML.includes('$23,500');

  // No portfolio param at all: alpha still shown, just never dollarized (no stray "$0/yr").
  const noPort = driveLeakage('?state=CA', STATE);
  out.no_port_no_dollar_stray = !noPort['h-note'].innerHTML.includes('$0/yr');
  out.no_port_still_has_alpha = noPort['h-note'].innerHTML.includes('+4.7%/yr');

  let failed = 0;
  for (const k of Object.keys(out)) {
    const ok = out[k] === true;
    if (!ok) failed++;
    console.log(`${ok ? 'PASS' : 'FAIL'}  leakage-personalization.${k}` + (ok ? '' : ` => ${out[k]}`));
  }
  console.log(`\n${Object.keys(out).length - failed}/${Object.keys(out).length} assertions passed`);
  process.exit(failed ? 1 : 0);
}

main();
