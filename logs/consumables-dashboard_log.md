# Session log — ONE LDN consumables dashboard

Rolling handoff log. **Newest entry at the top.** Prepend new entries directly below
this header; never append at the bottom and never edit prior entries.

Written and maintained by the `session-log` skill (`.claude/skills/session-log/`).
This is an engineering handoff for the next Claude session — it is **not** the
contractual documentation suite and nothing here goes to Notion.

**This repository is public.** No credential values, no personnel narrative.

---

# One workbook, items throughout, and the first real history in the database
**Date:** 2026-08-12
**Project:** ONE LDN consumables dashboard — catalogue, count sheet, dashboard engine, Supabase load
**Mode:** Rolling Log + Git Push
**Status:** Complete — PR #5 merged; Supabase now holds the catalogue, one stock take and six deliveries

---

## Project Context

See the **2026-08-05** entry for the full picture: sheet → Apps Script → Supabase →
dashboard, the minimum-stock method, and the v4 product list plan (`migration/PLAN-V4.md`).

That entry left the project as *analysis only* — nothing synced, no dashboard changes,
no database writes. **This session executed it.** PLAN-V4's sequence (§10) is now done
through step 9, with two structural additions the plan did not anticipate: the catalogue
moved into the stock take workbook, and the count sheet gained a per-product count
precision.

## Session Goal

Started as "situate me after four days off, and I need a simple Google Sheet with the
products for stock take". Grew, by the user's direction, into: fold the catalogue into
that sheet, correct the prices against supplied invoices, settle every outstanding
minimum, switch the dashboard from packs to items, and get it all into Supabase before
today's stock take.

## State Before This Session

- 39 active consumables in Supabase on the **old** keys and the old schema.
- `min_stock_units` existed but was **null on every row of the table, in every
  category** — the dashboard had been reading an empty column all along.
- The only consumables stock take was the 2026-07-29 artefact: 38 rows, every value
  the number `6`.
- `shop_consumable_deliveries` empty. No usage figure anywhere.
- `index.html` untouched since 2026-07-27 and carrying a live packs-vs-items bug.
- 14 lines below minimum per the 04/08 count; the reset order not placed.
- Tuesday 11/08 (count 2) had passed without a count.

## What Was Done

**Built the count sheet, then rebuilt it five times as the user's requirements
sharpened.** Final layout `Product name | Category | Location | Count | Unit | Record to`.
The iterations are worth knowing because each was a real correction, not churn:
units moved out of the product name into their own column; `Category` and `Location`
split into genuinely different axes; the slug came off the count sheet entirely; a
`Count step` column appeared. **Five superseded Google Sheets exist as a result** — IDs
in `migration/WORKBOOK.md`, all should be deleted.

**Folded the catalogue into the same workbook** (user's call: "so all the dependencies
are in one place and alterations take effect everywhere"). `Products` is now the master
tab; `Stock Count` and `Order Log` derive from it. Two things are formulas on purpose:
`Products!Minimum`, so changing a par or pack size updates the minimum; and the count
sheet's Category/Location/Unit/Record-to as per-row VLOOKUPs against `Products`.

**Rewrote `Code.gs` to read the Products tab everywhere** and never read the catalogue
back out of Supabase — a round trip through the database to rebuild a tab only creates a
way for the two to disagree. `_sbGet` became dead code and was removed.

**Trimmed the catalogue 35 → 30** and priced three lines from supplied documents
(see *Corrections*).

**Set the last seven minimums**, clearing the four long-standing `min_confirmed = no`
rows and the three blank pars. Nothing in the catalogue now carries an unconfirmed
minimum or an unset par.

**Added `Count step`** — the smallest fraction to record per product — after the user
asked how to account for products counted by eye. The rule that fell out: **the step is
set by the minimum, not the product.** A quarter of a toilet roll is noise against a
minimum of 24; a quarter of a 5L bottle is half the gap between "fine" and "reorder"
when the minimum is 2.

**Switched `index.html` to items and fixed the packs-vs-items bug** (see *Corrections*),
plus eight smaller PLAN-V4 §7 items. Added `tests/engine.test.js` — 29 cases, no
dependencies, extracting the model layer straight out of the HTML.

**Applied the schema change and loaded the data.** Five new columns, one type widening,
the junk take deleted, the catalogue synced, the 04/08 count and 07/08 deliveries loaded.
All verified by query afterwards.

**Found an unrelated security exposure** while reading the schema — see *Open Questions*.

**What was NOT done and why:**

- **First aid** stays out of the workbook. Separate 33-line list, quarterly cadence,
  data ready in `first_aid_v4.csv`. Not asked for; would have doubled the review surface.
- **`deliveries_backfill.csv`** (26 lines, Feb–Jul) still not loaded. Harmless right now:
  04/08 is the earliest count, so no pre-04/08 delivery falls inside any usage window.
- **Pens pack size and price** left blank. Amazon is blocked by this environment's egress
  proxy, so neither could be read off the listing supplied and neither was guessed.
- **The RLS fix** deliberately not applied — it needs a decision, not a paste.

## Artifacts Produced / Modified

| File | What it is | Status | Path |
|------|------------|--------|------|
| `index.html` | Dashboard switched to items; packs-vs-items bug fixed; 9 PLAN-V4 §7 items | **Modified** | root |
| `engine.test.js` | 29 cases over the prediction engine, extracted from `index.html` | **Created** | `tests/` |
| `Code.gs` | Reads the Products tab everywhere; new column map; `_sbGet` removed | **Modified** | `apps-script/` |
| `build_workbook.py` | Generates all three tabs; holds every decision as a documented constant | **Created** | `migration/scripts/` |
| `build_load_sql.py` | Emits the four-step Supabase load, re-runnably | **Created** | `migration/scripts/` |
| `products_tab.csv` | `Products` — 30 rows × 17 columns | **Created** | `migration/` |
| `stock_count_sheet.csv` | `Stock Count` — 30 rows, walk order | **Created** | `migration/` |
| `order_log_tab.csv` | `Order Log` — header + the 07/08 deliveries | **Created** | `migration/` |
| `WORKBOOK.md` | Layout contract, setup, counting rules, DDL, known gaps | **Created** | `migration/` |
| `DELIVERIES-LOG.md` | Deliveries after the baseline count, with the VAT finding | **Created** | `migration/` |
| `deliveries_since_baseline.csv` | The 07/08 deliveries; the Feb–Jul backfill is closed | **Created** | `migration/` |
| `build_stock_count_sheet.py` | Superseded by `build_workbook.py` | **Deleted** | `migration/scripts/` |
| `STOCK-COUNT-SHEET.md` | Superseded by `WORKBOOK.md` | **Deleted** | `migration/` |

`products_v4.csv` was **not** modified — it stays a faithful record of what the v4 sheet
said. Every change since lives as a dated constant in `build_workbook.py`, so the diff
between the sheet and the catalogue is always readable.

## Decisions & Reasoning

- **The catalogue moves into the stock take workbook** (user). One source of truth; edits
  propagate. Rejected: keeping a separate catalogue sheet, which is what created the
  drift PLAN-V4 spent a session mapping.
- **`Products!Minimum` is a formula, not a typed value.** Change a par or a pack size and
  the minimum follows. `Min override` (column M) is the place to state a requirement
  outright — overwriting the formula in column N breaks the propagation for that row.
- **Category and Location are separate columns** (user). The v4 sheet mixed them:
  `Toiletries` is a product type, `Gym Floor` is a place. Location keeps the v4 values and
  drives the walk order; Category was derived from the products, since nothing upstream
  carries it. The split earns its keep where they disagree — D Batteries are Category
  `Gym` (they run the ergs) but Location `FOH Desk` (that is where the drawer is).
- **No `product_name_raw` on the count sheet** (user: only if necessary). The slug stays on
  `Products`. The cost is real and stated: renaming a product on the count sheet breaks
  the join. So `submitCounts()` **refuses the entire submission** if any name fails to
  match, and names the offenders — a partial count reads as a real count and would
  corrupt usage for every product that dropped out silently.
- **Count unit gets its own column, after Count** (user). Rejected: dropping it, which
  would have undone PLAN-V4 §3's guard rail; and keeping it appended to the product name,
  which the user rejected in favour of a clean name.
- **`Count step` per product, set by the minimum.** Rejected: a single sheet-wide
  convention — the same failure mode as asserting one `Par Unit` for all rows.
- **Order size = clear the minimum, carry a month beyond where a usage figure exists,
  never less than one pack.** Rejected: the literal "minimum + one pack" target, which
  overshoots badly where the minimum is small against the pack — Blue Cloth's quarter-roll
  minimum against a case of 6 would target 6.25 and round up to **two cases, 12 rolls, to
  cover a quarter of one**.
- **Key fobs reclassified `measure_only` → `reorder`** (model, after the user set a
  minimum of 50). A minimum on a measure-only row never surfaces: the dashboard excludes
  that class from "order now". Flagged to the user as one word to revert.
- **Printer ink: four rows → one.** The invoice settles it rather than merely permitting
  it — the product is sold as a 4-pack, so the four colours were always one purchase. The
  cost: one row cannot tell you *yellow* specifically has run out. Tolerable only because
  ink is measure-only; worth revisiting, since toner is genuinely consumed unlike the key
  fobs it was grouped with.
- **The 04/08 count is kept, not discarded**, even though today's count sets the basis.
  It maps onto 29 of 30 products, and it is the only route to a usage reading before next
  Tuesday. Measured usage is computed from the two latest counts and never accumulated,
  so any contamination is transient — by next Tuesday the pair is clean.
- **Prices are net throughout**, and the catalogue holds *list* net. Out of Eden discounts
  by line (5% and 10% on the 07/08 invoice), so the discount belongs on the delivery
  record, not the catalogue.
- **`FIELD_UPDATE` entries compose rather than replace** (see *Corrections*).

## Corrections Made This Session

Nine. Several were the intuitive version being wrong.

1. **The dashboard added packs to items.** `usage = older.actual_count + ordersBetween −
   newer.actual_count`, where `ordersBetween` summed `qty_cases` (**packs**) into item
   counts. A delivery of one bin-bag pack read as **1 bag, not 200**. Both delivery
   reductions now convert with `pack_size`, preferring the size recorded **on the
   delivery** over the catalogue's current one — what arrived is what arrived. Where no
   pack size exists the arithmetic stops rather than guessing.
2. **v4's £25.19 for the four Out of Eden toiletries was VAT-inclusive, not net.**
   `20.99 × 1.20 = 25.19`. The 07/08 invoice states £20.99 net, and the Futures prices in
   the same column (£11.31, £26.98) match their invoice net to the penny — so the price
   column held two bases with nothing saying which. Same class of error as the £800.53
   total from the first session. Corrected to **£20.99** across four rows.
3. **`printer_ink_blk`'s £224.90 was simply wrong.** The 2026-08-05 entry flagged it as
   *"looks like a multipack booked against a single cartridge"*. It is not that either —
   the 4-pack costs **£38.32 net** (£45.99 gross). Not carried forward.
4. **Correction #5 from the first session is retired.** A pack size of 1 for key fobs was
   struck out then as invented. The procurement quote prices **per fob** at £3.59, with
   500 as the order quantity — so a pack size of 1 is evidenced, not invented.
   500 × £3.59 = £1,795.00 net, +£68.01 delivery = £1,863.01 ex VAT, ×1.20 = £2,235.61.
5. **The 04/08 wet kit bags count of 3 was 3 ROLLS, not 3 individual bags** (user). The
   earlier session recorded it as bags and concluded "almost out". As rolls against a
   1-roll minimum it is **not short, and it leaves the reset order** — PLAN-V4 §2a had it
   listed as below minimum with quantity TBC. Note the direction: this correction *removed*
   a line from the order.
6. **`min_stock_units` was `integer`, and would have rounded Blue Cloth's 0.25 to 0** —
   silently turning "reorder at a quarter roll" into "never reorder". Column widened to
   `numeric`; `syncProducts` now sends the minimum through `_num`, not `_int`.
   Verified after the load: the stored value is `0.25`.
7. **`monthly_usage_units` was missing from the DDL block in `WORKBOOK.md`** while being
   named in the prose beside it. `index.html` selects that column, so running the block as
   written would have left the dashboard still failing on one column. The block now says
   all six statements or none.
8. **My own: a duplicate key in a dict literal silently ate a set minimum.**
   `FIELD_UPDATE` had two `key_fobs` entries; Python kept the last, dropping the 50-fob
   minimum. Caught only because a test computed `None`. Now a list whose entries compose.
9. **My own: an edit to the `COL` map in `Code.gs` did not apply** (whitespace mismatch),
   which would have left `COL.step` undefined and thrown on every sync. Added a check that
   every `COL.<key>` referenced in the file exists in the literal — all 13 match.

Also: **two test expectations I wrote from memory failed, and the code was right both
times** — a delivery predating the last count needs no conversion, and the cadence
fallback correctly reads `ok` when an order landed a week ago. Recorded because it is the
argument for the test file existing: reasoning about this engine unaided is not reliable.

## Skills / Tooling Used

- **Google Drive MCP** — created the workbook. **No update/rename capability**, only
  create/copy, which is why each revision produced a new sheet rather than editing one.
- **Supabase MCP** — `apply_migration` for the DDL (named migration, in the project's
  history), `execute_sql` for the load and every verification. Both required interactive
  approval; the first write attempt returned `requires approval` and did not run.
- **GitHub MCP** — PR #5. Note two servers are exposed (`github` and `Github_MCP`);
  `Github_MCP` returned 403 on `create_pull_request` and `github` succeeded.
- **Playwright** — rendered `index.html` against mocked Supabase responses to check the
  render layer. Installed with `npm install --no-save playwright` and **removed again
  before committing**; `node_modules` is not in the repo and there is no `package.json`.
- **`node --check`** on `Code.gs` copied to a `.js` extension — node refuses `.gs`.
- **Everything that generates an artifact is now a committed script.** The 2026-08-05
  entry's largest handoff gap (model scripts in an ephemeral scratchpad) does not recur.

## Current State (end of session)

**PR #5 merged** into `master` at `ccfdd19`. Working tree clean.

Supabase, verified by query after the load:

| | |
|---|---|
| Consumables active | **30** (was 39) |
| Consumables inactive | 53 — the 9 intended deactivations plus 44 legacy rows |
| Other categories | **167, unchanged** — no shop or merch row touched |
| Stock takes, 2026-08-04 | **29** |
| 2026-07-29 `source='sheet'` | **0** — deleted |
| Shop's own 2026-07-29 `source='manual'` | **65, intact** |
| Deliveries | **6**, £283.64 net |
| Minimums set | **30 of 30** |
| Blue Cloth minimum | **0.25** — the fraction survived the type change |

The dashboard should now load and render. `tests/engine.test.js` passes 29/29.

**The workbook has one tab.** `Products` is populated; `Stock Count` and `Order Log` do
not exist yet — they are created by the Apps Script menu, which needs the script
properties set first.

## Next Steps

1. **Finish the workbook setup**, per `migration/WORKBOOK.md` § *Setting it up*: rename
   the imported tab to `Products`, paste `apps-script/Code.gs` into Extensions ▸ Apps
   Script, then run menu ② and ④ to create the other two tabs. Steps ①/③/⑤ need
   `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in Script properties first — names only,
   see `apps-script/SETUP.md`.
2. **Enter today's (12/08) count and submit it.** It lands as count 2 and produces the
   first measured usage figure this project has ever had. Two specifics: **count
   `microfibre_cloths`** (the one product with no 04/08 figure), and **recheck
   `water_softener_salt`** — 36 bags against a minimum of 10 is a large surplus and the
   £149.99 price basis is still unsettled.
3. **Place the reset order off today's numbers, not 04/08's.** Key fobs will be a 50-fob
   line at **£179.50 net** — the user confirmed on 12/08 that there are still none.
4. **Log every delivery in `Order Log`.** Usage is `opening + orders_between − closing`.
5. **Delete the five superseded Google Sheets** (IDs in `WORKBOOK.md`) and drop the "v2"
   from the surviving workbook's title.
6. **Decide the RLS exposure** — see below. Highest-risk open item.
7. From count 3 onward, write measured usage into `monthly_usage_units` for the fast
   movers. Expect to revise the estimated minimums upward.
8. When wanted: add First Aid as two more tabs from `first_aid_v4.csv`, and load
   `deliveries_backfill.csv`.

## Open Questions / Blockers

- ⚠ **`shop_sales_backup_20260803` has Row Level Security DISABLED** while the dashboard
  ships a public anon key in a public repo on GitHub Pages. 10,278 rows including
  customer names and email addresses are readable by anyone who views source. Every other
  table has RLS on. **Not touched** — enabling RLS with no policies blocks all access, and
  it is unknown what else reads that table. If it is a one-off backup nothing reads,
  dropping it is cleaner than securing it. **Needs the user's decision.**
- **Pens pack size and price** — the listing is linked (`B07TVR5X6W`) but Amazon is
  blocked by this environment's egress proxy. Two cells for the user.
- **Bags per roll for wet kit bags** — the count is in rolls, the pack is 250 bags, no
  bridge between them. Blocks sizing an order; blocks nothing today, since the line is
  above its minimum.
- **Water Softener Salt: £149.99 for what?** Pack size blank, `Par Unit` is `items` so the
  minimum is safe, but the price basis swings a costed order by an order of magnitude.
- **Key fob minimum order quantity** — 500 is the only purchase on record, so a 50-fob
  order may not be placeable as such.
- **Printer ink `order_class`** — left `measure_only`, but it now has a real price and pack
  size, and toner is genuinely consumed. Worth reconsidering.
- **`microfibre_cloths` Location** is a placement (Staff Room), not a settled answer.
- **Seven rows read `Toiletries | Toiletries`** — the v4 location for the changing rooms is
  the same word as the product type. Renaming the location to `Changing Rooms` clears it.
  Cosmetic.
- **Concept Spa's VAT basis** — still the last unverified line.
- **2 open repo issues** still not reviewed in any session.

## Environment & Config Notes

- Repo `ONE-LDN/consumables-dashboard`, **public**, GitHub Pages, default branch `master`.
- **PR #5 merged** at `ccfdd19`. Branch `claude/stock-take-sheet-gp9xyw` was restarted from
  the merged `master` for this log entry, per the merged-PR rule — a merged PR cannot
  track new work.
- Supabase project `ljjwssicvvyyueyznmou`. Migration applied:
  **`consumables_catalogue_item_units`** — adds `count_unit`, `count_step`,
  `min_confirmed`, `order_class`, `monthly_usage_units`; widens `min_stock_units` to
  `numeric`. `product_type` already existed. `monthly_par_packs` is no longer read by
  anything and can be dropped once nothing references it.
- **Live workbook:** `1ieGFxfZxttaYWwjq1XobvYwfqjUce1jMxhm_UNilK3k`.
  Superseded: `1linoZ_oo…`, `1xGKdynO2…`, `1CvPuwat…`, `1R_uIZfM…`, `13hUhCIw…`.
- `Code.gs` config: `PRODUCTS_SHEET='Products'`, `COUNT_SHEET='Stock Count'`,
  `ORDER_SHEET='Order Log'`, `CATEGORY='Consumables'`, plus `COUNT_WALK_ORDER`.
- Dashboard constants: `LEAD_DAYS = 2` (was 7), `CYCLE_DAYS = 30`, `DRIFT_RATIO = 1.5`.
- Credential **names** only: `index.html` carries the Supabase anon key (public by design,
  behind RLS). The Apps Script needs `SUPABASE_SERVICE_KEY` — the `service_role` key —
  which must never be committed anywhere and does not appear in this repo.
- `shop_stock_takes` has `UNIQUE (product_name_raw, take_date)`;
  `shop_consumable_deliveries` has **no** natural key.

## Notes & Gotchas

- **`syncProducts` still deactivates the whole `Consumables` category before upserting.**
  With column A present that is correct — it is what performed the 9 intended
  deactivations. Never run it against a Products tab whose keys have not been checked.
- **`Products!Minimum` is a formula.** Typing a number over it breaks propagation for that
  row. Use `Min override` (column M).
- **The count sheet's lookups are formulas too.** Pasting values over Category/Location/
  Unit/Record-to severs them from the catalogue.
- **Only adding or removing a product needs a count-sheet rebuild.** Field edits flow
  through by VLOOKUP. The lookups are keyed **per row** on purpose: a whole-range formula
  would re-sort the product names without moving the counts beside them, filing every
  count against the wrong product.
- **Precision is not accuracy.** Usage is a *difference* of two counts, so it carries
  roughly twice the single-count error. Two quarter-accurate counts give usage good to
  about ±0.5 of a bottle against a real weekly movement of about one. Hence: for eyeballed
  products read usage over a month or a quarter, not a week.
- **Opaque containers cannot be judged at all.** You can see you have 3 aerosols, not how
  full they are. Air Freshener and both Deodorants stay at whole units and a part-used can
  counts as whole until empty — a **bias that never averages out**, not noise.
- **The 04/08 → 12/08 usage window contains the 07/08 delivery**, which triggered a
  cupboard-to-dispenser refill round. Shampoo, hand wash, conditioner and lotion will read
  as *using* stock that only *moved*. Do not let that reading drive an order. It is
  transient — next Tuesday's pair is clean.
- **`blank` and `0` are different claims** throughout: blank means not counted, `0` means
  counted and none left. `microfibre_cloths` is absent from the 04/08 load for this reason,
  not zero.
- **Deliveries store their own `pack_size`**, and the dashboard prefers it over the
  catalogue's. Changing a catalogue pack size therefore does not retroactively rewrite
  history — which is the point.
- **Google Drive MCP cannot update or rename an existing file**, only create and copy.
  Any sheet revision means a new file and a stale one to delete.
- **Supabase MCP writes need interactive approval.** A blocked call returns
  `requires approval` and does **not** run — verify state before assuming either way.
- `node --check` cannot read a `.gs` file; copy it to `.js` first.
- The dashboard **requires all six DDL statements**. It names every new column in its
  select, so a partial run leaves the page blank rather than degraded.

---

# Sheet migration, minimum-stock model, first aid and VAT
**Date:** 2026-08-05
**Project:** ONE LDN consumables dashboard — catalogue migration & inventory method
**Mode:** Rolling Log + Git Push
**Status:** In Progress — analysis complete and pushed; nothing synced to Supabase yet

---

## Project Context

First entry, so the full picture. The dashboard is a read-mostly single-page app
(`index.html`) over Supabase, fed from a Google Sheet by a bound Apps Script
(`apps-script/Code.gs`). The sheet is the master; the script pushes to Supabase; the
dashboard reads. See `README.md` for the architecture.

The consumables product list was rebuilt from scratch in a new Google Sheet
(`1DA77H1SG9aLELsvNFxL6VksNvVCFj5_xHZftgV2UPC4`, "Copy of consumables_catalogue_v2"),
which had drifted badly from what is live in Supabase. This session was the analysis
of that drift and the design of an inventory method to go with it.

## Session Goal

Work out what the new sheet contains, how it maps to the live catalogue, and how to
derive a defensible minimum stock level per product so ordering stops being reactive.
Explicit constraint from the user at the outset: **no changes to the dashboard or the
Apps Script.** Analysis and agreed mapping only.

## State Before This Session

- Supabase held **40 active** consumables (plus ~40 already-inactive legacy rows),
  keyed on short slugs (`toilet_rolls`, `blue_rolls`, …).
- History was almost empty: **1 stock take (2026-07-29, 38 products) and 0
  deliveries.**
- No trustworthy usage figure existed anywhere in the system.
- Ordering was reactive — placed after stock ran out.
- No `migration/` directory, no `logs/`, no repo-level skills.

## What Was Done

**Mapped the sheet.** Three tabs: `Stock` (52 products, live counts), `Product List
(Updated)` (55, a superset by 3 stationery rows), `Consumables Invoices` (26 order
lines, Feb–Jul 2026, transcribed from 13 supplier invoices).

**Found the sync hazard.** The sheet identifies products by full supplier description
(`Jumbo T.Roll 2ply 2.25" Core J26300 300m`); Supabase keys on `toilet_rolls`.
`syncProducts()` in `Code.gs` reconciles by `product_name_raw` — it PATCHes
`active:false` across the whole category, then upserts. Run against the new sheet
as-is it would **deactivate all 40 live rows, insert 55 unrelated ones, and orphan
every count and delivery.** Cheap to fix now only because history is nearly empty.

**Built a minimum-stock method** (`MINIMUM-STOCK.md`). With a weekly Tuesday count,
`minimum = daily usage × (7 review days + lead time + safety days)`, and the minimum
is the **highest of four candidates** — the user's own `Par Qty`, the calculation, a
minimum written in the sheet's notes, or one pack. Taking the highest is what made
the model robust to the bad usage inputs described below.

**Reconciled the first aid kits** against a required list of 15 lines. The physical
count came to 41 lines / 35 distinct items — the kits hold far more than the list
tracks. 14 of 15 required lines are short, 247 individual items. Then derived a
grouping rule from the user's own accept/reject decisions and proposed a 31-line
tracked list (`FIRST-AID.md`).

**Settled the VAT basis**, which was the last thing stopping the reset order being a
real number. See Corrections.

**What did not work / was abandoned:**

- Deriving usage from the invoice tab. Purchases were reactive, so they are a
  **floor** on demand, not a measure of it.
- Using the existing `Stock` column at all. It silently mixes packs and items and 9
  products cannot be told apart. Not salvageable — needs a fresh count.
- Sizing orders from the burn rate. It overstates (see Corrections).
- `products_tab_proposed.csv` — superseded by `products_tab_final.csv` and deleted.

## Artifacts Produced / Modified

| File | What it is | Status | Path |
|------|------------|--------|------|
| `README.md` | Migration write-up; 7 numbered drift findings | Created | `migration/` |
| `MINIMUM-STOCK.md` | The method, the four candidates, the corrections | Created | `migration/` |
| `BASELINE-RESET.md` | Clear-the-slate plan; reset order £764.73 net | Created | `migration/` |
| `SHOPPING-LIST.md` | Reset order by supplier, in packs, with VAT resolution | Created, then fully rewritten | `migration/` |
| `FIRST-AID.md` | 4-box reconciliation + the 15→31 line proposal | Created | `migration/` |
| `crosswalk.csv` | 60 rows: sheet row → Supabase key, field-level drift. 34 matched, 14 new first-aid, 7 other new, 5 dropped, 9 flagged | Created | `migration/` |
| `min_stock_model.csv` | Per-product working, 52 rows, 22 cols | Created | `migration/` |
| `products_tab_final.csv` | Canonical 52 restructured for `Code.gs` | Created | `migration/` |
| `deliveries_backfill.csv` | 26 invoice lines as delivery rows, £1,659.59 net | Created | `migration/` |
| `shopping_list.csv` | Flat one-row-per-product with Status + VAT columns | Created | `migration/` |
| `products_tab_proposed.csv` | Superseded by `products_tab_final.csv` | Deleted | `migration/` |
| `SKILL.md` | The `session-log` skill | Created | `.claude/skills/session-log/` |
| `consumables-dashboard_log.md` | This log | Created | `logs/` |

**Nothing in `index.html`, `apps-script/Code.gs` or `apps-script/SETUP.md` was
touched.** No Supabase writes were made.

## Decisions & Reasoning

- **Count in individual items, not packs** (user). Makes `units_per_pack` mandatory
  for ordering; known for 45 of 52 products.
- **The `Stock` tab is the canonical product list** (user) — 52 products. The 3
  stationery rows only on `Product List (Updated)` are dropped.
- **The `Stock` tab's categories are canonical** (user), so `Greenspeed Techno Multi`
  is `Staff Room`, not `Cleaning` — the two tabs disagreed.
- **Minimum = highest of four candidates**, rather than one formula. Rejected: a
  single formula, which gives 0.3 of a 5L bottle for slow movers and nonsense
  wherever the usage figure is wrong.
- **Retire the `Cadence` column.** With a weekly count, order cadence is an *output*
  (`implied_order_every_days`), not an input.
- **Minimum and order-up-to are two separate numbers.** If they are equal you
  reorder every week. Rejected: ordering back to the minimum — worked example in
  `MINIMUM-STOCK.md` shows blue roll would be under minimum again within 7 days.
- **Split burn rate and purchase floor by consequence:** burn (higher) sets the
  minimum, because being wrong there is safe; purchase floor (lower) sizes the order,
  because being wrong there is expensive and a weekly count catches it in 7 days.
- **Never multiply an untrusted estimate.** Order size is `minimum + one month of
  usage` only for the 7 products with a defensible usage figure; `minimum + one pack`
  for the other 45. Rejected: applying the month-of-usage rule everywhere — it
  produced a £2,830 order.
- **Refuse to produce an order where the count basis is unknown** (see Corrections).
- **An explicitly-set human requirement overrides every computed candidate**,
  including the one-pack floor.
- **Net ex-VAT throughout**, matching the invoices.
- **Two product classes that are counted but never reordered:** measure-only (the
  four printer inks, key fobs) and equipment (first-aid tourniquet, tweezers,
  scissors, clothing cutters). A monthly usage figure is meaningless for both —
  they don't get used up, they go missing.

## Corrections Made This Session

Six, and the wrong version was the more intuitive one in most cases.

1. **Circular validation of the stored pars.** I claimed the invoice tab "proves the
   existing DB pars are already right — they match invoice-derived consumption to
   2 d.p." The pars were *derived from those same purchases*, so the match showed a
   number agreeing with its own source. Compounded by purchasing having been
   reactive, which suppresses measured consumption during stockouts. Both the
   purchase rate and the stored pars are now labelled **floors**. Retracted in
   `MINIMUM-STOCK.md`, `migration/README.md` and the PR body.
2. **Burn rate overstates.** Caught by the user asking why shampoo looked high. A
   delivery triggers a refill round — cupboard → wall dispenser — so the burn window
   counts stock *moving* as stock *used*. Evidence: the three big burn-to-floor gaps
   are all refill-into-something items; hand wash, at 1.04×, was measured over 71
   days, long enough to average out. Shampoo order 15 → 10 bottles, blue roll 11 → 7
   packs.
3. **The count column mixes packs and items.** Caught by the user stating there was a
   surplus of tampons and pads. Read as items, the model demanded an order of **444
   tampons**; read as packs, the counts of 4 and 11 are 256 and 484 items, matching
   the shelf. Added a `count_basis` per product; 9 remain undecidable. Order list
   went 29 → 19 lines.
4. **Invented lead times.** All 8 supplier lead times (3–14 days) were mine. The user
   confirmed everything arrives within 1–2 days. Set to 2 everywhere; cover became
   12 days normally, 16 for member-visible items.
5. **Invented pack sizes.** A pack size of 1 for Key Fobs produced "order 2 fobs";
   `Washproof Plasters` inherited pack size 1 and turned a Par Qty of 160 into "161
   packs". Both removed. Pack sizes must be evidenced or absent.
6. **£800.53 was not a real number.** It added 13 net prices to 9 gross ones.
   Resolved per line: verified net for Futures and Out of Eden (each matches an
   invoice line to the penny, and the invoice tab states its figures are net);
   converted from gross for 7 Amazon lines and 2 taken from the old DB record;
   Newline and Concept Spa marked **unverified** rather than assumed. Total is
   **£764.73 net / £917.67 gross**, with £23.82 of exposure on the two unverified
   lines.

Also corrected mid-session: I restated two historical comparison totals by dividing
mixed-basis figures by 1.20, which is not a valid conversion. They are now marked as
approximate and mixed-basis rather than falsely precise.

## Skills / Tooling Used

- **Google Drive MCP** — read the source sheet; `openpyxl` for parsing the XLSX.
- **Supabase MCP** (project `ljjwssicvvyyueyznmou`) — read-only inspection of
  `shop_product_lookup`, `shop_stock_takes`, `shop_consumable_deliveries`. No writes.
- **GitHub MCP** — draft PR #3, repo metadata.
- **⚠ Ad-hoc Python in the ephemeral scratchpad** — `minstock.py` (the model that
  generates `min_stock_model.csv` and `products_tab_final.csv`), `build.py`
  (`crosswalk.csv`), `reorder.py`, `vat.py`, `relist.py`. **These are NOT in the
  repo and will not survive the container.** See Gotchas — this is the largest
  handoff gap in the session.

## Current State (end of session)

Analysis complete, committed and pushed. 13 commits on
`claude/product-list-stock-sync-uw19ae`, draft **PR #3** open against `master`.

- Nothing has been synced to Supabase. The catalogue is untouched and safe.
- No dashboard or Apps Script code changed.
- The reset order is costed and ready to place: 15 priced lines, £764.73 net.
- The method is documented and the corrections are recorded in the docs themselves,
  not just in conversation.

## Next Steps

1. **Tuesday 2026-08-11 — take the baseline count.** Individual items, **with the
   unit written into the column header.** Do not convert the existing `Stock`
   column; it mixes packs and items. This is count 1 and the baseline.
2. Place the reset order from that count using the sizing rule in
   `BASELINE-RESET.md` §3, and **log every delivery in the Order Log** — usage is
   `opening + orders_between − closing`, so an off-book delivery makes the
   arithmetic lie.
3. **Rescue the model scripts from the scratchpad into the repo** (suggest
   `migration/scripts/`) before the container is reclaimed. Without them, none of
   the CSVs can be regenerated when a figure changes.
4. Load `deliveries_backfill.csv` into `shop_consumable_deliveries` — those 26 orders
   genuinely happened and `orders_between` needs them. Only the demand *inference*
   was unsafe.
5. Agree the 9 flagged rows in `crosswalk.csv`, then rebuild the sheet's `Products`
   tab from `products_tab_final.csv` **with a hidden `product_name_raw` column** so
   the slug stays the key.
6. Run `syncProducts()` and verify the 5 intentionally-dropped products deactivated
   and nothing else did.
7. From count 2 onward, replace estimated pars with measured usage — fast movers
   first, which are readable after one Tuesday. Expect to revise them upward.

## Open Questions / Blockers

Each needs the user, not the model:

- **The 31-line first-aid proposal** — awaiting approval. Changing the required list
  is a business decision. Least confident grouping: crepe vs elastic bandages.
- **Pack sizes and prices for all 15 first-aid lines** — none exist, so a 247-item
  shortfall cannot become a costed order. Worth asking the kit supplier whether they
  do a **BS 8599-1 refill pack**, which would be one order unit instead of 15.
- **Ice pack pack size.** Requirement is 16, 11 on hand, short 5. The only pack size
  on record is 24 (old DB row), which overshoots to 35.
- **Order sizing: monthly or fortnightly.** Resizing every line to minimum + two
  weeks takes roughly £150–200 off the total. Offered, not chosen.
- **Newline and Concept Spa VAT basis** — unverifiable until an invoice arrives.
- **Deodorant price** — absent everywhere; 10 packs are in the order unpriced. Also
  30 cans each is ~5 months' cover; suggested trimming to 3 packs.
- **5 products dropped from the sheet** would be silently deactivated:
  `plastic_food_bags`, `clinell_wipes`, `kleenex_tissues`, `dispenser_pumps`,
  `blue_plasters`. Intentional?
- **Three minimums rest on unverified pars:** bin bags (400/month ≈ 13 bags a day),
  chill sanitiser (60/month ≈ 2 tubs a day), hand sanitiser.
- **Microfibre Cloths has no category** on the `Stock` tab; **Glade**'s count basis
  is still ambiguous (3 cans or 3 packs of 4?).
- **2 open issues** on the repo, not yet reviewed in any session.

## Environment & Config Notes

- Repo `ONE-LDN/consumables-dashboard`, **public**, GitHub Pages enabled, default
  branch `master`.
- Working branch `claude/product-list-stock-sync-uw19ae`; draft **PR #3**; head
  commit `6b85c9c`. Branch base is `master`.
- Supabase project `ljjwssicvvyyueyznmou`. Tables: `shop_product_lookup`,
  `shop_stock_takes`, `shop_consumable_deliveries`.
- `Code.gs` config that matters: `PRODUCTS_SHEET='Products'`,
  `COUNT_SHEET='Stock Count'`, `ORDER_SHEET='Order Log'`,
  `CATEGORY='Consumables'`; reconciliation key is `product_name_raw`.
- Credential names only: `index.html` carries the Supabase **anon** key (public by
  design, behind RLS). The Apps Script requires `SUPABASE_SERVICE_KEY` — the
  `service_role` key — which per `apps-script/SETUP.md` must **never** be committed
  anywhere. It does not appear in this repo and must not.
- Source sheet: Google Sheets `1DA77H1SG9aLELsvNFxL6VksNvVCFj5_xHZftgV2UPC4`.
- A PR check-in was armed via an in-session cron job. **Session-scoped — it dies with
  the session** and will not survive into the next one.

## Notes & Gotchas

- **The generating scripts are not in the repo.** `minstock.py` produces
  `min_stock_model.csv` and `products_tab_final.csv` from the XLSX; it holds every
  hand-confirmed constant (`FIRST_AID_COUNT`, `COUNT_BASIS`, `PURCHASE_FLOOR`,
  `BURN`, `UPP`, `LEAD_DEFAULT=2`, `MEASURE_ONLY`, `SURPLUS_CONFIRMED`). It lives in
  the ephemeral scratchpad. **If it is lost, the CSVs become hand-maintained
  artifacts nobody can regenerate.** Rescuing it is Next Step 3 for a reason.
- **`syncProducts()` deactivates the whole category before upserting.** Never run it
  against a sheet whose keys have not been checked against `crosswalk.csv`.
- **The burn rate is not consumption.** A delivery triggers a dispenser refill round,
  and the burn window counts that as usage. Use it for the minimum, never to size an
  order.
- **The purchase rate is a floor, not a measure**, because ordering was reactive.
  Anything derived from it understates — probably by 40–60% for the fast movers.
- **Nothing may hit zero during the measurement window.** A stockout reads as low
  consumption (you cannot use what isn't there) and corrupts that product's
  baseline. During the reset, err generous.
- **A weekly count only resolves about one unit**, so products moving less than one
  unit a week show nothing on Tuesday. The 5L refills will take a quarter to read.
  That is expected, not a fault.
- **DB `subcategory` is a storage location; the sheet's `Category` is a mix of
  location and product type.** They are different axes, so adopting the sheet's
  categories changes what the dashboard's grouping means. Two columns would settle
  it properly.
- The sheet has typos worth fixing at source: `counteed`, `Highlighers`,
  `Permamnent`, `Glade airfreshner sparys`. Column I is unlabelled overflow — two
  note cells that spilled out of column H.
- Sanitary products are **zero-rated** for UK VAT, so tampons and pads need separate
  treatment if they ever enter a costed order. Neither is being ordered now.
- `printer_ink` is £224.90 in the DB with no sheet price — looks like a multipack
  booked against a single cartridge. Worth checking.
