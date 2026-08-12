# The consumables workbook

**Google Sheet:** [ONE LDN Consumables Catalogue and Stock Take](https://docs.google.com/spreadsheets/d/13hUhCIw-D46Fn1UDURBaVDHWtypxcS03MTsoWFrhvhI/edit)
(`13hUhCIw-D46Fn1UDURBaVDHWtypxcS03MTsoWFrhvhI`)

One workbook holds the catalogue, the weekly count and the delivery log. The
Apps Script pushes it to Supabase; the dashboard reads Supabase. **Nothing is
maintained in two places** — that is the whole point of folding the catalogue
into the stock take sheet.

```
Products tab ──► Stock Count tab      (VLOOKUP, live)
     │      ──► Order Log dropdown    (rebuilt on demand)
     │
     └─ syncProducts ──► Supabase ──► dashboard
```

> ⚠ **Delete the four superseded sheets:** `1linoZ_oo…`, `1xGKdynO2…`,
> `1CvPuwat…` and `1R_uIZfM…`. Each is an earlier draft with different columns,
> a different product set, or stale rows. Several near-identical sheets is how a
> count ends up in the wrong place.
>
> If you have already started working in `1R_uIZfM…`, keep it and paste
> `products_tab.csv` over cell A1 instead — it is the same 30 rows, so nothing
> is left behind.

Generated from `products_v4.csv` by `scripts/build_workbook.py`. Regenerate and
re-paste when the product list changes; do not hand-edit the CSVs.

| CSV | tab |
|---|---|
| `products_tab.csv` | `Products` — 30-line catalogue |
| `stock_count_sheet.csv` | `Stock Count` — weekly count |
| `order_log_tab.csv` | `Order Log` — deliveries, in packs |

First aid is **not** in the workbook yet: separate 33-line list, quarterly
cadence, data ready in `first_aid_v4.csv` (PLAN-V4 §8).

---

## Setting it up

1. Rename the imported tab to **`Products`**.
2. **Extensions ▸ Apps Script**, paste `apps-script/Code.gs`, save. Reload the
   sheet; a **Consumables** menu appears.
3. Menu ▸ **② Rebuild Stock Count sheet** — creates the tab, formatted, with the
   lookups wired up.
4. Menu ▸ **④ Rebuild Order Log sheet** — creates the tab with the product
   dropdown, then paste `order_log_tab.csv`'s six rows (the 07/08 deliveries).

None of that needs Supabase. Only steps ① and ③/⑤ talk to the database, and
they need the script properties in `apps-script/SETUP.md` first.

---

## `Products` — the catalogue

Hand-maintained. One row per product, 30 rows, 16 columns.

| col | | |
|---|---|---|
| A | `product_name_raw` | **the sync key. Never edit it.** Renaming it orphans every count and delivery for that product |
| B | Product name | what appears on the count sheet and the dashboard |
| C | Category | product type |
| D | Location | where you count it |
| E | Count unit | what a count of 1 means |
| F | Supplier | |
| G | Product description | the long supplier description — for ordering, not display |
| H | Pack size | items per order unit |
| I | Price per pack | **net of VAT** |
| J | Par qty | as written |
| K | Par unit | `packs` or `items` |
| L | Min override | a stated requirement, in items |
| M | **Minimum** | **formula** — items |
| N | Min confirmed | `yes` / `no` |
| O | Order class | `reorder` / `measure_only` |
| P | Notes | |

### Minimum is a formula

```
=IF(L<>"", L, IF(J="","", IF(K="packs", IF(H="","", J*H), J)))
```

Override if one is set, else Par × Pack size when the par is in packs, else the
par as written. **Change a par or a pack size and the minimum follows** — which
is the reason for one workbook rather than three.

One row carries an override, from the sheet's own notes, because an
explicitly-stated human requirement beats the computed candidate
(`MINIMUM-STOCK.md`): **D Batteries** 10, where Par × Pack gives 8. Every other
row's formula reproduces the agreed v4 minimum exactly.

A blank par gives a **blank** minimum, never `0`. "No minimum set" and "a
minimum of zero" are different claims, and the dashboard is meant to refuse to
compute rather than show a confident wrong number.

### Category and Location are different axes

The v4 sheet had one `Category` column that mixed them — `Toiletries` is a
product type, `Gym Floor` is a place. This is the split PLAN-V4 called for.

`Location` keeps the v4 values and drives the count walk: FOH Desk (6) → Cafe
(3) → Gym Floor (2) → Toiletries (14) → Staff Room (4) → Plant room (1).

`Category` is derived from the products themselves: Cleaning (8), Toiletries
(7), Washroom (4), Facilities (3), Member Supplies (3), Stationery (3), Gym (2).

The split earns its keep where the two disagree: **D Batteries** are Category
`Gym` (they run the ergs), Location `FOH Desk` (that is where the drawer is).

⚠ Seven rows read `Toiletries | Toiletries` — the v4 location for the changing
rooms is the same word as the product type. Worth renaming the location to
`Changing Rooms`. Cosmetic, not a data problem.

### Prices are net

Four prices were corrected on import. v4 carried **£25.19** for the Out of Eden
toiletries, which is VAT-inclusive: `20.99 × 1.20 = 25.19`. The 2026-08-07
invoice states £20.99 net, and the Futures prices in the same column (£11.31,
£26.98) match their invoice net to the penny. `hand_wash`, `conditioner`,
`moisturiser` and `shampoo` are now **£20.99**, flagged in Notes.

Out of Eden also discounts by line (5% and 10% on that invoice), so the price
paid is not the list price. The catalogue holds list net; the discount belongs
on the delivery record.

---

## `Stock Count` — the weekly count

| col | | |
|---|---|---|
| A | Product name | the join key |
| B | Category | VLOOKUP |
| C | Location | VLOOKUP |
| D | **Count** | the only column anyone types in |
| E | Unit | VLOOKUP |

`B1` take date (must be a real date), `B2` counted by, header row 3, products
from row 4 in walk order.

Category, Location and Unit look themselves up from `Products` **per row, keyed
on the name beside them**. Edit the catalogue and the count sheet follows.

Keyed per row deliberately: a whole-range formula would re-sort the product
names without moving the counts beside them, filing every count against the
wrong product. Only **adding or removing** a product needs a rebuild (menu ②).

### No `product_name_raw` column

Saffron's call: the slug stays on `Products`, not on the sheet people count
into. `submitCounts()` joins on the product name against the `Products` tab.

The cost, stated plainly: **renaming a product on the count sheet breaks the
join.** So it fails loudly — `submitCounts()` **refuses the entire submission**
if any name fails to match, and names the offenders. A partial count reads as a
real count and would corrupt usage for every product that silently dropped out.
`syncProducts()` enforces the other half, rejecting duplicate keys or names.

### Counting rules

Two of the shop sheet's rules are wrong here and would corrupt the baseline:

- **Decimals are correct and expected.** Half a 5L bottle is `0.5`.
  `actual_count` is `numeric`.
- **Count in items, never packs.** 24 rolls, not 4 packs. Column E says which.

Unchanged, and still the rules that matter most:

- **Blank means "not counted". `0` means "counted, none left."**
- **Every delivery goes in the Order Log.** Usage is
  `opening + orders_between − closing`; an unlogged delivery makes it lie.

---

## `Order Log` — deliveries

`Date | Product | Packs ordered | Unit cost £ (optional) | Supplier (optional) | Notes`.
Quantities in **packs**. Product is a dropdown built from `Products`, so no
order can name something submit will reject.

⑤ submits to `shop_consumable_deliveries` and then clears the rows — the log is
an inbox, not the archive. Rebuilding the tab (④) does **not** clear it, so an
entered-but-unsubmitted delivery survives a catalogue edit.

---

## What the script does now

Everything reads the `Products` tab; nothing reads the catalogue back out of
Supabase. The workbook is the master, so a round trip through the database to
rebuild a tab would only create a way for the two to disagree.

| function | reads | writes |
|---|---|---|
| ① `syncProducts` | Products | `shop_product_lookup` |
| ② `buildCountSheet` | Products | Stock Count tab |
| ③ `submitCounts` | Stock Count + Products | `shop_stock_takes` |
| ④ `buildOrderSheet` | Products | Order Log header + dropdown |
| ⑤ `submitOrders` | Order Log + Products | `shop_consumable_deliveries` |

⚠ `syncProducts` still **deactivates the whole `Consumables` category before
upserting**. With column A present that is correct — it is what deactivates the
4 intended drops. Never run it against a Products tab whose keys have not been
checked.

### Supabase columns needed before ① will run

`product_type` **already exists** and takes `Category` directly. Three do not:

```sql
alter table shop_product_lookup add column count_unit    text;
alter table shop_product_lookup add column min_confirmed boolean;
alter table shop_product_lookup add column order_class   text;
```

Add these alongside `monthly_usage_units` from PLAN-V4 §6. Until they exist,
`syncProducts` fails with a PostgREST error naming the missing column — which is
the intended behaviour, not a silent partial write.

`min_stock_units` already exists and is `integer`; `monthly_par_packs` stops
being written.

## Changes taken 2026-08-12

`products_v4.csv` stays a faithful record of what the v4 sheet said. These are
decisions on top of it, held as explicit constants in `build_workbook.py`, so
the diff between the sheet and the catalogue is always readable. **35 → 30
products.**

| | |
|---|---|
| **Urinal Shields** | removed |
| **Notepads** | removed |
| **Printer inks** | the four single-colour rows merged into one, `printer_ink` |
| **Pens** | product link added; pack size and price still needed |
| **Key Fobs** | pack size and price now evidenced |

### The ink merge

The supplied invoice settles it: **SODFACE TN248**, compatible with Brother
TN248XL, sold as a **4-pack** at **£38.32 net** (£45.99 gross, ×1.20 ✓). The
four colours were always one purchase, so one row is what the ordering actually
looks like.

Each of the four rows had a par of 1 cartridge, so the merged par of 1 pack —
4 cartridges — is the same requirement stated once, not a new one.

**It also closes a standing question.** The old `printer_ink_blk` row carried
**£224.90**, which the session log flagged as *"looks like a multipack booked
against a single cartridge"*. It is not that either: the pack costs £38.32.
£224.90 is simply wrong, and is not carried forward.

What the merge costs: one row cannot tell you that *yellow specifically* has run
out. Tolerable only because ink is `measure_only` — counted to spot it going
missing, never auto-ordered. Worth revisiting now that a real price and pack
size exist: toner is genuinely consumed by printing, unlike the key fobs it was
grouped with, so `reorder` may be the better class.

### Key fobs

The procurement quote reconciles exactly: **500 × £3.59 = £1,795.00** net,
plus **£68.01** delivery = **£1,863.01** ex VAT, ×1.20 = **£2,235.61** inc.

So `key_fobs` now carries **pack size 1** at **£3.59 net** — the quote prices
per fob, and 500 was the order quantity, not the pack. That **retires correction
#5 from the first session**, which struck out a pack size of 1 for fobs as
invented. It is no longer invented; it is on an invoice.

Still `measure_only`, and rightly so: fobs go missing rather than being consumed,
and reordering 500 at £1,863 is a procurement decision, not a reorder trigger.

Two caveats kept in Notes: the quote does not name the vendor (the part is
Gantner standard, `G-756026`), and a minimum order quantity may apply — 500 is
the only purchase on record.

### Effect on the next `syncProducts` run

39 live consumables today → **30**. Nine deactivate, three are created:

| | |
|---|---|
| deactivate (already planned) | `plastic_food_bags`, `clinell_wipes`, `kleenex_tissues`, `dispenser_pumps` |
| deactivate (new today) | `urinal_shields` |
| deactivate (replaced by `printer_ink`) | `printer_ink_blk`, `printer_ink_pink`, `printer_ink_blue`, `printer_ink_yellow` |
| move to First Aid | `blue_plasters`, `hs_refills`, `ice_packs` |
| created | `paper_printer`, `pens`, `printer_ink` |

`39 − 4 − 1 − 4 − 3 + 3 = 30`. **Notepads never reached Supabase** — it was one
of PLAN-V4's three new rows and was dropped before the first sync, so there is
nothing to deactivate; it simply never gets created.

All nine deactivations are intended. Step 7's verification is a confirmation,
not a check for a mistake.

## Known gaps

- **4 rows are `min_confirmed = no`** — Blue Cloth, Ice Bath Sanitiser, Wet Kit
  Bags, Nitrile Gloves. Each reads as `packs`, but each is a change from v3
  rather than a conversion, so each doubles a requirement (PLAN-V4 §12.1).
- **Water Softener Salt at £149.99 with no pack size.** Par Unit is `items`, so
  the minimum is safe, but the price basis still swings a costed order by an
  order of magnitude. Do not let it into an order until settled.
- **3 products have no pack size**, so no order can be sized: Water Softener
  Salt, Printer Paper, Pens. Key Fobs and Notepads left the list — the fobs now
  have an evidenced pack size, notepads were removed.
- **Pens still need a pack size and price.** The listing is linked but Amazon
  is unreachable from this environment, so neither could be read off it and
  neither is guessed.
- **Tampons and Sanitary Pads have a blank par** where v3 said 64 and 44. Both
  were in confirmed surplus, so blank probably means "do not reorder" — worth
  stating rather than leaving an empty cell that reads as an oversight.
- `microfibre_cloths` Location is a placement, not a settled answer.
- The `Category` values are mine, not the business's. Edit `CATEGORY` in
  `scripts/build_workbook.py` and re-paste.
- No data validation on `Par unit` / `Min confirmed` / `Order class`. CSV import
  cannot set dropdowns; worth adding by hand.
