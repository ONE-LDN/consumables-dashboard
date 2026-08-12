# Consumables Stock Take — Apps Script setup

`Code.gs` is bound to the **ONE LDN Consumables Catalogue and Stock Take**
workbook. The workbook is the master; this script pushes it to Supabase; the
dashboard reads Supabase. Layout and column contract: `migration/WORKBOOK.md`.

## Only three of the five menu items need Supabase

This matters because it means you can build and use the workbook before setting
any credentials up.

| Menu item | Needs the key? | Reads | Writes |
|---|---|---|---|
| ① Sync products to dashboard | **yes** | `Products` | `shop_product_lookup` |
| ② Rebuild Stock Count sheet | no | `Products` | the `Stock Count` tab |
| ③ Submit stock count | **yes** | `Stock Count` + `Products` | `shop_stock_takes` |
| ④ Rebuild Order Log sheet | no | `Products` | the `Order Log` header + dropdown |
| ⑤ Submit order log | **yes** | `Order Log` + `Products` | `shop_consumable_deliveries` |

`Missing SUPABASE_URL / SUPABASE_SERVICE_KEY in Script properties` means you ran
①, ③ or ⑤ before step 3 below. ② and ④ never raise it.

## Setup

1. Open the workbook → **Extensions ▸ Apps Script**.
2. Paste the contents of `Code.gs` into the editor, replacing what is there. Save.
3. **Project Settings ▸ Script properties**, add two:
   - `SUPABASE_URL` = `https://ljjwssicvvyyueyznmou.supabase.co`
   - `SUPABASE_SERVICE_KEY` = the **`service_role`** secret
     (Supabase ▸ Project Settings ▸ API Keys).

   It must be `service_role`. The anon key is public and RLS will refuse the
   writes. **Never commit this value anywhere** — it stays in Script properties,
   server-side, and is never exposed to the browser or the dashboard.
4. Reload the workbook. A **Consumables** menu appears.
5. Run ② and ④ to create the two working tabs.
6. Run ① once and approve the auth prompt.

> The catalogue was synced directly by SQL on 2026-08-12
> (`migration/scripts/build_load_sql.py`), so ① currently only re-pushes
> identical rows. It is still the route for every future catalogue edit.

## Tabs

| Tab | What it's for |
|---|---|
| **Products** | The catalogue you maintain by hand, 30 rows. Column A `product_name_raw` is the sync key — **never edit it**; renaming it orphans every count and delivery for that product. Headers are matched by name, so column order can change. Required: `product_name_raw`, `Product name`, `Category`, `Location`, `Count unit`, `Count step`, `Supplier`, `Product description`, `Pack size`, `Price per pack`, `Minimum`, `Min confirmed`, `Order class`. |
| **Stock Count** | Weekly on-hand counts **in items**, not packs. Rebuilt by ②. |
| **Order Log** | Deliveries, **in packs**. Cleared after ⑤ submits — the log is an inbox, not the archive. Rebuilding with ④ does *not* clear it, so an entered-but-unsubmitted row survives a catalogue edit. |

## Weekly routine

- **Count:** ② → fill the **Count** column only → ③.
  Counts are in **items** — 24 rolls, not 4 packs. The `Unit` and `Record to`
  columns say what to count and how finely. **Decimals are correct**: half a 5L
  bottle is `0.5`. **Blank means "not counted"; `0` means "counted, none left"** —
  they are different claims and the usage arithmetic treats them differently.
- **Order:** ④ → enter one delivery per row, quantities in **packs** → ⑤.
  Log every delivery. Usage is `opening + orders_between − closing`, so an
  unlogged delivery makes the arithmetic lie.
- **Catalogue change:** edit `Products` → ①. Removed items are deactivated
  (soft delete, scoped to Consumables only).

`Minimum` on the Products tab is a **formula**. To state a requirement outright,
use `Min override` — typing over the formula breaks the "change a par, the
minimum follows" behaviour for that row.

## How it maps to Supabase

| `Products` column | `shop_product_lookup` |
|---|---|
| `product_name_raw` | `product_name_raw` (key) |
| `Product name` | `display_name` |
| `Category` | `product_type` |
| `Location` | `subcategory` |
| `Count unit` | `count_unit` |
| `Count step` | `count_step` |
| `Supplier` | `supplier` |
| `Product description` | `order_url` |
| `Pack size` | `pack_size` |
| `Price per pack` | `cost_price` — **net of VAT** |
| `Minimum` | `min_stock_units` — **items**, and `numeric`, so fractions survive |
| `Min confirmed` | `min_confirmed` |
| `Order class` | `order_class` |

Counts → `shop_stock_takes` (`source='sheet'`, upsert by product + date).
Deliveries → `shop_consumable_deliveries` (`qty_cases` in packs, with the
`pack_size` at the time of delivery stored alongside).

`monthly_par_packs` is no longer written or read — it was in packs. Usage lives
in `monthly_usage_units`, in items per month.

## Two failure modes worth knowing

**③ refuses the whole submission** if any product name on the count sheet fails
to match the `Products` tab, and names the offenders. The count sheet carries no
slug column, so the product name is the join key — which means renaming a
product *there* breaks the join. Rename in `Products` and rebuild with ②. A
partial count would read as a real count and corrupt usage for every product
that silently dropped out.

**① deactivates the whole `Consumables` category before upserting.** With column
A present that is correct — it is what performs intended removals. Never run it
against a `Products` tab whose keys have not been checked.
