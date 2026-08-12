#!/usr/bin/env python3
"""
Build the weekly Stock Count sheet from `products_v4.csv`.

Output: `migration/stock_count_sheet.csv` — the exact cell layout to paste into
the Google Sheet's `Stock Count` tab. One row per consumable, ordered by the
route you actually walk when counting.

    B1                 take date          (COUNT_DATE_CELL)
    B2                 counted by
    row 3              header row         (COUNT_HEADER_ROW)
    row 4+             products           (COUNT_FIRST_ROW)

    col A  Product name   display_name — also the join key, see below
    col B  Category       what kind of thing it is
    col C  Location       where you count it
    col D  Count          what the counter types      <- read as actual_count
    col E  Unit           what a count of 1 means     <- reference, never typed in

CATEGORY AND LOCATION ARE DIFFERENT AXES. The v4 sheet's single `Category`
column mixed them — 'Toiletries' is a product type, 'Gym Floor' is a place.
That column becomes `Location` here (it is what you walk), and `Category` is
the product-type grouping declared in CATEGORY below.

NO product_name_raw COLUMN. Saffron's call: the slug stays on the catalogue
tab, not on the sheet people count into. `submitCounts()` therefore resolves
`display_name` -> `product_name_raw` against Supabase and refuses the whole
submission if any name fails to match. The cost of that choice: renaming a
product on the count sheet breaks the join. Rename in the catalogue and rebuild.
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

HEADERS = ["Product name", "Category", "Location", "Count", "Unit"]


def category_lookup():
    out = {}
    for name, keys in CATEGORY.items():
        for k in keys:
            if k in out:
                raise SystemExit("{} is in two categories".format(k))
            out[k] = name
    return out


def unit(display_name, count_unit):
    """'5L bottles' -> 'bottles' where the display name already says 5L.

    Leaving both in gives 'Hand Wash 5L' / '5L bottles', which reads as though
    the size were in question when it is not.
    """
    u = count_unit.strip()
    size = display_name.rsplit(" ", 1)[-1]
    if u.lower().startswith(size.lower() + " "):
        u = u[len(size) + 1:]
    return u


def main():
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
        # display_name is the join key now, so a collision is fatal, not cosmetic.
        raise SystemExit("duplicate display_name: {}".format(", ".join(sorted(dupes))))

    rows = []
    for p in products:
        key = p["product_name_raw"]
        location = LOCATION_OVERRIDE.get(key, p["location"]).strip()
        if location not in WALK_ORDER:
            raise SystemExit(
                "{}: location {!r} is not in WALK_ORDER".format(key, location)
            )
        rows.append([
            p["display_name"],
            cats[key],
            location,
            "",
            unit(p["display_name"], p["count_unit"]),
        ])

    rows.sort(key=lambda r: (WALK_ORDER.index(r[2]), r[0]))

    out = MIGRATION / "stock_count_sheet.csv"
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Take date:"] + [""] * (len(HEADERS) - 1))
        w.writerow(["Counted by:"] + [""] * (len(HEADERS) - 1))
        w.writerow(HEADERS)
        w.writerows(rows)

    print("{} products -> {}".format(len(rows), out))
    print("  by location:")
    for loc in WALK_ORDER:
        print("    {:<12} {}".format(loc, sum(1 for r in rows if r[2] == loc)))
    print("  by category:")
    for cat in sorted(CATEGORY):
        print("    {:<16} {}".format(cat, sum(1 for r in rows if r[1] == cat)))


if __name__ == "__main__":
    main()
