# ONE LDN — Consumables Dashboard

Stock-taking, ordering and prediction for gym/cafe/facilities consumables,
built on the same mechanism as the shop dashboard: a **Google Sheet master →
Supabase → read-mostly dashboard**.

## Architecture

```
Google Sheet (master)              Supabase (PT Dashboard)          Dashboard
  Products tab    ──syncProducts──▶ shop_product_lookup ──────────▶ reads +
  Stock Count tab ──submitCounts──▶ shop_stock_takes    ──────────▶ hybrid
  Order Log tab   ──submitOrders──▶ shop_consumable_deliveries ───▶ predict
      (Apps Script, service-role key)
```

- **Master data lives in the Google Sheet.** The bound Apps Script
  (`apps-script/Code.gs`) pushes the catalogue into `shop_product_lookup`
  (`category='Consumables'`), and writes counts and orders to Supabase.
- **`index.html`** is a single-file dashboard that reads Supabase with the
  anon key and computes predictions client-side. It does not enter stock
  counts (those come from the Sheet); it offers a quick-add for one-off orders.

## Data model (Supabase project `ljjwssicvvyyueyznmou`)

- `shop_product_lookup` — shared product master. Consumables are the rows with
  `category='Consumables'`; `subcategory` holds the location group (Main /
  Cafe (HP Cupboard) / FOH Desk / Printer). Consumable-specific columns:
  `supplier`, `order_url`, `monthly_par_packs` (plus existing `cost_price`,
  `pack_size`, `min_stock_units`). All consumables are `stock_tracked=false`
  so they never appear in the shop dashboard.
- `shop_stock_takes` — physical counts (shared table, `source='sheet'`),
  keyed by `(product_name_raw, take_date)`. Counts are **in packs**.
- `shop_consumable_deliveries` — orders/deliveries. `qty_cases` = packs ordered.

Everything is tracked in **packs** (the ordering unit).

## Prediction (hybrid model)

- **Baseline:** each product has a manual `monthly_par_packs`.
- **Correction:** with ≥2 counts, real usage is measured
  (`opening + orders_between − closing`) and used instead of par; it also
  surfaces a drift note when measured usage diverges from par.
- **Est. on-hand:** `last_count + orders_since − usage_since`.
- **Flags:** *Order now* when cover drops below the lead buffer / min stock,
  or — with no count yet — when ~a month has passed since the last order.
- **Suggested order:** tops back up to one month of par, costed and grouped by
  supplier into a shopping list.

See `apps-script/SETUP.md` for Google Sheet setup.
