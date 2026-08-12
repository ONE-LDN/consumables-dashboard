#!/usr/bin/env node
/**
 * Tests for the dashboard's prediction engine.
 *
 *   node tests/engine.test.js
 *
 * No dependencies and no build step: the model layer is extracted straight out
 * of `index.html` — from the MODEL CONSTANTS block down to `computeAll` — and
 * exercised with hand-built counts and deliveries.
 *
 * WHY THIS EXISTS. Every serious defect in this project so far has been a
 * silent arithmetic error that produced a plausible number: packs added to
 * items, a pack size guessed, a par validated against its own source, a
 * fractional minimum rounded to zero. None of them looked wrong on screen.
 * The cases below are the ones that bit, pinned so they cannot come back.
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

// ── Load the engine out of index.html ───────────────────────────────────────
const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const js = /<script>([\s\S]*?)<\/script>/.exec(html)[1];
const from = js.indexOf('const CYCLE_DAYS');
const to = js.indexOf('function computeAll');
if (from < 0 || to < 0) {
  console.error('Could not find the model layer in index.html — has it been renamed?');
  process.exit(2);
}
const sandbox = { module: { exports: {} }, console, Date, Math, Number, JSON, isNaN };
vm.createContext(sandbox);
vm.runInContext(
  'function sbGet() { return []; }\n' + js.slice(from, to) +
  '\nmodule.exports = { computeItem, setData: (t, o) => { takes = t; orders = o; } };',
  sandbox
);
const { computeItem, setData } = sandbox.module.exports;

// ── Harness ────────────────────────────────────────────────────────────────
let pass = 0, fail = 0;
const results = [];
function check(name, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  ok ? pass++ : fail++;
  results.push(`${ok ? '  ok  ' : ' FAIL '} ${name}` +
    (ok ? '' : `\n         got  ${JSON.stringify(got)}\n         want ${JSON.stringify(want)}`));
}
function section(title) { results.push(`\n${title}`); }

// Dates are fixed relative to a "today" the engine reads from the clock, so
// every fixture is anchored to the day the test runs.
const day = n => new Date(Date.now() + n * 86400000).toISOString().slice(0, 10);
const TODAY = day(0), YESTERDAY = day(-1), WEEK_AGO = day(-7), FORTNIGHT = day(-14);

const product = over => ({
  product_name_raw: 'p', display_name: 'Product', pack_size: 200, count_unit: 'bags',
  count_step: 1, min_stock_units: 200, min_confirmed: true, order_class: 'reorder',
  cost_price: 16.62, monthly_usage_units: null, ...over,
});
const take = (d, n) => ({ product_name_raw: 'p', take_date: d, actual_count: n });
const delivery = (d, packs, ps) => ({ product_name_raw: 'p', delivery_date: d, qty_cases: packs, pack_size: ps });

// ── 1. Deliveries are packs; counts are items ───────────────────────────────
// The bug this replaces summed qty_cases straight into an item count, so a
// delivery of one bin-bag pack read as one bag instead of 200.
section('deliveries convert from packs to items');
setData([take(TODAY, 250), take(WEEK_AGO, 100)], [delivery(day(-6), 1, 200)]);
let m = computeItem(product());
check('one 200-pack counts as 200 bags, so usage reads ~217/mo',
  Math.round(m.measuredMonthly), 217);
check('and est stock follows from it', Math.round(m.estItems), 250);

// The same fixture under the old arithmetic: 100 + 1 − 250 = −149. Negative
// usage was discarded, so the figure vanished rather than being wrong out loud.
section('a delivery whose pack size is unknown stops the arithmetic');
setData([take(TODAY, 8), take(WEEK_AGO, 12)], [delivery(day(-6), 1, null)]);
m = computeItem(product({ pack_size: null, min_stock_units: 2, count_unit: 'pens' }));
check('usage refused rather than guessed', m.measuredMonthly, null);
check('and the reason is surfaced', /pack size/.test(m.usageNote || ''), true);
check('order quantity withheld', m.blocked, 'needs a pack size');

section('a delivery before the last count does not need converting');
setData([take(YESTERDAY, 8), take(WEEK_AGO, 12)], [delivery(day(-6), 1, null)]);
m = computeItem(product({ pack_size: null, min_stock_units: 2, count_unit: 'pens' }));
check('est stock still stands on the last count', m.estItems, 8);

section('the pack size recorded on the delivery beats the catalogue');
// Gloves were 100/pack and are now 200/pack. A delivery logged at 100 must not
// be re-read as 200 — that would invent 100 gloves of usage.
setData([take(TODAY, 100), take(WEEK_AGO, 0)], [delivery(day(-6), 1, 100)]);
m = computeItem(product({ pack_size: 200, count_unit: 'gloves', min_stock_units: 50 }));
check('0 + 100 delivered − 100 counted = no usage', m.measuredMonthly, null);

// ── 2. Count precision ─────────────────────────────────────────────────────
section('movement inside the count precision is not a reading');
const cloth = { pack_size: 6, count_unit: 'rolls', count_step: 0.25, min_stock_units: 0.25, cost_price: 11.98 };
setData([take(TODAY, 5.75), take(WEEK_AGO, 6)], []);
m = computeItem(product(cloth));
check('a quarter roll of movement claims no usage', m.measuredMonthly, null);
check('and says why', /count precision/.test(m.usageNote || ''), true);

section('movement beyond two steps is a reading');
setData([take(TODAY, 5), take(WEEK_AGO, 6)], []);
m = computeItem(product(cloth));
check('a whole roll over a week does register', m.measuredMonthly > 0, true);

// ── 3. Fractional minimums ─────────────────────────────────────────────────
section('a fractional minimum survives and does not overshoot');
setData([take(TODAY, 0)], []);
m = computeItem(product(cloth));
check('flags at zero against a quarter-roll minimum', m.flag, 'now');
check('orders one case of 6, not two', m.suggested, 1);

// ── 4. Classes that must not generate orders ────────────────────────────────
section('measure_only never reaches "order now"');
setData([take(TODAY, 0)], []);
m = computeItem(product({ order_class: 'measure_only', min_stock_units: 4, pack_size: 4 }));
check('flagged as measure-only, not now', m.flag, 'measure');
check('no quantity', m.suggested, null);
check('reason given', m.blocked, 'counted, not reordered');

section('an unconfirmed minimum shows status but withholds the order');
setData([take(TODAY, 100)], []);
m = computeItem(product({ min_confirmed: false }));
check('still flagged short', m.flag, 'now');
check('quantity withheld', m.blocked, 'minimum unconfirmed');

section('no minimum means no verdict');
setData([take(TODAY, 100)], []);
m = computeItem(product({ min_stock_units: null }));
check('flag is none', m.flag, 'none');
check('quantity withheld', m.blocked, 'no minimum set');

// ── 5. Order sizing ────────────────────────────────────────────────────────
section('with a usage figure, carry a month beyond the minimum');
setData([take(TODAY, 100)], []);
m = computeItem(product({ monthly_usage_units: 217 }));
check('target 417 from 100 on hand → 2 packs', m.suggested, 2);
check('cost is packs × net pack price', Number(m.estCost.toFixed(2)), 33.24);

section('without a usage figure, just clear the minimum');
setData([take(TODAY, 100)], []);
m = computeItem(product());
check('one pack clears a 200 minimum from 100', m.suggested, 1);

section('nothing to order when already above target');
setData([take(TODAY, 500)], []);
m = computeItem(product({ monthly_usage_units: 217 }));
check('suggested is zero, not a top-up', m.suggested, 0);
check('and the flag is ok', m.flag, 'ok');

// ── 6. Data integrity signals ──────────────────────────────────────────────
section('stock rising with no logged delivery is surfaced');
setData([take(TODAY, 400), take(WEEK_AGO, 100)], []);
m = computeItem(product());
check('no usage invented', m.measuredMonthly, null);
check('and the Order Log is named', /Order Log/.test(m.usageNote || ''), true);

section('a single count is not enough for usage');
setData([take(TODAY, 100)], []);
m = computeItem(product());
check('no measured usage', m.measuredMonthly, null);
check('but est stock is the count itself', m.estItems, 100);

section('lead time is two days, not seven');
// 3 days of cover: under the old LEAD_DAYS of 7 this was "order now"; at 2 it
// is merely "soon". Usage 100/week → ~14.3/day; 43 items ≈ 3 days.
setData([take(TODAY, 43)], []);
m = computeItem(product({ min_stock_units: 10, monthly_usage_units: 100 * 52 / 12 }));
check('three days of cover reads as soon, not now', m.flag, 'soon');

// ── Report ─────────────────────────────────────────────────────────────────
console.log(results.join('\n'));
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
