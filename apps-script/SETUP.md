# Consumables Stock Take — Apps Script setup

The master **Consumables catalogue** Google Sheet drives the dashboard. This
Apps Script (`Code.gs`) is bound to that workbook and keeps Supabase in sync.

## One-time setup

1. Open the master workbook → **Extensions ▸ Apps Script**.
2. Paste the contents of `Code.gs` into the editor (replace `Code.gs` there).
3. **Project Settings ▸ Script properties**, add:
   - `SUPABASE_URL` = `https://ljjwssicvvyyueyznmou.supabase.co`
   - `SUPABASE_SERVICE_KEY` = *the `service_role` key* (Supabase ▸ Project Settings ▸ API).
     **Never** the anon key, and never commit this value anywhere.
4. Reload the workbook. A **Consumables** menu appears.
5. Run **① Sync products to dashboard** once and approve the auth prompt.

## Tabs

| Tab | What it's for |
|---|---|
| **Products** | The catalogue you maintain. One row per item. Required columns (any order): `product_name_raw`, `display_name`, `location`, `supplier`, `order_link_or_desc`, `price_per_pack_gbp`, `units_per_pack`, `packs_per_month_par`. |
| **Stock Count** | Weekly on-hand counts **in packs**. Rebuilt from the live product list. |
| **Order Log** | Orders placed (one per row). Cleared after submitting. |

## Weekly routine

- **Count:** Consumables menu → *Rebuild Stock Count sheet* → fill the **Count (packs)** column → *Submit stock count*.
- **Order:** Consumables menu → *Rebuild Order Log sheet* → enter orders → *Submit order log*.
- **Catalogue change** (price, supplier, par, new/removed item): edit the **Products** tab → *Sync products to dashboard*. Removed items are deactivated automatically (soft delete, scoped to Consumables only).

## How it maps to Supabase

| Sheet column | `shop_product_lookup` |
|---|---|
| `product_name_raw` | `product_name_raw` (key) |
| `display_name` | `display_name` |
| `location` | `subcategory` |
| `supplier` | `supplier` |
| `order_link_or_desc` | `order_url` |
| `price_per_pack_gbp` | `cost_price` |
| `units_per_pack` | `pack_size` |
| `packs_per_month_par` | `monthly_par_packs` |

Counts → `shop_stock_takes` (`source='sheet'`, upsert by product+date).
Orders → `shop_consumable_deliveries`.
