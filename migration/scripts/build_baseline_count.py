#!/usr/bin/env python3
"""
Stage the 2026-08-04 physical count as baseline count 1.

Source: the `Stock` column of `consumables_catalogue_v3`
(1DA77H1SG9aLELsvNFxL6VksNvVCFj5_xHZftgV2UPC4), supplied by Saffron 2026-08-05
with the basis stated:

    "Counted primarily per item and where bottles or tubs were in question,
     fractions etc"

So the default basis is ITEMS, with a decimal where a container was part used.
That is a much better position than the previous session concluded ("the count
column silently mixes packs and items; 9 products are undecidable"). Under
Saffron's rule 30 of 34 counted lines read cleanly as items. The other four --
tampons, pads, bin bags, wet kit bags -- needed her to state the basis directly;
all four were confirmed 2026-08-05 and are recorded in RESOLVED_BASIS below.

The count predates the v4 rebuild, so it is keyed against the OLD product names.
COUNT_TO_V4_KEY maps them onto the v4 slugs. Three v3 rows are Sea Kelp products
replaced by Odyssey equivalents; their counts carry over to the reused keys,
because what is being counted is 5L of hand wash in a cupboard, not a brand.

Run:  python3 migration/scripts/build_baseline_count.py
Writes: migration/baseline_count_2026_08_04.csv

Depends on migration/products_v4.csv, so run build_v4.py first.
"""

import csv
import os

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..")
TAKE_DATE = "2026-08-04"

# ---------------------------------------------------------------------------
# The count, transcribed verbatim. (v3_product_name, stock_as_written)
# None = the cell was blank, i.e. not counted. A blank is NOT a zero.
# ---------------------------------------------------------------------------
COUNT_V3 = [
    ('Jumbo T.Roll 2ply 2.25" Core J26300 300m',                    27),
    ("2ply Blue Embossed C/feed Roll 150m 96711",                   20),
    ("Greenspeed Techno Multi - Single 5L (Multi Surface Cleaner)",  2.5),
    ("Sea Kelp Liquid Hand Wash Refill 5L",                         0),
    ("Sea Kelp Luxury Shampoo 5L Refill",                           1),
    ("Sea Kelp Luxury Conditioner Refill 5L",                       1),
    ("Sea Kelp Luxury Hand & Body Lotion 5L Refill (Moisturiser)",  3),
    ("Odyssey Black Pepper & Sandalwood Shampoo & Body Wash 5L",     3),
    ("Hair Bands",                                                  0),
    ("Chalk Block",                                                 1),
    ("Puly Caffe Cleaner",                                          0.5),
    ("Tampons",                                                     4),
    ("Sanitary Pads",                                               11),
    ("D Batteries (Ergs)",                                          5),
    ("Key Fobs",                                                    0),
    ("Blue cloth",                                                  0),
    ("Chill Tubs Sanitiser",                                        3),
    ("Chill Tub Filters",                                           10),
    ("Wet kit bag",                                                 3),
    ("Bin bags",                                                    0.5),
    ("Washing up liquid",                                           0.5),
    ("Water Softener Salt",                                         36),
    ("Urinal case",                                                 0),
    ("Blue Gloves Large",                                           0),
    ("Printer Ink - Black",                                         1),
    ("Printer Ink - Pink",                                          1),
    ("Printer Ink - Blue",                                          1),
    ("Printer Ink - Yellow",                                        1),
    ("Paper - printer",                                             0.5),
    ("Deodorant - Men",                                             0),
    ("Deodorant - Women",                                           0),
    ("Glade airfreshner sparys",                                    3),
    ("Microfibre Cloths",                                        None),
    ("Hand sanitiser",                                              1),
    ("Pens",                                                        12),
    ("Notepads",                                                 None),
]

# v3 product name -> v4 product_name_raw. None = no v4 row (retired product).
COUNT_TO_V4_KEY = {
    'Jumbo T.Roll 2ply 2.25" Core J26300 300m':                     "toilet_rolls",
    "2ply Blue Embossed C/feed Roll 150m 96711":                    "blue_rolls",
    "Greenspeed Techno Multi - Single 5L (Multi Surface Cleaner)":   "multipurpose_cleaner",
    "Sea Kelp Liquid Hand Wash Refill 5L":                          "hand_wash",
    "Sea Kelp Luxury Shampoo 5L Refill":                            None,
    "Sea Kelp Luxury Conditioner Refill 5L":                        "conditioner",
    "Sea Kelp Luxury Hand & Body Lotion 5L Refill (Moisturiser)":   "moisturiser",
    "Odyssey Black Pepper & Sandalwood Shampoo & Body Wash 5L":     "shampoo",
    "Hair Bands":                                                   "hair_bands",
    "Chalk Block":                                                  "chalk_block",
    "Puly Caffe Cleaner":                                           "puly_caffe_cleaner",
    "Tampons":                                                      "tampons",
    "Sanitary Pads":                                                "pads",
    "D Batteries (Ergs)":                                           "d_batteries",
    "Key Fobs":                                                     "key_fobs",
    "Blue cloth":                                                   "blue_cloth",
    "Chill Tubs Sanitiser":                                         "chill_tubs_sanitiser",
    "Chill Tub Filters":                                            "chill_tub_filters",
    "Wet kit bag":                                                  "wet_kit_bags",
    "Bin bags":                                                     "bin_bags",
    "Washing up liquid":                                            "washing_up_liquid",
    "Water Softener Salt":                                          "water_softener_salt",
    "Urinal case":                                                  "urinal_shields",
    "Blue Gloves Large":                                            "blue_gloves_large",
    "Printer Ink - Black":                                          "printer_ink_blk",
    "Printer Ink - Pink":                                           "printer_ink_pink",
    "Printer Ink - Blue":                                           "printer_ink_blue",
    "Printer Ink - Yellow":                                         "printer_ink_yellow",
    "Paper - printer":                                              "paper_printer",
    "Deodorant - Men":                                              "sure_deodorant_men",
    "Deodorant - Women":                                            "sure_deodorant_women",
    "Glade airfreshner sparys":                                     "glade_sprays",
    "Microfibre Cloths":                                            "microfibre_cloths",
    "Hand sanitiser":                                               "sanitiser_gel",
    "Pens":                                                         "pens",
    "Notepads":                                                     "notepads",
}

# The four lines Saffron's "items, fractions for containers" rule did not settle
# on its own. All four CONFIRMED by her 2026-08-05.
#   (key, multiplier, resulting_items, basis_label, how it was settled)
# multiplier is what the written figure is multiplied by to reach items.
RESOLVED_BASIS = {
    "tampons":      (64,  256, "packs (boxes of 64)",
                     "confirmed: 4 boxes, not 4 tampons. 256 items, which is the surplus "
                     "recorded on 2026-08-04"),
    "pads":         (44,  484, "packs (packets of 44)",
                     "confirmed: 11 packets, not 11 pads. 484 items, matching the recorded surplus"),
    "bin_bags":     (200, 100, "packs (half a 200-bag pack)",
                     "confirmed: half a 200-bag pack, so 100 bags - not half a roll of 50"),
    "wet_kit_bags": (1,     3, "items",
                     "confirmed: 3 individual bags, so almost out whichever pack size applies"),
}

# Products confirmed to be in surplus, so they stay out of any reset order
# regardless of what their (blank) Par Qty implies.
SURPLUS_CONFIRMED = {
    "tampons": "256 items against a Par Qty of one 64-pack. Blank Par Qty in v4 reads as 'do not reorder'",
    "pads":    "484 items against a Par Qty of one 44-pack. Same",
}

# Lines where the on-hand figure is below EVERY plausible minimum candidate, so
# the order decision does not depend on the unresolved Par Unit question.
ROBUST_ORDER = {
    "wet_kit_bags": "3 bags is below every candidate minimum (20 on the old par, 500 on the "
                    "new one), so this is orderable now without settling Par Unit first",
}

# Counts that need an adjustment before they mean on-hand stock.
ADJUSTED = {
    "chill_tub_filters": (10, 4,
                          'v3 note reads "4 new ones. 6 old." Only the 4 new filters are '
                          "usable stock; the 6 old ones are spent and should not count "
                          "toward a minimum of 1"),
}


def load_products():
    path = os.path.join(OUT, "products_v4.csv")
    with open(path, encoding="utf-8") as fh:
        return {r["product_name_raw"]: r for r in csv.DictReader(fh)}


def build():
    products = load_products()
    rows, unmapped = [], []

    for name, raw in COUNT_V3:
        key = COUNT_TO_V4_KEY[name]
        if key is None:
            unmapped.append((name, raw))
            continue
        p = products[key]

        basis, on_hand, note = "items", raw, ""
        confirmed = "yes"

        if raw is None:
            basis, on_hand, note, confirmed = "", None, "not counted - blank cell, not a zero", "n/a"
        elif key in ADJUSTED:
            was, adj, why = ADJUSTED[key]
            basis, on_hand, note = "items (adjusted)", adj, why
        elif key in RESOLVED_BASIS:
            mult, items, label, why = RESOLVED_BASIS[key]
            basis, on_hand, note = label, items, why

        min_units = p["min_stock_units"]
        min_ok = p["min_confirmed"] == "yes"
        status, short = "", ""
        if on_hand is None:
            status = "unknown"
        elif key in SURPLUS_CONFIRMED:
            status = "surplus (confirmed)"
            note = (note + ". " if note else "") + SURPLUS_CONFIRMED[key]
        elif key in ROBUST_ORDER:
            # Below every candidate minimum, so the order is safe to place, but
            # the shortfall itself cannot be quantified until Par Unit is settled.
            status, short = "BELOW minimum (qty TBC)", ""
            note = (note + ". " if note else "") + ROBUST_ORDER[key]
        elif min_units == "":
            status = "no minimum set"
        elif not min_ok:
            status = "minimum unconfirmed"
        else:
            m = float(min_units)
            if on_hand < m:
                status, short = "BELOW minimum", round(m - on_hand, 2)
            elif on_hand > m * 1.5:
                status = "surplus"
            else:
                status = "ok"

        rows.append({
            "take_date": TAKE_DATE,
            "product_name_raw": key,
            "display_name": p["display_name"],
            "location": p["location"],
            "count_as_written": "" if raw is None else raw,
            "count_basis": basis,
            "on_hand_items": "" if on_hand is None else on_hand,
            "count_unit": p["count_unit"],
            "basis_confirmed": confirmed,
            "min_stock_units": min_units,
            "min_confirmed": p["min_confirmed"],
            "status": status,
            "short_items": short,
            "order_class": p["order_class"],
            "note": note,
        })
    return rows, unmapped


def write(path, rows):
    with open(os.path.join(OUT, path), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path}: {len(rows)} rows")


if __name__ == "__main__":
    rows, unmapped = build()
    write("baseline_count_2026_08_04.csv", rows)

    assert len(COUNT_V3) == 36, f"expected 36 count lines, got {len(COUNT_V3)}"
    assert set(n for n, _ in COUNT_V3) == set(COUNT_TO_V4_KEY), "count/key map out of step"

    counted = [r for r in rows if r["on_hand_items"] != ""]
    below = [r for r in rows if r["status"].startswith("BELOW minimum")]
    surplus = [r for r in rows if r["status"].startswith("surplus")]
    held = [r for r in rows if r["basis_confirmed"] == "no"]
    nomin = [r for r in rows if r["status"] in ("no minimum set", "minimum unconfirmed")]

    print(f"\n{len(rows)} lines mapped to v4 keys, {len(counted)} with a usable on-hand figure")
    print(f"  BELOW minimum : {len(below)}")
    print(f"  surplus       : {len(surplus)}  ({', '.join(r['display_name'] for r in surplus)})")
    print(f"  basis held    : {len(held)}  ({', '.join(r['display_name'] for r in held) or 'none - all 34 counted lines resolved'})")
    print(f"  no usable min : {len(nomin)}")
    print(f"  not counted   : {len([r for r in rows if r['count_as_written'] == ''])}")
    if unmapped:
        print(f"\nnot in v4, count discarded: "
              f"{', '.join(f'{n} ({v})' for n, v in unmapped)}")

    print("\nBELOW MINIMUM, worst first:")
    for r in sorted(below, key=lambda r: -(float(r["short_items"]) if r["short_items"] != "" else -1)):
        short = r["short_items"] if r["short_items"] != "" else "TBC"
        print(f"  {r['display_name'][:26]:28} {r['on_hand_items']:>6} / {str(r['min_stock_units']):>5} "
              f"{r['count_unit']:12} short {short}")
