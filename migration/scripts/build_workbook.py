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
    "Washroom": ["toilet_rolls", "tampons", "pads", "glade_sprays"],
    "Toiletries": [
        "hand_wash", "conditioner", "moisturiser", "shampoo", "sanitiser_gel",
        "sure_deodorant_men", "sure_deodorant_women",
    ],
    "Cleaning": [
        "blue_rolls", "blue_cloth", "washing_up_liquid", "puly_caffe_cleaner",
        "bin_bags", "microfibre_cloths", "multipurpose_cleaner",
        "blue_gloves_large",
    ],
    "Stationery": ["pens", "paper_printer", "printer_ink"],
    "Facilities": [
        "chill_tub_filters", "chill_tubs_sanitiser", "water_softener_salt",
    ],
    # D batteries are for the ergs, so they sit with the gym kit rather than
    # with stationery or general equipment.
    "Gym": ["chalk_block", "d_batteries"],
    # Things handed to members rather than consumed by the building.
    "Member Supplies": ["hair_bands", "key_fobs", "wet_kit_bags"],
}

# ── Changes on top of the v4 transcription ──────────────────────────────────
# products_v4.csv stays a faithful record of what the v4 sheet said. Decisions
# taken since live here, each with a date and a reason, so the diff between the
# sheet and the catalogue is always readable.

# Dropped from the catalogue. Both are live in Supabase, so both deactivate on
# the next syncProducts run — intended, not an accident.
DROP = {
    "urinal_shields": "removed from the catalogue 2026-08-12",
    "notepads": "removed from the catalogue 2026-08-12",
}

# The four single-colour ink rows become one. Each had a par of 1 cartridge, so
# a consolidated minimum of 4 items is the same requirement, not a new one.
#
# What it costs: one row cannot tell you that yellow specifically has run out.
# Tolerable only because ink is measure_only — counted to spot it going missing,
# never auto-ordered — so the count is a check, not an order trigger.
INK_MERGE_FROM = [
    "printer_ink_blk", "printer_ink_pink", "printer_ink_blue", "printer_ink_yellow",
]
#
# The invoice Saffron supplied settles the product outright: SODFACE TN248,
# compatible with Brother TN248XL, sold as a 4-pack — so the four colours were
# always one purchase, and one row is what the ordering actually looks like.
#   1 x £38.32 net, +20% VAT = £45.99 gross.  38.32 x 1.20 = 45.98 ✓
#
# It also closes a standing question: the old printer_ink_blk row carried
# £224.90, which the session log flagged as "looks like a multipack booked
# against a single cartridge". It is not that either — the pack costs £38.32.
# £224.90 is simply wrong and is not carried forward.
INK_MERGED = {
    "product_name_raw": "printer_ink",
    "display_name": "Printer Ink",
    "location": "FOH Desk",
    "supplier": "Amazon",
    "order_link_or_desc": "SODFACE TN248 Toner Cartridge, compatible with Brother "
                          "TN248XL, 4-pack — https://www.amazon.co.uk/dp/B0D2HN4V4Y",
    "price_per_pack_gbp": "38.32",   # net; £45.99 gross
    "units_per_pack": "4",           # cartridges per pack, from the invoice
    "count_unit": "cartridges",
    # One spare pack = 4 cartridges, which is what the four separate rows asked
    # for between them (1 each). Same requirement, stated once.
    "par_qty_sheet": "1",
    "par_unit": "packs",
    "min_stock_units": "4",
    "min_confirmed": "yes",
    # Left as measure_only, as the four rows were. Worth revisiting now that a
    # price and pack size exist: toner is genuinely consumed by printing, unlike
    # the key fobs it was grouped with, so reorder may be the better class.
    "order_class": "measure_only",
    "_review": "merged from the 4 single-colour rows 2026-08-12: the 4-pack was "
               "always one purchase; price and pack size from the supplied "
               "invoice; still measure_only — reconsider, toner is consumed",
}

# Field-level updates from documents Saffron supplied 2026-08-12. Each carries
# the evidence in its note, because every price and pack size in this catalogue
# has to be attributable — guessing them is what produced "order 161 packs of
# plasters" and "order 2 fobs" in earlier passes.
FIELD_UPDATE = {
    # Amazon is unreachable from here, so pack size and price could not be read
    # off the listing and stay blank rather than guessed.
    "pens": (
        {"order_link_or_desc": "https://www.amazon.co.uk/dp/B07TVR5X6W"},
        "product link supplied 2026-08-12; pack size and price still needed from "
        "the listing",
    ),
    # Procurement quote: 500 x £3.59 = £1,795.00 net, +£68.01 delivery,
    # sub-total £1,863.01 ex VAT, £2,235.61 inc. ✓
    #
    # This retires correction #5 from the first session, which struck out a pack
    # size of 1 for fobs as invented. It is no longer invented: the quote prices
    # per fob, and 500 was the order quantity, not the pack.
    "key_fobs": (
        {
            "order_link_or_desc": "GAT Key Tag 180 F7 1k black — MIFARE 7Byte UID, "
                                  "coded to Gantner Standard, part G-756026",
            "units_per_pack": "1",
            "price_per_pack_gbp": "3.59",
        },
        "unit price from the 500-fob procurement quote (500 x £3.59 = £1,795.00 "
        "net); delivery charged separately at £68.01; the quote does not name the "
        "vendor and a minimum order quantity may apply",
    ),
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
    fields = list(products[0].keys())

    for key in list(DROP) + INK_MERGE_FROM:
        if not any(p["product_name_raw"] == key for p in products):
            raise SystemExit("nothing to remove: {} is not in products_v4".format(key))
    removed = set(DROP) | set(INK_MERGE_FROM)
    products = [p for p in products if p["product_name_raw"] not in removed]

    merged = {f: INK_MERGED.get(f, "") for f in fields}
    products.append(merged)

    for key, (updates, why) in FIELD_UPDATE.items():
        p = next((x for x in products if x["product_name_raw"] == key), None)
        if p is None:
            raise SystemExit("no such product for field update: " + key)
        for field, value in updates.items():
            if field not in p:
                raise SystemExit("{}: no such field {!r}".format(key, field))
            p[field] = value
        # Drop the stale "unknown" flags this update has just answered.
        stale = [n for n in p["_review"].split("; ")
                 if not (("pack size" in n and "units_per_pack" in updates)
                         or (n.strip() == "no price" and "price_per_pack_gbp" in updates))]
        p["_review"] = "; ".join(filter(None, stale + [why]))

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
