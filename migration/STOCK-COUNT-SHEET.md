# The weekly Stock Count sheet

**Google Sheet:** [ONE LDN — Consumables Stock Take](https://docs.google.com/spreadsheets/d/1xGKdynO2CSU6iDL1FKHn6wZqQZeLWZrvRpVESdeKEnE/edit)
(`1xGKdynO2CSU6iDL1FKHn6wZqQZeLWZrvRpVESdeKEnE`)

> ⚠ An earlier sheet (`1linoZ_oo_UDEAeMFPjwzsPYNwSmQUH-3LkMlCUhRrZ8`) had the
> superseded layout and should be **deleted**. Two sheets with the same name and
> different columns is exactly how a count ends up in the wrong place.

Generated from `products_v4.csv` by `scripts/build_stock_count_sheet.py` into
`stock_count_sheet.csv`, which is the exact cell layout. Regenerate and re-paste
whenever the product list changes — do not hand-edit the rows.

35 consumables. First aid is **not** here: separate 33-line list, quarterly
cadence (`FIRST-AID.md`, PLAN-V4 §8).

---

## Layout

| cell | |
|---|---|
| `B1` | Take date — **must be a real date**, not text, or submit refuses it |
| `B2` | Counted by |
| row 3 | header |
| row 4–38 | the 35 products, in walk order |

| col | | |
|---|---|---|
| A | **Product name** | also the join key — see below |
| B | **Category** | what kind of thing it is |
| C | **Location** | where you count it |
| D | **Count** | the only column anyone types in |
| E | **Unit** | what a count of 1 means |

### Category and Location are different axes

The v4 sheet had one `Category` column that mixed them — `Toiletries` is a
product type, `Gym Floor` is a place. PLAN-V4 flagged this as needing two
columns; this is that fix.

`Location` keeps the v4 values and drives the walk order: FOH Desk (10) → Cafe
(3) → Gym Floor (2) → Toiletries (15) → Staff Room (4) → Plant room (1).

`Category` is new, derived from the products themselves since nothing upstream
carries it: Cleaning (8), Stationery (7), Toiletries (7), Washroom (5),
Facilities (3), Member Supplies (3), Gym (2). Every category has more than one
member — a category of one is a label, not a grouping.

The split earns its keep where the two disagree: **D Batteries** are Category
`Gym` (they run the ergs) but Location `FOH Desk` (that is where the drawer is).

⚠ Seven rows read `Toiletries | Toiletries`, because the v4 location value for
the changing rooms is the same word as the product type. Worth renaming the
location to `Changing Rooms` at source; it is cosmetic, not a data problem.

### No `product_name_raw` column

Saffron's call: the slug stays on the catalogue tab, not on the sheet people
count into. `submitCounts()` joins on `display_name` instead.

The cost, stated plainly: **renaming a product on the count sheet breaks the
join.** Rename in the catalogue and rebuild the count sheet. To stop that
failing silently, `submitCounts()` now **refuses the entire submission** if any
name fails to match, and names the offenders. A partial count reads as a real
count and would corrupt the usage arithmetic for every product that went
missing.

The generator enforces the other half of this: it aborts if two products share a
`display_name`.

## Three things to finish by hand

The sheet was created by CSV import, which cannot set these:

1. **Format `B1` as a date** (`yyyy-mm-dd`).
2. **Freeze row 3.**
3. **Rename the tab to `Stock Count`** if the Apps Script is bound to this
   workbook — `COUNT_SHEET` matches by name.

`buildCountSheet()` sets all of these itself once the sync is live.

## How it differs from the shop sheet

Two of the shop sheet's rules are wrong here, and following them would corrupt
the baseline:

- **Decimals are correct and expected.** Half a 5L bottle is a count of `0.5`.
  The shop sheet says whole numbers only because it counts sealed cans and bars.
  `actual_count` is `numeric`, so fractions store fine.
- **Count in items, never packs.** 24 rolls, not 4 packs. Mixing the two is what
  made the v3 `Stock` column unusable. Column E says which.

Unchanged, and still the rules that matter most:

- **Blank means "not counted". `0` means "counted, none left."**
- **Every delivery goes in the Order Log.** Usage is
  `opening + orders_between − closing`; an unlogged delivery makes it lie.

## `Code.gs` changes in this layout

`buildCountSheet()` and `submitCounts()` were changed together, because a sheet
whose columns the reader does not expect is worse than either one alone.

- `buildCountSheet` writes the five columns, sorts by `COUNT_WALK_ORDER`, greys
  everything except Count, and no longer hides column 1.
- `submitCounts` resolves `display_name` → `product_name_raw` from Supabase and
  throws on any unmatched name. It no longer writes `notes` — the column is gone.
- `clearCounts` is unaffected: Count is still column 4.

**Two new columns are needed on `shop_product_lookup` before
`buildCountSheet()` can run:**

```sql
alter table shop_product_lookup add column product_type text;   -- Category
alter table shop_product_lookup add column count_unit   text;   -- Unit
```

Until they exist the rebuild will fail with a PostgREST error naming the missing
column. That is the intended behaviour — it cannot quietly write blank columns.
Add these alongside the `monthly_usage_units` column in PLAN-V4 §6.

## Known gaps

- `microfibre_cloths` is filed under **Staff Room**. The v4 sheet leaves its
  Category blank (PLAN-V4 §12.3) — a placement, not a settled answer.
- The 4 printer inks and Key Fobs are `measure_only`: counted, never reordered.
  On the sheet on purpose.
- The `Category` values are mine, not the business's. Cheap to change — edit
  `CATEGORY` in the generator and re-paste.
