// Committed DOM-shim verification harness for the Tax Lab UI flows.
// Run: `node tests/web/run.js` — exits non-zero on any failed assertion (CI-gateable).
'use strict';
const shim = require('./shim');

// Eval the inline script (init stripped) with env installed, then run the driver's async __run().
async function drive(search, driver) {
  const env = shim.installEnv(search);
  const FIXTURE = JSON.parse(JSON.stringify(shim.FIXTURE));
  global.window.__STATE__ = FIXTURE;
  const scriptBody = shim.extractInline();
  // eslint-disable-next-line no-eval
  eval(scriptBody + '\n' + driver);
  return await globalThis.__run();
}

// ---- Flow: estate strict conditional rendering (T2) + dynamic federal exemption (T3) ----
const estateDriver = `
globalThis.__run = async () => {
  const out = {}; S = FIXTURE;
  const setv = (id,v) => { document.getElementById(id).value = String(v); };
  const html = () => document.getElementById('estresult').innerHTML;
  // TX — no state estate tax -> green card, no Illinois leakage
  document.getElementById('state').value = 'TX';
  setv('estind',5000000); setv('estjoint',0); setv('esttrust',0); renderEstate();
  out.tx_no_state_card = html().includes('No State Estate Tax');
  out.tx_no_illinois   = !/Illinois/.test(html());
  out.tx_green         = html().includes('est-cliff safe');
  // Exemption (T3): joint=0 -> $15.0M individual
  const p0 = document.getElementById('estparams').innerHTML;
  out.exempt_individual = p0.includes('$15.0 Million') && p0.includes('individual');
  // joint>0 -> $30.0M couple
  setv('estjoint',2000000); renderEstate();
  const p1 = document.getElementById('estparams').innerHTML;
  out.exempt_couple = p1.includes('$30.0 Million') && p1.includes('couple');
  // IL over exclusion -> cliff (danger)
  document.getElementById('state').value = 'IL';
  setv('estind',10000000); setv('estjoint',0); setv('esttrust',0); renderEstate();
  out.il_cliff = html().includes('Illinois Estate Tax Cliff');
  // IL under exclusion -> $0 safe
  setv('estind',3000000); renderEstate();
  out.il_under = html().includes('under the exclusion');
  // NY -> neutral card naming the environment, NO Illinois numbers, not green
  document.getElementById('state').value = 'NY';
  setv('estind',12000000); renderEstate();
  const ny = html();
  out.ny_neutral     = ny.includes('est-cliff neutral') && ny.includes('a state estate tax');
  out.ny_no_illinois = !/Illinois/.test(ny);
  out.ny_not_green   = !ny.includes('est-cliff safe');
  return out;
};`;

// ---- Flow: lead funnel (regression guard for the money path) ----
const leadDriver = `
globalThis.__run = async () => {
  const out = {}; S = FIXTURE;
  stateBleed = () => ({ P:1000000, stateTotal:200000, totalTotal:958000, horizon:30, totalAnnual:31900, stateAnnual:9600 });
  document.getElementById('state').value = 'IL';
  const tick = async () => { await Promise.resolve(); await Promise.resolve(); await Promise.resolve(); };
  const form = (email) => { ctaForm(); document.getElementById('leademail').value = email; document.getElementById('leadsend').disabled = false; };
  // success on 2xx + Web3Forms endpoint + UTM in payload
  ENV.setFetch({ ok:true, status:200 }); _leadBusy = false; LEAD_UTM = { utm_source:'linkedin', utm_campaign:'il_md' };
  form('a@b.com'); submitLead({ preventDefault(){} }); await tick();
  out.ok_success = document.getElementById('leadcta').innerHTML.includes('Your analysis');   // honest success card (P0-5: no "on its way")
  out.ok_web3forms = ENV.fetchLog[ENV.fetchLog.length-1].url.includes('web3forms.com');
  out.ok_utm = ENV.fetchLog[ENV.fetchLog.length-1].body.utm_campaign === 'il_md';
  // failure on !ok -> error path, not success
  ENV.setFetch({ ok:false, status:500 }); _leadBusy = false; form('a@b.com');
  submitLead({ preventDefault(){} }); await tick();
  const err = document.getElementById('leadcta').innerHTML;
  out.err_recover = err.includes('driftwoodplanning.com') && !err.includes('Your analysis');
  // invalid email -> no POST
  _leadBusy = false; const before = ENV.fetchLog.length; form('nope'); submitLead({ preventDefault(){} });
  out.invalid_nopost = ENV.fetchLog.length === before;
  // mailto fallback when no endpoint -> honest copy
  CONFIG.formEndpoint = ''; _leadBusy = false; form('a@b.com'); submitLead({ preventDefault(){} });
  out.mailto_honest = document.getElementById('leadcta').innerHTML.includes('email app should open');
  return out;
};`;

// ---- Flow: mobile state picker (F1) — a severity chip grid (replaced the bare <select>), all wired
// through the single selectState handler (map <-> chips <-> the model stay in sync, no desync path) ----
const mobileDriver = `
globalThis.__run = async () => {
  const out = {}; S = FIXTURE; render = () => {}; flashDisc = () => {};
  buildLeadStates();                                                              // build the mobile chip grid from S.states
  const lhtml = document.getElementById('leadstate').innerHTML;
  out.ss_chip_grid   = /data-st="TX"/.test(lhtml) && /class="grid"/.test(lhtml);  // chips, not a bare native select
  selectState('TX');
  out.ss_sets_state  = document.getElementById('state').value === 'TX';           // the one handler drives the model
  out.ss_fires_event = ENV.events.some(e => e[0] === 'state_selected' && e[1] && e[1].state === 'TX');
  return out;
};`;

// ---- Flow: State Tax Map dimension tabs over the cartogram (cap-gains keeps the calc; the other
// dimensions recolor the map + swap the detail from the embedded statemap dataset) ----
const statemapDriver = `
globalThis.__run = async () => {
  const out = {}; S = FIXTURE;
  document.getElementById('state').value = 'IL';
  buildSmTabs();
  const tabs = document.getElementById('smtabs').innerHTML;
  out.tabs_built = /data-k="estate"/.test(tabs) && /data-k="alpha"/.test(tabs);
  MAPDIM = 'estate'; buildMap();
  out.map_recolors = document.getElementById('usmap').innerHTML.includes('fill="#15806a"');   // IL estate -> teal
  renderDisc(rates());
  out.detail_swaps = document.getElementById('discbody').innerHTML.includes('Estate tax');     // dimension detail, not the rate ledger
  MAPDIM = 'alpha'; buildMap(); renderDisc(rates());
  out.alpha_deeplink = document.getElementById('discbody').innerHTML.includes('leakage.html?state=IL');
  return out;
};`;

// ---- Flow: a11y + honesty + UI-token static guards (must not regress) ----
function staticFlow() {
  const t = shim.templateText();
  return {
    aria_checked: t.includes('aria-checked'),
    aria_pressed: t.includes('aria-pressed'),
    focus_visible: t.includes(':focus-visible'),
    vh_class: t.includes('.vh{'),
    aria_valuetext: t.includes('aria-valuetext'),
    state_estate_js: t.includes('S.assumptions.estate.state_estate'),
    booking_tracked: t.includes('calendly.event_scheduled') && t.includes('booking_scheduled'),  // the real conversion event
    portfolio_tracked: t.includes('portfolio_adjusted'),                                          // lead-gen slider funnel event
    leadstate_markup: t.includes('id="leadstate"'),
    leadstate_wired: t.includes('buildLeadStates(') && t.includes('paintLeadSel('),   // chip grid wired via the shared handler
    leadstate_mobile_css: t.includes('body.on-implementation .leadstate'),
    ui_tokens: shim.cssText().includes('--s4:16px') && shim.cssText().includes('--t-mid'),   // tokens now live in driftwood.css
    reduced_motion: t.includes('prefers-reduced-motion'),
  };
}

async function main() {
  const flows = [];
  // leadDriver references ENV — inject by aliasing inside drive():
  flows.push(['estate', await drive('', estateDriver)]);
  // For the lead flow we need ENV visible to the driver; re-run drive with ENV alias.
  flows.push(['lead', await driveWithEnv(leadDriver)]);
  flows.push(['mobile', await driveWithEnv(mobileDriver)]);
  flows.push(['statemap', await drive('', statemapDriver)]);
  flows.push(['static-a11y', staticFlow()]);

  let failed = 0, total = 0;
  for (const [name, out] of flows) {
    for (const k of Object.keys(out)) {
      total++;
      const ok = out[k] === true;
      if (!ok) failed++;
      console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}.${k}` + (ok ? '' : ` => ${out[k]}`));
    }
  }
  console.log(`\n${total - failed}/${total} assertions passed`);
  process.exit(failed ? 1 : 0);
}

// Variant of drive() that exposes the env handle as ENV to the driver (lead flow needs fetch controls).
async function driveWithEnv(driver) {
  const ENV = shim.installEnv('');
  const FIXTURE = JSON.parse(JSON.stringify(shim.FIXTURE));
  global.window.__STATE__ = FIXTURE;
  const scriptBody = shim.extractInline();
  // eslint-disable-next-line no-eval
  eval(scriptBody + '\n' + driver);
  return await globalThis.__run();
}

main().catch(e => { console.error(e); process.exit(2); });
