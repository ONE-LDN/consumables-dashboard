# Migration — `consumables_catalogue_v2` → dashboard catalogue

Analysis of the new Google Sheet
([`1DA77H1SG9aLELsvNFxL6VksNvVCFj5_xHZftgV2UPC4`](https://docs.google.com/spreadsheets/d/1DA77H1SG9aLELsvNFxL6VksNvVCFj5_xHZftgV2UPC4/edit))
against what is live in Supabase (`shop_product_lookup`, `category='Consumables'`).

**No dashboard or Apps Script code has been changed.** These are read-only
working files to agree the mapping before anything is synced.

## What's in the new sheet

| Tab | Rows | Columns | Role |
|---|---|---|---|
| `Stock` | 52 products | Product, Category, Supplier, Par Qty, Cost, Cadence, **Stock**, Notes, *(unlabelled col I)* | The stock count sheet. Authoritative per Saffron. Carries live on-hand counts. |
| `Product List (Updated)` | 55 products | Product, Category, Supplier, Qty, Cost, Cadence, Notes | The catalogue. Superset of `Stock` by 3 stationery rows. |
| `Consumables Invoices` | 26 order lines | Invoice Date, Description, Qty, Supplier, Price, Net Amount | Feb–Jul 2026 purchase history, transcribed from 13 supplier invoices. |

Live in Supabase: **40 active** consumables (+ ~40 already-inactive legacy rows),
keyed on short slugs (`toilet_rolls`, `blue_rolls`, …) with a separate friendly
`display_name`.

## The drift, in order of consequence

### 1. No trustworthy usage figure exists anywhere

`monthly_par_packs` is the baseline of the prediction model, and nothing in the
system currently supplies a reliable one.

- The sheet has no usage column at all. `Par Qty` is target on-hand, and
  `Cadence` is free text in five formats (`6 pk/pm`, `1 p/m`, bare `1`/`7`, `?`,
  blank).
- The stored pars match the invoice purchase rate to 2 d.p. — but they were
  *derived* from those purchases, so that's circularity, not validation.
- **The purchases themselves are unreliable.** The previous operations manager
  ordered reactively, after running out, so consumption was suppressed during the
  dry spells. Purchase rate is a **floor** on demand, not a measure of it.

A burn check against the 29/07 count suggests the fast movers are understated by
**40–60%** (toilet roll 7.61 packs/mo vs a 5.59 floor; blue roll 8.46 vs 4.97;
shampoo 11.42 vs 6.42). Full working in `MINIMUM-STOCK.md`.

Consequences: minimums are safe because they take the **highest** of four
candidates and `Par Qty` was already carrying the fast movers. **Order quantities
were too small** — and undersized orders are the mechanism that perpetuates
reactive ordering. Those have been raised.

The first few Tuesday counts will be the first trustworthy usage data this system
has had. Don't overwrite `monthly_par_packs` from `Par Qty` or `Cadence`; let
measured usage from consecutive counts take over.

### 2. Product names changed wholesale, so a naive sync wipes the catalogue

The sheet identifies products by full supplier description
(`Jumbo T.Roll 2ply 2.25" Core J26300 300m`); Supabase keys on `toilet_rolls`.
`syncProducts` reconciles by `product_name_raw`, so running it against the new
sheet as-is would deactivate all 40 live rows, insert 55 unrelated ones, and
orphan every count and delivery.

Mitigating factor: history is currently **1 stock take (2026-07-29, 38 products)
and 0 deliveries**. A re-key is cheap today and gets more expensive every week.

Recommended: keep the slug as the key, add a hidden `product_name_raw` column to
the sheet (same pattern the `Stock Count` tab already uses), and let the full
supplier description live in `order_link_or_desc` where it belongs.

### 3. Cost column mixes VAT bases

The seven trade-supplier prices are **net ex-VAT** in the sheet and **gross** in
the DB — exactly ×1.20 in every case, verified against the invoice tab. The
Amazon prices are identical in both, i.e. VAT-inclusive retail.

So the sheet's `Cost` column is currently net for Futures/Out of Eden and gross
for Amazon. The shopping-list totals need one basis. Recommend **net ex-VAT
throughout** (matches the invoices), which means dividing the Amazon figures.

Six prices have genuinely changed and should be taken from the sheet:

| product | DB | sheet |
|---|---|---|
| Sanitary Pads | £28.76 | £7.99 |
| D Batteries (Ergs) | £10.76 | £15.99 |
| Chalk Block | £13.32 | £15.99 |
| Puly Caffe Cleaner | £19.79 | £21.47 |
| Washing up liquid | £12.46 | £11.87 |
| Hair Bands | £4.89 | £3.99 |

Printer ink is £224.90 in the DB with no sheet price — that looks like a whole
multipack booked against one cartridge and is worth checking.

### 4. Category means something different now

DB `subcategory` is a storage location (`Main` / `FOH Desk` /
`Cafe (HP Cupboard)` / `Printer`). The sheet's `Category` is a mix of location
and product type: `Toiletries`, `Gym Floor`, `Staff Room`, `First Aid`,
`FOH Desk`, `Cafe`, `Plant room`, `Cleaning`.

The new taxonomy is more useful for ordering, but it is a different axis, so the
dashboard's location grouping changes meaning. Note `Greenspeed Techno Multi` is
`Staff Room` on the Stock tab and `Cleaning` on the Product List — the two tabs
disagree. Two columns (location + category) would settle this properly.

### 5. First aid went from one line to sixteen

The DB holds a single `hs_refills` (320-piece kit, £24.53) plus `ice_packs`. The
sheet itemises 16 first-aid lines, all `Split between 4 boxes`, all with no cost
and supplier `Amazon?`. They also have no stock counts.

These are consumption-tracked components of restock boxes, not order units. They
will produce 14 new products with no price, no par and no count — every one
flagged "order now" with a £0 suggested order.

### 6. Counting unit conflicts with the schema — resolved

`shop_stock_takes` stores counts in packs; the sheet counts toilet roll and blue
roll in rolls. **Decided: count in individual units throughout**, with
`units_per_pack` converting for ordering. See `MINIMUM-STOCK.md`.

### 7. Smaller items

- 5 live products have no row in the new sheet and would be silently
  deactivated: `plastic_food_bags`, `clinell_wipes`, `kleenex_tissues`,
  `dispenser_pumps`, `blue_plasters`. Intentional or dropped by accident?
- `Sea Kelp Luxury Shampoo 5L Refill` is noted `no longer stock` but is still a
  row in both tabs — retire it rather than add it. Odyssey replaced it.
- `Urinal case` vs DB `Urinal Shields (x10)` — same item?
- `Hand sanitiser` vs DB `Sanitiser Gel` (5L, Futures) — sheet has no supplier
  and the note reads `Oceanfree Professional?`.
- 3 stationery rows exist on the Product List but not the Stock tab
  (`Highlighers`, `White board marker`, `Permamnent marker`) — count them or drop
  them.
- `Notes` mixes order descriptions (`DCS 200 heavy duty bin bags 80L`) with
  operational instructions (`stock take every tuesday`, `need 1 on hand`). Only
  the first kind belongs in `order_link_or_desc`.
- Column I is unlabelled overflow — two cells of notes that spilled out of H.
- Typos to fix at source: `counteed`, `Highlighers`, `Permamnent`,
  `Glade airfreshner sparys`.
- `units_per_pack` has no column at all; pack size only appears inside note text.

## Files here

| File | What it is |
|---|---|
| `crosswalk.csv` | Every sheet row mapped to its live Supabase key, with field-level drift, VAT basis, and 9 rows flagged for a decision. 34 matched, 14 new first-aid, 7 other new, 5 dropped. |
| `products_tab_final.csv` | The canonical 52 products from the `Stock` tab, restructured for `Code.gs`, keys preserved, with `units_per_pack` / `count_unit` / `min_stock_units` / `order_up_to_units` added. |
| `min_stock_model.csv` | The minimum-stock working for all 52 products: inputs, which candidate set the minimum, order-up-to level, implied cadence, count basis, per-row flags. |
| `MINIMUM-STOCK.md` | How the minimum is worked out, and why. |
| `deliveries_backfill.csv` | All 26 invoice lines as `shop_consumable_deliveries` rows, mapped to keys. 8 products, £1,659.59 net, Feb–Jul 2026. Still worth loading — the orders genuinely happened and `orders_between` needs them; it was only the demand inference that was unsafe. |

## Decisions taken (2026-08-04)

- **Counting is in individual units, not packs.** `units_per_pack` becomes
  required for ordering. Consequences in `MINIMUM-STOCK.md`.
- **The `Stock` tab is the canonical product list** — 52 products. The 3
  stationery rows that exist only on `Product List (Updated)` (`Highlighers`,
  `White board marker`, `Permamnent marker`) are dropped.
- **The `Stock` tab's categories are canonical**, so `Greenspeed Techno Multi` is
  `Staff Room`, not `Cleaning`.
- **Minimum stock is derived and `Cadence` is retired.** Weekly Tuesday counts
  make order cadence an output rather than an input — method in
  `MINIMUM-STOCK.md`.

## Suggested sequence

1. Agree the 9 flagged rows in `crosswalk.csv`.
2. Settle the remaining schema question: VAT basis (net throughout recommended).
3. Rebuild the sheet's `Products` tab from `products_tab_final.csv`, adding a
   hidden `product_name_raw` column.
4. Load `deliveries_backfill.csv` into `shop_consumable_deliveries` — that gives
   the hybrid model 5 months of real usage immediately instead of waiting for a
   second stock count.
5. Run `syncProducts`, then check the 5 dropped products deactivated as intended.
6. Take a fresh unit count on the first Tuesday, with the unit in the column
   header. Do **not** convert the existing `Stock` column — it mixes packs and
   items, and 9 products can't be told apart (see `MINIMUM-STOCK.md`).
