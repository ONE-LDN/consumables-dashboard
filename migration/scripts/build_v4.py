#!/usr/bin/env python3
"""
Build the v4 catalogue CSVs from the hand-confirmed constants below.

Source of truth for the product set is the Google Sheet
`consumables_catalogue_v4` (1iWeiiY2a_hc98gy7T-Itsst9VMHfuiRXfcwJ16OH-z8),
one tab, `Product List (Updated)`, range A1:G36 — 35 products, columns
Product / Category / Supplier / Pack Size / Par Qty / Cost / Notes.

Everything the sheet does NOT carry is declared here as an explicit constant
with a provenance tag, so no figure in the output CSVs is unattributable:

    SHEET_V4      transcribed from the sheet, verbatim
    KEY           the Supabase product_name_raw slug (unchanged since v1)
    SHORT_NAME    brand-free display name — Saffron's requirement that the
                  count sheet and dashboard not carry brand names
    COUNT_UNIT    the noun that goes in the count sheet's column header
    ORDER_CLASS   reorder | measure_only  (measure-only items are counted but
                  never auto-ordered: they go missing, they are not consumed)
    PACK_OVERRIDE where the sheet's Pack Size is not "items per order unit"
    NOTE_MIN      a minimum written into the sheet's Notes column

Run:  python3 migration/scripts/build_v4.py
Writes: migration/products_v4.csv
        migration/first_aid_v4.csv
        migration/unit_basis_v4.csv

This script is the ONLY way these CSVs should be regenerated. Do not hand-edit
the outputs — a previous session lost its generators to an ephemeral container
and left the CSVs unreproducible.
"""

import csv
import os

OUT = os.path.join(os.path.dirname(__file__), "..")

# ---------------------------------------------------------------------------
# 1. The sheet, transcribed verbatim.
#    (key, product_description, category, supplier, pack_size, par_qty, cost, notes)
#    pack_size / par_qty / cost are None where the sheet cell is blank.
# ---------------------------------------------------------------------------
SHEET_V4 = [
    ("toilet_rolls",         'Jumbo T.Roll 2ply 2.25" Core J26300 300m',                     "Toiletries", "Futures Supplies",   6,   4,    17.52, "Counted individually"),
    ("blue_rolls",           "2ply Blue Embossed C/feed Roll 150m 96711",                    "Gym Floor",  "Futures Supplies",   6,   5,    11.31, "counted individually"),
    ("multipurpose_cleaner", "Greenspeed Techno Multi - Single 5L (Multi Surface Cleaner)",   "Staff Room", "Futures Supplies",   1,   2,    14.23, ""),
    ("hand_wash",            "Odyssey Black Pepper & Sandalwood Hand Wash 5L",               "Toiletries", "Out of Eden",        1,   2,    25.19, ""),
    ("conditioner",          "Odyssey Black Pepper & Sandalwood Conditioner 5L",             "Toiletries", "Out of Eden",        1,   2,    25.19, ""),
    ("moisturiser",          "Odyssey Black Pepper & Sandalwood Hand & Body Lotion 5L",      "Toiletries", "Out of Eden",        1,   3,    25.19, ""),
    ("shampoo",              "Odyssey Black Pepper & Sandalwood Shampoo & Body Wash 5L",     "Toiletries", "Out of Eden",        1,   6,    25.19, ""),
    ("hair_bands",           "Hair Bands",                                                   "FOH Desk",   "Amazon?",         None,   1,     3.99, ""),
    ("chalk_block",          "Chalk Block",                                                  "Gym Floor",  "Amazon",             8,   2,    15.99, ""),
    ("puly_caffe_cleaner",   "Puly Caffe Cleaner",                                           "Cafe",       "Amazon",             2,   1,    21.47, ""),
    ("tampons",              "Tampons",                                                      "Toiletries", "Amazon",            64, None,   17.28, ""),
    ("pads",                 "Sanitary Pads",                                                "Toiletries", "Amazon",            44, None,    7.99, ""),
    ("d_batteries",          "D Batteries (Ergs)",                                           "FOH Desk",   "Amazon",             8,   1,    15.99, "Need to have 10 on hand"),
    ("key_fobs",             "Key Fobs",                                                     "FOH Desk",   "",                None, None,    None, ""),
    ("blue_cloth",           "J Cloth Roll — 6 Blue Cloth Rolls, 150 Sheets",                "Cafe",       "Amazon",           150,   2,    11.98, "J Cloth Roll, Cleaning Cloth Roll, Soft and Quick-Drying can Be Used Repeatedly, 6 Blue Cloth Rolls, 150 Sheets, Blue."),
    ("chill_tubs_sanitiser", "Chill Tubs Sanitiser",                                         "Toiletries", "Concept Spa",       20,   2,    15.00, "tubs"),
    ("chill_tub_filters",    "Chill Tub Filters",                                            "Toiletries", "Concept Spa",        1,   1,    20.00, "Replacement every 3 months"),
    ("wet_kit_bags",         "Wet kit bag",                                                  "Toiletries", "Amazon",           250,   2,    12.99, ""),
    ("bin_bags",             "DCS 200 heavy duty bin bags 80L",                              "Staff Room", "Amazon",           200,   1,    16.62, ""),
    ("washing_up_liquid",    "Ecover washing up liquid 5L",                                  "Cafe",       "Amazon",             1,   1,    11.87, ""),
    ("water_softener_salt",  "Water Softener Salt",                                          "Plant room", "Halite",          None,  10,   149.99, "6 packs to fill tub. needs to be checked weekly"),
    ("urinal_shields",       "Urinal case",                                                  "Toiletries", "Amazon",          None, None,    None, ""),
    ("blue_gloves_large",    "Blue Nitrile disposable gloves L (8.5)",                       "Staff Room", "Amazon",           200,   1,     3.41, ""),
    ("printer_ink_blk",      "Printer Ink - Black (Sodface)",                                "FOH Desk",   "Amazon",             1,   1,     None, "Sodface"),
    ("printer_ink_pink",     "Printer Ink - Pink (Sodface)",                                 "FOH Desk",   "Amazon",             1,   1,     None, "Sodface"),
    ("printer_ink_blue",     "Printer Ink - Blue (Sodface)",                                 "FOH Desk",   "Amazon",             1,   1,     None, "Sodface"),
    ("printer_ink_yellow",   "Printer Ink - Yellow (Sodface)",                               "FOH Desk",   "Amazon",             1,   1,     None, "Sodface"),
    ("paper_printer",        "Paper - printer",                                              "FOH Desk",   "Amazon",          None,   2,     None, "2 on hand"),
    ("sure_deodorant_men",   "Deodorant - Men",                                              "Toiletries", "Amazon",             6,   4,    10.50, ""),
    ("sure_deodorant_women", "Deodorant - Women",                                            "Toiletries", "Amazon",             6,   4,    10.50, ""),
    ("glade_sprays",         "Glade air freshener sprays",                                   "Toiletries", "Amazon",          None, None,    None, ""),
    ("microfibre_cloths",    "MR.SIGA microfibre cloths pack of 12",                         "",           "Amazon",            12,   1,     9.49, ""),
    ("sanitiser_gel",        "BioHygiene UNFRAGRANCED Sanitiser 5L",                         "Toiletries", "Futures Supplies",   1,   1,    26.98, "5L. Oceanfree Professional?"),
    ("pens",                 "Pens",                                                         "FOH Desk",   "Amazon",          None, None,    None, ""),
    ("notepads",             "Notepads",                                                     "FOH Desk",   "Amazon",          None, None,    None, "need 1 on hand"),
]

# ---------------------------------------------------------------------------
# 2. Brand-free short names for the count sheet and the dashboard.
#    Saffron: "Stock count sheet & consumables dashboard doesn't have to
#    include the brand name - these can be accounted for in the product
#    catalogue."
# ---------------------------------------------------------------------------
SHORT_NAME = {
    "toilet_rolls":         "Toilet Roll",
    "blue_rolls":           "Blue Roll (centrefeed)",
    "multipurpose_cleaner": "Multi-Surface Cleaner 5L",
    "hand_wash":            "Hand Wash 5L",
    "conditioner":          "Conditioner 5L",
    "moisturiser":          "Hand & Body Lotion 5L",
    "shampoo":              "Shampoo & Body Wash 5L",
    "hair_bands":           "Hair Bands",
    "chalk_block":          "Chalk Block",
    "puly_caffe_cleaner":   "Coffee Machine Cleaner",
    "tampons":              "Tampons",
    "pads":                 "Sanitary Pads",
    "d_batteries":          "D Batteries (Ergs)",
    "key_fobs":             "Key Fobs",
    "blue_cloth":           "Blue Cloth Roll",
    "chill_tubs_sanitiser": "Ice Bath Sanitiser",
    "chill_tub_filters":    "Ice Bath Filter",
    "wet_kit_bags":         "Wet Kit Bags",
    "bin_bags":             "Bin Bags 80L",
    "washing_up_liquid":    "Washing Up Liquid 5L",
    "water_softener_salt":  "Water Softener Salt",
    "urinal_shields":       "Urinal Shields",
    "blue_gloves_large":    "Nitrile Gloves (L)",
    "printer_ink_blk":      "Printer Ink - Black",
    "printer_ink_pink":     "Printer Ink - Pink",
    "printer_ink_blue":     "Printer Ink - Blue",
    "printer_ink_yellow":   "Printer Ink - Yellow",
    "paper_printer":        "Printer Paper",
    "sure_deodorant_men":   "Deodorant - Men",
    "sure_deodorant_women": "Deodorant - Women",
    "glade_sprays":         "Air Freshener Spray",
    "microfibre_cloths":    "Microfibre Cloths",
    "sanitiser_gel":        "Hand Sanitiser 5L",
    "pens":                 "Pens",
    "notepads":             "Notepads",
}

# The noun that goes into the count sheet column header, so a count can never
# again be recorded without its unit. This is the fix for the pack/item
# ambiguity that made the previous Stock column unsalvageable.
COUNT_UNIT = {
    "toilet_rolls": "rolls", "blue_rolls": "rolls", "multipurpose_cleaner": "5L bottles",
    "hand_wash": "5L bottles", "conditioner": "5L bottles", "moisturiser": "5L bottles",
    "shampoo": "5L bottles", "hair_bands": "bands", "chalk_block": "blocks",
    "puly_caffe_cleaner": "bottles", "tampons": "tampons", "pads": "pads",
    "d_batteries": "batteries", "key_fobs": "fobs", "blue_cloth": "rolls",
    "chill_tubs_sanitiser": "tubs", "chill_tub_filters": "filters",
    "wet_kit_bags": "bags", "bin_bags": "bags", "washing_up_liquid": "5L bottles",
    "water_softener_salt": "bags", "urinal_shields": "shields",
    "blue_gloves_large": "gloves", "printer_ink_blk": "cartridges",
    "printer_ink_pink": "cartridges", "printer_ink_blue": "cartridges",
    "printer_ink_yellow": "cartridges", "paper_printer": "reams",
    "sure_deodorant_men": "cans", "sure_deodorant_women": "cans",
    "glade_sprays": "cans", "microfibre_cloths": "cloths",
    "sanitiser_gel": "5L bottles", "pens": "pens", "notepads": "pads",
}

# Counted, never auto-ordered. These do not get consumed — they go missing or
# they last until they fail, so a monthly usage figure is meaningless.
MEASURE_ONLY = {
    "printer_ink_blk", "printer_ink_pink", "printer_ink_blue",
    "printer_ink_yellow", "key_fobs",
}

# ---------------------------------------------------------------------------
# 3. Where the sheet's Pack Size is NOT "items per order unit".
#    Each entry is (items_per_order_unit, why).
# ---------------------------------------------------------------------------
PACK_OVERRIDE = {
    # The sheet's 150 is sheets per roll. The order unit is a case of 6 rolls,
    # and the count is in rolls, so items per order unit is 6.
    "blue_cloth": (6, "sheet's 150 is sheets/roll; order unit is a 6-roll case"),
}

# Pack sizes the sheet leaves blank, carried over from the live Supabase row.
# Provenance: shop_product_lookup.pack_size, read 2026-08-05. NOT independently
# verified against a supplier listing — flagged in the output.
PACK_FROM_DB = {
    "hair_bands":          100,
    "urinal_shields":      10,
    "glade_sprays":        4,
    # water_softener_salt is deliberately absent. The DB says 10/pack, but the
    # sheet's note ("6 packs to fill tub") uses "pack" to mean one bag, and
    # £149.99 looks like a pallet price rather than a per-bag one. Leaving the
    # pack size unknown is more honest than multiplying Par Qty 10 by a guess
    # and producing a 100-bag / ~£1,500 minimum.
}

# A minimum stated in words in the sheet's Notes column. An explicitly-set
# human requirement wins outright over any computed candidate.
NOTE_MIN = {
    "d_batteries":  (10, "Need to have 10 on hand"),
    "paper_printer": (2, "2 on hand"),
    "notepads":      (1, "need 1 on hand"),
}

# Rows where reading Par Qty as PACKS disagrees with the unit figure the
# previous sheet (v3) carried. Listed so they get asked about rather than
# silently adopted. (key, v3_par_in_units, v4_par_x_pack, note)
PAR_DIVERGENCE = {
    "chalk_block":          (2,   16,  "v3 said 2 blocks and the shelf held 1, so 2 probably still means 2 blocks, not 2 cases of 8"),
    "blue_cloth":           (6,   12,  "v3 said 6 rolls (one case); 2 cases = 12 rolls"),
    "chill_tubs_sanitiser": (20,  40,  "v3 said 20 tubs (one pack); 2 packs = 40 tubs"),
    "wet_kit_bags":         (20, 500,  "supplier changed Newline (pack of 20) to Amazon (pack of 250), so v3's 20 does not carry over"),
    "water_softener_salt":  (10, None, "pack size unknown; 10 most likely means 10 bags, not 10 packs"),
    "blue_gloves_large":    (None, 200, "v3 blank; DB pack was 100, sheet now says 200 - which is right?"),
}

# Rows where reading Par Qty as packs produces a figure large enough to be
# worth refusing to sync until a human confirms it. Everything in
# PAR_DIVERGENCE is emitted with min_confirmed=no; these are the ones where
# being wrong is expensive rather than merely untidy.
MIN_DO_NOT_SYNC = {"wet_kit_bags", "water_softener_salt", "chalk_block"}

# ---------------------------------------------------------------------------
# 4. First Aid — split onto its own tab. Counted on its own cadence and
#    ordered as refill packs, not item by item.
#    Requirements and on-hand counts are from the 2026-08-04 physical count of
#    all four boxes combined (see migration/FIRST-AID.md).
#    (key, short_name, group, required, on_hand_2026_08_04, class)
# ---------------------------------------------------------------------------
FIRST_AID = [
    # --- BS 8599-1 required list: 15 lines, counted 2026-08-04 ---
    # blue_plasters keeps its existing slug: it is already a live Supabase row
    # carrying a real price (£3.57), and reusing it avoids orphaning that.
    ("blue_plasters",          "Washproof Plasters (blue detectable)", "Required", 160,   0, "consumable"),
    ("fa_sterile_wipes",       "Sterile Wipes",                       "Required",  80,  40, "consumable"),
    ("fa_safety_pins",         "Safety Pins",                         "Required",  48,  44, "consumable"),
    ("fa_gloves_nitrile",      "Nitrile Gloves (individual)",         "Required",  24,  12, "consumable"),
    ("fa_dressing_12x12",      "First Aid Dressing 12x12cm",          "Required",   8,   4, "consumable"),
    ("fa_finger_dressing",     "Finger Dressing",                     "Required",   8,   1, "consumable"),
    ("fa_triangular_bandages", "Triangular Bandages",                 "Required",   8,  12, "consumable"),
    ("fa_eye_pad_bandages",    "Eye Pad Bandages",                    "Required",   8,  23, "consumable"),
    ("fa_dressing_18x18",      "First Aid Dressing 18x18cm",          "Required",   4,   3, "consumable"),
    ("fa_burn_dressing_10x10", "Burn Dressing 10x10cm",               "Required",   4,   2, "consumable"),
    ("fa_conforming_bandages", "Conforming Bandages",                 "Required",   4,   2, "consumable"),
    ("fa_waterproof_tape",     "Waterproof Tape",                     "Required",   4,   0, "consumable"),
    ("fa_face_shield",         "Face Shield",                         "Required",   4,   3, "consumable"),
    ("fa_foil_blankets",       "Foil Blankets",                       "Required",   4,   3, "consumable"),
    ("fa_clothing_cutters",    "Clothing Cutters",                    "Required",   4,   0, "equipment"),
    # --- merged variants: 13 count lines collapsed into 4 tracked lines ---
    ("fa_gauze_swabs",         "Gauze Swabs / Non-Woven Compress",    "Held",    None,  14, "consumable"),
    ("fa_plasters_beige",      "Adhesive Plasters (non-detectable)",  "Held",    None, 222, "consumable"),
    ("fa_elastic_bandages",    "Elastic Bandages",                    "Held",    None,   4, "consumable"),
    ("fa_cotton_wool",         "Cotton Wool (pads / balls)",          "Held",    None,   4, "consumable"),
    # --- held, genuinely distinct items, not on the required list ---
    ("fa_crepe_bandages",      "Crepe Cotton Bandages",               "Held",    None,   4, "consumable"),
    ("fa_eye_wash_pod",        "Sterile Eye Wash Pod",                "Held",    None,   2, "consumable"),
    ("fa_burn_gel",            "Emergency Burn Gel",                  "Held",    None,   1, "consumable"),
    ("fa_blanket",             "First Aid Blanket",                   "Held",    None,   1, "consumable"),
    ("fa_gloves_vinyl",        "Vinyl Gloves",                        "Held",    None,   2, "consumable"),
    ("fa_nonadherent_10x10",   "Non-Adherent Dressing 10x10cm",       "Held",    None,   1, "consumable"),
    ("fa_cotton_tips",         "Cotton Tips",                         "Held",    None,   1, "consumable"),
    ("fa_plaster_sheet",       "Plaster Sheet",                       "Held",    None,   1, "consumable"),
    ("fa_adhesive_tape",       "Adhesive Tape",                       "Held",    None,   2, "consumable"),
    # --- equipment: check present, never reorder on a usage rule ---
    ("fa_tourniquet",          "Tourniquet",                          "Equipment", 1,    1, "equipment"),
    ("fa_tweezers",            "Tweezers",                            "Equipment", 1,    1, "equipment"),
    ("fa_safety_scissors",     "Safety Scissors",                     "Equipment", 1,    1, "equipment"),
    # --- the order units: what actually gets bought ---
    # hs_refills keeps its existing slug too - it is already the live
    # "Health & Safety / First Aid Kit" row at £24.53, which is the closest
    # thing on record to a refill-pack price.
    ("hs_refills",             "BS 8599-1 Refill Pack",               "Order unit", 4, None, "order_unit"),
    ("ice_packs",              "Ice Packs",                           "Order unit", 16,  11, "consumable"),
]


def _n(v):
    return "" if v is None else v


def build_products():
    rows = []
    for key, desc, cat, sup, pack, par, cost, notes in SHEET_V4:
        # items per order unit
        if key in PACK_OVERRIDE:
            upp, upp_src = PACK_OVERRIDE[key][0], "override: " + PACK_OVERRIDE[key][1]
        elif pack is not None:
            upp, upp_src = pack, "sheet Pack Size"
        elif key in PACK_FROM_DB:
            upp, upp_src = PACK_FROM_DB[key], "carried from live Supabase row - unverified"
        else:
            upp, upp_src = None, "unknown"

        # Par Qty is read as PACKS. Evidence: on 14 of the rows that changed
        # between v3 and v4, v4_par x pack_size reproduces v3's unit figure
        # exactly (24, 30, 2, 8, 200, 24, 12, ...).
        par_units = None
        par_src = "no Par Qty set"
        if par is not None and upp is not None:
            par_units = par * upp
            par_src = f"sheet Par Qty ({par} packs) x {upp} items/pack"
        elif par is not None:
            par_src = f"sheet Par Qty ({par}) but pack size unknown"

        # Minimum. With the baseline being reset there is no trustworthy usage
        # figure for any product, so the minimum is Saffron's Par Qty in items,
        # raised by an explicit note-stated requirement where one exists.
        # Measured usage from consecutive weekly counts replaces this.
        min_units, min_src = par_units, ("Par Qty in items" if par_units is not None else "not set")
        if key in NOTE_MIN:
            want, why = NOTE_MIN[key]
            if min_units is None or want > min_units:
                min_units, min_src = want, f'stated in sheet notes: "{why}"'

        flags = []
        min_confirmed = "yes"
        if key in PAR_DIVERGENCE:
            v3, v4x, why = PAR_DIVERGENCE[key]
            flags.append(f"CONFIRM par basis: {why}")
            min_confirmed = "no"
        if key in MIN_DO_NOT_SYNC:
            min_confirmed = "no - do not sync"
        if upp is None:
            flags.append("pack size unknown - cannot size an order")
        elif upp_src.startswith("carried"):
            flags.append("pack size unverified (from old DB row)")
        if cost is None:
            flags.append("no price")
        if not cat:
            flags.append("no category")
        if key in MEASURE_ONLY:
            flags.append("measure-only: counted, never auto-ordered")

        rows.append({
            "product_name_raw": key,
            "display_name": SHORT_NAME[key],
            "location": cat,
            "supplier": sup,
            "order_link_or_desc": desc,
            "price_per_pack_gbp": _n(cost),
            "units_per_pack": _n(upp),
            "count_unit": COUNT_UNIT[key],
            "par_packs_sheet": _n(par),
            "min_stock_units": _n(min_units),
            "min_confirmed": min_confirmed,
            "order_class": "measure_only" if key in MEASURE_ONLY else "reorder",
            "units_per_pack_source": upp_src,
            "par_source": par_src,
            "min_source": min_src,
            "_review": "; ".join(flags),
        })
    return rows


def build_first_aid():
    rows = []
    for key, name, group, required, have, cls in FIRST_AID:
        short = None if required is None or have is None else required - have
        rows.append({
            "product_name_raw": key,
            "display_name": name,
            "group": group,
            "item_class": cls,
            "required_items": _n(required),
            "counted_2026_08_04": _n(have),
            "short_items": _n(short if short is not None and short > 0 else (0 if short is not None else None)),
            "reorderable": "no" if cls == "equipment" else "yes",
            "_review": "no pack size or price on record" if cls != "equipment" else "check present only",
        })
    return rows


def build_unit_basis(products):
    """One row per product stating, in words, what a count of 1 means and how
    the order quantity is derived from it. This is the artefact that stops the
    pack/item ambiguity coming back."""
    rows = []
    for p in products:
        upp = p["units_per_pack"]
        rows.append({
            "product_name_raw": p["product_name_raw"],
            "display_name": p["display_name"],
            "count_header": f'Count ({p["count_unit"]})',
            "one_count_means": f'1 {p["count_unit"].rstrip("s")}',
            "items_per_order_unit": upp,
            "order_unit": (f'pack of {upp} {p["count_unit"]}' if upp not in ("", 1) else "single item")
                          if upp != "" else "UNKNOWN",
            "minimum_items": p["min_stock_units"],
            "minimum_confirmed": p["min_confirmed"],
            "basis_source": p["units_per_pack_source"],
        })
    return rows


def write(path, rows):
    if not rows:
        return
    full = os.path.join(OUT, path)
    with open(full, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path}: {len(rows)} rows")


if __name__ == "__main__":
    products = build_products()
    write("products_v4.csv", products)
    write("first_aid_v4.csv", build_first_aid())
    write("unit_basis_v4.csv", build_unit_basis(products))

    # Consistency checks — fail loudly rather than emit a quietly wrong CSV.
    assert len(SHEET_V4) == 35, f"expected 35 sheet rows, got {len(SHEET_V4)}"
    keys = [r[0] for r in SHEET_V4]
    assert len(set(keys)) == len(keys), "duplicate product key"
    assert set(keys) == set(SHORT_NAME) == set(COUNT_UNIT), "name/unit map out of step with the sheet"
    fa_keys = [r[0] for r in FIRST_AID]
    assert len(set(fa_keys)) == len(fa_keys), "duplicate first aid key"

    no_pack = [p["product_name_raw"] for p in products if p["units_per_pack"] == ""]
    no_price = [p["product_name_raw"] for p in products if p["price_per_pack_gbp"] == ""]
    print(f"\n{len(products)} consumables, {len(FIRST_AID)} first aid lines")
    print(f"pack size unknown ({len(no_pack)}): {', '.join(no_pack)}")
    print(f"no price ({len(no_price)}): {', '.join(no_price)}")
    print(f"par basis to confirm ({len(PAR_DIVERGENCE)}): {', '.join(PAR_DIVERGENCE)}")
