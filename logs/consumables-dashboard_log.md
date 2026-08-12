# Session log — ONE LDN consumables dashboard

Rolling handoff log. **Newest entry at the top.** Prepend new entries directly below
this header; never append at the bottom and never edit prior entries.

Written and maintained by the `session-log` skill (`.claude/skills/session-log/`).
This is an engineering handoff for the next Claude session — it is **not** the
contractual documentation suite and nothing here goes to Notion.

**This repository is public.** No credential values, no personnel narrative.

---

# v4 product list, the junk count, and a salvaged baseline
**Date:** 2026-08-12
**Project:** ONE LDN consumables dashboard — v4 catalogue, baseline count, first aid split
**Mode:** Rolling Log + Git Push
**Status:** Complete (planning) — PR #4 merged. **Nothing executed yet:** no code
change, no Supabase write, junk count still live.

---

## Project Context

See the 2026-08-05 entry for the architecture (Sheet → Apps Script → Supabase →
`index.html`) and the minimum-stock method. What is new: the product list was
rebuilt **again**, as `consumables_catalogue_v4`, and most of the previous
session's artifacts are superseded by it.

Sheet lineage, which is confusing and worth pinning down:

| sheet | ID | what it is |
|---|---|---|
| `consumables_catalogue_v3` | `1DA77H1SG9aLELsvNFxL6VksNvVCFj5_xHZftgV2UPC4` | the sheet the 2026-08-05 session called "v2". **Renamed**, not replaced. Its `Stock` column is the 04/08 baseline count |
| `consumables_catalogue_v4` | `1iWeiiY2a_hc98gy7T-Itsst9VMHfuiRXfcwJ16OH-z8` | current. One tab, `Product List (Updated)`, A1:G36, 35 products |

## Session Goal

Plan the adjustment of the dashboard and stock-take sheet to the v4 product list:
agree the product set, split first aid onto its own tab, remove brand names from
the count sheet and dashboard, and wire in the 2026-08-04 stock count.

## State Before This Session

Per the 2026-08-05 entry: analysis complete on PR #3 (merged), nothing synced to
Supabase, 40-ish active consumables, and what was believed to be one real stock
take (2026-07-29, 38 rows) plus zero deliveries. **That belief was wrong** — see
Corrections.

## What Was Done

**Read v4 and reconciled it against the live DB.** 35 consumables. Against 39
live active rows: 32 stay, 4 deactivate, 3 move to First Aid, 3 are new.
`39 − 4 − 3 + 3 = 35`, no key collisions.

**Found the 29/07 count is junk** (Correction 1) and traced what it would have
done to the dashboard.

**Found the missing 04/08 count** — it was v3's `Stock` column, unlabelled as a
count, which is why the previous session and this one both failed to locate it
until Saffron pasted it. She then supplied the basis, which unlocked it
(Correction 2).

**Designed the unit model.** One unit — items — everywhere; pack size converts to
packs only at the ordering step. Two guard rails, because "count in items" was
already the 2026-08-05 decision and it still went wrong: the count-sheet header
carries the noun per product (`Count (rolls)`), and `unit_basis_v4.csv` states
for all 35 products what a count of 1 means.

**Found a live bug in `index.html`** — see Notes & Gotchas. Not fixed.

**Wrote committed generators.** `build_v4.py` and `build_baseline_count.py`,
closing the largest handoff gap the 2026-08-05 entry recorded (its model lived in
an ephemeral scratchpad and was lost with the container, exactly as predicted).

**What did not work / was abandoned:**

- **Reading `Par Qty` as packs everywhere.** Seven rows multiply out to v3's item
  figure exactly, which looked conclusive, but the same rule gives Water Softener
  Salt a 100-bag / ~£1,500 minimum. Abandoned in favour of a per-row `Par Unit`
  column.
- **Deriving anything from the 29/07 count.** It is 38 copies of the number 6.
- **`send_later` for the PR check-in.** The `Claude_Code_Remote` MCP server
  flapped repeatedly; fell back to an in-session `CronCreate` job, which then
  vanished from the session store on its own. Neither survives the container.

## Artifacts Produced / Modified

| File | What it is | Status | Path |
|------|------------|--------|------|
| `PLAN-V4.md` | The plan: unit model, naming, tab structure, Supabase + dashboard changes, sequence, decisions, 6 still open | Created | `migration/` |
| `build_v4.py` | Generator for the catalogue CSVs. Holds every hand-confirmed constant with a provenance tag (`SHEET_V4`, `SHORT_NAME`, `COUNT_UNIT`, `PACK_OVERRIDE`, `PACK_FROM_DB`, `PAR_UNIT_ITEMS`, `PAR_UNIT_UNCERTAIN`, `NOTE_MIN`, `MEASURE_ONLY`, `FIRST_AID`) | Created | `migration/scripts/` |
| `build_baseline_count.py` | Stages the 04/08 count against v4 keys (`COUNT_V3`, `COUNT_TO_V4_KEY`, `RESOLVED_BASIS`, `ADJUSTED`, `SURPLUS_CONFIRMED`, `ROBUST_ORDER`) | Created | `migration/scripts/` |
| `products_v4.csv` | 35 consumables, with `par_unit`, `par_unit_basis`, `min_confirmed`, `order_class` | Created | `migration/` |
| `first_aid_v4.csv` | 33 first-aid lines. Independently reproduces `FIRST-AID.md`: 14 short, 247 items | Created | `migration/` |
| `unit_basis_v4.csv` | Per product: count header, what 1 means, order unit, minimum | Created | `migration/` |
| `baseline_count_2026_08_04.csv` | Baseline count 1, 35 rows keyed to v4 | Created | `migration/` |
| `README.md` | Superseded banner; which of its 7 findings survive | Modified | `migration/` |
| `MINIMUM-STOCK.md` | Three retractions prepended | Modified | `migration/` |
| `consumables-dashboard_log.md` | This entry | Modified | `logs/` |

**Not touched:** `index.html`, `apps-script/Code.gs`, `apps-script/SETUP.md`. **No
Supabase writes.**

## Decisions & Reasoning

- **`Par Unit` becomes a per-row column on the sheet** (Saffron, overriding my
  recommendation of a `Par Qty (packs)` header). Mine was wrong: a uniform rule is
  only safe if the data is uniform, and it isn't. Her call produced 25 syncable
  minimums vs 23, and resolved all three implausible figures.
- **Keys stay as they are.** Brand/supplier changes move the *description*, not
  the key, so the four re-branded toiletries keep their invoice history. Saffron:
  *"The names don't matter in the long run for the stock baseline."*
- **Three name fields, not one:** hidden slug / short brand-free `display_name`
  (count sheet + dashboard) / full supplier description (catalogue + shopping list
  only). Directly from Saffron's requirement that brand not appear on the count
  sheet.
- **First Aid gets its own Supabase `category`, not a subcategory.** Different
  regime — quarterly vs weekly, BS 8599-1 compliance vs consumption, kit-level vs
  item-level ordering. One category would put 33 never-reordered rows into the
  Consumables prediction model. Rejected: `subcategory='First Aid'`.
- **First aid is ordered via a BS 8599-1 refill pack** (Saffron), not item by
  item. Rejected: pricing up all 12 short lines.
- **The 4 absent products are dropped on purpose** (Saffron) — `plastic_food_bags`,
  `clinell_wipes`, `kleenex_tissues`, `dispenser_pumps`.
- **Add `monthly_usage_units`** rather than store items in `monthly_par_packs`. A
  column named "packs" holding items is the same class of mistake as the untyped
  `Stock` column and will be believed by whoever reads it next.
- **Minimum = `Par Qty` in items, full stop.** With the burn-rate evidence
  retracted there is no usage figure at all, so the four-candidate model collapses
  to Saffron's judgement plus note-stated requirements. Measured usage takes over
  from count 2.
- **Refuse to compute rather than compute through a gap.** `min_confirmed` and
  `basis_confirmed` exist so the dashboard can say "needs a pack size" instead of
  showing a confident wrong number.
- **Chill Tub Filters counted 10 → adjusted to 4** (my judgement, flagged in the
  CSV). Note reads "4 new ones. 6 old."; counting spent filters against a minimum
  of 1 suppresses a reorder indefinitely.
- **Wet Kit Bags is orderable despite an unconfirmed minimum.** 3 bags is below
  every candidate (20 old par, 500 new), so the *decision* is safe even though the
  *quantity* isn't. Worth separating those two — most held lines block both.

## Corrections Made This Session

Five. The first two invalidate substantial parts of the 2026-08-05 entry.

1. **The 2026-07-29 stock take is not data.** The prior entry calls it "1 stock
   take (2026-07-29, 38 products)" and plans around preserving it and not
   orphaning it. All 38 rows have `actual_count = 6` — one distinct value.
   `SELECT take_date, count(DISTINCT actual_count) …` shows `distinct_vals = 1,
   min = 6, max = 6`. It is deleted, not migrated. Consequence: with deliveries
   also empty, there is **no consumables history at all**, which is what makes the
   reset free.
2. **"The existing counts can't be salvaged" was wrong.** The prior entry states
   the `Stock` column "silently mixes packs and items and 9 products cannot be
   told apart. Not salvageable — needs a fresh count." Saffron: *"Counted
   primarily per item and where bottles or tubs were in question, fractions
   etc."* Under that rule **30 of 34 lines read cleanly**, and the decimals land
   exactly where they should (2.5 Greenspeed, 0.5 Puly, 0.5 ream). Only 4 needed
   her to state the basis. The column was usable; the convention had never been
   written down. **Consequence: no redo count is needed**, so the next Tuesday
   count is count 2 — the first usage reading — not a repeat of count 1.
3. **The 2026-08-05 burn-rate evidence has no measurement behind it.** The
   "fast movers understated by 40–60%" finding, and all four burn-checked usage
   figures, derive from the junk count. Retracted in `MINIMUM-STOCK.md` as
   removed, not merely uncertain. Three of the four products no longer exist
   anyway (Sea Kelp → Odyssey).
4. **Reading `Par Qty` as packs everywhere.** My first pass produced Chalk Block
   16 blocks (v3 said 2, shelf held 1), Water Softener Salt 100 bags ≈ £1,500, and
   Printer Paper 2 packs against a note reading "2 on hand". The intuitive reading
   — seven exact hits! — was the wrong one. Fixed by `PAR_UNIT_ITEMS`.
5. **Dates in the v4 docs were stamped 2026-08-05.** Every "Decided/confirmed
   2026-08-05" in `PLAN-V4.md`, both scripts and `MINIMUM-STOCK.md` referred to
   *this* session's decisions and has been corrected to **2026-08-12** — they were
   misattributing this session's calls to the previous one. Same root cause: the
   plan said "count Tue 11/08", which had already passed uncounted. Now 18/08,
   with the 14-day interval called out. (GitHub's API reported PR #4's `created_at`
   as `2026-08-05T15:47Z`, which is what seeded the confusion; the container clock
   and commit timestamps both say 2026-08-12. **Do not trust that API field here.**)

## Skills / Tooling Used

- **Google Drive MCP** — `read_file_content` on both sheets. Note it returns *all*
  tabs concatenated, which is how v3's `Stock` column and invoice tab were
  recovered without a download.
- **Supabase MCP** (`ljjwssicvvyyueyznmou`) — read-only. Diagnosed the junk count,
  confirmed 0 deliveries, `min_stock_units` NULL across all 39 rows, and that
  `stock_tracked=false` already varies by category. **No writes.**
- **GitHub MCP** — PR #4 create / body refresh / status. Flapped constantly;
  expect to re-`ToolSearch` after most disconnect notices.
- **`migration/scripts/*.py`** — both committed, both verified to regenerate their
  CSVs byte-identically. Unlike last session, these survive the container.

## Current State (end of session)

- **PR #4 merged** into `master` (`f104249`). Working branch reset onto it and
  re-pushed (the branch was deleted on merge, so the push recreated it).
- **Nothing executed.** No `Code.gs` or `index.html` change, no Supabase write.
  The 38 junk counts are **still in `shop_stock_takes`**.
- The log-entry commit and the Correction-5 date fixes are the only uncommitted
  work at the time of writing.
- Merging PR #4 was **not** approval to execute — it put the plan on `master`.
  Saffron was asked directly whether to start and has not answered.

## Next Steps

1. **Delete the junk count**, before anything reads it:
   ```sql
   delete from shop_stock_takes
   where take_date = '2026-07-29' and source = 'sheet'
     and product_name_raw in (select product_name_raw from shop_product_lookup
                              where category = 'Consumables');
   ```
   38 rows. Scoped so the shop dashboard's own 2026-07-29 set (65 rows,
   `source='manual'`) is untouched.
2. **Fix `index.html`** — multiply `qty_cases` by `pack_size` in both delivery
   reductions in `computeItem()` (`ordersBetween` and `ordersSince`). See Gotchas.
3. **Parameterise `Code.gs`** — `syncProducts(sheet, category)` etc. for the two
   tab pairs; `buildCountSheet` writes `Count (${count_unit})`.
4. `alter table shop_product_lookup add column monthly_usage_units numeric;` and
   create the `First Aid` category.
5. **Rebuild the sheet** — `Products` from `products_v4.csv` with a hidden
   `product_name_raw` column and a `Par Unit` column; new `First Aid` tab.
6. **Run `syncProducts`** for both tabs; verify 35 + 33 active and exactly the 4
   intended deactivations.
7. Load `baseline_count_2026_08_04.csv` (29 usable lines) and
   `deliveries_backfill.csv` (26 orders, £1,659.59 net).
8. **Place the reset order** from the 14 below-minimum lines, re-costed at v4
   prices, and **log it in `Order Log` before 18/08**.
9. **Count Tue 18/08 as count 2.**

## Open Questions / Blockers

All need Saffron. Full text in `PLAN-V4.md` §12.

- **Whether to start executing.** Asked directly, not answered. Steps 1–4 depend
  on nothing else.
- **3 `Par Unit` rows** — Blue Cloth, Ice Bath Sanitiser, Nitrile Gloves. (Wet Kit
  Bags no longer blocks the order, only the quantity.)
- **Water Softener Salt: £149.99 for what?** Pack size blank, note says "6 packs
  to fill tub". Per-bag vs per-pallet moves the shopping list by an order of
  magnitude. Keep out of any costed order until settled.
- **`Microfibre Cloths` has no category** — the only blank on v4. Suggested
  `Staff Room`.
- **Does the kit supplier sell a BS 8599-1 refill pack?** The whole first-aid
  ordering plan rests on it. A phone call, not a modelling problem.
- **Concept Spa's VAT basis** — last unverified line, £15.00 exposure.
- **Tampons and pads have a blank `Par Qty`.** On a confirmed surplus (256 and 484
  items) blank means "do not reorder", but it should be stated rather than left as
  an empty cell someone later fills in as an oversight.

## Environment & Config Notes

- Repo `ONE-LDN/consumables-dashboard`, **public**, Pages enabled, default branch
  `master` at `f104249`.
- Working branch `claude/consumables-dashboard-planning-u2apmy`. **PR #4 merged**
  — per the branch rules, follow-up work restarts the branch from `master`; do not
  stack on merged history or reuse PR #4.
- Commits this session: `a2e6541`, `94f427a`, `2396d9a`, `5fa633b`.
- **No CI.** No `.github/workflows`; `get_status` returns `total_count: 0`. There
  is nothing to go green — do not wait on checks.
- Supabase `ljjwssicvvyyueyznmou`. Tables `shop_product_lookup`,
  `shop_stock_takes`, `shop_consumable_deliveries`. `shop_stock_takes` is **shared
  with the shop dashboard** — always scope deletes by category.
- `Code.gs` config: `PRODUCTS_SHEET='Products'`, `COUNT_SHEET='Stock Count'`,
  `ORDER_SHEET='Order Log'`, `CATEGORY='Consumables'`; reconciliation key is
  `product_name_raw`.
- Credential names only: `index.html` carries the Supabase **anon** key (public by
  design, behind RLS). Apps Script needs `SUPABASE_SERVICE_KEY` — the
  `service_role` key — which per `apps-script/SETUP.md` must **never** be
  committed. It is not in this repo and must not be.
- **0 open issues** on the repo. The 2026-08-05 entry says "2 open issues"; there
  are none, so that line is stale.

## Notes & Gotchas

- **`index.html` adds packs to items.** `computeItem()` computes
  `older.actual_count + ordersBetween − newer.actual_count`, but `ordersBetween`
  sums `qty_cases`, which is **packs**, while counts become **items**. A delivery
  of one bin-bag pack reads as 1 bag, not 200. This must land in the same change
  as the unit switch or the first two counts produce nonsense — it silently
  corrupts the very data the reset exists to collect.
- **`syncProducts()` still deactivates the whole category before upserting.** Run
  against a sheet with no `product_name_raw` column it deactivates all 39 live
  rows and inserts 35 unrelated ones. The hidden key column is what makes it safe.
- **The v4 `Pack Size` column does not always mean items-per-order-unit.** Blue
  Cloth reads 150, which is *sheets per roll*; the order unit is a 6-roll case.
  Handled by `PACK_OVERRIDE`; worth fixing at source.
- **The 04/08 count's four container exceptions do not follow one rule** —
  tampons and pads are packs, bin bags is half a pack, wet kit bags is items. This
  is precisely why basis belongs per product (`count_basis`) rather than asserted
  once for the sheet.
- **Blank count cells are not zeros.** Microfibre Cloths and Notepads were not
  counted. Recording them as 0 would fabricate a stockout.
- **A weekly count resolves about one unit.** Products moving under one unit a
  week show nothing on a Tuesday; the 5L refills take a quarter to read. Expected,
  not a fault.
- **Nothing may hit zero during the measurement window.** A stockout reads as low
  consumption and corrupts that product's baseline. During the reset, err generous.
- **Burn rate is still not consumption** (a delivery triggers a dispenser refill
  round) and **the purchase rate is still a floor** (ordering was reactive). Those
  two conclusions from 2026-08-05 survive; only the *numbers* were retracted.
- **`hs_refills` and `blue_plasters` were deliberately reused** as first-aid keys
  rather than minting `fa_*` ones — they are live rows carrying real prices
  (£24.53, £3.57).
- **MCP servers flap badly in this environment.** Expect `ToolSearch` to be needed
  repeatedly. `send_later` and `CronCreate` both proved unreliable for PR
  check-ins, and both are session-scoped regardless.

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
