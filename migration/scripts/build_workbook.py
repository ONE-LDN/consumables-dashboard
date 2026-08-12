#!/usr/bin/env python3
"""
Build every tab of the consumables workbook from `products_v4.csv`.

The workbook is the single source of truth. The Apps Script pushes it to
Supabase; the dashboard reads Supabase. Nothing is maintained in two places —
which is the point of folding the catalogue into the stock take sheet.

Outputs, one CSV per tab:

    products_tab.csv        `Products`     the 35-line catalogue, hand-maintained
    stock_count_sheet.csv   `Stock Count`  weekly count, derived from Products
    order_log_tab.csv       `Order Log`    deliveries, in packs

`Stock Count` and `Order Log` can also be rebuilt in-place by the Apps Script
menu, which reads the `Products` tab directly — so they never need pasting
twice, and neither needs Supabase to be set up.

TWO THINGS ARE FORMULAS, ON PURPOSE

1. `Products!Minimum` is computed from Par qty x Pack size, so changing a par
   or a pack size updates the minimum everywhere without anyone recalculating.
   `Min override` wins where a human has stated a requirement outright — see
   MIN_OVERRIDE.
2. `Stock Count`'s Category, Location and Unit are VLOOKUPs against Products,
   keyed on the product name in the same row. Editing the catalogue flows
   straight through to the count sheet.

   Keyed per row, deliberately. A whole-range formula would re-sort the product
   names without moving the counts beside them, which silently files every count
   against the wrong product. Only adding or removing a product needs a rebuild.
"""

import csv
import pathlib

MIGRATION = pathlib.Path(__file__).resolve().parent.parent

# The route through the building. Anything with a location not listed here is
# an error rather than a silent append — a new location means the walk changed.
WALK_ORDER = [
    "FOH Desk",
    "Cafe",
    "Gym Floor",
    "Toiletries",
    "Staff Room",
    "Plant room",
]

# `microfibre_cloths` is the one blank Category on the v4 sheet (PLAN-V4 §12.3).
# Placed here so it does not float to the end of the count; still needs
# confirming at source.
LOCATION_OVERRIDE = {
    "microfibre_cloths": "Staff Room",
}

# Product type. Derived from the products themselves, not from the sheet —
# there is no such column upstream. Grouped so that every category has more
# than one member; a category of one is a label, not a grouping.
CATEGORY = {
    "Washroom": [
        "toilet_rolls", "tampons", "pads", "urinal_shields", "glade_sprays",
    ],
    "Toiletries": [
        "hand_wash", "conditioner", "moisturiser", "shampoo", "sanitiser_gel",
        "sure_deodorant_men", "sure_deodorant_women",
    ],
    "Cleaning": [
        "blue_rolls", "blue_cloth", "washing_up_liquid", "puly_caffe_cleaner",
        "bin_bags", "microfibre_cloths", "multipurpose_cleaner",
        "blue_gloves_large",
    ],
    "Stationery": [
        "pens", "notepads", "paper_printer", "printer_ink_blk",
        "printer_ink_blue", "printer_ink_pink", "printer_ink_yellow",
    ],
    "Facilities": [
        "chill_tub_filters", "chill_tubs_sanitiser", "water_softener_salt",
    ],
    # D batteries are for the ergs, so they sit with the gym kit rather than
    # with stationery or general equipment.
    "Gym": ["chalk_block", "d_batteries"],
    # Things handed to members rather than consumed by the building.
    "Member Supplies": ["hair_bands", "key_fobs", "wet_kit_bags"],
}

# An explicitly-stated human requirement beats the computed candidate — the
# rule from MINIMUM-STOCK.md. These are the only two rows where Par x Pack Size
# does not reproduce the agreed minimum, and both come from the sheet's notes.
MIN_OVERRIDE = {
    "d_batteries": (10, 'sheet note: "Need to have 10 on hand"; Par x Pack Size gives 8'),
    "notepads": (1, 'sheet note: "need 1 on hand"; no Par Qty on the sheet'),
}

# v4 carries GBP 25.19 for the four Out of Eden toiletries, which is the VAT
# INCLUSIVE price: 20.99 x 1.20 = 25.19. The 2026-08-07 invoice states 20.99
# net, and the Futures prices in the same column (11.31, 26.98) are net. Prices
# in this workbook are net throughout, so these four are corrected.
PRICE_OVERRIDE = {
    "hand_wash": 20.99,
    "conditioner": 20.99,
    "moisturiser": 20.99,
    "shampoo": 20.99,
}
PRICE_OVERRIDE_NOTE = "price corrected to net; v4's 25.19 was VAT-inclusive (invoice 2026-08-07)"

# ── Products tab ────────────────────────────────────────────────────────────
# Header names are matched case-insensitively by Code.gs, so they must stay
# stable. No punctuation in them: '£' and brackets make the match brittle.
PRODUCTS_HEADERS = [
    "product_name_raw",   # A  the sync key — never edited
    "Product name",       # B
    "Category",           # C  what kind of thing it is
    "Location",           # D  where you count it
    "Count unit",         # E  what a count of 1 means
    "Supplier",           # F
    "Product description",# G  the long supplier description, for ordering
    "Pack size",          # H  items per order unit
    "Price per pack",     # I  NET of VAT, per pack
    "Par qty",            # J  as written on the sheet
    "Par unit",           # K  packs | items
    "Min override",       # L  a stated requirement, in items
    "Minimum",            # M  FORMULA — items
    "Min confirmed",      # N  yes | no
    "Order class",        # O  reorder | measure_only
    "Notes",              # P
]

# M = override if set, else Par x Pack Size when the par is in packs, else Par.
# Blank par -> blank minimum, never 0: "no minimum set" and "minimum of zero"
# are different claims and the dashboard treats them differently.
MIN_FORMULA = '=IF(L{r}<>"",L{r},IF(J{r}="","",IF(K{r}="packs",IF(H{r}="","",J{r}*H{r}),J{r})))'

COUNT_HEADERS = ["Product name", "Category", "Location", "Count", "Unit"]

# Products!B:E — 1=Product name, 2=Category, 3=Location, 4=Count unit.
COUNT_LOOKUP = '=IFERROR(VLOOKUP($A{r},Products!$B:$E,{col},FALSE),"")'

ORDER_HEADERS = [
    "Date", "Product", "Packs ordered", "Unit cost £ (optional)",
    "Supplier (optional)", "Notes",
]


def category_lookup():
    out = {}
    for name, keys in CATEGORY.items():
        for k in keys:
            if k in out:
                raise SystemExit("{} is in two categories".format(k))
            out[k] = name
    return out


def unit(display_name, count_unit):
    """'5L bottles' -> 'bottles' where the display name already says 5L."""
    u = count_unit.strip()
    size = display_name.rsplit(" ", 1)[-1]
    if u.lower().startswith(size.lower() + " "):
        u = u[len(size) + 1:]
    return u


def load_products():
    with open(MIGRATION / "products_v4.csv", newline="") as fh:
        products = list(csv.DictReader(fh))

    cats = category_lookup()
    missing = [p["product_name_raw"] for p in products if p["product_name_raw"] not in cats]
    if missing:
        raise SystemExit("no category for: {}".format(", ".join(missing)))
    extra = set(cats) - {p["product_name_raw"] for p in products}
    if extra:
        raise SystemExit("categorised but not in products_v4: {}".format(", ".join(sorted(extra))))

    names = [p["display_name"] for p in products]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        # display_name is the join key for both count and order submission.
        raise SystemExit("duplicate display_name: {}".format(", ".join(sorted(dupes))))

    for p in products:
        key = p["product_name_raw"]
        p["_category"] = cats[key]
        p["_location"] = LOCATION_OVERRIDE.get(key, p["location"]).strip()
        p["_unit"] = unit(p["display_name"], p["count_unit"])
        if p["_location"] not in WALK_ORDER:
            raise SystemExit(
                "{}: location {!r} is not in WALK_ORDER".format(key, p["_location"])
            )
    return products


def build_products(products):
    rows = []
    for i, p in enumerate(products):
        key = p["product_name_raw"]
        r = i + 2  # header on row 1

        review = p["_review"]
        if key in LOCATION_OVERRIDE:
            # The raw flag just says "no category", which is no longer true now
            # that one has been assigned. Say what was done instead.
            review = review.replace("no category", "").strip("; ").strip()
            review = "; ".join(filter(None, [
                review,
                "Location set to {} — the v4 sheet left this row's Category "
                "blank; confirm".format(LOCATION_OVERRIDE[key]),
            ]))
        notes = [n for n in [review] if n]
        override, price = "", p["price_per_pack_gbp"]
        if key in MIN_OVERRIDE:
            override, why = MIN_OVERRIDE[key]
            notes.append(why)
        if key in PRICE_OVERRIDE:
            price = "{:.2f}".format(PRICE_OVERRIDE[key])
            notes.append(PRICE_OVERRIDE_NOTE)

        rows.append([
            key,
            p["display_name"],
            p["_category"],
            p["_location"],
            p["_unit"],
            p["supplier"],
            p["order_link_or_desc"],
            p["units_per_pack"],
            price,
            p["par_qty_sheet"],
            p["par_unit"],
            override,
            MIN_FORMULA.format(r=r),
            p["min_confirmed"],
            p["order_class"],
            "; ".join(notes),
        ])
    return rows


def build_count(products):
    rows = sorted(
        products,
        key=lambda p: (WALK_ORDER.index(p["_location"]), p["display_name"]),
    )
    out = []
    for i, p in enumerate(rows):
        r = i + 4  # take date row 1, counted by row 2, header row 3
        out.append([
            p["display_name"],
            COUNT_LOOKUP.format(r=r, col=2),
            COUNT_LOOKUP.format(r=r, col=3),
            "",
            COUNT_LOOKUP.format(r=r, col=4),
        ])
    return out


def build_order_log(products):
    """Header plus the deliveries already known since the baseline count."""
    by_key = {p["product_name_raw"]: p for p in products}
    rows = []
    path = MIGRATION / "deliveries_since_baseline.csv"
    if path.exists():
        with open(path, newline="") as fh:
            for d in csv.DictReader(fh):
                p = by_key.get(d["product_name_raw"])
                if not p:
                    raise SystemExit("delivery for unknown product: " + d["product_name_raw"])
                rows.append([
                    d["delivery_date"], p["display_name"], d["qty_cases"],
                    d["unit_cost_net"], d["supplier"], "",
                ])
    return rows


def write(path, header_rows, header, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        for hr in header_rows:
            w.writerow(hr + [""] * (len(header) - len(hr)))
        w.writerow(header)
        w.writerows(rows)
    print("  {:<24} {} rows".format(path.name, len(rows)))


def main():
    products = load_products()
    print("{} products".format(len(products)))

    write(MIGRATION / "products_tab.csv", [], PRODUCTS_HEADERS, build_products(products))
    write(MIGRATION / "stock_count_sheet.csv",
          [["Take date:"], ["Counted by:"]], COUNT_HEADERS, build_count(products))
    write(MIGRATION / "order_log_tab.csv", [], ORDER_HEADERS, build_order_log(products))

    print("  by location:")
    for loc in WALK_ORDER:
        print("    {:<12} {}".format(loc, sum(1 for p in products if p["_location"] == loc)))
    print("  by category:")
    for cat in sorted(CATEGORY):
        print("    {:<16} {}".format(cat, sum(1 for p in products if p["_category"] == cat)))


if __name__ == "__main__":
    main()
