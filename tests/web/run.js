// DOM-shim verification harness for client-side UI logic that can't be exercised by pytest.
// Run: `node tests/web/run.js` — exits non-zero on any failed assertion (CI-gateable).
//
// The Tax Lab UI flows this harness used to drive (estate cliff rendering, the lead funnel, the
// mobile state picker, the State Tax Map tabs, and a11y/token static guards) lived on
// workspace.html, deleted as an orphan page during the 2026 redesign (its 10 Python-side tests were
// removed at the same time — see git history). Removed here to complete that same cleanup on the JS
// side, rather than asserting forever against a file that can never exist again. If any of that
// coverage still matters, it needs an owner decision on where the underlying UI now lives (if
// anywhere) and fresh tests written against that — not a resurrection of these flows.
'use strict';

const fs = require('fs');
const path = require('path');

function extractInline(templatePath, marker) {
  const html = fs.readFileSync(templatePath, 'utf8');
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
  const main = scripts.find((s) => s.includes(marker));
  if (!main) throw new Error(`${marker} not found in ${templatePath}`);
  return main;
}

async function main() {
  const flows = [];

  // leakage.html personalization (2026-07-26 review fix): self-contained script, run as a
  // subprocess so its own PASS/FAIL detail prints directly.
  flows.push(['leakage-personalization', await (async () => {
    try {
      const { execFileSync } = require('child_process');
      execFileSync(process.execPath, [path.join(__dirname, 'test_leakage_personalization.js')], { stdio: 'inherit' });
      return {};
    } catch (e) {
      return { [`ERROR: ${e.message}`]: false };
    }
  })()]);

  // Layers 1-2 of the operating system (dw-context.js): the household context's drivers field and
  // the "Your Next Decision" recommendation engine. Same subprocess pattern, so its own PASS/FAIL
  // detail prints directly.
  flows.push(['next-decision', await (async () => {
    try {
      const { execFileSync } = require('child_process');
      execFileSync(process.execPath, [path.join(__dirname, 'test_next_decision.js')], { stdio: 'inherit' });
      return {};
    } catch (e) {
      return { [`ERROR: ${e.message}`]: false };
    }
  })()]);

  // the-interval-problem.html's two instruments, driven through ?cadence= and ?missed=. Same
  // subprocess pattern; the flow also pins the essay's own claim that the period return is
  // identical on every checking cadence.
  flows.push(['interval-instruments', await (async () => {
    try {
      const { execFileSync } = require('child_process');
      execFileSync(process.execPath, [path.join(__dirname, 'test_interval_instruments.js')], { stdio: 'inherit' });
      return {};
    } catch (e) {
      return { [`ERROR: ${e.message}`]: false };
    }
  })()]);

  // the-shortest-line.html's window instrument, driven through ?stop=.
  flows.push(['shortest-line', await (async () => {
    try {
      const { execFileSync } = require('child_process');
      execFileSync(process.execPath, [path.join(__dirname, 'test_shortest_line.js')], { stdio: 'inherit' });
      return {};
    } catch (e) {
      return { [`ERROR: ${e.message}`]: false };
    }
  })()]);

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

module.exports = { extractInline };

main().catch((e) => { console.error(e); process.exit(2); });
