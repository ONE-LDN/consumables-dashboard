# Session log — ONE LDN consumables dashboard

Rolling handoff log. **Newest entry at the top.** Prepend new entries directly below
this header; never append at the bottom and never edit prior entries.

Written and maintained by the `session-log` skill (`.claude/skills/session-log/`).
This is an engineering handoff for the next Claude session — it is **not** the
contractual documentation suite and nothing here goes to Notion.

**This repository is public.** No credential values, no personnel narrative.

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
