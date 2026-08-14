// Behaviour guard for coordination-atlas.html — the Coordination Atlas workspace.
//
// The rule this file exists to enforce is the one in CLAUDE.md, written after the 2026-07-26
// leakage.html incident: when a page accepts the same household field from BOTH a URL parameter and
// a UI-driven value, the URL path gets its own test. It is not enough to have exercised the
// dropdown. This workspace has exactly that shape and then some — it carries the household in its
// own hash query (that is what "Copy a link for your CPA" mints) while dw-context.js merges
// `location.search` from a link arriving off any other Driftwood page.
//
// So the workspace does not parse a portfolio at all: it hands the raw parameter to
// dwTaxContext.save(), which owns parsePortfolioLike(). This file drives the REAL dw-context.js
// alongside the real inline script to prove that is still true — `port=2M` and `port=2000000` must
// scale the same figure, and neither may render the "$0/yr" that the original bug produced.
//
// Self-contained, in the style of the other flows in this directory: no jsdom, a shim that
// auto-vivifies anything the render path touches, and assertions against the HTML actually emitted.
'use strict';
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..', '..');
const TEMPLATE = path.join(ROOT, 'src', 'drift', 'web', 'coordination-atlas.html');
const CONTEXT = path.join(ROOT, 'src', 'drift', 'web', 'dw-context.js');
const BUILT_STATEMAP = path.join(ROOT, 'docs', 'statemap.html');

// The real Atlas payload, read out of the shipped exhibit rather than mocked: a fixture would let
// the test keep passing after the law review changed a regime the assertions below depend on.
function atlasData() {
  const html = fs.readFileSync(BUILT_STATEMAP, 'utf8');
  const m = html.match(/window\.__STATE__ = ([\s\S]*?);\s*\n/);
  if (!m) throw new Error('no window.__STATE__ in docs/statemap.html — run `drift statemap`');
  return JSON.parse(m[1]);
}

function workspaceScript() {
  const html = fs.readFileSync(TEMPLATE, 'utf8');
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  const main = scripts.find((s) => s.includes('The Coordination Atlas workspace'));
  if (!main) throw new Error('coordination-atlas.html workspace script not found');
  return main;
}

// ── DOM shim ────────────────────────────────────────────────────────────────────────────────
function makeEl(tag) {
  const attrs = {};
  const o = { tagName: tag || 'div', textContent: '', innerHTML: '', style: {}, hidden: false, value: '', children: [] };
  o.getAttribute = (k) => (k in attrs ? attrs[k] : null);
  o.setAttribute = (k, v) => { attrs[k] = String(v); };
  o.removeAttribute = (k) => { delete attrs[k]; };
  o.hasAttribute = (k) => k in attrs;
  o.addEventListener = () => {};
  o.querySelector = () => null;
  o.querySelectorAll = () => [];
  o.insertBefore = (child) => { o.children.push(child); };
  o.appendChild = (child) => { o.children.push(child); };
  o.removeChild = () => {};
  o.select = () => {};
  o.closest = () => null;
  return o;
}

function makeLocation(hash, search) {
  return {
    hash: hash || '',
    search: search || '',
    href: 'https://driftwoodwealth.com/coordination-atlas.html' + (search || '') + (hash || ''),
    pathname: '/coordination-atlas.html',
  };
}

/**
 * Boot the workspace exactly as a browser would: dw-context.js first (it is a <head> script and
 * merges location.search into storage before anything else runs), then the page's inline module.
 * Returns the shim's element store so assertions can read what was rendered.
 */
function boot({ hash = '', search = '', stored = null } = {}) {
  const store = {};
  const routeLinks = ['atlas', 'assessment', 'review'].map((r) => {
    const el = makeEl('a');
    el.setAttribute('data-route-link', r);
    return el;
  });

  const memory = {};
  if (stored) memory.dw_tax_context = JSON.stringify(stored);
  global.localStorage = {
    getItem: (k) => (k in memory ? memory[k] : null),
    setItem: (k, v) => { memory[k] = String(v); },
    removeItem: (k) => { delete memory[k]; },
  };

  const location = makeLocation(hash, search);
  const document = {
    getElementById: (id) => (store[id] || (store[id] = makeEl())),
    querySelectorAll: (sel) => (sel === '[data-route-link]' ? routeLinks : []),
    querySelector: () => null,
    createElement: (tag) => makeEl(tag),
    addEventListener: () => {},
    body: makeEl('body'),
    documentElement: makeEl('html'),
  };

  const atlas = atlasData();
  global.document = document;
  global.location = location;
  global.URLSearchParams = require('url').URLSearchParams;
  // node 22 defines a getter-only global `navigator`; the page only reads window.navigator.
  const navigator = { clipboard: null };
  global.window = {
    document, location, localStorage: global.localStorage, navigator,
    innerWidth: 1400, addEventListener: () => {}, print: () => {},
    setTimeout, clearTimeout, __STATE__: atlas,
  };
  global.window.window = global.window;

  // eslint-disable-next-line no-eval
  eval(fs.readFileSync(CONTEXT, 'utf8'));
  if (!global.window.dwTaxContext) throw new Error('dw-context.js did not install window.dwTaxContext');
  // eslint-disable-next-line no-eval
  eval(workspaceScript());

  return { store, main: () => store['cw-main'].innerHTML, ctx: () => global.window.dwTaxContext.get(), location };
}

// ── assertions ──────────────────────────────────────────────────────────────────────────────
function main() {
  const out = {};
  const D = atlasData();

  // 1 · The URL-parameter path, both accepted portfolio forms. This is the guarded rule.
  //     California's modeled figure is ~$X per $1M; on $2M the workspace must show twice that, and
  //     the two spellings of "two million" must land on the identical string.
  const perM = D.states.CA.alpha.usd_per_m;
  const raw = boot({ hash: '#/atlas?state=CA&port=2000000' });
  const shorthand = boot({ hash: '#/atlas?state=CA&port=2M' });
  // Mirrors the page's own money(): millions above $1M, thousands below it.
  const onTwoM = perM * 2;
  const expectDollars = '~' + (onTwoM >= 1000000
    ? '$' + (onTwoM / 1000000).toFixed(onTwoM >= 10000000 ? 1 : 2).replace(/\.0+$/, '') + 'M'
    : '$' + Math.round(onTwoM / 1000) + 'k') + ' a year';

  out['hash_port_raw_dollars_scale_the_figure'] =
    raw.main().includes(expectDollars) || `expected ${expectDollars}; got ${(raw.main().match(/~\$[^<]*a year/) || ['none'])[0]}`;
  out['hash_port_M_shorthand_matches_raw_dollars'] =
    (shorthand.main().match(/~\$[^<]*a year/) || [''])[0] === (raw.main().match(/~\$[^<]*a year/) || ['x'])[0]
      || `2M rendered ${(shorthand.main().match(/~\$[^<]*a year/) || ['none'])[0]}`;
  out['hash_port_never_renders_zero'] =
    !/~\$0\b/.test(shorthand.main()) || 'the "$0/yr" regression is back on the hash path';
  out['hash_port_reaches_the_shared_household'] =
    shorthand.ctx().portfolio === 2000000 || `dwTaxContext.portfolio = ${shorthand.ctx().portfolio}`;

  // 2 · The search-param path — a link arriving from any other Driftwood tool — resolves to the
  //     same number through the same parser, with no hash at all.
  const viaSearch = boot({ search: '?state=CA&port=2M' });
  out['search_param_path_matches_the_hash_path'] =
    (viaSearch.main().match(/~\$[^<]*a year/) || [''])[0] === (raw.main().match(/~\$[^<]*a year/) || ['x'])[0]
      || 'the ?search path and the #hash path disagree on the same portfolio';

  // 3 · With no portfolio the figure is softened to a percentage, never a dollar amount.
  const noPort = boot({ hash: '#/atlas?state=CA' });
  out['impact_defaults_to_a_percentage_of_taxable_assets'] =
    /~\d+\.\d% of taxable assets/.test(noPort.main()) || 'the default impact figure is not a percentage';
  out['impact_offers_to_scale_to_dollars'] =
    noPort.main().includes('Scale this to your taxable portfolio') || 'no progressive portfolio affordance';

  // 4 · The inventory arrives on the URL, lights its levers, and reaches the shared household.
  const drivers = boot({ hash: '#/atlas?state=CA&drivers=qsbs-founder,relocation' });
  out['drivers_from_the_url_mark_levers_live'] =
    drivers.main().includes('Live for your household') || 'no lever was marked live from ?drivers';
  out['drivers_reach_the_shared_household'] =
    drivers.ctx().drivers.join(',').includes('qsbs-founder') || `drivers = ${drivers.ctx().drivers}`;
  out['live_summary_counts_seven_levers'] =
    /\d of 7 levers live for your household/.test(drivers.main()) || 'the live-lever summary is missing';

  // 5 · Legacy driver slugs still restore a visitor's boxes rather than dropping them silently.
  const legacy = boot({ hash: '#/assessment?state=CA&drivers=multi-state' });
  out['legacy_multi_state_slug_maps_onto_relocation'] =
    legacy.main().includes('Residency sequencing') || 'a pre-upgrade personalized link lost its checked box';

  // 6 · Derived regime notes come from the Atlas data, and only where it supports them.
  //     California is decoupled from §1202; Illinois conforms. Neither sentence is modeled here.
  const caQsbs = boot({ hash: '#/assessment?state=CA&drivers=qsbs-founder' }).main();
  const ilQsbs = boot({ hash: '#/assessment?state=IL&drivers=qsbs-founder' }).main();
  out['qsbs_note_follows_the_states_own_conformance'] =
    (caQsbs.includes('decoupled from §1202') && ilQsbs.includes('conforms to §1202'))
    || 'the QSBS regime note does not track the dataset';

  // 7 · The Assessment is a ruled ledger — ten rows, two columns, no scoring device.
  const assess = boot({ hash: '#/assessment?state=IL' }).main();
  out['assessment_lists_exactly_ten_factors'] =
    (assess.match(/data-factor="/g) || []).length === 10 || `${(assess.match(/data-factor="/g) || []).length} rows`;
  out['assessment_carries_the_state_column'] =
    assess.includes('What Illinois does about it') || 'the state column header is missing';
  out['assessment_refuses_to_grade'] =
    assess.includes('No score, no grade') || 'the no-grade promise is gone';

  // 8 · The Review's scope preview is built from the checked inventory, and says so.
  const review = boot({ hash: '#/review?state=IL&drivers=business,trusts' }).main();
  out['review_scope_is_built_from_the_inventory'] =
    review.includes('Built from the 2 factors you checked') || 'the scope preview is not built from the inventory';
  out['review_scope_names_the_matters_back'] =
    review.includes('Succession, and the tax the entity pays meanwhile') && review.includes('Trust funding &amp; titling')
      || 'the scope preview does not name the checked matters';
  const emptyReview = boot({ hash: '#/review?state=IL&drivers=' }).main();
  out['review_with_nothing_checked_asks_for_the_inventory'] =
    emptyReview.includes('there is nothing to name back') || 'the empty scope state is missing';

  // 9 · The three printable documents, each stamped with the date it was generated.
  const today = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  const stateDoc = boot({ hash: '#/brief?state=IL&drivers=business' }).main();
  out['state_brief_stamps_the_generated_date'] =
    stateDoc.includes('Brief generated ' + today) || 'the single-state brief is not date-stamped';
  out['state_brief_is_addressed_to_the_cpa'] =
    stateDoc.includes("Prepared for the household's CPA") || 'the brief is not addressed to the CPA';

  const cmpDoc = boot({ hash: '#/brief?state=IL&pins=IL,TX&doc=compare' }).main();
  out['comparison_brief_stamps_the_generated_date'] =
    cmpDoc.includes('Brief generated ' + today) || 'the comparison brief is not date-stamped';
  out['comparison_brief_carries_a_difference_report'] =
    cmpDoc.includes('Where they differ') && cmpDoc.includes('Illinois:') || 'no difference report in the comparison brief';
  out['comparison_brief_names_both_states'] =
    cmpDoc.includes('Illinois and Texas') || 'the comparison title does not name the pinned states';

  const moveDoc = boot({ hash: '#/brief?state=IL&move=TX&drivers=relocation&doc=move' }).main();
  out['move_brief_stamps_the_generated_date'] =
    moveDoc.includes('Brief generated ' + today) || 'the move brief is not date-stamped';
  out['move_brief_is_directional'] =
    moveDoc.includes('Illinois → Texas') || 'the move brief is not directional';
  out['move_brief_asks_which_side_of_the_line'] =
    moveDoc.includes('Which side of the line') && moveDoc.includes('The change of domicile itself')
      || 'the move brief drops the sequencing section';

  // A doc that the household has not earned falls back to the state brief rather than rendering empty.
  const noPins = boot({ hash: '#/brief?state=IL&doc=compare' }).main();
  out['comparison_brief_without_pins_falls_back'] =
    noPins.includes("Prepared for the household's CPA") && !noPins.includes('Where they differ')
      || 'an unearned comparison document rendered anyway';

  // 10 · The move tab lists only the levers that actually change, and says what is unchanged.
  //      Illinois → Indiana is the useful pair: four of the seven levers agree, so both halves of
  //      the reading are exercised. (Illinois → Texas shares none, which is why it is not used here.)
  const move = boot({ hash: '#/atlas?state=IL&move=IN&tab=move' }).main();
  out['move_tab_reports_what_is_unchanged'] =
    move.includes('Unchanged at the line:') || 'the move view does not report the levers that agree';
  out['move_tab_omits_the_levers_that_agree'] =
    !/class="cw-moverow[^"]*"[^>]*><div[^>]*><div[^>]*>Basis step-up/.test(move)
      || 'a lever that does not change was listed as a change';
  out['move_tab_reads_from_the_household_state'] =
    move.includes('A move is a sequence, not a destination') || 'the move tab did not render';

  // 11 · The compare view's segmented control appears only once there are two states to differ.
  const onePin = boot({ hash: '#/atlas?state=IL&pins=IL&tab=compare' }).main();
  const twoPins = boot({ hash: '#/atlas?state=IL&pins=IL,TX&tab=compare' }).main();
  out['segmented_control_is_hidden_with_one_pin'] =
    !onePin.includes('Differences only') || 'the difference filter appears with nothing to compare';
  out['segmented_control_appears_with_two_pins'] =
    twoPins.includes('All eight') && twoPins.includes('Differences only') || 'the difference filter is missing';

  // 12 · The CPA link carries the whole household back out again.
  const round = boot({ hash: '#/atlas?state=CA&port=2M&drivers=relocation,trusts&pins=CA,TX&move=TX' });
  const mint = round.location.hash;
  out['cpa_link_carries_state_portfolio_and_inventory'] =
    mint.includes('state=CA') && mint.includes('port=2000000') && mint.includes('drivers=relocation,trusts')
    && mint.includes('pins=CA,TX') && mint.includes('move=TX')
      || `the copied link drops household state: ${mint}`;
  const rehydrated = boot({ hash: mint });
  out['a_copied_link_rehydrates_the_same_workspace'] =
    rehydrated.ctx().portfolio === 2000000 && rehydrated.ctx().state === 'CA'
      || 'a link minted by the workspace does not restore the household it carried';

  // 13 · Route resolution, including a hostile one.
  out['unknown_route_falls_back_to_the_atlas'] =
    boot({ hash: '#/nonsense?state=IL' }).main().includes('lever by lever') || 'an unknown route did not fall back';

  let failed = 0, total = 0;
  for (const k of Object.keys(out)) {
    total++;
    const ok = out[k] === true;
    if (!ok) failed++;
    console.log(`${ok ? 'PASS' : 'FAIL'}  coordination-atlas.${k}` + (ok ? '' : ` => ${out[k]}`));
  }
  console.log(`\n${total - failed}/${total} coordination-atlas assertions passed`);
  process.exit(failed ? 1 : 0);
}

main();
