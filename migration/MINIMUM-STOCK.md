# How to work out the minimum stock

Short version: **you have already written it — it's the `Par Qty` column.** The
job is to check it against measured usage, not replace it.

## The rule

With a count every Tuesday, the minimum stock is *whatever has to last until you
next get a chance to look, plus the wait for delivery, plus a bit of slack*:

```
minimum stock (units) = daily usage x (7 + lead time + safety days)
```

- **7 days** — if an item slips past this Tuesday's count you don't get another
  look for a week.
- **lead time** — days from placing the order to it arriving.
- **safety days** — 3 normally, 7 for anything a member would notice running out
  (toilet roll, blue roll, shampoo, hand wash, sanitiser, bin bags, tampons, pads).

For most items that lands around 12–17 days of cover, i.e. **roughly two weeks'
worth**. That's the whole idea; everything below is guard rails on it.

## Why the weekly count matters more than the number

The invoice tab records four `Ran out before next order` lines — toilet roll and
blue roll, twice each. The cause is visible in the order dates:

| Jumbo T.Roll | gap | |
|---|---|---|
| 26/02 | — | 4 packs |
| 11/03 | +13d | 4 packs |
| 10/04 | +30d | 4 packs |
| 19/05 | **+39d** | 5 packs ← ran out |
| 04/06 | +16d | 4 packs ← ran out |
| 23/07 | **+49d** | 6 packs |

Orders averaged 29 days apart but ranged from 13 to 49, while each order bought
about one month of stock. The 39- and 49-day gaps were always going to empty the
cupboard.

Counting every Tuesday fixes that on its own — the worst case stops being "49
days until someone notices" and becomes "7 days". **The cadence stops being
something you set and becomes something the count produces.** You don't need the
`Cadence` column at all; it can go.

## Four inputs, take the highest

A single formula gives silly answers at both ends — 0.3 of a 5L bottle for slow
movers, and nonsense wherever the usage figure is wrong. So the minimum is the
highest of four candidates:

| Candidate | Why it's there |
|---|---|
| **Your `Par Qty`** | Your judgement about the place. It is never overridden downwards. |
| **usage × cover days** | The calculation above. Can only ever *raise* your figure. |
| **A minimum written in the notes** | e.g. D Batteries `Need to have 10 on hand`, Paper `2 on hand`, Notepads `need 1 on hand`. |
| **One pack** | You buy in packs, so a trigger below one pack is meaningless. |

Taking the highest means the calculation can catch a par that's too low, but can
never talk you *down* from a level you set on purpose.

## Does your `Par Qty` hold up?

Tested against the 7 items where the invoices give real measured usage:

| item | your Par Qty | calculated | verdict |
|---|---|---|---|
| Jumbo T.Roll | 24 rolls | 18.7 | 1.3× — safely conservative |
| 2ply Blue roll | 30 rolls | 16.7 | 1.8× — safely conservative |
| Odyssey Shampoo | 6 | 3.6 | 1.7× — safely conservative |
| Greenspeed Multi | 2 | 0.2 | calc is under one bottle; yours is the sensible one |
| Sea Kelp Hand Wash | 2 | 0.5 | as above |
| Sea Kelp Conditioner | 2 | 0.3 | as above |
| Sea Kelp Moisturiser | 3 | 0.3 | as above |

Every one is at or above the calculated minimum. Your column is sound — it just
had no way to prove it before.

## How much to order

```
order up to = minimum stock + one month of usage,  rounded up to whole packs
```

The cadence then falls out of the numbers rather than being set by hand: fast
movers land on ~30 days, slow movers on 60–150. See
`implied_order_every_days` in `min_stock_model.csv`.

## Seven usage figures that look wrong

The existing monthly par is invoice-verified for 7 products. The other 28 were
typed in by hand and several look like a **units-per-month figure entered as
packs-per-month** — multiplying by pack size gives an implausible result:

| product | stored par | implies | your Par Qty |
|---|---|---|---|
| Ice packs | 24 packs/mo | 576 ice packs/mo | (blank) |
| Tampons | 6 packs/mo | 384 tampons/mo | 64 |
| Sanitary Pads | 6 packs/mo | 264 pads/mo | 44 |
| D Batteries | 8 packs/mo | 64 batteries/mo | 8 (note says 10 on hand) |
| Water Softener Salt | 10 packs/mo | 100 bags/mo | 10 |
| Hair Bands | 1 pack/mo | 100 bands/mo | 1 |
| Chalk Block | 2 packs/mo | 16 blocks/mo | 2 |

Where that happens the model ignores the par and falls back to your `Par Qty` or
one pack, and flags the row. Nothing silently inherits a bad number — but these
seven do need a real usage figure eventually.

Bin bags is the one genuine judgement call left: 2 packs/month is 400 bags, which
is ~13 a day. Plausible for a busy gym, but it drives a minimum of 210 bags, so
worth confirming.

## Counting in individual units

Counting units rather than packs means:

- `shop_stock_takes.actual_count` becomes **units**, and every product needs
  `units_per_pack` to convert for ordering. It's known for 45 of 52; unknown for
  Pens, Notepads, Paper, and 14 first-aid lines.
- **Decimals are still fine and expected** — half a 5L bottle is a real count of
  0.5. Don't force whole numbers.
- **The existing count needs converting.** Several figures in the current `Stock`
  column are part-*packs*, not units: bin bags `0.5`, washing up liquid `0.5`,
  Puly `0.5`, paper `0.5`, Greenspeed `2.5`. Read as units, 0.5 bin bags instead
  of 100 is badly wrong. The first Tuesday count under the new scheme should be
  a fresh count, not a conversion.

## What this produces right now

Against the counts currently in the sheet, **29 of 52 products are at or below
their minimum**. That is expected on a first proper count rather than a sign the
thresholds are wrong — plenty of rows genuinely read `0`. It'll settle after a
cycle or two of ordering.

## Still needs a number from you

- **Pens** — no `Par Qty`, no pack size, no usage. The only product with nothing
  to work from.
- **Microfibre Cloths** — no category on the Stock tab.
- **The 14 first-aid lines** — `Par Qty` gives them a minimum, but with no pack
  size and no prices they can't produce an order. They're components of restock
  boxes rather than order units; consider tracking the 4 boxes as one item and
  keeping the component list as a checklist.
