#!/usr/bin/env python3
"""
Emit the SQL that gets the catalogue and the first real history into Supabase.

    python3 migration/scripts/build_load_sql.py > /tmp/load.sql

Four steps, in this order and for this reason:

  1. DELETE the 2026-07-29 take. 38 rows, every value the number 6 — an artefact
     of a bad submitCounts run, not a count. It goes first so nothing reads it.
  2. SYNC the catalogue from products_tab.csv. Required before step 3:
     shop_stock_takes has a foreign key to shop_product_lookup, and three keys
     (printer_ink, pens, paper_printer) do not exist in the database yet.
  3. LOAD the 2026-08-04 count as the first stock take.
  4. LOAD the 2026-08-07 deliveries.

STEP 2 IS THE SAME WORK syncProducts() DOES, from the same source — the Products
tab, via the CSV it is generated from — so the two cannot drift. Once the Apps
Script is wired up, running ① re-pushes identical rows.

The Minimum column in products_tab.csv is a spreadsheet formula, so the minimum
is recomputed here from the same rule: override, else Par x Pack size when the
par is in packs, else the par.
"""

import csv
import pathlib

MIGRATION = pathlib.Path(__file__).resolve().parent.parent
CATEGORY = "Consumables"
TAKE_DATE = "2026-08-04"

# The four single-colour ink counts sum into the merged printer_ink row. Only
# valid because all four were counted — a partial sum would understate.
INK_MERGE_FROM = ["printer_ink_blk", "printer_ink_pink", "printer_ink_blue", "printer_ink_yellow"]


def q(v):
    """SQL literal. Empty string is NULL, not ''."""
    if v is None or v == "":
        return "null"
    return "'" + str(v).replace("'", "''") + "'"


def n(v):
    return "null" if v is None or v == "" else str(float(v))


def minimum(r):
    """Same rule as the sheet's Minimum formula."""
    if r["Min override"]:
        return float(r["Min override"])
    if not r["Par qty"]:
        return None
    if r["Par unit"] == "packs":
        return None if not r["Pack size"] else float(r["Par qty"]) * float(r["Pack size"])
    return float(r["Par qty"])


def main():
    with open(MIGRATION / "products_tab.csv", newline="") as fh:
        products = list(csv.DictReader(fh))
    with open(MIGRATION / "baseline_count_2026_08_04.csv", newline="") as fh:
        baseline = {r["product_name_raw"]: r for r in csv.DictReader(fh)}
    with open(MIGRATION / "deliveries_since_baseline.csv", newline="") as fh:
        deliveries = list(csv.DictReader(fh))

    keys = [p["product_name_raw"] for p in products]
    out = []
    out.append("begin;\n")

    # ── 1. the junk take ────────────────────────────────────────────────────
    out.append("-- 1. Delete the 29/07 artefact: 38 rows, every value 6.")
    out.append("--    Scoped to Consumables + source='sheet' so the shop dashboard's own")
    out.append("--    29/07 set (65 rows, source='manual') is untouched.")
    out.append("delete from shop_stock_takes")
    out.append("where take_date = '2026-07-29' and source = 'sheet'")
    out.append("  and product_name_raw in (select product_name_raw from shop_product_lookup")
    out.append("                           where category = '%s');\n" % CATEGORY)

    # ── 2. the catalogue ────────────────────────────────────────────────────
    out.append("-- 2. Catalogue: upsert the 30 products, then deactivate every other")
    out.append("--    Consumables row. Same order as syncProducts() — the deactivate is")
    out.append("--    scoped to this category, so no shop or merch row can be touched.")
    cols = ("product_name_raw, display_name, brand, category, product_type, subcategory, "
            "count_unit, count_step, supplier, order_url, cost_price, pack_size, "
            "min_stock_units, min_confirmed, order_class, active, stock_tracked")
    rows = []
    for p in products:
        rows.append("  (%s, %s, '', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true, false)" % (
            q(p["product_name_raw"]), q(p["Product name"]), q(CATEGORY),
            q(p["Category"]), q(p["Location"]), q(p["Count unit"]), n(p["Count step"]),
            q(p["Supplier"]), q(p["Product description"]),
            n(p["Price per pack"]),
            "null" if not p["Pack size"] else str(int(float(p["Pack size"]))),
            n(minimum(p)),
            "true" if p["Min confirmed"] == "yes" else "false",
            q(p["Order class"]),
        ))
    out.append("insert into shop_product_lookup (%s) values" % cols)
    out.append(",\n".join(rows))
    out.append("""on conflict (product_name_raw) do update set
  display_name = excluded.display_name, brand = excluded.brand,
  category = excluded.category, product_type = excluded.product_type,
  subcategory = excluded.subcategory, count_unit = excluded.count_unit,
  count_step = excluded.count_step, supplier = excluded.supplier,
  order_url = excluded.order_url, cost_price = excluded.cost_price,
  pack_size = excluded.pack_size, min_stock_units = excluded.min_stock_units,
  min_confirmed = excluded.min_confirmed, order_class = excluded.order_class,
  active = true, stock_tracked = false;\n""")
    out.append("update shop_product_lookup set active = false")
    out.append("where category = %s and product_name_raw not in (%s);\n" % (
        q(CATEGORY), ", ".join(q(k) for k in keys)))

    # ── 3. the baseline count ───────────────────────────────────────────────
    out.append("-- 3. The 04/08 count. In ITEMS, decimals intentional.")
    ink_parts = [baseline[k]["on_hand_items"] for k in INK_MERGE_FROM if baseline.get(k)]
    if len(ink_parts) != len(INK_MERGE_FROM) or any(v == "" for v in ink_parts):
        raise SystemExit("refusing to sum the ink counts: not all four are present")
    ink_total = sum(float(v) for v in ink_parts)

    take_rows, skipped = [], []
    for p in products:
        key = p["product_name_raw"]
        if key == "printer_ink":
            val, note = ink_total, "summed from the 4 single-colour counts (1 each)"
        else:
            r = baseline.get(key)
            if not r or r["on_hand_items"] == "":
                skipped.append(key)
                continue
            val, note = float(r["on_hand_items"]), r["count_basis"]
        take_rows.append("  (%s, '%s', %s, %s, 'sheet')" % (q(key), TAKE_DATE, val, q(note)))
    for key in skipped:
        out.append("--    not counted on 04/08, left absent rather than zero: %s" % key)
    out.append("insert into shop_stock_takes (product_name_raw, take_date, actual_count, notes, source) values")
    out.append(",\n".join(take_rows))
    # shop_stock_takes has UNIQUE (product_name_raw, take_date), so re-running
    # corrects the row rather than duplicating it.
    out.append("""on conflict (product_name_raw, take_date) do update set
  actual_count = excluded.actual_count, notes = excluded.notes, source = excluded.source;\n""")

    # ── 4. the deliveries ───────────────────────────────────────────────────
    out.append("-- 4. The 07/08 deliveries, in PACKS. pack_size is stored alongside so the")
    out.append("--    conversion to items survives a later catalogue change.")
    by_key = {p["product_name_raw"]: p for p in products}
    del_rows = []
    for d in deliveries:
        p = by_key[d["product_name_raw"]]
        ps = p["Pack size"]
        del_rows.append("  ('%s'::date, %s, %s, %s, %s, %s, %s, %s)" % (
            d["delivery_date"], q(d["product_name_raw"]), q(p["Location"]),
            str(int(float(d["qty_cases"]))),
            "null" if not ps else str(int(float(ps))),
            d["unit_cost_net"], d["net_amount"], q(d["supplier"])))
    # No natural key on deliveries, so a plain insert would duplicate on a
    # re-run — and a phantom delivery is the one error that makes usage lie in
    # the direction of UNDERSTATING consumption. Guarded on date + product.
    out.append("insert into shop_consumable_deliveries")
    out.append("  (delivery_date, product_name_raw, subcategory, qty_cases, pack_size, unit_cost, total, supplier)")
    out.append("select * from (values")
    out.append(",\n".join(del_rows))
    out.append(""") as v(delivery_date, product_name_raw, subcategory, qty_cases, pack_size, unit_cost, total, supplier)
where not exists (
  select 1 from shop_consumable_deliveries d
  where d.delivery_date = v.delivery_date::date
    and d.product_name_raw = v.product_name_raw);\n""")
    out.append("commit;")

    print("\n".join(out))


if __name__ == "__main__":
    main()
