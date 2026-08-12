#!/usr/bin/env python3
"""
Build the weekly Stock Count sheet from `products_v4.csv`.

Output: `migration/stock_count_sheet.csv` — the exact cell layout to paste into
the Google Sheet's `Stock Count` tab. One row per consumable, ordered by the
route you actually walk when counting.

LAYOUT IS NOT FREE. `submitCounts()` in `apps-script/Code.gs` reads fixed
positions, so the columns cannot be reordered or inserted into:

    B1                 take date          (COUNT_DATE_CELL)
    row 3              header row         (COUNT_HEADER_ROW)
    row 4+             products           (COUNT_FIRST_ROW)
    col A  product_name_raw   the sync key — hidden, never edited
    col B  Product            display_name + the count unit in brackets
    col C  Location           where you count it
    col D  Count              what the counter types      <- read as actual_count
    col E  Notes              free text                   <- read as notes

Only columns A, D and E are read on submit. The unit therefore cannot have its
own column without pushing Notes out of position, which is why it rides in the
Product cell instead — PLAN-V4 §3 guard rail 1 requires a count to be
impossible to record without its unit, and this satisfies that within the
layout the script already expects.

Locations are emitted in walk order, not alphabetically: you count a room at a
time, and a list that jumps between rooms gets counted wrong.
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

HEADERS = ["product_name_raw", "Product", "Location", "Count", "Notes"]


def label(display_name, count_unit):
    """Product cell: 'Toilet Roll — rolls'. The unit is always visible.

    Separated by a dash rather than brackets because several display names
    already end in brackets ('Blue Roll (centrefeed)', 'Nitrile Gloves (L)')
    and a second pair reads as a typo.

    Where the display name already carries the container size ('... 5L') the
    size is stripped from the unit, so it reads 'bottles' rather than the
    redundant '5L bottles'.
    """
    unit = count_unit.strip()
    size = display_name.rsplit(" ", 1)[-1]
    if unit.lower().startswith(size.lower() + " "):
        unit = unit[len(size) + 1:]
    return "{} — {}".format(display_name, unit)


def main():
    with open(MIGRATION / "products_v4.csv", newline="") as fh:
        products = list(csv.DictReader(fh))

    rows = []
    for p in products:
        key = p["product_name_raw"]
        location = LOCATION_OVERRIDE.get(key, p["location"]).strip()
        if location not in WALK_ORDER:
            raise SystemExit(
                "{}: location {!r} is not in WALK_ORDER".format(key, location)
            )
        rows.append([key, label(p["display_name"], p["count_unit"]), location, "", ""])

    rows.sort(key=lambda r: (WALK_ORDER.index(r[2]), r[1]))

    out = MIGRATION / "stock_count_sheet.csv"
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Take date:", "", "", "", ""])
        w.writerow(["Counted by:", "", "", "", ""])
        w.writerow(HEADERS)
        w.writerows(rows)

    print("{} products -> {}".format(len(rows), out))
    for loc in WALK_ORDER:
        print("  {:<12} {}".format(loc, sum(1 for r in rows if r[2] == loc)))


if __name__ == "__main__":
    main()
