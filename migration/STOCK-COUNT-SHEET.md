# The weekly Stock Count sheet

**Google Sheet:** [ONE LDN — Consumables Stock Take](https://docs.google.com/spreadsheets/d/1linoZ_oo_UDEAeMFPjwzsPYNwSmQUH-3LkMlCUhRrZ8/edit)
(`1linoZ_oo_UDEAeMFPjwzsPYNwSmQUH-3LkMlCUhRrZ8`)

Generated from `products_v4.csv` by `scripts/build_stock_count_sheet.py` into
`stock_count_sheet.csv`, which is the exact cell layout. Regenerate and re-paste
whenever the product list changes — do not hand-edit the rows.

35 consumables. First aid is **not** here: it is a separate 33-line list on a
quarterly cadence (`FIRST-AID.md`, PLAN-V4 §8).

---

## Layout

Modelled on the shop's stock take sheet, and on the fixed positions
`submitCounts()` in `apps-script/Code.gs` already reads:

| cell | |
|---|---|
| `B1` | Take date — **must be a real date**, not text, or submit refuses it |
| `B2` | Counted by — not read by the script, there for accountability |
| row 3 | header |
| row 4–38 | the 35 products, in walk order |

| col | | read on submit |
|---|---|---|
| A | `product_name_raw` — the sync key | ✅ as the product |
| B | Product, with the count unit after a dash | — |
| C | Location | — |
| D | **Count** — the only column the counter types in | ✅ as `actual_count` |
| E | Notes | ✅ as `notes` |

**The columns cannot be reordered or inserted into.** `submitCounts()` reads
columns 1, 4 and 5 by position. That is also why the count unit rides in the
Product cell rather than having a column of its own — a sixth column between
Count and Notes would silently send the wrong field to Supabase.

Rows are ordered by the route you walk, not alphabetically: FOH Desk (10) →
Cafe (3) → Gym Floor (2) → Toiletries (15) → Staff Room (4) → Plant room (1).

## Three things to finish by hand

The sheet was created by CSV import, which cannot set these:

1. **Hide column A.** It is the key that joins the count to the catalogue. It
   must stay in the sheet and never be edited.
2. **Rename the tab to `Stock Count`** if the Apps Script is ever bound to this
   workbook — `COUNT_SHEET` matches by name.
3. **Format `B1` as a date** (`yyyy-mm-dd`).

## How it differs from the shop sheet

Two of the shop sheet's rules are wrong here, and following them would corrupt
the baseline:

- **Decimals are correct and expected.** Half a 5L bottle is a count of `0.5`.
  The shop sheet says whole numbers only because it counts sealed cans and bars.
  `actual_count` is `numeric`, so fractions store fine.
- **Count in items, never packs.** 24 rolls, not 4 packs. Mixing the two is what
  made the v3 `Stock` column unusable. The unit after each product name is the
  one to count in.

Unchanged from the shop sheet, and still the rules that matter most:

- **Blank means "not counted". `0` means "counted, none left".** They are not
  the same thing, and the usage arithmetic treats them very differently.
- **Every delivery goes in the Order Log.** Usage is
  `opening + orders_between − closing`; an unlogged delivery makes it lie.

## Known gaps

- `microfibre_cloths` is filed under **Staff Room** here. The v4 sheet leaves
  its Category blank (PLAN-V4 §12.3) — this is a placement so it does not float
  to the end of the count, not a settled answer.
- The 4 printer inks and Key Fobs are `measure_only`: counted, never reordered.
  They are on the sheet on purpose.
- This sheet stands alone until the v4 sync runs (PLAN-V4 §10). Once
  `syncProducts` has run, `buildCountSheet()` can regenerate the tab from
  Supabase instead — at which point the unit labels need adding to
  `buildCountSheet`, or they will be lost on the next rebuild.
