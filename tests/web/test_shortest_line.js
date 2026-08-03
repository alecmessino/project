// The window instrument on the-shortest-line.html, driven through ?stop=.
//
// Same rule as tests/web/test_interval_instruments.js and the same reason (CLAUDE.md): a value
// that arrives both from a control and from a URL is two code paths, and the link is the one
// nobody clicking the slider will ever exercise. A link to a particular window is also the most
// useful thing anyone can share from this page, since the window IS the argument.
'use strict';
const fs = require('fs');
const path = require('path');

const TEMPLATE = path.join(__dirname, '..', '..', 'src', 'drift', 'web', 'the-shortest-line.html');

function scripts() {
  const html = fs.readFileSync(TEMPLATE, 'utf8');
  return [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
}
const dataScript = () => {
  const s = scripts().find((x) => x.includes('window.__ASIA__'));
  if (!s) throw new Error('the generated __ASIA__ data block is missing');
  return s;
};
const instrumentScript = () => {
  const s = scripts().find((x) => x.includes('function parseStop'));
  if (!s) throw new Error('the instrument script is missing');
  return s;
};

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
  // A real DOM composes textContent from the node AND its descendants, and clears children when
  // you assign to it. The ranking rows nest a flag span inside the label span, so a shim that
  // only reports its own text would hide exactly the thing being asserted.
  Object.defineProperty(el, 'textContent', {
    get() {
      return text + el.children.map(function (c) { return c.textContent; }).join('');
    },
    set(v) {
      text = v === null || v === undefined ? '' : String(v);
      el.children = [];
    },
    configurable: true, enumerable: true,
  });
  for (const k of Object.keys(a)) if (k.startsWith('data-')) el.dataset[k.slice(5)] = a[k];
  return el;
}

function drive(search) {
  const byId = {};
  const get = (id) => byId[id] || (byId[id] = makeEl('div'));
  const fig = makeEl('svg', { 'data-paths-figure': '0' });
  const list = makeEl('ol');
  const marks = [29, 50, 246].map((s) => makeEl('button', { 'data-stop': String(s) }));
  byId.stop = makeEl('input');
  byId.stop.value = '0';
  byId['rank-list'] = list;

  global.document = {
    getElementById: (id) => (id === 'rank-list' ? list : get(id)),
    createElement: (t) => makeEl(t),
    createElementNS: (_ns, t) => makeEl(t),
    querySelector: (sel) => (sel === '[data-paths-figure]' ? fig : null),
    querySelectorAll: (sel) => (sel === '[data-stop]' ? marks : []),
  };
  const location = { search };
  global.window = { location };
  global.location = location;
  global.URLSearchParams = require('url').URLSearchParams;

  // eslint-disable-next-line no-eval
  eval(dataScript() + '\n' + instrumentScript());

  const rows = list.children.map((li) => li.children.map((c) => c.textContent));
  return {
    stop: fig.getAttribute('data-paths-figure'),
    slider: byId.stop.value,
    out: get('stop-out').textContent,
    caption: get('paths-cap').textContent,
    leader: rows.length ? rows[0][0] : null,
    order: rows.map((r) => r[0]),
    data: global.window.__ASIA__,
  };
}

const out = {};
const eq = (n, got, want) => { out[n] = got === want ? true : `got ${JSON.stringify(got)}, want ${JSON.stringify(want)}`; };
const ok = (n, cond, why) => { out[n] = cond ? true : why; };

const bare = drive('');
eq('default-is-where-korea-is', bare.stop, String(bare.data.stopsAt));
eq('default-slider-follows', bare.slider, String(bare.data.stopsAt));
ok('default-leader-is-korea', /Kospi, 2026/.test(bare.leader), `leader was ${bare.leader}`);
eq('all-five-ranked', bare.order.length, 5);

eq('stop-50', drive('?stop=50').stop, '50');
eq('stop-300', drive('?stop=300').stop, '300');
eq('stop-clamped-high', drive('?stop=99999').stop, String(bare.data.horizon - 1));
eq('stop-clamped-low', drive('?stop=1').stop, '5');
eq('stop-garbage', drive('?stop=soon').stop, String(bare.data.stopsAt));
eq('stop-empty', drive('?stop=').stop, String(bare.data.stopsAt));
eq('stop-rounded', drive('?stop=99.6').stop, '100');
eq('stop-url-moves-the-slider', drive('?stop=246').slider, '246');

// THE ARGUMENT: the title changes hands as the window moves.
const leaders = ['?stop=50', '?stop=120', '?stop=300', '?stop=900'].map((q) => drive(q).leader);
ok('leader-changes-with-the-window', new Set([bare.leader, ...leaders]).size >= 4,
  `only ${new Set([bare.leader, ...leaders]).size} distinct leaders: ${JSON.stringify([bare.leader, ...leaders])}`);
ok('nikkei-owns-the-long-window', /Nikkei, 1989/.test(leaders[3]),
  `at session 900 the leader was ${leaders[3]}`);

// An event with no reading that far out is flagged, never dropped.
const far = drive('?stop=900');
eq('unfinished-event-still-ranked', far.order.length, 5);
ok('unfinished-event-flagged', far.order.some((l) => /record ends at/.test(l)),
  `no short-record flag in ${JSON.stringify(far.order)}`);

// The caption restates the state, since it is what a screen reader gets instead of the chart.
ok('caption-names-the-session', /session 300/.test(drive('?stop=300').caption),
  `caption was ${drive('?stop=300').caption}`);

let failed = 0, total = 0;
for (const k of Object.keys(out)) {
  total++;
  const good = out[k] === true;
  if (!good) failed++;
  console.log(`${good ? 'PASS' : 'FAIL'}  shortest-line.${k}` + (good ? '' : ` => ${out[k]}`));
}
console.log(`\n${total - failed}/${total} assertions passed`);
process.exit(failed ? 1 : 0);
