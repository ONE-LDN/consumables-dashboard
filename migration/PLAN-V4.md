# Plan — v4 product list, stock count sheet and dashboard

Source: Google Sheet **`consumables_catalogue_v4`**
([`1iWeiiY2a_hc98gy7T-Itsst9VMHfuiRXfcwJ16OH-z8`](https://docs.google.com/spreadsheets/d/1iWeiiY2a_hc98gy7T-Itsst9VMHfuiRXfcwJ16OH-z8/edit)),
one tab, `Product List (Updated)`, A1:G36 — **35 products**.

This supersedes the v2/v3 analysis. What is still good from it, and what is now
dead, is set out in *§9 What this supersedes*.

---

## 1. Three findings that reshape the plan

### 1.1 The one "existing" stock take is junk

The previous session treated `2026-07-29` (38 rows, `source='sheet'`) as the
system's only real history and planned around preserving it. It is not real:

```
take_date    source   rows   distinct values   min   max
2026-07-29   sheet      38                 1     6     6
```

**Every one of the 38 counts is the number 6.** Not a count — an artefact of a
bad `submitCounts` run. Nothing can be derived from it, and worse, the dashboard
*would* derive from it: `computeItem()` uses the latest take as `last_count` and
projects on-hand forward from it. Leaving it in place means the dashboard shows
confident, wrong numbers.

**It gets deleted, not migrated.** The other `take_date`s in that table (65-row
sets from June/July) belong to the shop dashboard and are untouched.

Combined with `shop_consumable_deliveries` being **empty (0 rows)**, the true
state is: **no usable consumables history at all.** That is not a setback — it
is what makes the baseline reset free. There is nothing to orphan, so keys,
units and groupings can all be settled now at zero cost.

### 1.2 The sheet now carries `Pack Size`, which was the missing column

v3 had no pack-size column at all; pack sizes only appeared inside note text,
and the previous session had to guess several and got two wrong. v4 has a
`Pack Size` column populated for **30 of 35** products. This is the single input
that makes ordering computable, and it closes most of last session's guesswork.

Unknown for 5: `key_fobs`, `water_softener_salt`, `paper_printer`, `pens`,
`notepads`.

One caveat: `Pack Size` is not consistently *items per order unit*. For
**Blue Cloth** it reads `150`, which is sheets per roll — the order unit is a
case of 6 rolls. Handled as an explicit override in the build script; worth
fixing at source so the column means one thing.

### 1.3 `Par Qty` changed unit, and not uniformly

v4's `Par Qty` is mostly in **packs** where v3's was in **items**. The evidence
is strong: on every row whose number changed, `v4 Par × Pack Size` reproduces
v3's item figure exactly.

| product | v3 Par (items) | v4 Par | × Pack Size | |
|---|---|---|---|---|
| Toilet Roll | 24 | 4 | 4 × 6 = **24** | ✓ |
| Blue Roll | 30 | 5 | 5 × 6 = **30** | ✓ |
| Bin Bags | 200 | 1 | 1 × 200 = **200** | ✓ |
| Deodorant (each) | 24 | 4 | 4 × 6 = **24** | ✓ |
| Microfibre Cloths | 12 | 1 | 1 × 12 = **12** | ✓ |
| D Batteries | 8 | 1 | 1 × 8 = **8** | ✓ |
| Coffee Machine Cleaner | 2 | 1 | 1 × 2 = **2** | ✓ |

Seven independent exact hits is not coincidence. **But it does not hold
everywhere**, and reading those rows as packs produces figures that are plainly
wrong:

| product | Par | Pack | as packs | plausible? |
|---|---|---|---|---|
| Wet Kit Bags | 2 | 250 | 500 bags minimum | cheap at £26, so *possibly* fine |
| Water Softener Salt | 10 | — | 10 bags or 10 packs? | 10 packs at £149.99 ≈ £1,500 — no |
| Chalk Block | 2 | 8 | 16 blocks | v3 said 2, shelf held 1 — probably 2 |
| Ice Bath Sanitiser | 20 → 2 | 20 | 40 tubs | doubled the requirement — deliberate? |
| Blue Cloth | 6 → 2 | (6) | 12 rolls | doubled — deliberate? |
| Nitrile Gloves (L) | — | 200 | 200 gloves | sheet says 200/pack, DB said 100 |

So the honest position is that **`Par Qty`'s unit is mixed per row**, which is
exactly the failure mode that made v3's `Stock` column unsalvageable.

**Decided 2026-08-05: the sheet gains an explicit `Par Unit` column** stating
`packs` or `items` per row. Rejected: asserting one basis for all 35 rows in the
header, which is what produced the 100-bag salt minimum — a uniform rule is only
safe if the data is uniform, and it isn't.

`products_v4.csv` carries `par_unit` pre-filled with a proposed value and
`par_unit_basis` with the evidence for it, so the column is checked rather than
filled from scratch. **The sheet's column is authoritative once Saffron has it.**

| | rows | |
|---|---|---|
| `packs` — v4 Par × Pack Size reproduces v3's item figure exactly | 21 | adopt |
| `packs` — pack of 1, so both readings give the same number | 7 | adopt |
| **`items`** | 3 | Chalk Block (2 blocks), Water Softener Salt (10 bags), Printer Paper (2 reams) |
| **`packs`, but a change from v3 rather than a conversion** | 4 | Blue Cloth, Ice Bath Sanitiser, Wet Kit Bags, Nitrile Gloves — **confirm** |

That resolves the three implausible figures: Chalk Block 16 → **2**, Water
Softener Salt unknown → **10**, Printer Paper → **2**. **25 of 35 minimums are
now safe to sync**, up from 23, with 4 held on the `Par Unit` question and 6
simply unset because the sheet has no `Par Qty` for them.

---

## 2. The product list

**35 consumables + 33 first-aid lines**, reconciled against the 39 live
Supabase rows:

| | count | |
|---|---|---|
| live and staying | 32 | keys unchanged |
| **deactivate** | 4 | `plastic_food_bags`, `clinell_wipes`, `kleenex_tissues`, `dispenser_pumps` |
| **move to First Aid** | 3 | `blue_plasters`, `hs_refills`, `ice_packs` |
| **new rows** | 3 | `paper_printer`, `pens`, `notepads` |
| = consumables | **35** | |
| first-aid lines | 33 | 30 new + the 3 moved |

`39 − 4 − 3 + 3 = 35`. No key collides between the two tabs.

The v3 row `Sea Kelp Luxury Shampoo 5L Refill` ("no longer stock") is gone from
v4 and was never a live key, so nothing to retire.

### Keys stay as they are

Saffron: *"The names don't matter in the long run for the stock baseline we're
setting."* Right — so the `product_name_raw` slugs (`toilet_rolls`,
`blue_rolls`, …) stay exactly as they are and remain the sync key. Brand and
supplier changes move the *description*, not the key.

This matters most for the four re-branded toiletries. `hand_wash`,
`conditioner` and `moisturiser` were Sea Kelp / Futures Supplies and are now
Odyssey / Out of Eden; `sanitiser_gel` is now BioHygiene / Futures. Keeping the
keys means the 5 months of invoice history still lands on the right line —
they are the same 5L product in the same dispenser doing the same job, and it
is *consumption per week* the reset is trying to measure, not brand loyalty.

Two slugs now carry stale brand names internally (`sure_deodorant_men/women`
for an unbranded deodorant, `puly_caffe_cleaner`). They are keys, never
displayed. Leave them.

### Supplier and price changes to adopt from v4

| product | was | now |
|---|---|---|
| Hand Wash / Conditioner / Lotion | Sea Kelp, Futures, £29.12 | Odyssey, Out of Eden, £25.19 |
| Hand Sanitiser 5L | unnamed, no supplier, no price | BioHygiene, Futures Supplies, £26.98 |
| Wet Kit Bags | Newline, £48.96, pack 20 | Amazon, £12.99, pack 250 |
| Deodorant — Men / Women | no supplier, **no price** | Amazon, £10.50 |
| Nitrile Gloves (L) | Futures, pack 100 | Amazon, £3.41, pack 200 |
| Ice Bath Filters | £20.00, par 4/mo | £20.00, par 1 |

Two of these close open questions from last session outright: the **deodorant
price** now exists, and **Newline is gone**, which removes one of the two
unverified-VAT lines. Only **Concept Spa** remains unverified.

Still absent: prices for the 4 printer inks, `paper_printer`, `pens`,
`notepads`, `glade_sprays`, `key_fobs`, `urinal_shields`. The inks and fobs are
measure-only so it barely matters; the rest are cheap.

⚠ `water_softener_salt` at **£149.99** with a blank pack size is the one price
worth checking before it enters any order. Read as a per-bag price it would
dominate the whole shopping list.

---

## 3. The unit model — one unit, stated everywhere

This is the part that has broken twice. The rule:

> **Count in items. Set minimums in items. Order in packs.
> `Pack Size` is the only bridge between them, and it is written down per product.**

Concretely:

| field | unit | where it lives |
|---|---|---|
| stock count | **items** | `shop_stock_takes.actual_count` |
| minimum | **items** | `shop_product_lookup.min_stock_units` |
| usage | **items / month** | new column (see §5) |
| pack size | items per order unit | `shop_product_lookup.pack_size` |
| order quantity | **packs** | `shop_consumable_deliveries.qty_cases` |

Two guard rails, because "we decided items" was already the decision last time
and it still went wrong:

1. **The count sheet header carries the noun.** Not `Count`, but
   `Count (rolls)`, `Count (5L bottles)`, `Count (tubs)`. Generated per product
   from `count_unit` — see `unit_basis_v4.csv`, which states for all 35 products
   what a count of 1 means and what the order unit is. A count can then never
   again be recorded without its unit.
2. **Decimals are expected.** Half a 5L bottle is a real count of `0.5`.
   `actual_count` is `numeric`, so this already works.

### A live bug this exposes

`index.html` computes usage as:

```js
const usage = Number(older.actual_count) + ordersBetween - Number(newer.actual_count);
//                   ^ items                 ^ PACKS        ^ items
```

`ordersBetween` sums `qty_cases`, which is **packs**. Once counts are in items,
this adds packs to items and every measured usage figure is wrong — badly wrong
for the large packs (a delivery of 1 bin-bag pack would read as 1 bag, not 200).

**Fix: multiply `qty_cases` by `pack_size` wherever deliveries enter the
arithmetic** — the two `ordersBetween` / `ordersSince` reductions in
`computeItem()`. This must land in the same change as the unit switch, or the
first two counts will produce nonsense.

---

## 4. Names — three fields, not one

Saffron: *"Stock count sheet & consumables dashboard doesn't have to include the
brand name — these can be accounted for in the product catalogue."*

So one field becomes three:

| field | example | shown where |
|---|---|---|
| `product_name_raw` | `toilet_rolls` | nowhere — hidden key column |
| `display_name` | **Toilet Roll** | count sheet, dashboard |
| `order_link_or_desc` | `Jumbo T.Roll 2ply 2.25" Core J26300 300m` | catalogue and shopping list only |

The v4 sheet only has the long description, so **the catalogue needs a short
name column added.** All 35 are proposed in `products_v4.csv` — e.g.
`Greenspeed Techno Multi - Single 5L` → **Multi-Surface Cleaner 5L**,
`Odyssey Black Pepper & Sandalwood Shampoo & Body Wash 5L` →
**Shampoo & Body Wash 5L**, `Puly Caffe Cleaner` → **Coffee Machine Cleaner**,
`Chill Tubs Sanitiser` → **Ice Bath Sanitiser**.

Brand survives where it is the only useful identifier on the shelf, and
disappears where it is noise. The full description stays on the shopping list,
because that is where you need to know which product to actually buy.

---

## 5. Google Sheet structure

Five tabs. `Code.gs` currently expects three (`Products`, `Stock Count`,
`Order Log`) and one category.

| tab | role | who writes it |
|---|---|---|
| `Products` | the 35-line catalogue. Hidden col A = `product_name_raw`. Long description, brand, supplier, price, `Pack Size`, `Par Qty`, **`Par Unit`**, short `display_name` | Saffron, by hand |
| `Stock Count` | weekly. Rebuilt from Supabase. `Count (<unit>)` header per row | whoever counts |
| `Order Log` | every delivery, in packs | whoever orders |
| **`First Aid`** *(new)* | the 33-line first-aid catalogue | Saffron, by hand |
| **`First Aid Count`** *(new)* | quarterly. Required vs on-hand vs short | whoever counts |

### `Code.gs` changes

Small and mechanical. Today `PRODUCTS_SHEET`, `COUNT_SHEET` and `CATEGORY` are
module-level constants and `syncProducts()` reads them directly. They become
parameters:

- `syncProducts(sheet, category)`, `buildCountSheet(...)`, `submitCounts(...)`
- menu grows a *First Aid* section calling the same functions with the other pair
- `buildCountSheet` writes `Count (${count_unit})` instead of `Count (packs)`
- **`syncProducts` keeps its category-scoped deactivate**, which is what makes
  the split safe: syncing Consumables can no longer touch a First Aid row, and
  vice versa

The one genuinely dangerous line stays dangerous and needs the checked key list
before it runs:

```js
_sbSend('PATCH', 'shop_product_lookup', 'category=eq.' + CATEGORY, { active: false });
```

Run against the current sheet without a `product_name_raw` column, it would
deactivate all 39 live rows and insert 35 unrelated ones. With the hidden key
column present it does exactly the right thing — including deactivating the 4
intended drops.

---

## 6. Supabase changes

1. **Delete the junk take.**
   ```sql
   delete from shop_stock_takes
   where take_date = '2026-07-29' and source = 'sheet'
     and product_name_raw in (select product_name_raw from shop_product_lookup
                              where category = 'Consumables');
   ```
   38 rows. Scoped so the shop dashboard's own `2026-07-29` set (65 rows,
   `source='manual'`) is untouched.

2. **Add one column.**
   ```sql
   alter table shop_product_lookup add column monthly_usage_units numeric;
   ```
   Because usage is now in items and `monthly_par_packs` says *packs*. Storing
   items in a column named packs is the same class of mistake as the untyped
   `Stock` column, and it will be believed by whoever reads it next. Nullable,
   so the shop dashboard is unaffected. `monthly_par_packs` stops being read.

3. **New category `First Aid`**, `stock_tracked=false`. A separate category, not
   a subcategory, because the two have genuinely different regimes — quarterly
   vs weekly, statutory BS 8599-1 compliance vs consumption, kit-level vs
   item-level ordering. Keeping them in one category means 33 never-reordered
   rows sitting in the Consumables prediction model and in "items below par".
   Existing categories already vary `stock_tracked` (Merch and Coffee are both
   `false`), so adding one is routine.

4. **Load `deliveries_backfill.csv`** — 26 invoice lines, £1,659.59 net,
   Feb–Jul 2026, 8 products. Still valid: those orders genuinely happened and
   `orders_between` needs them. Only the *demand inference* from them was
   unsafe. Note the 3 Sea Kelp lines land on the reused `hand_wash` /
   `conditioner` / `moisturiser` keys, which is intended.

---

## 7. Dashboard changes (`index.html`)

| # | change | why |
|---|---|---|
| 1 | `qty_cases × pack_size` in both delivery reductions | the packs-vs-items bug in §3 — **required, not cosmetic** |
| 2 | read `monthly_usage_units`, drop `monthly_par_packs` | items, per §3 |
| 3 | show counts and minimums in items, with the unit label | `24 rolls`, not `24` |
| 4 | suggested order in **packs**: `ceil((order_up_to − est_on_hand) / pack_size)`, cost `× price_per_pack` | you buy packs |
| 5 | new **First Aid** tab: required / on hand / short, no reorder prediction | different regime |
| 6 | exclude `order_class = 'measure_only'` from "order now" and the shopping list | the 4 inks and key fobs go missing, they are not consumed |
| 7 | suppress a suggested order where `pack_size` is null or `min_confirmed = 'no'` | refusing to answer beats a confident wrong number |
| 8 | `CYCLE_DAYS`/`LEAD_DAYS`: lead time is **2 days, every supplier** (confirmed) | the hardcoded 7 was a guess |
| 9 | shopping list keeps the long description; everything else uses `display_name` | §4 |

Item 7 is the one to hold onto. Of 35 products, 5 have no pack size and 12 have
an unconfirmed minimum. The dashboard should show those as *"needs a pack
size"* / *"minimum unconfirmed"* rather than compute through the gap.

---

## 8. First Aid

Split off, per Saffron: separate tab, different count cadence, **not ordered
item by item**.

`first_aid_v4.csv` — 33 lines, from the 2026-08-04 four-box count:

| group | lines | what it is |
|---|---|---|
| `Required` | 15 | the BS 8599-1 required list. 14 short, **247 items** |
| `Held` | 13 | in the kits, absent from the required list. 13 count lines merged to 4 + 9 distinct items |
| `Equipment` | 3 | tourniquet, tweezers, safety scissors — check present, never reorder |
| `Order unit` | 2 | `hs_refills` (BS 8599-1 refill pack × 4) and `ice_packs` |

The merge rule is Saffron's own, derived from what she accepted and rejected:
**merge size and brand variants of one item; never merge different items.** So
four gauze sizes become one line, but crepe ≠ conforming bandage, safety
scissors ≠ clothing cutters, adhesive tape ≠ waterproof tape.

**Ordering is kit-level.** 12 separate Amazon lines to buy £4 of safety pins is
not a process anyone will follow twice. One BS 8599-1 refill pack per box is one
purchase covering most of the 247 items, and gives first aid a single sensible
order unit. Two lines stay standalone because they are the big, cheap,
consequential gaps: **blue detectable plasters** (160 short, zero on hand, and
there is a cafe on site) and **ice packs** (5 short).

Cadence: **quarterly**, aligned to the filter-change interval already in the
notes, with the plaster and ice-pack lines checked at the weekly count since
they are the ones that actually run out.

Still blocked: **no pack size or price exists for any of the 15 required
lines.** The 247-item shortfall cannot become a costed order until the kit
supplier confirms whether they sell a refill pack. That is a phone call, not a
modelling problem.

---

## 9. What this supersedes

| artefact | status |
|---|---|
| `products_tab_final.csv` | **superseded** by `products_v4.csv` — 52 rows incl. first aid, old brands, guessed pack sizes |
| `min_stock_model.csv` | **superseded**. Built on invoice-derived usage for products that no longer exist, and on 9 undecidable count bases |
| `SHOPPING-LIST.md`, `shopping_list.csv` | **dead**. Priced 15 lines at old suppliers; Newline and 3 Sea Kelp lines are gone. The reset order gets re-costed from the real count |
| `BASELINE-RESET.md` | **method still good, numbers dead.** The reset logic is the plan; £764.73 is not |
| `crosswalk.csv` | **spent.** Its job was the v2→live mapping; §2 above replaces it |
| `MINIMUM-STOCK.md` | **keep.** The reasoning survives — highest-of-candidates, burn ≠ consumption, purchase rate is a floor, explicit human requirement wins. Its *inputs* are gone |
| `FIRST-AID.md` | **keep.** The count and the grouping rule are the input to §8 |
| `deliveries_backfill.csv` | **keep and load.** Still 26 real orders |
| `migration/README.md` | findings 1, 3, 5, 6 resolved by v4; 2 and 4 still live |

Six of last session's open questions are now closed by v4 itself: deodorant
price, Newline VAT, pack sizes for 30 products, the first-aid split, the
`Cadence` column (gone), and the `Stock` column (gone).

---

## 10. Sequence

1. **Delete the 38 junk counts.** Before anything reads them.
2. **Settle the 4 `Par Unit` rows** in §1.3 and the salt price in §12.
3. **Rebuild the sheet:** `Products` from `products_v4.csv` with a hidden
   `product_name_raw` column and a `Par Unit` column; new `First Aid` tab from
   `first_aid_v4.csv`.
4. **Patch `Code.gs`** — parameterise sheet/category, unit-aware count headers.
5. **Patch `index.html`** — the `qty_cases × pack_size` fix first; it is the one
   that silently corrupts data.
6. **Add `monthly_usage_units`; create the `First Aid` category.**
7. **Run `syncProducts`** for both tabs. Verify: 35 + 33 active, and exactly the
   4 intended deactivations (confirmed intentional — §11).
8. **Wire in the 04/08/2026 count** as baseline count 1, once supplied.
9. **Load `deliveries_backfill.csv`.**
10. **Place the reset order** from the baseline count, re-costed at v4 prices.
    Log every delivery in `Order Log` — usage is
    `opening + orders_between − closing`, so an unlogged delivery makes the
    arithmetic lie.
11. **Count every Tuesday.** From count 2, measured usage replaces the estimated
    minimums, fast movers first. Expect to revise upward.

### What is readable, and when

A weekly count resolves roughly one unit, so a product moving less than one unit
a week shows nothing on a Tuesday. Toilet roll, blue roll and shampoo are
readable after one week; the 5L refills will take a quarter. That is the design,
not a fault — and it is why nothing may hit zero during the measurement window.
**A stockout reads as low consumption** and corrupts that product's baseline.
During the reset, err generous.

---

## 11. Decisions taken 2026-08-05

- **`Par Unit` becomes a column on the sheet**, per row, rather than the header
  asserting one basis for all 35. See §1.3.
- **The 4 products absent from v4 are dropped on purpose** —
  `plastic_food_bags`, `clinell_wipes`, `kleenex_tissues`, `dispenser_pumps`.
  They go inactive on the next `syncProducts` run and that is the intended
  outcome, so step 7's verification is a confirmation rather than a check for a
  mistake.
- **First aid is ordered via a BS 8599-1 refill pack.** Chase the kit supplier
  before buying any of the 15 required lines individually. The item-by-item
  costing route is explicitly not taken.
- **The 04/08/2026 count will be supplied by Saffron** and wired in as baseline
  count 1.

## 12. Still open

1. **The 04/08/2026 count itself.** Saffron has it; it is not in Supabase, v3 or
   v4. Step 8 waits on the numbers. It needs a unit per line — the count is in
   items, and `unit_basis_v4.csv` states what a count of 1 means for each of the
   35 products.
2. **The 4 `Par Unit` rows** flagged in §1.3 — Blue Cloth, Ice Bath Sanitiser,
   Wet Kit Bags, Nitrile Gloves. All read as `packs`, but each is a change from
   v3 rather than a conversion of it, so each doubles or otherwise moves the
   requirement. Held at `min_confirmed = no`.
3. **Water Softener Salt: £149.99 for what?** Pack size blank, note says
   "6 packs to fill tub". `Par Unit` is now set to `items` (10 bags), which makes
   the minimum safe, but the *price* basis still changes the shopping list by an
   order of magnitude. Do not let this line into a costed order until it is
   settled.
4. **`Microfibre Cloths` has no category** — the only blank on the sheet.
   Suggest `Staff Room`, alongside the other cleaning items.
5. **Does the kit supplier sell a BS 8599-1 refill pack?** The route is decided;
   the answer is not in yet. If they don't, §8's ordering plan needs revisiting.
6. **`Chill Tub Filters`**: v3 counted 10 (4 new, 6 old) against a par of 1, and
   the note says replace every 3 months. Is the count new filters only?
7. **Tampons and pads have a blank `Par Qty`** in v4, where v3 said 64 and 44.
   Both were in confirmed surplus, so blank probably means "don't reorder" —
   worth making explicit rather than leaving an empty cell that reads as an
   oversight. Both are zero-rated for VAT if they ever enter a costed order.
8. **Concept Spa's VAT basis** — the last unverified line, worth £15.00 of
   exposure. Newline's departure closed the other one.
