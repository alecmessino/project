// Guard for Layers 1-2 of the operating system, both of which live in src/drift/web/dw-context.js:
// the shared household context (state, drivers, steps, done) and the recommendation engine that
// turns it into ONE "Your Next Decision" card per module.
//
// Why this harness and not pytest: the engine is browser JavaScript with no Python mirror, so the
// only way to catch a regression is to run it. Unlike the leakage harness this loads a plain .js
// file, so there is no <script> extraction — just read and eval, which runs all five IIFEs.
//
// Two rules here are load-bearing beyond ordinary correctness:
//
//   * URL params are tested DIRECTLY, not only through a save() call. CLAUDE.md requires this: a
//     value that arrives both from a URL and from the UI is two code paths for one field, and they
//     have silently diverged before (?port=2M rendering "$0/yr" — the 2026-07-26 incident).
//   * The rendered card must contain no currency. That is what keeps this feature outside
//     FIGURE_PROVENANCE.md's standing mandate; if it ever renders a figure, the figure needs a
//     provenance row first and this test should fail until it has one.
'use strict';
const fs = require('fs');
const path = require('path');

const SRC = path.join(__dirname, '..', '..', 'src', 'drift', 'web', 'dw-context.js');

// Auto-vivifying element stub. querySelectorAll returns a real Array (not a bare object) because
// the production code calls .forEach on it, which a NodeList also supports.
function makeEl(id) {
  const attrs = {};
  const o = { textContent: '', innerHTML: '', style: {}, id: id || '', href: '', dataset: {},
              className: '', classList: { add() {}, remove() {}, toggle() {}, contains: () => false } };
  o.getAttribute = (k) => (k in attrs ? attrs[k] : null);
  o.setAttribute = (k, v) => { attrs[k] = String(v); };
  o.removeAttribute = (k) => { delete attrs[k]; };
  o.querySelector = () => null;
  o.querySelectorAll = () => [];
  o.appendChild = () => {};
  o.insertBefore = () => {};
  o.addEventListener = () => {};
  o.closest = () => null;
  return o;
}

// Boot dw-context.js against a synthetic page carrying one #dw-next mount.
function boot({ search = '', stored = null, page = 'leakage' } = {}) {
  const data = stored ? { dw_tax_context: JSON.stringify(stored) } : {};
  const localStorage = {
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => { data[k] = String(v); },
    removeItem: (k) => { delete data[k]; },
  };

  const mount = makeEl('dw-next');
  mount.setAttribute('data-page', page);
  // The card's own .ow-cta lookup after render() — return a stub so the click wiring is exercised.
  mount.querySelector = () => makeEl();

  const head = makeEl('head');
  global.document = {
    readyState: 'complete',                 // run the IIFEs now, not on DOMContentLoaded
    head,
    createElement: (t) => makeEl(t),
    getElementById: (id) => (id === 'dw-next' ? mount : null),
    addEventListener: () => {},
    querySelector: () => null,              // no .journey-rail, no nav on this synthetic page
    querySelectorAll: (sel) => (sel === '#dw-next' ? [mount] : []),
  };
  const location = { search, href: 'https://driftwoodwealth.com/' + page + '.html' + search };
  global.location = location;
  global.localStorage = localStorage;
  global.window = {
    location, localStorage,
    addEventListener: () => {},
    matchMedia: () => ({ matches: true, addEventListener() {}, addListener() {} }),
  };
  global.URL = require('url').URL;
  global.URLSearchParams = require('url').URLSearchParams;

  // eslint-disable-next-line no-eval
  eval(fs.readFileSync(SRC, 'utf8'));

  return { ctx: global.window.dwTaxContext, next: global.window.dwNextBest, mount, data };
}

function main() {
  const out = {};

  // ── Layer 1: the drivers field ────────────────────────────────────────────────────────────────
  let b = boot({});
  b.ctx.save({ drivers: ['concentration', 'multi-state'] });
  out.drivers_persist_via_save =
    JSON.stringify(b.ctx.get().drivers) === JSON.stringify(['concentration', 'multi-state']);

  // clean() whitelists: anything not a known slug is dropped rather than stored and later trusted.
  b = boot({});
  b.ctx.save({ drivers: ['concentration', '<script>', '', 'not-a-driver'] });
  out.drivers_whitelist_rejects_junk =
    JSON.stringify(b.ctx.get().drivers) === JSON.stringify(['concentration']);

  // Canonical order + dedupe, so two visitors who checked the same boxes in a different sequence
  // store byte-identical context.
  b = boot({});
  b.ctx.save({ drivers: ['multi-state', 'concentration', 'concentration'] });
  out.drivers_canonical_order_and_dedupe =
    JSON.stringify(b.ctx.get().drivers) === JSON.stringify(['concentration', 'multi-state']);

  // THE URL PATH, tested on its own — not via save(). See the header note.
  b = boot({ search: '?drivers=concentration,multi-state' });
  out.drivers_from_url_param =
    JSON.stringify(b.ctx.get().drivers) === JSON.stringify(['concentration', 'multi-state']);

  // URL beats storage, the precedence guardrail the whole context file is built on.
  b = boot({ search: '?drivers=concentration', stored: { drivers: ['charity'] } });
  out.url_param_wins_over_stored_drivers =
    JSON.stringify(b.ctx.get().drivers) === JSON.stringify(['concentration']);

  // Unchecking every box is a real answer and must survive as [], not be discarded as "no opinion".
  b = boot({ stored: { drivers: ['charity'] } });
  b.ctx.save({ drivers: [] });
  out.empty_drivers_is_storable = JSON.stringify(b.ctx.get().drivers) === JSON.stringify([]);

  // The visited -> steps migration: a returning visitor's 4-step numbering must not survive to be
  // misread against the 3-step rail.
  b = boot({ stored: { visited: [1, 2, 3, 4], state: 'CA' } });
  out.legacy_visited_is_dropped = b.ctx.get().visited === undefined;

  // ── Layer 2: ranking ──────────────────────────────────────────────────────────────────────────
  b = boot({ search: '?drivers=concentration', page: 'leakage' });
  let r = b.next.recommend('leakage');
  // The reason must name the DRIVER that argued for the tool, not recite the tool's generic pitch.
  out.rank_concentration_first = r.key === 'concentration' && /one position/i.test(r.why);

  b = boot({ search: '?drivers=multi-state', page: 'leakage' });
  out.rank_multistate_to_statemap = b.next.recommend('leakage').key === 'statemap';

  // Never send someone to the page they are already standing on.
  b = boot({ search: '?drivers=concentration', page: 'concentration' });
  out.never_recommends_the_current_page = b.next.recommend('concentration').key !== 'concentration';

  // A cold visitor is taught the system first: the Assessment is what makes everything else
  // personalize, so it outranks any default when nothing at all is known.
  b = boot({ page: 'leakage' });
  r = b.next.recommend('leakage');
  out.empty_context_recommends_the_assessment = r.key === 'score';

  b = boot({ page: 'score' });
  out.score_never_self_recommends = b.next.recommend('score').key !== 'score';

  // Drivers no shipped tool answers must route to the Review and SAY so, rather than being
  // quietly mapped to a calculator that only half addresses them.
  b = boot({ search: '?drivers=trusts,estate-tax', page: 'leakage' });
  r = b.next.recommend('leakage');
  out.review_only_drivers_reach_the_review = r.key === 'review';
  out.review_only_drivers_explain_themselves = /no self-serve analysis covers that/i.test(r.why);

  // ── Rendering ─────────────────────────────────────────────────────────────────────────────────
  b = boot({ search: '?drivers=concentration', page: 'leakage' });
  const html = b.mount.innerHTML;
  out.renders_a_card = html.includes('dwn-k') && html.includes('Your next decision');
  out.renders_one_recommendation = (html.match(/class="ow-cta"/g) || []).length === 1;
  out.renders_outcomes = (html.match(/<li>/g) || []).length >= 3;
  // Platform rule: no dollar or percent figure here. See the header note.
  out.renders_no_currency = !html.includes('$');
  out.renders_no_percent = !/\d%/.test(html);

  // The rail must not mark the step you are standing on as finished. markVisited() records the
  // current step before renderJourney() reads the list back, so without an explicit guard every
  // page told its reader they had completed the page they were still on — and the teal "done" pip
  // beat the blue "you are here" pip in the cascade, so it was visible, not just semantic.
  const ctxSrc = fs.readFileSync(SRC, 'utf8');
  out.rail_current_step_is_not_marked_done = ctxSrc.includes('n !== step && (n < step ||');

  // Never render an empty block, whatever the context.
  b = boot({ search: '?state=CA&bracket=37&port=2000000&drivers=trusts', page: 'taxlab' });
  out.never_renders_empty = b.mount.innerHTML.trim().length > 0;

  let failed = 0;
  const keys = Object.keys(out);
  for (const k of keys) {
    const ok = out[k] === true;
    if (!ok) failed++;
    console.log(`${ok ? 'PASS' : 'FAIL'}  next-decision.${k}` + (ok ? '' : ` => ${out[k]}`));
  }
  console.log(`\n${keys.length - failed}/${keys.length} assertions passed`);
  process.exit(failed ? 1 : 0);
}

main();
